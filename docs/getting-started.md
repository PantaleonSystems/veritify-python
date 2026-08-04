# Getting Started

## Installation

```bash
pip install veritify
```

Requires Python 3.9 or later. If you're working from a clone of this repo
instead:

```bash
git clone https://github.com/PantaleonSystems/veritify-python.git
cd veritify-python
pip install -e ".[dev]"   # [dev] adds pytest, responses, python-dotenv
```

## Getting your API key

Veritify's signup is self-service — one call, no approval queue.

**In Python:**

```python
from veritify import VeritifyClient

# signup() is the one method that works without an api_key configured —
# it's how you get your first one.
with VeritifyClient(base_url="https://veritify-api-production.up.railway.app") as client:
    result = client.signup("you@example.com")
    print(result.api_key)   # shown ONCE — copy it now
    print(result.plan)      # "free"
```

Or with the ready-made example script:

```bash
python examples/signup.py you@example.com
```

**With `curl`, if you're not using Python:**

```bash
curl -X POST https://veritify-api-production.up.railway.app/api/v1/signup \
     -H "Content-Type: application/json" \
     -d '{"email": "you@example.com"}'
```

Either way, the response looks like:

```json
{
  "api_key": "vrfy_live_...",
  "plan": "free",
  "message": "Guarde esta chave agora — ela nao sera mostrada novamente."
}
```

### Important: the key is shown exactly once

Veritify doesn't store your key in a way that lets it show it to you again.
If you lose it, there's no recovery endpoint — you'll need to sign up again
with a **different email**. Signing up again with the same email that
already has an active key returns an error (`409 Conflict`), not a second
key. See [Errors](errors.md) for the full picture of what that looks like
in code.

**Save your key immediately** — the most common way is to drop it straight
into a local `.env` file (never commit this file):

```bash
cp .env.example .env
# then edit .env and paste your key into VERITIFY_API_KEY=
```

## Configuration

`VeritifyClient` can be configured two ways, and they can be mixed:

```python
# Explicit — always wins over environment variables
client = VeritifyClient(
    base_url="https://veritify-api-production.up.railway.app",
    api_key="vrfy_live_...",
)

# Or via environment variables (VERITIFY_BASE_URL, VERITIFY_API_KEY) —
# useful with a .env file loaded by python-dotenv
client = VeritifyClient()
```

`api_key` is optional for now — requests without one still work, sharing an
anonymous rate limit. Once you have a key, pass it (or set
`VERITIFY_API_KEY`) to get your own limit instead of the shared one. See
[API Reference](api-reference.md#veritifyclient) for every constructor
option.

## Your first call

```python
from veritify import VeritifyClient

client = VeritifyClient()  # reads VERITIFY_BASE_URL / VERITIFY_API_KEY from env

result = client.mine("recording.wav")
print(f"Novel: {result.is_novel}")
print(f"Delta S: {result.delta_s}")
print(f"Receipt: {result.receipt_hash}")

# Anyone can independently confirm this result later, without your key:
verification = client.verify(result.receipt_hash)
print(f"Publicly verifiable: {verification.known}")
```

## Next steps

- **[API Reference](api-reference.md)** — every method, every field, in detail.
- **[Errors](errors.md)** — every status code the API can return, and how to
  handle each one in code.
- Runnable examples in [`examples/`](https://github.com/PantaleonSystems/veritify-python/tree/main/examples):
  `quickstart.py`, `signup.py`, `dual_query.py`, `error_handling.py`.
- No Python handy?
  [Run the collection in Postman](https://www.postman.com/pantaleonsystems/veritify/collection/4sf5u84/veritify-api?action=share&creator=57133975)
  and call every endpoint directly, or import the file yourself from
  [`postman/veritify.postman_collection.json`](https://github.com/PantaleonSystems/veritify-python/blob/main/postman/veritify.postman_collection.json).
