# Changelog

## Unreleased

- Adds `usage()` — look up how many calls the configured `api_key` has
  made, and when it was first/last used. Requires an `api_key`; a key
  that's never made a call returns `total_calls=0`, not an error.

## 0.1.0 — 2026-08-04

- Initial release: `VeritifyClient` with `signup()`, `mine()`, `verify()`,
  `health()`, and `stats()`.
- Client points to the live production API by default in examples and docs
  (`https://veritify-api-production.up.railway.app`).
- Full documentation: `docs/getting-started.md`, `docs/api-reference.md`,
  `docs/errors.md`, plus runnable examples for signup, dual queries, and
  error handling.
