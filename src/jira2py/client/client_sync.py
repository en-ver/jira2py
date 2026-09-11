"""Synchronous JIRA client implementation."""

import atexit
import contextlib
import io
import logging
import math
import random
import re
import threading
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, BinaryIO, NoReturn

import httpx
from tenacity import (
    RetryCallState,
    Retrying,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from jira2py.exceptions import (
    JiraAPIError,
    JiraAuthenticationError,
    JiraConnectionError,
    JiraError,
    JiraNotFoundError,
    JiraRateLimitError,
    JiraValidationError,
)

from .credentials import JiraCredentials

logger = logging.getLogger("jira2py")

# Default HTTP client configuration
_DEFAULT_TIMEOUT = 30.0
_DEFAULT_CONNECT_TIMEOUT = 10.0
_DEFAULT_POOL_TIMEOUT = 5.0
_DEFAULT_MAX_KEEPALIVE_CONNECTIONS = 20
_DEFAULT_MAX_CONNECTIONS = 50
_DEFAULT_KEEPALIVE_EXPIRY = 30.0

# Default retry configuration (per Atlassian official documentation)
_DEFAULT_MAX_RETRIES = 4
_DEFAULT_INITIAL_RETRY_DELAY = 5.0
_DEFAULT_MAX_RETRY_DELAY = 30.0
_DEFAULT_JITTER_RANGE = (0.7, 1.3)

# HTTP header and status code constants
_HEADER_RETRY_AFTER = "Retry-After"
_HEADER_RATELIMIT_REASON = "RateLimit-Reason"
_STATUS_RATE_LIMITED = 429
_BOUNDED_CONTENT_CHUNK_SIZE = 64 * 1024
_ATTACHMENT_TRANSFER_CHUNK_SIZE = 64 * 1024
_CONTENT_RANGE_RE = re.compile(r"(?i:bytes)[ \t]+([0-9]+)-([0-9]+)/([0-9]+)")


@dataclass(slots=True)
class _BoundedJiraContent:
    """Private, validated Jira-host content retained only in memory."""

    body: io.BytesIO
    complete: bool


class _RedirectResponseError(Exception):
    """Sanitized private redirect failure used only to drive 429 retries."""

    def __init__(self, status_code: int, retry_after: float | None = None) -> None:
        self.status_code = status_code
        self.retry_after = retry_after
        super().__init__(status_code, retry_after)


class _RedirectTransportError(Exception):
    """Sanitized private redirect transport failure."""


class _BoundedContentResponseError(Exception):
    """Sanitized private bounded-content response failure."""

    def __init__(self, status_code: int, retry_after: float | None = None) -> None:
        self.status_code = status_code
        self.retry_after = retry_after
        super().__init__(status_code, retry_after)


class _BoundedContentTransportError(Exception):
    """Sanitized private bounded-content transport failure."""


class _BoundedContentProtocolError(Exception):
    """Sanitized private bounded-content protocol failure."""


class _AttachmentTransferResponseError(Exception):
    """Sanitized private streaming-transfer response failure."""

    def __init__(self, status_code: int, retry_after: float | None = None) -> None:
        self.status_code = status_code
        self.retry_after = retry_after
        super().__init__(status_code, retry_after)


class _AttachmentTransferTransportError(Exception):
    """Sanitized private streaming-transfer transport failure."""


class _AttachmentTransferProtocolError(Exception):
    """Sanitized private streaming-transfer validation failure."""


class _AttachmentTransferDestinationError(Exception):
    """Sanitized private streaming-transfer destination failure."""


def _create_httpx_client(credentials: JiraCredentials) -> httpx.Client:
    """Create an httpx.Client configured for the JIRA API.

    Args:
        credentials: JIRA authentication credentials.

    Returns:
        httpx.Client instance with connection pooling, timeouts, and auth.
    """
    return httpx.Client(
        base_url=f"{credentials.url}/rest/api/3",
        headers={"Accept": "application/json"},
        auth=httpx.BasicAuth(credentials.username, credentials.api_token),
        limits=httpx.Limits(
            max_keepalive_connections=_DEFAULT_MAX_KEEPALIVE_CONNECTIONS,
            max_connections=_DEFAULT_MAX_CONNECTIONS,
            keepalive_expiry=_DEFAULT_KEEPALIVE_EXPIRY,
        ),
        timeout=httpx.Timeout(
            _DEFAULT_TIMEOUT,
            connect=_DEFAULT_CONNECT_TIMEOUT,
            pool=_DEFAULT_POOL_TIMEOUT,
        ),
        http2=True,
    )


class JiraClientSync:
    """Synchronous JIRA client.

    Provides synchronous HTTP requests to the JIRA API with connection pooling
    and automatic retry with exponential backoff on rate limit (429) responses.

    Args:
        credentials: JIRA authentication credentials.
        max_retries: Maximum number of retries on 429 responses. Set to 0 to disable.
        max_retry_delay: Maximum delay in seconds between retries.
    """

    # Class-level storage for shared persistent clients
    _class_persistent_clients: dict[str, httpx.Client] = {}
    _clients_lock = threading.Lock()

    def __init__(
        self,
        credentials: JiraCredentials,
        max_retries: int = _DEFAULT_MAX_RETRIES,
        max_retry_delay: float = _DEFAULT_MAX_RETRY_DELAY,
    ) -> None:
        """Initialize the synchronous client.

        Args:
            credentials: JIRA authentication credentials.
            max_retries: Maximum number of retries on 429 responses. Set to 0 to disable.
            max_retry_delay: Maximum delay in seconds between retries.
        """
        self.credentials = credentials
        self._max_retries = max_retries
        self._max_retry_delay = max_retry_delay
        self._client_key = (
            f"{credentials.url}:{credentials.username}:{credentials.api_token}"
        )
        self._backoff = wait_exponential(
            multiplier=_DEFAULT_INITIAL_RETRY_DELAY,
            min=_DEFAULT_INITIAL_RETRY_DELAY,
            max=float("inf"),
        )

    def _get_persistent_client(self) -> httpx.Client:
        """Get or create a persistent HTTP client for connection pooling.

        Uses double-checked locking for thread safety.

        Returns:
            The persistent HTTP client instance.
        """
        if self._client_key not in self._class_persistent_clients:
            with self._clients_lock:
                if self._client_key not in self._class_persistent_clients:
                    self._class_persistent_clients[self._client_key] = (
                        _create_httpx_client(self.credentials)
                    )
        return self._class_persistent_clients[self._client_key]

    def _request_jira(
        self,
        method: str,
        context_path: str,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        *,
        extra_params: Mapping[str, Any] | None = None,
        extra_data: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        files: Any | None = None,
        follow_redirects: bool = False,
    ) -> dict[str, Any] | list[dict[str, Any]] | None:
        """Make a synchronous request to the JIRA API.

        Automatically retries on HTTP 429 (rate limit) responses with exponential
        backoff and jitter, respecting the ``Retry-After`` header when present.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            context_path: API endpoint path (without leading slash).
            params: Query parameters.
            data: Request body data.
            extra_params: Additional query parameters. Keys in extra_params take priority
                over named parameters and can be used to override or extend them.
            extra_data: Additional body data. Keys in extra_data take priority over named
                data parameters and can be used to override or extend them.
            headers: Optional request headers to merge into the request.
            files: Optional multipart file payload for uploads.
            follow_redirects: Whether to follow HTTP redirects for this request.

        Returns:
            Response data as dict, list, or None for empty responses.
        """
        response = self._send_jira_request(
            method=method,
            context_path=context_path,
            params=params,
            data=data,
            extra_params=extra_params,
            extra_data=extra_data,
            headers=headers,
            files=files,
            follow_redirects=follow_redirects,
        )
        return self._handle_response(response)

    def _request_jira_stream_to(
        self,
        *,
        context_path: str,
        destination: BinaryIO,
        max_bytes: int,
        expected_size: int | None,
        params: dict[str, Any] | None = None,
        extra_params: Mapping[str, Any] | None = None,
        follow_redirects: bool,
    ) -> int:
        """Stream Jira attachment bytes to a caller-owned binary destination."""
        if isinstance(max_bytes, bool) or not isinstance(max_bytes, int):
            raise TypeError("max_bytes must be an integer")
        if max_bytes < 1:
            raise ValueError("max_bytes must be at least 1")
        if expected_size is not None:
            if isinstance(expected_size, bool) or not isinstance(expected_size, int):
                raise TypeError("expected_size must be an integer or None")
            if expected_size < 0:
                raise ValueError("expected_size must not be negative")
            if expected_size > max_bytes:
                raise ValueError("expected_size must not exceed max_bytes")

        merged_params = {
            key: value
            for key, value in {**(params or {}), **(extra_params or {})}.items()
            if value is not None
        }
        request_kwargs: dict[str, Any] = {"follow_redirects": follow_redirects}
        if merged_params:
            request_kwargs["params"] = merged_params

        status_code: int | None = None
        retry_after: float | None = None
        connection_error: str | None = None
        protocol_error = False
        destination_error = False
        try:
            for attempt in Retrying(
                stop=stop_after_attempt(self._max_retries + 1),
                wait=self._wait_for_retry,
                retry=retry_if_exception(self._is_retryable),
                before_sleep=self._log_retry,
                reraise=True,
            ):
                with attempt:
                    status_code = None
                    retry_after = None
                    connection_error = None
                    protocol_error = False
                    destination_error = False
                    observed = 0
                    try:
                        with self._get_persistent_client().stream(
                            "GET", context_path, **request_kwargs
                        ) as response:
                            try:
                                status_code = response.status_code
                                if status_code == _STATUS_RATE_LIMITED:
                                    retry_after = self._parse_retry_after(
                                        response.headers.get(_HEADER_RETRY_AFTER)
                                    )
                                elif status_code == 200:
                                    chunk: bytes | None = None
                                    try:
                                        for chunk in response.iter_bytes(
                                            chunk_size=_ATTACHMENT_TRANSFER_CHUNK_SIZE
                                        ):
                                            if not isinstance(chunk, bytes):
                                                protocol_error = True
                                                break
                                            next_observed = observed + len(chunk)
                                            if next_observed > max_bytes or (
                                                expected_size is not None
                                                and next_observed > expected_size
                                            ):
                                                protocol_error = True
                                                break
                                            try:
                                                self._write_attachment_chunk(
                                                    destination, chunk
                                                )
                                            except Exception:
                                                destination_error = True
                                                break
                                            observed = next_observed
                                    except httpx.HTTPError as error:
                                        self._scrub_redirect_transport_request(error)
                                        connection_error = "Network error."
                                        del error
                                    except Exception:
                                        connection_error = "Network error."
                                    finally:
                                        chunk = None
                                    if (
                                        expected_size is not None
                                        and observed != expected_size
                                    ):
                                        protocol_error = True
                                elif 200 <= status_code < 400:
                                    protocol_error = True
                            finally:
                                del response
                    except httpx.TimeoutException as error:
                        connection_error = "Request timed out."
                        self._scrub_redirect_transport_request(error)
                        del error
                    except httpx.TransportError as error:
                        connection_error = "Network error."
                        self._scrub_redirect_transport_request(error)
                        del error
                    except httpx.HTTPError as error:
                        connection_error = "HTTP error occurred."
                        self._scrub_redirect_transport_request(error)
                        del error

                    if connection_error is not None:
                        raise _AttachmentTransferTransportError(connection_error)
                    if status_code == _STATUS_RATE_LIMITED:
                        raise _AttachmentTransferResponseError(status_code, retry_after)
                    if status_code is not None and status_code >= 400:
                        raise _AttachmentTransferResponseError(status_code, retry_after)
                    if destination_error:
                        raise _AttachmentTransferDestinationError()
                    if protocol_error:
                        raise _AttachmentTransferProtocolError()
                    if status_code == 200:
                        return observed
                    raise _AttachmentTransferProtocolError()
        except _AttachmentTransferResponseError as error:
            status_code = error.status_code
            retry_after = error.retry_after
            del error
        except _AttachmentTransferTransportError as error:
            connection_error = str(error)
            del error
        except _AttachmentTransferProtocolError as error:
            del error
            protocol_error = True
        except _AttachmentTransferDestinationError as error:
            del error
            destination_error = True

        del merged_params
        del request_kwargs
        del context_path
        del params
        del extra_params

        if connection_error is not None:
            raise JiraConnectionError(connection_error)
        if status_code is not None and status_code >= 400:
            self._raise_content_status_error(status_code, retry_after)
        if destination_error:
            raise JiraError("Failed to write attachment content to destination.")
        if protocol_error:
            raise JiraError("Jira attachment content response failed validation.")
        raise JiraError(
            "Unexpected error: attachment content request completed without a response"
        )

    @staticmethod
    def _write_attachment_chunk(destination: BinaryIO, chunk: bytes) -> None:
        """Write a complete chunk, rejecting short or non-progressing writes."""
        offset = 0
        while offset < len(chunk):
            written = destination.write(chunk[offset:])
            if (
                isinstance(written, bool)
                or not isinstance(written, int)
                or written < 1
                or written > len(chunk) - offset
            ):
                raise OSError("Binary destination did not accept attachment bytes")
            offset += written

    def _request_jira_bounded_content(
        self,
        *,
        context_path: str,
        expected_size: int,
        max_bytes: int,
        byte_range: tuple[int, int] | None = None,
    ) -> _BoundedJiraContent:
        """Read authenticated Jira-host content under a strict byte contract.

        This is intentionally private: public attachment downloads instead use the
        separate redirect-following streaming transfer contract.
        """
        if (
            isinstance(expected_size, bool)
            or not isinstance(expected_size, int)
            or expected_size < 1
            or isinstance(max_bytes, bool)
            or not isinstance(max_bytes, int)
            or max_bytes < 1
        ):
            raise JiraError("Invalid private attachment content bounds")
        if byte_range is not None:
            start, end = byte_range
            if (
                isinstance(start, bool)
                or isinstance(end, bool)
                or not isinstance(start, int)
                or not isinstance(end, int)
                or start != 0
                or end < start
                or end >= expected_size
                or end - start + 1 > max_bytes
            ):
                raise JiraError("Invalid private attachment byte range")
        elif expected_size > max_bytes:
            raise JiraError("Invalid private attachment content bounds")

        headers = {
            "Accept": "*/*",
            "Accept-Encoding": "identity",
        }
        if byte_range is not None:
            headers["Range"] = f"bytes={byte_range[0]}-{byte_range[1]}"
        request_kwargs: dict[str, Any] = {
            "params": {"redirect": "false"},
            "headers": headers,
            "follow_redirects": False,
        }

        status_code: int | None = None
        retry_after: float | None = None
        connection_error: str | None = None
        protocol_error = False
        content: _BoundedJiraContent | None = None
        try:
            for attempt in Retrying(
                stop=stop_after_attempt(self._max_retries + 1),
                wait=self._wait_for_retry,
                retry=retry_if_exception(self._is_retryable),
                before_sleep=self._log_retry,
                reraise=True,
            ):
                with attempt:
                    status_code = None
                    retry_after = None
                    protocol_error = False
                    connection_error = None
                    body: io.BytesIO | None = None
                    try:
                        with self._get_persistent_client().stream(
                            "GET", context_path, **request_kwargs
                        ) as response:
                            try:
                                status_code = response.status_code
                                if status_code == _STATUS_RATE_LIMITED:
                                    retry_after = self._parse_retry_after(
                                        response.headers.get(_HEADER_RETRY_AFTER)
                                    )
                                elif status_code in {200, 206}:
                                    contract = self._bounded_content_contract(
                                        response.headers,
                                        status_code=status_code,
                                        expected_size=expected_size,
                                        max_bytes=max_bytes,
                                        byte_range=byte_range,
                                    )
                                    if contract is None:
                                        protocol_error = True
                                    else:
                                        expected_length, complete = contract
                                        body = io.BytesIO()
                                        received = 0
                                        chunk: bytes | None = None
                                        try:
                                            for chunk in response.iter_raw(
                                                chunk_size=_BOUNDED_CONTENT_CHUNK_SIZE
                                            ):
                                                if not isinstance(chunk, bytes):
                                                    protocol_error = True
                                                    break
                                                next_received = received + len(chunk)
                                                if next_received > expected_length:
                                                    protocol_error = True
                                                    break
                                                body.write(chunk)
                                                received = next_received
                                        except Exception as error:
                                            if isinstance(error, httpx.HTTPError):
                                                self._scrub_redirect_transport_request(
                                                    error
                                                )
                                            connection_error = "Network error."
                                            del error
                                        chunk = None
                                        if received != expected_length:
                                            protocol_error = True
                                        if (
                                            protocol_error
                                            or connection_error is not None
                                        ):
                                            body.close()
                                            del body
                                            body = None
                                        else:
                                            body.seek(0)
                                            content = _BoundedJiraContent(
                                                body, complete
                                            )
                                            body = None
                                else:
                                    protocol_error = 200 <= status_code < 400
                            finally:
                                del response
                    except httpx.TimeoutException as error:
                        connection_error = "Request timed out."
                        self._scrub_redirect_transport_request(error)
                        del error
                    except httpx.TransportError as error:
                        connection_error = "Network error."
                        self._scrub_redirect_transport_request(error)
                        del error
                    except httpx.HTTPError as error:
                        connection_error = "HTTP error occurred."
                        self._scrub_redirect_transport_request(error)
                        del error

                    if connection_error is not None:
                        raise _BoundedContentTransportError(connection_error)
                    if status_code == _STATUS_RATE_LIMITED:
                        raise _BoundedContentResponseError(status_code, retry_after)
                    if status_code is not None and status_code >= 400:
                        raise _BoundedContentResponseError(status_code, retry_after)
                    if protocol_error:
                        raise _BoundedContentProtocolError()
                    if content is not None:
                        return content
                    raise _BoundedContentProtocolError()
        except _BoundedContentResponseError as error:
            status_code = error.status_code
            retry_after = error.retry_after
            del error
        except _BoundedContentTransportError as error:
            connection_error = str(error)
            del error
        except _BoundedContentProtocolError as error:
            del error
            raise JiraError(
                "Jira attachment content response failed validation."
            ) from None

        del headers
        del request_kwargs
        del context_path
        del byte_range

        if connection_error is not None:
            raise JiraConnectionError(connection_error)
        if status_code is not None:
            self._raise_content_status_error(status_code, retry_after)
        raise JiraError(
            "Unexpected error: bounded content request completed without a response"
        )

    @staticmethod
    def _bounded_content_contract(
        headers: httpx.Headers,
        *,
        status_code: int,
        expected_size: int,
        max_bytes: int,
        byte_range: tuple[int, int] | None,
    ) -> tuple[int, bool] | None:
        """Validate headers without retaining a response or its untrusted body."""
        encoding_values = headers.get_list("content-encoding")
        try:
            if encoding_values and (
                len(encoding_values) != 1
                or encoding_values[0].strip().casefold() != "identity"
            ):
                return None
        finally:
            encoding_values.clear()
            del encoding_values

        range_values = headers.get_list("content-range")
        length_values = headers.get_list("content-length")
        try:
            if status_code == 200:
                if range_values:
                    return None
                response_length = expected_size
                complete = True
            else:
                if byte_range is None or len(range_values) != 1:
                    return None
                matched = _CONTENT_RANGE_RE.fullmatch(range_values[0].strip())
                if matched is None:
                    return None
                start, end, total = (
                    JiraClientSync._header_decimal(value) for value in matched.groups()
                )
                if (
                    start is None
                    or end is None
                    or total is None
                    or start != byte_range[0]
                    or end != byte_range[1]
                    or end < start
                    or total != expected_size
                ):
                    return None
                response_length = end - start + 1
                complete = start == 0 and end == expected_size - 1

            if response_length > max_bytes:
                return None
            if length_values:
                if len(length_values) != 1:
                    return None
                content_length = JiraClientSync._header_decimal(length_values[0])
                if content_length != response_length:
                    return None
            return response_length, complete
        finally:
            range_values.clear()
            length_values.clear()
            del range_values
            del length_values

    @staticmethod
    def _header_decimal(value: str) -> int | None:
        """Parse one safe non-negative decimal HTTP header value."""
        value = value.strip()
        if not value or not value.isascii() or not value.isdecimal():
            return None
        try:
            return int(value)
        except ValueError:
            return None

    @staticmethod
    def _raise_content_status_error(
        status_code: int, retry_after: float | None
    ) -> NoReturn:
        """Raise a typed attachment-content status error without a response."""
        if status_code == 401:
            raise JiraAuthenticationError(
                "Authentication failed. Check your credentials.",
                status_code=status_code,
                response=None,
                error_messages=[],
            )
        if status_code == 403:
            raise JiraAuthenticationError(
                "Access forbidden. You don't have permission to access this resource.",
                status_code=status_code,
                response=None,
                error_messages=[],
            )
        if status_code == 404:
            raise JiraNotFoundError(
                "Resource not found.",
                status_code=status_code,
                response=None,
                error_messages=[],
            )
        if status_code == _STATUS_RATE_LIMITED:
            raise JiraRateLimitError(
                "API rate limit exceeded.",
                status_code=status_code,
                response=None,
                error_messages=[],
                retry_after=retry_after,
            )
        if status_code == 400:
            raise JiraValidationError(
                "Request validation failed. Check your input data.",
                status_code=status_code,
                response=None,
                error_messages=[],
            )
        if 400 <= status_code < 500:
            raise JiraAPIError(
                f"Client error: {status_code}",
                status_code=status_code,
                response=None,
                error_messages=[],
            )
        if status_code >= 500:
            raise JiraAPIError(
                f"Server error: {status_code}",
                status_code=status_code,
                response=None,
                error_messages=[],
            )
        raise JiraError("Jira attachment content response failed validation.")

    def _request_jira_redirect_location(
        self,
        method: str,
        context_path: str,
        params: dict[str, Any] | None = None,
        *,
        extra_params: Mapping[str, Any] | None = None,
    ) -> str:
        """Get one Jira attachment redirect target without reading or following it.

        This private seam intentionally performs a headers-only request.  It is used
        only to identify Jira-managed attachment media; public attachment downloads
        separately follow redirects while streaming to caller-owned destinations.
        """
        merged_params = {
            key: value
            for key, value in {**(params or {}), **(extra_params or {})}.items()
            if value is not None
        }
        request_kwargs: dict[str, Any] = {"follow_redirects": False}
        if merged_params:
            request_kwargs["params"] = merged_params

        redirect_status_code: int | None = None
        redirect_retry_after: float | None = None
        connection_error: str | None = None
        try:
            for attempt in Retrying(
                stop=stop_after_attempt(self._max_retries + 1),
                wait=self._wait_for_retry,
                retry=retry_if_exception(self._is_retryable),
                before_sleep=self._log_retry,
                reraise=True,
            ):
                with attempt:
                    location: str | None = None
                    retry_after: float | None = None
                    transport_error: str | None = None
                    try:
                        with self._get_persistent_client().stream(
                            method, context_path, **request_kwargs
                        ) as response:
                            try:
                                status_code = response.status_code
                                if status_code == 303:
                                    locations = response.headers.get_list("location")
                                    try:
                                        if len(locations) == 1 and locations[0]:
                                            location = locations[0]
                                    finally:
                                        locations.clear()
                                        del locations
                                elif status_code == _STATUS_RATE_LIMITED:
                                    retry_after = self._parse_retry_after(
                                        response.headers.get(_HEADER_RETRY_AFTER)
                                    )
                            finally:
                                del response
                    except httpx.TimeoutException as error:
                        location = None
                        transport_error = "Request timed out."
                        self._scrub_redirect_transport_request(error)
                        del error
                    except httpx.TransportError as error:
                        location = None
                        transport_error = "Network error."
                        self._scrub_redirect_transport_request(error)
                        del error
                    except httpx.HTTPError as error:
                        location = None
                        transport_error = "HTTP error occurred."
                        self._scrub_redirect_transport_request(error)
                        del error
                    except Exception:
                        location = None
                        raise

                    if transport_error is not None:
                        raise _RedirectTransportError(transport_error)
                    if location is not None:
                        return location
                    raise _RedirectResponseError(status_code, retry_after)
        except _RedirectResponseError as error:
            redirect_status_code = error.status_code
            redirect_retry_after = error.retry_after
            del error
        except _RedirectTransportError as error:
            connection_error = str(error)
            del error

        del merged_params
        del request_kwargs
        del method
        del context_path
        del params
        del extra_params

        if redirect_status_code is not None:
            self._raise_redirect_status_error(
                redirect_status_code, redirect_retry_after
            )
        if connection_error is not None:
            raise JiraConnectionError(connection_error)
        raise JiraError(
            "Unexpected error: redirect request completed without a response"
        )

    def _send_jira_request(
        self,
        method: str,
        context_path: str,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        *,
        extra_params: Mapping[str, Any] | None = None,
        extra_data: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        files: Any | None = None,
        follow_redirects: bool = False,
    ) -> httpx.Response:
        """Make a synchronous request to the JIRA API and return the raw response."""
        # Merge parameters; strip None from query params (httpx sends None as "None")
        # extra_params takes priority over params (later keys win in dict merge)
        merged_params = {
            k: v
            for k, v in {**(params or {}), **(extra_params or {})}.items()
            if v is not None
        }
        # Preserve None in body data (serialized as JSON null, needed to clear fields)
        # extra_data takes priority over data (later keys win in dict merge)
        merged_data = {**(data or {}), **(extra_data or {})}

        request_kwargs: dict[str, Any] = {"follow_redirects": follow_redirects}
        if merged_params:
            request_kwargs["params"] = merged_params
        if headers:
            request_kwargs["headers"] = dict(headers)
        if files is not None:
            request_kwargs["files"] = files
            if merged_data:
                request_kwargs["data"] = merged_data
        elif merged_data:
            request_kwargs["json"] = merged_data

        client = self._get_persistent_client()
        response: httpx.Response | None = None

        try:
            for attempt in Retrying(
                stop=stop_after_attempt(self._max_retries + 1),
                wait=self._wait_for_retry,
                retry=retry_if_exception(self._is_retryable),
                before_sleep=self._log_retry,
                reraise=True,
            ):
                with attempt:
                    response = client.request(method, context_path, **request_kwargs)
                    response.raise_for_status()
        except Exception as e:
            self._handle_error(e)

        if response is None:
            raise JiraError("Unexpected error: request completed without a response")
        return response

    @staticmethod
    def _is_retryable(error: BaseException) -> bool:
        """Check if an error is retryable (HTTP 429 only)."""
        return (
            isinstance(error, httpx.HTTPStatusError)
            and error.response.status_code == _STATUS_RATE_LIMITED
        ) or (
            isinstance(
                error,
                (
                    _RedirectResponseError,
                    _BoundedContentResponseError,
                    _AttachmentTransferResponseError,
                ),
            )
            and error.status_code == _STATUS_RATE_LIMITED
        )

    @staticmethod
    def _scrub_redirect_transport_request(error: httpx.HTTPError) -> None:
        """Remove the ephemeral request from a private redirect transport failure."""
        request = getattr(error, "_request", None)
        if isinstance(request, httpx.Request):
            request.headers.clear()
        del request
        with contextlib.suppress(AttributeError):
            delattr(error, "_request")

    @staticmethod
    def _parse_retry_after(value: str | None) -> float | None:
        """Return a usable Retry-After value without retaining its raw header."""
        if not value:
            return None
        with contextlib.suppress(ValueError, OverflowError):
            retry_after = float(value)
            if math.isfinite(retry_after) and retry_after >= 0:
                return retry_after
        return None

    @staticmethod
    def _raise_redirect_status_error(
        status_code: int, retry_after: float | None
    ) -> NoReturn:
        """Raise a public error using only sanitized redirect response metadata."""
        if status_code == 303:
            raise JiraError(
                "Attachment content redirect did not provide one Location header"
            )
        if status_code == 401:
            raise JiraAuthenticationError(
                "Authentication failed. Check your credentials.",
                status_code=status_code,
                response=None,
                error_messages=[],
            )
        if status_code == 403:
            raise JiraAuthenticationError(
                "Access forbidden. You don't have permission to access this resource.",
                status_code=status_code,
                response=None,
                error_messages=[],
            )
        if status_code == 404:
            raise JiraNotFoundError(
                "Resource not found.",
                status_code=status_code,
                response=None,
                error_messages=[],
            )
        if status_code == _STATUS_RATE_LIMITED:
            raise JiraRateLimitError(
                "API rate limit exceeded.",
                status_code=status_code,
                response=None,
                error_messages=[],
                retry_after=retry_after,
            )
        if status_code == 400:
            raise JiraValidationError(
                "Request validation failed. Check your input data.",
                status_code=status_code,
                response=None,
                error_messages=[],
            )
        if 400 <= status_code < 500:
            raise JiraAPIError(
                f"Client error: {status_code}",
                status_code=status_code,
                response=None,
                error_messages=[],
            )
        if status_code >= 500:
            raise JiraAPIError(
                f"Server error: {status_code}",
                status_code=status_code,
                response=None,
                error_messages=[],
            )
        raise JiraError("Attachment content redirect did not return HTTP 303")

    def _wait_for_retry(self, retry_state: RetryCallState) -> float:
        """Calculate wait time for retry, respecting Retry-After header.

        Follows Atlassian's official retry strategy:
        - Use Retry-After header value when present
        - Fall back to exponential backoff: initial_delay * 2^(attempt-1)
        - Apply jitter to avoid thundering herd
        - Cap at max_retry_delay

        When the server provides a Retry-After header, jitter is applied only
        *above* the server-specified minimum (additive, 0–30%) to respect the
        minimum wait. For exponential backoff, multiplicative jitter (0.7x–1.3x)
        is used. The exponential base is computed via ``tenacity.wait_exponential``.
        """
        wait = self._backoff(retry_state)
        has_retry_after = False

        exc = retry_state.outcome.exception() if retry_state.outcome else None
        retry_after = None
        if isinstance(exc, httpx.HTTPStatusError):
            retry_after = self._parse_retry_after(
                exc.response.headers.get(_HEADER_RETRY_AFTER)
            )
        elif isinstance(
            exc,
            (
                _RedirectResponseError,
                _BoundedContentResponseError,
                _AttachmentTransferResponseError,
            ),
        ):
            retry_after = exc.retry_after
        if retry_after is not None:
            wait = retry_after
            has_retry_after = True

        if has_retry_after:
            # Additive jitter above the server minimum (0–30%)
            wait += random.uniform(0, wait * 0.3)  # noqa: S311
        else:
            # Multiplicative jitter for exponential backoff
            jitter = random.uniform(*_DEFAULT_JITTER_RANGE)  # noqa: S311
            wait *= jitter

        return min(wait, self._max_retry_delay)

    @staticmethod
    def _log_retry(retry_state: RetryCallState) -> None:
        """Log retry attempts at WARNING level."""
        exc = retry_state.outcome.exception() if retry_state.outcome else None
        retry_after = None
        reason = None
        if isinstance(exc, httpx.HTTPStatusError):
            retry_after = exc.response.headers.get(_HEADER_RETRY_AFTER)
            reason = exc.response.headers.get(_HEADER_RATELIMIT_REASON)
        elif isinstance(
            exc,
            (
                _RedirectResponseError,
                _BoundedContentResponseError,
                _AttachmentTransferResponseError,
            ),
        ):
            retry_after = exc.retry_after

        logger.warning(
            "Rate limited by Jira (attempt %d). reason=%s, retry_after=%s",
            retry_state.attempt_number,
            reason,
            retry_after,
        )

    @staticmethod
    def _handle_response(
        response: httpx.Response,
    ) -> dict[str, Any] | list[dict[str, Any]] | None:
        """Handle HTTP response and extract JSON data.

        Args:
            response: HTTP response object.

        Returns:
            Parsed JSON response as dict or list, or None for
            responses with no content (e.g., 204 No Content).

        Raises:
            ValueError: If response has content that cannot be parsed as JSON.
        """
        if response.status_code == 204 or not response.content:
            return None
        try:
            return response.json()
        except Exception as e:
            raise ValueError(f"Failed to parse response as JSON: {e}") from e

    def _extract_error_messages(self, response: httpx.Response) -> list[str]:
        """Extract error messages from JIRA API response.

        Accumulates messages from all error fields in the Jira Error Collection
        schema (``errorMessages``, ``errors``, ``message``). Jira always includes
        both ``errorMessages`` and ``errors`` in error responses, and either or
        both may contain content. Only JSON/encoding parse errors (ValueError,
        UnicodeDecodeError) are suppressed; programming errors propagate.

        Args:
            response: httpx.Response object.

        Returns:
            List of error message strings.
        """
        try:
            data = response.json()
        except (ValueError, UnicodeDecodeError):
            return []

        if not isinstance(data, dict):
            return []

        messages: list[str] = []

        if isinstance(data.get("errorMessages"), list):
            messages.extend(data["errorMessages"])

        if isinstance(data.get("errors"), dict):
            messages.extend(str(v) for v in data["errors"].values())

        if "message" in data:
            messages.append(data["message"])

        return messages

    def _handle_error(self, error: Exception) -> NoReturn:
        """Handle HTTP errors and convert to appropriate jira2py exceptions.

        Args:
            error: The original exception from httpx.

        Raises:
            JiraAuthenticationError: For 401/403 responses.
            JiraNotFoundError: For 404 responses.
            JiraRateLimitError: For 429 responses.
            JiraValidationError: For 400 responses.
            JiraAPIError: For other 4xx/5xx responses.
            JiraConnectionError: For transport/timeout errors.
            JiraError: For any other errors.
        """
        if isinstance(error, httpx.HTTPStatusError):
            response = error.response
            status_code = response.status_code
            error_messages = self._extract_error_messages(response)

            if status_code == 401:
                raise JiraAuthenticationError(
                    "Authentication failed. Check your credentials.",
                    status_code=401,
                    response=response,
                    error_messages=error_messages,
                ) from error

            if status_code == 403:
                raise JiraAuthenticationError(
                    "Access forbidden. You don't have permission to access this resource.",
                    status_code=403,
                    response=response,
                    error_messages=error_messages,
                ) from error

            if status_code == 404:
                raise JiraNotFoundError(
                    "Resource not found.",
                    status_code=status_code,
                    response=response,
                    error_messages=error_messages,
                ) from error

            if status_code == _STATUS_RATE_LIMITED:
                retry_after = self._parse_retry_after(
                    response.headers.get(_HEADER_RETRY_AFTER)
                )

                raise JiraRateLimitError(
                    "API rate limit exceeded.",
                    status_code=status_code,
                    response=response,
                    error_messages=error_messages,
                    retry_after=retry_after,
                    rate_limit_reason=response.headers.get(_HEADER_RATELIMIT_REASON),
                    reset_at=response.headers.get("X-RateLimit-Reset"),
                ) from error

            if status_code == 400:
                raise JiraValidationError(
                    "Request validation failed. Check your input data.",
                    status_code=status_code,
                    response=response,
                    error_messages=error_messages,
                ) from error

            if 400 <= status_code < 500:
                raise JiraAPIError(
                    f"Client error: {status_code}",
                    status_code=status_code,
                    response=response,
                    error_messages=error_messages,
                ) from error

            if status_code >= 500:
                raise JiraAPIError(
                    f"Server error: {status_code}",
                    status_code=status_code,
                    response=response,
                    error_messages=error_messages,
                ) from error

        if isinstance(error, httpx.TimeoutException):
            raise JiraConnectionError(
                f"Request timed out: {error}",
            ) from error

        if isinstance(error, httpx.TransportError):
            raise JiraConnectionError(
                f"Network error: {error}",
            ) from error

        if isinstance(error, httpx.HTTPError):
            raise JiraError(
                f"HTTP error occurred: {error}",
            ) from error

        raise JiraError(
            f"Unexpected error: {error}",
        ) from error

    @classmethod
    def close_all(cls) -> None:
        """Close all persistent clients and release resources."""
        with cls._clients_lock:
            for client in cls._class_persistent_clients.values():
                try:
                    client.close()
                except Exception:
                    logger.debug(
                        "Failed to close HTTP client during cleanup", exc_info=True
                    )
            cls._class_persistent_clients.clear()


# Register cleanup on interpreter exit
atexit.register(JiraClientSync.close_all)
