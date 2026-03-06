from importlib.metadata import version

from .api import JiraAPI, JiraAPIAsync
from .exceptions import (
    JiraAPIError,
    JiraAuthenticationError,
    JiraConnectionError,
    JiraError,
    JiraNotFoundError,
    JiraRateLimitError,
    JiraValidationError,
)

__version__ = version("jira2py")

__all__ = [
    "JiraAPI",
    "JiraAPIAsync",
    "JiraError",
    "JiraAuthenticationError",
    "JiraConnectionError",
    "JiraAPIError",
    "JiraNotFoundError",
    "JiraRateLimitError",
    "JiraValidationError",
]
