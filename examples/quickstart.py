"""Quickstart — process a file and publicly verify its receipt.

Run against a Veritify instance you have available (e.g. a local dev
server). Reads VERITIFY_BASE_URL / VERITIFY_API_KEY from a .env file in the
repo root if present (copy .env.example to .env and edit it), or from the
environment directly:

    export VERITIFY_BASE_URL=http://localhost:8000
    python examples/quickstart.py path/to/file.wav
"""

from __future__ import annotations

import sys

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass  # python-dotenv is a dev-only convenience, not a runtime dependency

from veritify import VeritifyClient


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python quickstart.py <file>")
        raise SystemExit(1)

    client = VeritifyClient()  # reads VERITIFY_BASE_URL from the environment
    result = client.mine(sys.argv[1])

    print(f"Novel:        {result.is_novel}")
    print(f"Delta S:      {result.delta_s}")
    print(f"Regime:       {result.regime_name}")
    print(f"Receipt hash: {result.receipt_hash}")

    # Anyone — not just this client — can independently confirm the result:
    verification = client.verify(result.receipt_hash)
    print(f"\nPublicly verifiable: {verification.known}")


if __name__ == "__main__":
    main()
