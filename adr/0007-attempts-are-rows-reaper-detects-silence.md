# ADR-0007: Attempts are rows, and the reaper detects silence and backs off

**Status:** Accepted
**Date:** 2026-11-03
**Amends:** core §3.1 (`Budget`), §4.1, §4.2, §4.4, §5.3, §5.4, §5.7, §6, §10, §11, §12;
`odoo-adaptation` §6.3; rule 94; R57
**Guarded by:** the `stalled`-then-succeeded rate; core §11's kill tests; core §10's new rows
**Informed by:** OpenAI Symphony `SPEC.md` and Databricks, "Simplify AI agent orchestration with
Lakebase Postgres", both read 3 November 2026. Neither has been run here.

## Context

Reviewing both designs against core found the queue mechanics already covered, and more strongly:
`SKIP LOCKED`, priority ordering, leases and a sweep are all present, and fencing and kill-first go
further than either source describes. What they showed up is the edges of those mechanics:

- **The record cannot answer per-attempt questions.** `tasks` holds one `failure_class` and one
  `model_used`. `model_calls` holds per-call cost, but nothing holds what an attempt was: when it ran,
  who ran it, why it ended, what its check said. `ledger.last_attempt()` in `jig-sketch.py` reads a
  row core never defined. Policy §10 names the record as the sole differentiator.
- **R57 has no detector.** A worker can heartbeat indefinitely with a hung loop.
- **`not_before` exists and nothing sets it.** A reaped card is claimable immediately, and each try
  costs a container, a clone and an install.
- **`failed` is documented as reaped back to pending, and the reaper never selected it.**
- **"The lease row carries its id" names a column §4.1 does not have.** A worker that dies before
  writing it would leave an unkillable container.
- **§6 does not say what a workspace failure does.** In the sketch, a Postgres blip during a template
  clone reaches the generic handler and quarantines a healthy card as `harness_bug`.
- **`Budget` is one line in the vocabulary**, with nowhere defined for its state to live.
- **The reaper as written did not parse.** Its `CASE` resolves to `text`, which Postgres will not
  assign to `task_state`. Found by running it on Postgres 16 while testing this change; now cast.

## Decision

**`task_attempts` is added, keyed `(task_id, n)`.** A row is written in the claim's transaction and
closed in the transaction that ends the attempt. The name and key are the ones `initial_plan.md` §3c
already chose. Cost stays in `model_calls`; the row does not duplicate it.

**The reaper gains a stall clause.** The card loop stamps `last_progress_at` on each model response
and each finished tool call. The reaper treats `last_progress_at + stall_after < now()` as it treats
an expired lease, recording `stalled`. Silence only: it claims nothing about whether the work is
useful.

**The reaper flips per row, after teardown, sets backoff, and also collects `failed`.** Backoff is
`min(10 s × 2^(attempts-1), 5 min)`.

**A free retry raises `max_attempts`; it never lowers `attempts`.** `attempts` is the fencing token
and `n`. Lowering it would reuse a fence and collide on the primary key.

**Workspace names derive from the card id and attempt**, so the reaper can kill what a dead worker
never recorded. A path outside the workspace root, or a database name that is not `card_*`, refuses
teardown rather than running it.

**Workspace failures have defined outcomes.** Provisioning failure consumes an attempt and retries as
`provision_failed`. Failure to kill or reset **blocks** requeue. Failure to drop an attempt's database
is logged and does not.

**`Budget` is a claim-time query**: summed `model_calls` cost against `runs.max_cost_usd`. It is in
the claim and not in `ready(t)`, which stays a pure function of the graph. The limit lives on `runs`
and not in the pin, so raising it does not change what any card saw.

## Alternatives considered

**Keep the history in `model_calls` alone.** It carries `(task_id, attempt, seq)`, so attempts can be
inferred. Rejected: an attempt that died before its first model call leaves no row, and that is the
case the record most needs to explain.

**Leave R57 as a residual until a stall is observed.** Core §5.4 said it reopens on observation, and
**no stall has been observed here**, because nothing has run. This is the serious alternative, and
this ADR overrides it on cost: one column, one clause, and a false positive costs one attempt.
Should the false-positive rate come back high, this alternative wins (below).

**Symphony's stall detector as-is.** Adopted in shape. Its 5-minute default is not: an Odoo test rung
can run longer, so `stall_after` is set per role and must exceed the longest tool and model-call
timeouts.

