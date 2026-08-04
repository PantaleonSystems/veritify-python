# Errors

Every non-2xx response from the API raises `VeritifyAPIError`, with two
attributes:

```python
exc.status_code   # int, e.g. 422
exc.detail         # whatever the API sent back as the error message
```

`detail` is usually a plain string — but for a handful of cases where
FastAPI's own request validation rejects the input before our code even
runs (confirmed live: an invalid `email` on `signup()`), `detail` comes
back as a structured list of validation errors instead of a string, e.g.:

```python
[{'type': 'value_error', 'loc': ['body', 'email'],
  'msg': "Value error, email invalido: 'not-an-email'", ...}]
```

Treat `detail` as "whatever's useful to log or show a developer", not as a
guaranteed string — don't assume you can always call `.upper()` on it, for
instance.

Network-level failures (DNS resolution, connection refused, timeout before
any response arrives) raise `VeritifyConnectionError` instead —
there's no `status_code`, because the request never got a response at all.

## Full status code table

| Status | Where | Cause |
|---|---|---|
| **401** | `mine()` | Secure mode: missing/invalid/expired signature (anti-replay window). Or: an `Authorization` header was sent with an invalid or revoked API key — never silently falls back to the anonymous rate limit. |
| **401** | `usage()` | No `api_key` configured, or it's invalid/revoked. Unlike `mine()`, there's no anonymous fallback here — usage history only makes sense per key. |
| **403** | `mine()` | Uploading a raw file when the server isn't running in demo mode. Not observable against the current production instance today (it runs in demo mode), documented for when that changes. |
| **409** | `signup()` | The email already has an active key. `detail` is a plain string. |
| **413** | `mine()` | The file is larger than the server's configured upload ceiling. Nothing beyond the limit is ever written server-side. |
| **422** | `mine()` | Several distinct causes share this code: an empty file, a corrupted/unreadable payload, an unsupported schema version, a chunk-size mismatch, or the physics pipeline itself rejecting the data as topologically incoherent. |
| **422** | `verify()` | `receipt_hash` isn't a well-formed SHA-256 (64 hex characters, `0x` prefix optional). An **unknown but well-formed** hash is never an error — see below. |
| **422** | `signup()` | `email` failed validation. `detail` is the structured Pydantic list described above, not a plain string. |
| **429** | `mine()`, `signup()` | Rate limit exceeded — by IP if you didn't send an API key, by your key's own limit if you did. `signup()` has its own, separate, stricter limit per IP (to stop it being used to mint unlimited free keys). |
| **503** | `mine()` | The server is at its concurrency ceiling. Safe to retry shortly — this is a fail-fast response, not a sign anything is broken. |
| **504** | `mine()` | Processing exceeded the server's timeout. See the dual-mode nuance below — this one has a sharp edge. |

## `verify()` never errors on an "unknown" hash

This is worth calling out on its own: a **well-formed** hash that the
server has simply never seen returns normally, with `known=False` — it is
**not** a `404` and does **not** raise anything:

```python
v = client.verify("f" * 64)   # well-formed, but never submitted
v.known        # False
v.mined_at     # None
# no exception raised
```

Only a **malformed** hash (wrong length, non-hex characters) raises
`VeritifyAPIError(422)`.

## The 504 dual-mode nuance

If you call `mine(file, question=...)` and get back a `504`, read this
before retrying blindly:

The server processes the **data** first (and commits it — updates its
internal state, registers the receipt) and only *then* runs the **query**
comparison. If the timeout happens during the query phase, **your data has
already been absorbed and its receipt already registered** — only the
question timed out.

Practically: if you have the file's content stable and reproducible, you
can check whether it went through by computing what the receipt would be
and calling `verify()` — though in most cases the simplest move is just to
resend the same file (without `question=`) and see whether it comes back
`is_novel=False` (a strong sign it was already absorbed) before assuming
nothing happened.

A `504` on a call **without** `question=` is simpler: nothing was
committed, and it's safe to just retry.

## Handling errors in code

```python
from veritify import VeritifyClient
from veritify.exceptions import VeritifyAPIError, VeritifyConnectionError

client = VeritifyClient()

try:
    result = client.mine("recording.wav")
except VeritifyAPIError as exc:
    if exc.status_code == 429:
        print(f"Rate limited: {exc.detail}")
    elif exc.status_code == 422:
        print(f"Invalid request: {exc.detail}")
    else:
        print(f"API error {exc.status_code}: {exc.detail}")
except VeritifyConnectionError as exc:
    print(f"Couldn't reach the server: {exc}")
```

See [`examples/error_handling.py`](https://github.com/PantaleonSystems/veritify-python/blob/main/examples/error_handling.py)
for a fuller version covering every status code above, runnable as-is.
