"""Dual pipeline — compare a file against a question instead of just
scoring the file on its own.

Passing `question=` to `mine()` switches the response from `MineResult` to
`MineResultDual`, which carries a `verdict` plus the raw overlap scores
between the data and the query.

    python examples/dual_query.py path/to/file.txt "your question here"
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
    if len(sys.argv) < 3:
        print('Usage: python dual_query.py <file> "<question>"')
        raise SystemExit(1)

    file_path, question = sys.argv[1], sys.argv[2]

    client = VeritifyClient()  # reads VERITIFY_BASE_URL/VERITIFY_API_KEY from env
    result = client.mine(file_path, question=question)

    print(f"Mode:               {result.mode}")
    print(f"Verdict:            {result.verdict}")
    print(f"Geometric overlap:  {result.geometric_overlap:.4f}")
    print(f"Spectral resonance: {result.spectral_resonance:.4f}")
    print(f"Regime alignment:   {result.regime_alignment:.4f}")
    print(f"Data regime:        {result.data_regime}")
    print(f"Query regime:       {result.query_regime}")
    print(f"Cross-modal:        {result.cross_modal}")
    print(f"Receipt hash:       {result.receipt_hash}")


if __name__ == "__main__":
    main()
