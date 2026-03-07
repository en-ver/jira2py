from importlib.metadata import version

from .api import JiraAPI
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
    "JiraError",
    "JiraAuthenticationError",
    "JiraConnectionError",
    "JiraAPIError",
    "JiraNotFoundError",
    "JiraRateLimitError",
    "JiraValidationError",
]
