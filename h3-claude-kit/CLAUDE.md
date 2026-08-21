# H3 — Humble Helper Harness

A Postgres ledger of work cards and stateless workers that claim them. The board is the only
place state lives; no component holds a plan. This repo builds the substrate first.

**Design documents are in `docs/`. They are authoritative; this file is a summary.**
Read the specific section before implementing against it — do not work from this summary alone.

| Question | Read |
|---|---|
| Substrate: board, predicate, claim, lease, fencing, reaper, workspace, replay | `docs/harness-core-v3.md` |
| Roles, decomposition, verification, tiering, experiments | `docs/harness-policy-v3.md` |
| Odoo conventions, check ladder, schema anchor | `docs/odoo-adaptation.md` |
| Rule and risk numbers (**authority**) | `docs/rules-and-risks.md` |
| Why something was deleted | `docs/adr/` |
| What to build next, in order | `docs/h3-project-breakdown.md` |

## Stack

- Python 3.12+, `uv`, src layout. Package `harness/`; console script `h3`. **Never** name the
  import package `h3` — that collides with Uber's geospatial library on PyPI.
- `psycopg` 3 + `psycopg_pool`. **No ORM, no SQLAlchemy, no Alembic.**
- SQL lives in `harness/ledger/sql/*.sql`, one statement per file, loaded at import.
- Migrations: numbered `.sql` under `migrations/`, forward-only, applied by our own runner
  under a `pg_advisory_lock`.
- `pydantic` v2 for jig output schemas. `typer` for the CLI. `structlog` for logs.
- Tests: `pytest`, `hypothesis` for the predicate, `testcontainers[postgresql]` for real-Postgres
  tests. `ruff` for lint and format, `mypy --strict` on `harness/`.
- Synchronous code with one background **thread** for the heartbeat. No asyncio.
  Parallelism is N worker processes, one role each.

## Commands

```
uv sync                      # install
uv run pytest                # tests
uv run pytest -m "not slow"  # skip container tests
uv run ruff check . && uv run ruff format --check .
uv run mypy harness
uv run h3 db migrate         # apply migrations
make check-static            # rung 0; must stay runnable standalone
```

## Invariants — these are not style preferences

1. **All time comes from the store's clock.** No `datetime.now()` or `time.time()` anywhere in
   `harness/ledger/`. Clock skew between workers is real. (core §5.3)
2. **No unfenced write.** Every lease-guarded statement carries `id`, `lease_holder` and
   `attempts`. Pass a `Lease` value object; never the three fields loose. (core §5.5, rule 41)
3. **Never log the fencing token beside a task id.** Treat it as a capability.
4. **The content store is never queried.** Two methods only: `put(bytes) -> ref`,
   `get(ref) -> bytes`. No `WHERE` over `body`, no index on its contents. (core §4.3)
5. **No default tier, no default effort.** Absence is a config validation error, not a
   fallback. (rules 72, 107)
6. **Commit is a harness operation, not a card operation.** The card returns; the harness runs
   `pre_commit` hooks on the host and writes. (core §5.7)
7. **The reaper kills before it requeues**: kill container → drop clone → `git reset --hard` +
   `clean -fdx` → flip to pending. (rule 86)
8. **The ledger database and the workspace Postgres are different instances.** The ledger is
   never deleted and is backed up; workspace clones are dropped per attempt.
9. **Generated files are generated.** `__manifest__.py` and every `__init__.py` in the Odoo
   module are emitted by a hook. A card needing a dependency emits `spec_conflict`. (rule 78)

## Principles that decide arguments

- **The predicate is the scheduler.** Anything you would put in an orchestrator must be a
  dependency edge or a readiness rule.
- **Prefer the cheapest mechanism that can do the job.** Where a mechanical check and a model
  call cover the same ground, the mechanical check wins.
- **Every mechanism costs whether or not it fires.** A mechanism that never fires is a candidate
  for deletion, not a safety margin.
- **Checks a card can fix are visible to it; checks that establish trust are hidden from it.**
- **A deterministic sub-second transformation is a hook, not a card.**
- **Rule 62:** every documented failure mode names its symptom, why it hides, and its detector —
  or states that none exists.

## Banned

**Names.** `Agent` as a role suffix · `Orchestrator` / `Coordinator` / `Manager` / `Controller`
(if a class wants one of these names, the design is wrong) · `Swarm` / `Hive` / `Colony` ·
`Pipeline` · `TaskCard` · a `cards` table. In code it is `task`; *card* is prose only.

**Deleted, not deferred — do not reintroduce without an ADR carrying evidence.**
`judge`, best-of-N, per-card temperature (ADR-0002) · notification, relay, `outbox`, `Relay`
(ADR-0003) · per-tool quota, side-effect layer, in-card approval, fail-closed table (ADR-0003) ·
router · supervisor · compactor · formatter role.

**Anti-milestones — none of these is progress:** a dashboard before the queries are painful ·
a router · notification · a second content backend before the first is uncomfortable · a jig
that grew a second stage · depth before a measured per-level rate · any mechanism that has
never fired.

## How changes land

Three landing places, and there is no fourth (rule 133):

| Change | Lands |
|---|---|
| A section is wrong, incomplete or superseded | Edit the design doc in place |
| A decision, especially a deletion | A new ADR naming what it amends and what would reopen it |
| A new rule or risk | Appended to `docs/rules-and-risks.md`, numbered from that file |

**Do not create new design documents.** "We need a document to hold these changes" is the
sentence that starts the failure loop this project has already been through twice.
**Check `docs/rules-and-risks.md` before assigning any rule or risk number** — it has already
resolved three collisions.

## Working style in this repo

- Explore and plan before editing. Prefer plan mode for anything touching the ledger, the
  reaper or the workspace triple.
- When a task has a phase ID from `docs/h3-project-breakdown.md`, say which one, and restate
  its exit criteria before writing code.
- A task is done when it has a test, a named detector for the failure it prevents, and — if it
  is a mechanism — an answer to *has it fired?*
- Write the test first where the behaviour has a stateable semantic. The implementation must
  not edit the test.
- If you find yourself adding a mechanism the design does not name, stop and say so rather than
  adding it.
