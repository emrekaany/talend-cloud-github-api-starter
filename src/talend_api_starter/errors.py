"""Public, deliberately low-detail error types.

Remote response bodies and request headers are never included in these errors.
That keeps an upstream echo, proxy diagnostic, or PAT out of terminal output.
"""

from __future__ import annotations

from dataclasses import dataclass


class StarterError(Exception):
    """Base class for expected, user-safe failures."""


class ConfigurationError(StarterError):
    """Raised when required environment configuration is absent or invalid."""


class ValidationError(StarterError):
    """Raised before unsafe or ambiguous input can reach a remote service."""


class BudgetExceeded(StarterError):
    """Raised instead of returning a silently incomplete inventory."""


class XmlSafetyError(StarterError):
    """Raised when an XML document is unsafe, malformed, or over budget."""


@dataclass(frozen=True, slots=True)
class ApiError(StarterError):
    """A redacted remote failure safe to display to a CLI user."""

    provider: str
    status_code: int | None
    code: str
    retry_after_seconds: int | None = None

    def __str__(self) -> str:
        status = f" HTTP {self.status_code}" if self.status_code is not None else ""
        retry = (
            f"; retry after about {self.retry_after_seconds}s"
            if self.retry_after_seconds is not None
            else ""
        )
        return f"{self.provider}{status}: {self.code}{retry}"
