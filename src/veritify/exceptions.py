"""Exceptions raised by the Veritify SDK."""

from __future__ import annotations


class VeritifyError(Exception):
    """Base class for every error raised by this SDK."""


class VeritifyAPIError(VeritifyError):
    """The Veritify API responded with an error (4xx/5xx status code)."""

    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"Veritify API error {status_code}: {detail}")


class VeritifyConnectionError(VeritifyError):
    """Could not reach the Veritify API instance (network issue, wrong
    base_url, server not running, etc.)."""
