# Veritify

[![Tests](https://github.com/PantaleonSystems/veritify-python/actions/workflows/test.yml/badge.svg)](https://github.com/PantaleonSystems/veritify-python/actions/workflows/test.yml)
[![PyPI version](https://img.shields.io/pypi/v/veritify.svg)](https://pypi.org/project/veritify/)
[![Python versions](https://img.shields.io/pypi/pyversions/veritify.svg)](https://pypi.org/project/veritify/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/PantaleonSystems/veritify-python/blob/main/LICENSE)

**Official Python SDK for Veritify** — measure the integrity, novelty, and
authenticity of data, with a cryptographically verifiable proof behind every
result.

[Getting Started](https://github.com/PantaleonSystems/veritify-python/blob/main/docs/getting-started.md) ·
[API Reference](https://github.com/PantaleonSystems/veritify-python/blob/main/docs/api-reference.md) ·
[Errors](https://github.com/PantaleonSystems/veritify-python/blob/main/docs/errors.md) ·
[PyPI](https://pypi.org/project/veritify/) ·
[Issues](https://github.com/PantaleonSystems/veritify-python/issues)

---

## Features

- 🔍 **Novelty detection** — measure how much new information a piece of data contributes, not just whether it "looks like" something seen before
- 🔐 **Cryptographic receipts** — every result ships a hash anyone can independently verify, publicly, without trusting us or holding an API key
- 🧩 **Multi-modal** — audio, text, and documents today, through the same call
- ⚡ **Simple API** — one client, four core methods: `signup`, `mine`, `verify`, `stats`
- 🔑 **Self-service API keys** — get one in one call, no approval wait

## Installation

```bash
pip install veritify
```

Requires Python 3.9+. The only runtime dependency is [`requests`](https://pypi.org/project/requests/).

## Quickstart

```python
from veritify import VeritifyClient

client = VeritifyClient(base_url="https://veritify-api-production.up.railway.app")

result = client.mine("recording.wav")
print(result.is_novel, result.delta_s, result.receipt_hash)

# Anyone can independently verify the receipt later — no trust required:
verification = client.verify(result.receipt_hash)
print(verification.known, verification.mined_at)
```

You can also set `VERITIFY_BASE_URL` and `VERITIFY_API_KEY` as environment
variables instead of passing them explicitly — copy `.env.example` to `.env`
and fill it in (`.env` is gitignored; never commit real values).

## Getting your API key

No signup form, no approval queue — one call, and you have a working key:

```python
from veritify import VeritifyClient

with VeritifyClient(base_url="https://veritify-api-production.up.railway.app") as client:
    result = client.signup("you@example.com")
    print(result.api_key)  # shown ONCE — save it now
```

Or run the ready-made example: `python examples/signup.py you@example.com`.
Full walkthrough, including the `curl` equivalent: [Getting Started](https://github.com/PantaleonSystems/veritify-python/blob/main/docs/getting-started.md).

## Documentation

- **[Getting Started](https://github.com/PantaleonSystems/veritify-python/blob/main/docs/getting-started.md)** — install, get a key, configure, first call
- **[API Reference](https://github.com/PantaleonSystems/veritify-python/blob/main/docs/api-reference.md)** — every method, every field, in detail
- **[Errors](https://github.com/PantaleonSystems/veritify-python/blob/main/docs/errors.md)** — every status code the API can return, and how to handle each

More runnable examples live in [`examples/`](https://github.com/PantaleonSystems/veritify-python/tree/main/examples):
a dual query (`question=` comparing data against a query), and full
error-handling coverage.

Prefer testing the API straight from your HTTP client instead of Python? Import
[`postman/veritify.postman_collection.json`](https://github.com/PantaleonSystems/veritify-python/blob/main/postman/veritify.postman_collection.json)
into Postman — every endpoint, pre-filled against production.

## Status

Veritify is under active development. The SDK's contract (`signup`, `mine`,
`verify`, `health`, `stats`) mirrors the API as it exists today, live at
`https://veritify-api-production.up.railway.app`. This may move to a custom
domain later — we'll announce it here if so.

## Development

```bash
git clone https://github.com/PantaleonSystems/veritify-python.git
cd veritify-python
pip install -e ".[dev]"
pytest
```

## License

MIT — see [LICENSE](https://github.com/PantaleonSystems/veritify-python/blob/main/LICENSE).
