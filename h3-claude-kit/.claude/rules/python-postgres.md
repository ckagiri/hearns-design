---
paths:
  - "harness/**/*.py"
  - "tools/**/*.py"
  - "tests/**/*.py"
---

# Python and Postgres conventions

## Database access

- `psycopg` 3 only. `row_factory=dict_row`. Never `psycopg2`.
- SQL text lives in `harness/ledger/sql/<operation>.sql` and is loaded at import. Do not inline
  multi-line SQL in Python, and do not build SQL by string concatenation. Parameters are always
  bound, never interpolated.
- Claim is **one statement** (`WITH candidate AS (... FOR UPDATE SKIP LOCKED) UPDATE ...`).
  Never a `SELECT` followed by an `UPDATE` — two workers will both claim.
- Every write that depends on holding a lease goes through a function taking a `Lease`
  dataclass and emits `WHERE id = %s AND lease_holder = %s AND attempts = %s`. This applies to
  commit, heartbeat and release alike.
- Set `statement_timeout` and `idle_in_transaction_session_timeout` on the pool. A transaction
  must never stay open across a model call or a container run.
- Pool size tracks worker count, not card count.
- No worker may connect to the workspace template database. Enforce it in the connection layer,
  not by convention (rule 87).

## Time

Every timestamp and every deadline comes from Postgres (`now()`), not from Python. If you need
a wall-clock value in Python for logging only, name the variable so it is obviously not used for
scheduling.

## Types and errors

- `mypy --strict` on `harness/`. Public functions are fully annotated.
- Rows cross the boundary as `pydantic` models or frozen dataclasses. Nothing lazy-loads.
- Prefer narrow exception types. A failure that consumes an attempt and a failure that does not
  are different things: map to `failure_class` explicitly rather than letting a bare `except`
  decide.

## Structure

- `harness/ledger/` — claim, heartbeat, commit, release, reaper, SQL files.
- `harness/worker/` — the claim loop, role config, drain.
- `harness/workspace/` — worktree, container, database clone.
- `harness/store/` — content store, truncation.
- `harness/config/` — pin, `kind_hash`, validation.
- `harness/cli/` — typer app; thin wrappers over the above. If a CLI command grows logic, the
  logic belongs elsewhere.
- `tools/` — standalone scripts (`introspect.py`, `generate.py`, `schema_lint.py`). These must
  run without the harness existing, and stay that way.

## Tests

- Contention, kill and replay tests use a real Postgres via `testcontainers`; mark them `slow`.
- Predicate tests are property tests: generate graphs, assert no card is ready whose subtree is
  unfinished.
- Assert on the **terminal graph**, never on execution order. Interleaving may differ between
  runs; the causal graph will not.
- Hash-stability tests are cheap and load-bearing: reformatting config or reordering
  `skills.yaml` must not move `kind_hash`; changing a rendering comment must.

## Things that look helpful and are not

- Retry decorators around ledger writes. Lease expiry is the entire crash-recovery story.
- A `Task` service class that wraps the SQL. The SQL being readable by a human a year from now
  is the point.
- Caching rows in the worker. The board is the only state.
