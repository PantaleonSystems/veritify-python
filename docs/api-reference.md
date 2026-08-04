# API Reference

Every method of `VeritifyClient`, with full parameter and return-value
detail. For "what error can this raise, and what do I do about it", see
[Errors](errors.md).

- [`VeritifyClient`](#veritifyclient) — constructor
- [`signup()`](#signup)
- [`mine()`](#mine) — single mode and dual mode
- [`verify()`](#verify)
- [`health()`](#health)
- [`stats()`](#stats)
- [`close()` / context manager](#close--context-manager)
- [Advanced: raw endpoints](#advanced-raw-endpoints)

---

## `VeritifyClient`

```python
VeritifyClient(
    base_url: str | None = None,
    *,
    api_key: str | None = None,
    timeout: float = 60.0,
)
```

| Parameter | Type | Required | Default | Notes |
|---|---|---|---|---|
| `base_url` | `str` | One of `base_url` / `VERITIFY_BASE_URL` env var | — | Root URL of the Veritify instance, e.g. `https://veritify-api-production.up.railway.app`. Raises `ValueError` at construction time if neither is set. Trailing slash is stripped automatically. |
| `api_key` | `str` | No | `None` | Falls back to the `VERITIFY_API_KEY` environment variable if not passed explicitly. An explicit value always wins over the env var. Sent as `Authorization: Bearer <key>` on every request except `signup()`. |
| `timeout` | `float` | No | `60.0` | Per-request timeout, in seconds, passed straight to `requests`. |

`base_url` resolution order: explicit argument → `VERITIFY_BASE_URL` env var
→ `ValueError`. `api_key` resolution order: explicit argument →
`VERITIFY_API_KEY` env var → `None` (unauthenticated).

---

## `signup()`

```python
client.signup(email: str) -> SignupResult
```

Creates a new API key. The **only** method that works without an `api_key`
configured on the client — it's how you get your first one. See
[Getting Started](getting-started.md#getting-your-api-key) for the full
walkthrough.

| Parameter | Type | Required | Notes |
|---|---|---|---|
| `email` | `str` | Yes | Must contain `@` and a `.` after it. |

**Returns `SignupResult`:**

| Field | Type | Notes |
|---|---|---|
| `api_key` | `str` | Shown **exactly once** — this call is the only place it ever appears in plaintext. Starts with `vrfy_live_`. |
| `plan` | `str` | Currently always `"free"`. |
| `message` | `str` | Human-readable reminder to save the key now. |

**Raises:** `VeritifyAPIError` with `status_code` `409` (email already has an
active key), `422` (malformed email), or `429` (too many signups from your
IP). See [Errors](errors.md#signup-errors).

```python
result = client.signup("you@example.com")
print(result.api_key)
```

---

## `mine()`

```python
client.mine(
    file_path: str | Path,
    *,
    question: str | None = None,
    teacher_wallet: str | None = None,
    signature: str | None = None,
) -> MineResult | MineResultDual
```

Uploads a file and gets back its integrity/novelty verdict. This is the
core of the API.

| Parameter | Type | Required | Notes |
|---|---|---|---|
| `file_path` | `str` or `Path` | Yes | Path to a local file. Today: audio, text, and document formats are the validated domain. |
| `question` | `str` | No | If provided, switches to **dual mode**: the file is compared against this question instead of scored on its own. Return type changes from `MineResult` to `MineResultDual`. |
| `teacher_wallet` | `str` | No | Advanced / secure-mode use — associates the submission with a wallet address. |
| `signature` | `str` | No | Advanced / secure-mode use — a pre-computed EIP-191 signature over the payload hash. Required if the server isn't running in demo mode (see [Errors](errors.md), 401 and 403). |

### Single mode (no `question`) — returns `MineResult`

| Field | Type | Notes |
|---|---|---|
| `mode` | `str` | Always `"single"`. |
| `delta_s` | `float` | ≥ 0. How much new information this data contributed — higher means more novel. |
| `e0_normalized` | `float` | ≥ 0. Dominant eigenvalue, normalized. |
| `regime` | `float` | 0–1. Raw regime score behind `regime_name`. |
| `eigenvalues` | `list[float]` | Always exactly 8 values. |
| `is_novel` | `bool` | Whether `delta_s` cleared the novelty threshold. |
| `energy_concentration` | `str` | One of `"ALTA"`, `"MODERADA"`, `"DIFUSA"`. |
| `regime_name` | `str` | One of `"QUÂNTICO"`, `"TRANSIÇÃO"`, `"COSMOLÓGICO"`. |
| `discontinuity` | `bool` | Whether a structural discontinuity was detected. |
| `original_format` | `str` | The input's detected format, e.g. `"audio/wav"`, `"text/plain"`. |
| `receipt_hash` | `str` | 64 lowercase hex characters (SHA-256). Pass this to `verify()`. |
| `lambda_snapshot` | `dict[str, float]` | The model's calibration parameters at the time of this call. |
| `processing_ms` | `int` | ≥ 0. Server-side processing time. |
| `n_chunks` | `int` | ≥ 1. How many chunks the input was split into. |
| `compression_ratio` | `float` | > 1.0. |
| `spectral_flatness` | `float` | 0–1, default `0.0`. Noise-detector signal (see `noise_suspect`). |
| `noise_suspect` | `bool` | Default `False`. `True` if the input looked statistically like noise rather than structured data. |
| `teacher_address` | `str \| None` | Default `None`. Populated only in secure mode with a valid `signature`. |

```python
result = client.mine("recording.wav")
print(result.is_novel, result.delta_s, result.receipt_hash)
```

### Dual mode (`question=...`) — returns `MineResultDual`

All the single-mode fields conceptually still apply, but under different
names split by data vs. query, plus overlap scores between the two:

| Field | Type | Notes |
|---|---|---|
| `mode` | `str` | Always `"dual"`. |
| `data_e0` | `float` | ≥ 0. Same meaning as `e0_normalized`, for the file. |
| `data_regime` | `str` | Regime name for the file — same 3 closed values as `regime_name`. |
| `data_energy_concentration` | `str` | Same 3 closed values as `energy_concentration`, for the file. |
| `query_e0` | `float` | ≥ 0. Same, for the question. |
| `query_regime` | `str` | Regime name for the question. |
| `geometric_overlap` | `float` | -1 to 1. Raw geometric overlap between data and query. |
| `spectral_resonance` | `float` | -1 to 1. |
| `regime_alignment` | `float` | 0 to 1. How aligned the two regimes are. |
| `verdict` | `str` | One of exactly 5 values (see below). |
| `is_novel` | `bool` | Whether the underlying data was novel (same meaning as single mode). |
| `delta_s` | `float` | ≥ 0. |
| `original_format` | `str` | |
| `receipt_hash` | `str` | Refers to the **data**, not the query — pass this to `verify()`. |
| `lambda_snapshot` | `dict[str, float]` | |
| `processing_ms` | `int` | |
| `n_chunks` | `int` | |
| `spectral_flatness` | `float` | Default `0.0`. Refers to the data. |
| `noise_suspect` | `bool` | Default `False`. Refers to the data. |
| `teacher_address` | `str \| None` | Default `None`. |
| `cross_modal` | `bool` | Default `False`. `True` when the query and the data are of different modalities (e.g. a text question against an audio file) — the overlap scores are less directly comparable in that case. |

`verdict` is always one of:

```
"PADRÃO DETECTADO — SEVERIDADE ALTA"
"PADRÃO DETECTADO — SEVERIDADE MODERADA"
"PADRÃO NÃO ENCONTRADO NO DADO"
"ESCALAS TEMPORAIS INCOMPATÍVEIS — REGIMES DISTINTOS"
"CORRELAÇÃO PARCIAL DETECTADA"
```

```python
result = client.mine("report.pdf", question="does this mention Q3 revenue?")
print(result.verdict, result.geometric_overlap)
```

**Raises:** `VeritifyAPIError` — see [Errors](errors.md#mine-errors) for the
full table (401, 403, 413, 422, 429, 503, 504). `VeritifyConnectionError` on
network failure.

---

## `verify()`

```python
client.verify(receipt_hash: str) -> VerifyResult
```

Publicly confirms a receipt hash returned by a previous `mine()` call.
**Never requires an API key.** Always succeeds — an unrecognized hash is not
an error, it's a normal `known=False` result.

| Parameter | Type | Required | Notes |
|---|---|---|---|
| `receipt_hash` | `str` | Yes | The hash to look up. |

**Returns `VerifyResult`:**

| Field | Type | Notes |
|---|---|---|
| `receipt_hash` | `str` | Echoes the input. |
| `known` | `bool` | Whether this hash has ever been seen. |
| `mined_at` | `float \| None` | Unix timestamp, only when `known` is `True`. |
| `delta_s` | `float \| None` | Only when `known`. |
| `e0_normalized` | `float \| None` | Only when `known`. |
| `regime` | `float \| None` | Only when `known`. |
| `is_novel` | `bool \| None` | Only when `known`. |
| `original_format` | `str \| None` | Only when `known`. |

```python
verification = client.verify(result.receipt_hash)
if verification.known:
    print(f"Mined at {verification.mined_at}, delta_s={verification.delta_s}")
else:
    print("Unknown hash")
```

**Raises:** `VeritifyAPIError` with `status_code=422` only if `receipt_hash`
itself is malformed (not 64 hex characters) — never for an unknown-but-valid
hash. See [Errors](errors.md#verify-errors).

---

## `health()`

```python
client.health() -> HealthStatus
```

Checks whether the instance is up. No parameters, no API key required.

| Field | Type | Notes |
|---|---|---|
| `status` | `str` | `"ok"` when reachable. |
| `device` | `str` | `"cpu"` or `"cuda"` / `"cuda:N"` — what the server is running on. |
| `chunk_size` | `int` | One of `256`, `512`, `1024`, `2048`, `4096`. |
| `uptime_s` | `float` | ≥ 0. Seconds since the server process started. |

```python
status = client.health()
print(status.status, status.uptime_s)
```

---

## `stats()`

```python
client.stats() -> Stats
```

Aggregate counters for the instance — how much it has processed in total.
No parameters, no API key required.

| Field | Type | Notes |
|---|---|---|
| `total_processed` | `int` | ≥ 0. |
| `novel_count` | `int` | ≥ 0. Always ≤ `total_processed`. |
| `novelty_rate` | `float` | 0–1. `novel_count / total_processed`. |
| `dual_query_count` | `int` | ≥ 0. How many of `total_processed` used `question=`. |
| `lambda_current` | `dict[str, float]` | Current model calibration parameters. |
| `g_base_dimension` | `int` | ≥ 1. Internal state dimensionality. |
| `g_base_nonzero` | `int` | ≥ 0. |

```python
stats = client.stats()
print(f"{stats.novel_count}/{stats.total_processed} were novel")
```

---

## `close()` / context manager

```python
client.close() -> None
```

Closes the underlying HTTP session. `VeritifyClient` also supports the
context manager protocol, which calls `close()` automatically:

```python
with VeritifyClient() as client:
    result = client.mine("file.txt")
# session is closed here
```

---

## Advanced: raw endpoints

If you're calling the API directly instead of through this SDK, note one
real quirk: `mine`, `verify`, and `signup` are namespaced under `/api/v1`,
but `health` and `stats` are mounted at the root (no `/api/v1` prefix). The
SDK hides this — you never need to think about it through `VeritifyClient` —
but it matters if you're constructing raw HTTP requests yourself.

| Method | Path |
|---|---|
| `POST` | `/api/v1/mine` |
| `GET` | `/api/v1/verify/{receipt_hash}` |
| `POST` | `/api/v1/signup` |
| `GET` | `/health` |
| `GET` | `/stats` |
