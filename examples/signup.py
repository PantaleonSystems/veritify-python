"""Get an API key — self-service, no approval wait.

    python examples/signup.py you@example.com

Prints the key ONCE. Veritify never stores it in a recoverable form — if
you lose it, sign up again with a different email (the same email with an
active key returns 409, not a second key).
"""

from __future__ import annotations

import sys

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass  # python-dotenv is a dev-only convenience, not a runtime dependency

from veritify import VeritifyClient
from veritify.exceptions import VeritifyAPIError

_DEFAULT_BASE_URL = "https://veritify-api-production.up.railway.app"


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python signup.py <email>")
        raise SystemExit(1)

    email = sys.argv[1]

    # signup() needs no api_key — it's the one call that creates your identity.
    with VeritifyClient(base_url=_DEFAULT_BASE_URL) as client:
        try:
            result = client.signup(email)
        except VeritifyAPIError as exc:
            if exc.status_code == 409:
                print(f"{email} already has an active key. {exc.detail}")
                raise SystemExit(1)
            raise

    print("=" * 60)
    print("SAVE THIS KEY NOW — it will not be shown again.")
    print("=" * 60)
    print(f"API key: {result.api_key}")
    print(f"Plan:    {result.plan}")
    print()
    print("Add it to your .env file:")
    print(f"  VERITIFY_API_KEY={result.api_key}")


if __name__ == "__main__":
    main()
