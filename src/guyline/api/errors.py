"""API error types for Guyline."""

from __future__ import annotations


class GuylineApiError(RuntimeError):
    """Base class for upstream API failures."""


class AuthenticationFailure(GuylineApiError):
    """Raised when the upstream service rejects the provided credentials."""


class RateLimitFailure(GuylineApiError):
    """Raised when the upstream service rejects the request due to rate limits."""


class RequestFailure(GuylineApiError):
    """Raised for generic request or transport failures."""
