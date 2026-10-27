# Starling memory adapter

Starling is an optional derived memory projection. Actio `Store`, `Ledger`,
`Facts`, run terminal, evidence and replay remain authoritative. The default
profile is `off`; `shadow` is safe for offline projection and read comparison.

The adapter has no import-time Starling dependency. Install a future Starling
extra or provide a public facade/sidecar client through `StarlingMemoryAdapter`
when that runtime is available. On Windows, use a single owner sidecar for a
Starling SQLite database; do not open multiple embedded writers. The current
repository probe found no stable Windows Starling wheel, so this change does
not claim a native Starling build.

Projection is an Actio SQLite outbox (`memory_outbox`) with a unique
`stream/seq/slot/mapper` source key, certified source hash, canonical payload
hash, bounded attempts and explicit `needs_reconcile`. A duplicate source is
returned as `duplicate`; a conflicting hash is rejected. Starling and Actio
transactions are intentionally separate.

Payloads are canonical JSON, UTF-8 limited to 16 KiB, and reject credentials,
authorization tokens, `GM_PRIVATE_FULL_LOG`, stderr markers and similar secret
patterns. Only `assistant.final` is enabled by default. Tool/world sources and
replay projection require an explicit experimental profile.

`frozen_context` stores the context, hash, as-of time, source hashes, receipt,
adapter version and policy in the run input. Replay consumes that snapshot and
never queries live Starling. `live_context` is rejected for candidate,
evaluation and replay purposes.

The adapter maps common runtime failures to stable codes (`unready`,
`llm_not_configured`, `extraction_failed`, `db_locked`, `timeout`,
`sidecar_crash`, `degraded`); none changes an already certified Actio result.
`tick(now, deadline_ms)` requires explicit UTC time and a positive deadline.
`close(drain=True)` marks the adapter unready after the owner has drained.

To roll back, set the profile to `{"mode":"off"}`. Existing outbox rows and
receipts remain auditable; no Starling database is deleted by this adapter.
