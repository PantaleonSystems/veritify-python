"""How to handle every error the API can return.

Every non-2xx response raises VeritifyAPIError with two attributes:
`.status_code` (int) and `.detail` (the message the API sent). Network-level
failures (DNS, connection refused, timeout) raise VeritifyConnectionError
instead — there's no status_code because the request never got a response.

See docs/errors.md for the full table of when each status code happens.
"""

from __future__ import annotations

from veritify import VeritifyClient
from veritify.exceptions import VeritifyAPIError, VeritifyConnectionError


def handle_mine_errors(client: VeritifyClient, file_path: str) -> None:
    try:
        result = client.mine(file_path)
        print(f"OK: {result.receipt_hash}")

    except VeritifyAPIError as exc:
        if exc.status_code == 401:
            # Missing/invalid signature (secure mode), or an invalid/revoked
            # API key. Check your VERITIFY_API_KEY.
            print(f"Not authorized: {exc.detail}")
        elif exc.status_code == 403:
            # Raw file upload while the server isn't running in demo mode —
            # send a pre-signed Ψ_USF.pt payload instead.
            print(f"Forbidden: {exc.detail}")
        elif exc.status_code == 413:
            # File bigger than the server's MAX_UPLOAD_MB.
            print(f"File too large: {exc.detail}")
        elif exc.status_code == 422:
            # Malformed input: empty file, corrupted payload, unsupported
            # format, or the physics pipeline rejected the data outright.
            print(f"Invalid request: {exc.detail}")
        elif exc.status_code == 429:
            # Rate limited — the response includes a Retry-After hint in its
            # body (the SDK doesn't parse the header automatically today).
            print(f"Rate limited, slow down: {exc.detail}")
        elif exc.status_code == 503:
            # Server at its concurrency ceiling — safe to retry shortly.
            print(f"Server busy, retry soon: {exc.detail}")
        elif exc.status_code == 504:
            # Timed out. IMPORTANT in dual mode (question=...): if this
            # happens, your DATA may already have been absorbed and its
            # receipt already registered — only the query timed out. See
            # docs/errors.md for how to check with verify().
            print(f"Timed out: {exc.detail}")
        else:
            print(f"Unexpected error {exc.status_code}: {exc.detail}")

    except VeritifyConnectionError as exc:
        # Couldn't reach the server at all — wrong base_url, no network,
        # or the server is down.
        print(f"Connection failed: {exc}")


def handle_signup_errors(client: VeritifyClient, email: str) -> None:
    try:
        result = client.signup(email)
        print(f"Key issued: {result.api_key}")

    except VeritifyAPIError as exc:
        if exc.status_code == 409:
            # This email already has an active key — there is no recovery
            # endpoint; the original key is gone forever if it was lost.
            print(f"Already registered: {exc.detail}")
        elif exc.status_code == 422:
            print(f"Invalid email: {exc.detail}")
        elif exc.status_code == 429:
            print(f"Too many signups from this IP: {exc.detail}")
        else:
            print(f"Unexpected error {exc.status_code}: {exc.detail}")


if __name__ == "__main__":
    client = VeritifyClient()  # reads VERITIFY_BASE_URL/VERITIFY_API_KEY from env
    handle_signup_errors(client, "not-an-email")   # triggers 422 on purpose
    handle_mine_errors(client, "/dev/null")          # triggers 422 (empty file)