**Symphony's rule that cleanup failures are logged and ignored.** Rejected for kill and reset. Its
rule covers hooks around workspace use and removal, under one orchestrator that owns its workers.
Here, requeueing past a failed kill or reset is the exact failure kill-first exists to prevent. Kept
for dropping a per-attempt database, whose name a retry never reuses.

**Hash suffix on sanitized workspace names (Symphony).** Rejected. Card ids are a hex hash plus dotted
segments, so mapping `.` and `-` to `_` cannot collide. An over-long name fails provisioning instead,
because Postgres truncates identifiers past 63 bytes without an error.

**An in-memory token bucket for `Budget`.** Rejected: per-worker state that resets on restart, in a
design whose premise is that no component holds state. **A lock around the budget check** is also
rejected: it would serialize every claim to prevent a small overshoot.

**Symphony's `WORKFLOW.md` hot reload.** Rejected. It contradicts the config pin (core §8.1, R60).

**Symphony's in-memory scheduling state.** Rejected. It gives up the record this design exists for.

**Symphony's per-state concurrency limits.** Not needed. A worker runs one role for life, so worker
count already sets the limit.

**Databricks' `LISTEN/NOTIFY`.** Rejected, unchanged from ADR-0003. Databricks keeps polling as a
permanent fallback anyway, because streams through proxies drop silently.

## Consequences

**Good.** Every attempt is explainable, including ones that died early. A hung loop ends before the
deadline. Retries stop hammering an outage. Reaped containers are always findable.

**Accepted costs.**

- **Core §5.4 argued against this shape.** It says inferring stuck work from stale timestamps is a
  judgement that needs a check, and that is what the chain of watchers it criticizes exists to do.
  The stall clause is narrower, since it asserts silence rather than uselessness and a wrong call
  costs one attempt, but it is the same kind of signal, and the claim that the reaper has no
  judgement to get wrong is now weaker. No second watcher is added; the check on it is a query.
- **Busy loops remain a residual (rule 62).** A loop that keeps making calls is never silent. The turn
  limit and `deadline_at` bound it; nothing detects it.
- **Free retries have no attempt ceiling.** With `max_attempts` rising, only `deadline_at` bounds
  them, and it is nullable. Backoff limits the rate, not the total.
- **The budget can overshoot.** Concurrent claims each see the same sum, and in-flight cards spend
  after being admitted. It is a brake, not a guarantee.
- **The claim query gains a correlated sum**, which R15's `EXPLAIN ANALYZE` must now cover.
- **A blocked teardown stalls that card visibly** rather than failing it. This is deliberate, and it
  is the same inert failure mode core §5.4 relies on.

**Evidence.** The claim and reaper SQL were run on Postgres 16 against a stub schema: stall, expiry,
backoff and its cap, stale flips, budget refusal, and 20 concurrent workers on 10 cards. That shows
the SQL behaves as specified, not that the mechanisms are worth having. No stall or crash has been
observed, because this design has not run, and both sources are designs read, not systems run. The
`failure_class` values, the 5-minute cap and all time limits are unmeasured. Teardown has no code to
test yet.

**Follow-on work required.**

- `001_initial.sql` is not in this checkout. It needs `task_attempts`, `tasks.last_progress_at`,
  `tasks.stall_after` and `runs.max_cost_usd`: edited in if unapplied, or added as a new migration.
- `jig-sketch.py`: add `provision_failed`, `stalled` and `released` to `FailureClass`; stamp
  `last_progress_at` in the loop; stop routing provisioning errors to `HARNESS_BUG`.

## What would change our mind

- **More than a third of `stalled` attempts succeed on retry with no config change, across at least
  20 stalls.** The clause is killing live work: raise `stall_after`, and if that does not fix it,
  delete the clause and return R57 to a residual.
- **Ten real runs with no true stall.** The clause is margin and is deleted, as rule 121 treats a
  skill with no reproducing case.
- **A hung worker is observed that kept making model calls.** Then silence is the wrong signal, and
  this is the evidence for a real progress measure.
- **A run overshoots its budget by more than one card's typical cost.** The brake is too loose and
  the lock rejected above is reconsidered.
- **No lessons query ever reads `task_attempts`, and step 7's record question is answered without
  it.** The table is over-build.
