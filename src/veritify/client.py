"""veritify.client — VeritifyClient, the SDK's single entry point."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional, Union

import requests

from .exceptions import VeritifyAPIError, VeritifyConnectionError
from .models import HealthStatus, MineResult, MineResultDual, Stats, VerifyResult

_DEFAULT_TIMEOUT = 60.0

# Real quirk of the API today: /mine and /verify are namespaced under
# /api/v1, but /health and /stats are mounted at the root. Encoding this
# here means SDK users never need to know it.
_MINE_PATH = "/api/v1/mine"
_VERIFY_PATH = "/api/v1/verify/{receipt_hash}"
_HEALTH_PATH = "/health"
_STATS_PATH = "/stats"


class VeritifyClient:
    """Official Python client for the Veritify API.

    Parameters
    ----------
    base_url:
        Root URL of the Veritify API instance to call (e.g.
        ``"http://localhost:8000"`` during local development). If omitted,
        the ``VERITIFY_BASE_URL`` environment variable is used. One of the
        two is required — Veritify does not yet have a single public hosted
        endpoint, so every client must point at a known instance.
    api_key:
        Sent as a Bearer token when provided. If omitted, falls back to the
        ``VERITIFY_API_KEY`` environment variable (same pattern as
        ``OPENAI_API_KEY``/``ANTHROPIC_API_KEY``). Authentication is being
        rolled out on the API side; requests without a key are accepted
        today, but passing one now is forward-compatible.
    timeout:
        Per-request timeout in seconds.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        *,
        api_key: Optional[str] = None,
        timeout: float = _DEFAULT_TIMEOUT,
    ) -> None:
        resolved_base_url = base_url or os.getenv("VERITIFY_BASE_URL")
        if not resolved_base_url:
            raise ValueError(
                "base_url is required (or set the VERITIFY_BASE_URL "
                "environment variable) — point it at your Veritify API "
                "instance, e.g. http://localhost:8000"
            )
        self.base_url = resolved_base_url.rstrip("/")
        self.api_key = api_key or os.getenv("VERITIFY_API_KEY")
        self.timeout = timeout
        self._session = requests.Session()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def mine(
        self,
        file_path: Union[str, Path],
        *,
        question: Optional[str] = None,
        teacher_wallet: Optional[str] = None,
        signature: Optional[str] = None,
    ) -> Union[MineResult, MineResultDual]:
        """Process a file and get back its integrity/novelty verdict.

        Passing ``question`` runs the dual pipeline (data vs. query) and
        returns a :class:`MineResultDual` instead of a :class:`MineResult`.
        """
        path = Path(file_path)
        form: dict[str, str] = {}
        if question is not None:
            form["question"] = question
        if teacher_wallet is not None:
            form["teacher_wallet"] = teacher_wallet
        if signature is not None:
            form["signature"] = signature

        with open(path, "rb") as fh:
            payload = self._request(
                "POST", _MINE_PATH, files={"file": (path.name, fh)}, data=form
            )

        if payload.get("mode") == "dual":
            return MineResultDual.from_dict(payload)
        return MineResult.from_dict(payload)

    def verify(self, receipt_hash: str) -> VerifyResult:
        """Publicly verify a receipt hash returned by a previous `mine()` call.

        Always succeeds with ``known=False`` for an unrecognized hash —
        never raises just because the hash wasn't found.
        """
        path = _VERIFY_PATH.format(receipt_hash=receipt_hash)
        payload = self._request("GET", path)
        return VerifyResult.from_dict(payload)

    def health(self) -> HealthStatus:
        """Check whether the Veritify instance is up."""
        return HealthStatus.from_dict(self._request("GET", _HEALTH_PATH))

    def stats(self) -> Stats:
        """Aggregate statistics for the Veritify instance (all requests processed so far)."""
        return Stats.from_dict(self._request("GET", _STATS_PATH))

    def close(self) -> None:
        self._session.close()

    def __enter__(self) -> "VeritifyClient":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _headers(self) -> dict[str, str]:
        if self.api_key:
            return {"Authorization": f"Bearer {self.api_key}"}
        return {}

    def _request(self, method: str, path: str, **kwargs: Any) -> dict:
        url = f"{self.base_url}{path}"
        try:
            response = self._session.request(
                method, url, headers=self._headers(), timeout=self.timeout, **kwargs
            )
        except requests.RequestException as exc:
            raise VeritifyConnectionError(f"Could not reach {url}: {exc}") from exc

        if response.status_code >= 400:
            try:
                detail = response.json().get("detail", response.text)
            except ValueError:
                detail = response.text
            raise VeritifyAPIError(response.status_code, detail)

        return response.json()
