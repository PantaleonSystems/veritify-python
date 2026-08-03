# Veritify — Python SDK

Official Python client for **Veritify** — an API that measures the **integrity,
novelty, and authenticity of data** (audio, text, and documents today), returning
a cryptographically verifiable proof for every result.

> ⚠️ **Early access.** A publicly hosted Veritify API is not live yet — point this
> client at your own running instance while it's in development (see
> [Status](#status)).

## Install

```bash
pip install veritify
```

## Quickstart

```python
from veritify import VeritifyClient

client = VeritifyClient(base_url="http://localhost:8000")

result = client.mine("recording.wav")
print(result.is_novel, result.delta_s, result.receipt_hash)

# Anyone can independently verify the receipt later — no trust required:
verification = client.verify(result.receipt_hash)
print(verification.known, verification.mined_at)
```

You can also set `VERITIFY_BASE_URL` (and, optionally, `VERITIFY_API_KEY`) as
environment variables instead of passing them explicitly:

```bash
cp .env.example .env   # then edit .env with your own values
```

`.env` is gitignored — never commit it. `examples/quickstart.py` loads it
automatically if `python-dotenv` is installed (included in the `dev` extra).

## What you get back

Every call to `mine()` returns a typed result. The most commonly used fields:

| Field | Meaning |
|---|---|
| `delta_s` | How much new information this data contributed — higher means more novel |
| `is_novel` | Whether the data passed the novelty threshold |
| `regime_name` | The structural regime detected in the data |
| `receipt_hash` | A public, independently verifiable proof of this result |

Pass a `question` to `mine()` to compare a file against a query instead — it
returns a `MineResultDual` with a `verdict` field describing the relationship
between the two.

## Verifying a receipt

Any receipt hash returned by `mine()` can be verified by anyone, at any time,
without an API key — this is the whole point:

```python
verification = client.verify(receipt_hash)
```

An unrecognized hash returns `known=False` rather than an error.

## Status

Veritify is under active development. The SDK's contract (`mine`, `verify`,
`health`, `stats`) mirrors the API as it exists today. A publicly hosted,
always-available endpoint is on the roadmap — until then, point `base_url` at
an instance you run yourself.

## Development

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT — see [LICENSE](LICENSE).
