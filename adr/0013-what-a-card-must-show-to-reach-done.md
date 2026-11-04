# ADR-0013: What a card must show to reach `done`, and what a retry may learn

**Status:** Accepted. The owner delegated these decisions on 4 November 2026.
**Date:** 2026-11-04
**Amends:** core §4.1, §5.4, §5.7, §6, §7, §8, §9.4, §10, §11; policy §2.2, §4.1 and its failure table;
ADR-0006 (`misclassified`); ADR-0011 decision 4; ADR-0012's retry table; rule 68; `jig-sketch.py`;
`harness/ledger/sql/`; `queries/`
**Adds:** rules 145–149; R63
**Guarded by:** the `done_means_checked` constraint; `tests/ledger/`; core §11's new tests
**Informed by:** an independent audit of the reconstructed schema, and an adversarial review of the first
draft of this decision, which changed all four of its answers. Neither ran the design.

## Context

Reconstructing `001_initial.sql` and running core's SQL against it showed that the design's state machine
had never been traced end to end.

- **A failed check can reach `done`.** `commit()` maps state from outcome alone, so `ok` with a failed
  oracle commits as `done` and releases dependents. `done_with_concerns` skips the oracle entirely.
- **The sketch writes states the enum rejects:** `blocked`, `needs_review`, `refused`.
- **`misclassified` has two contradictory routes.** Policy and the worked run replace the card with no
  person. ADR-0006 and the sketch send it to review.
- **A dotted replacement would not hold dependents.** A `done` parent with a quarantined child passes
  both predicate clauses, recreating ADR-0006's missing interface.
- **`retry_safe` does nothing.** Nothing sets it, and the reaper never reads it.
- **A dead worker's retry pays twice.** It raises effort and renders the dead attempt in layer 7, so every
  cached call misses, though a crash says nothing about the work.
- **Nothing writes `tier`,** though the claim filters on it, so escalation has no mechanism.
- **A late commit can land after teardown.** The reaper removes the branch of an expired lease, the paused
  worker wakes with a matching fence and commits, and the row is `done` with no branch for `integrate`.
- **The record forgets.** A later commit overwrites `outcome`, so core §9.4's `needs_context` count falls
  to zero once a person answers and the card succeeds.

## Decision

**1. The six states stand.** No state is added. Each outcome lands as follows:

| Outcome | State |
|---|---|
| `ok`, `expanded`, `done_with_concerns` | `done`, if the check allows it (decision 3) |
| `needs_context`, `spec_conflict`, `blocked`, `refused` | `awaiting_review`, lease cleared |
| `misclassified` | see decision 2 |
| `exploration_cap`, `schema_violation` | `failed` |

`awaiting_review` holds dependents under clause (a), the reaper does not select it, and core §7's verbs lead
out of it. The worked run already routes `needs_context` and `spec_conflict` there.

**2. A misclassified card becomes a `split`, on the same row.** Kind, tier and `config_hash` change, and
the state returns to `pending`. Clause (a) then holds dependents, because the row is not `done`. The worked
run shows this shape: the children of `t-7c21.9` sit directly under it. It is the kind ratchet applied to one
row. A `split` that reports `misclassified` goes to `awaiting_review`, so no chain can form, and the prose
cap on refusal loops is no longer needed. Core §7's `split` verb uses the same rewrite.

**3. The hidden oracle decides, and the database enforces it.** Rule 145.

- `passed` commits. `not_applicable` commits only for `expanded`, or for a kind with an empty ladder. Emission
  rejects a `check_spec` that selects no rungs on any other kind.
- `failed` goes to state `failed`, charged, as `check_failed`. A rung that started and then timed out is
  `failed`, because the card's own code may have hung it.
- `unavailable` means a rung could not start. It is a free class, `check_unavailable`. Past
  `runs.max_free_retries` the card goes to `awaiting_review`, not quarantine, because quarantine would release
  dependents over unchecked work.
- `done_with_concerns` runs the oracle like any other completion.
- Enforced three ways: `CONSTRAINT done_means_checked` on `tasks`, a literal `state='done'` with
  `AND state='leased'` in `commit.sql`, and a separate `park.sql`. Not by a hook: hooks are config.

**Hidden output stays hidden.** It is stored in `task_attempts.hidden_check_ref`, and layer 7 renders only *a
hidden check failed; output withheld*. Visible rungs' output is rendered as before. Failing a card on a hidden
check is what principle 5 asks for. Showing it the output would hand it the oracle.

**4. A person's way back cannot strand the card.** `review_return.sql` sets `max_attempts` to at least
`attempts + 3` and never lowers `attempts`. The verb sets a new deadline and records it in `reviews`, because
time spent in review can otherwise expire the card on return.

**5. A failed `retry_safe: false` card goes to review, with its evidence.** Rule 149. This covers any failure,
including a dead worker, and drain. `provision_failed` is exempt, because no work ran. The reaper still kills
the container, but keeps the worktree and database until the verb. Worktrees are per attempt (ADR-0011), so a
kept one blocks nothing. `retry_safe` is carried through emission.

**6. Only evidence about the work changes what a retry sees.** Rule 147. `lease_expired`, `stalled`, free
classes and parked outcomes are not evidence. Layer 7 and the effort rung count evidence attempts alone, so a
retry after a crash has a byte-identical prompt, keeps its effort, and serves earlier calls from cache.

`attempts` still counts every delivery, so the crash-loop bound holds. **The last delivery still escalates, by
position** (rule 68), because identical retries of a work-caused crash would otherwise repeat exactly. The worked
run shows a reap from CPU saturation that an escalation then passed. A free flip never escalates.

**7. Escalation is written.** `escalate_tier.sql` sets `tier` and `config_hash` in the flip's transaction. The
effort rung is read at claim from the evidence count.

**8. The reaper revokes before it tears down.** Rule 148. `reaper_revoke.sql` clears `lease_holder`, rechecking
the expiry, so a late commit's fence fails and a worker that heartbeated in the gap keeps its card. The row stays
`leased` until the flip, so nothing can claim it mid-teardown, and a reaper that dies here leaves it selectable.

**9. Attempts remember why.** `task_attempts` gains `refusal jsonb`, holding the payload of a parked or
misclassified attempt, and a parked attempt records its outcome as `failure_class`. Core §9.4's first three queries
read attempts rather than the card's current `outcome`.

**10. `queries/stalled.sql` follows clause (b) as well as deps,** since ADR-0006 is safe only if stalls are visible.

## Alternatives considered

**Add `blocked` and `refused` as states.** More legible on the board, but every predicate and reaper clause would
have to learn them, for behaviour `awaiting_review` already has. `outcome` carries the difference.

**Keep the replacement as a dotted child of a `done` parent.** Quarantine of the replacement releases dependents,
and a jig with empty `emits` releases them at once.

**Send every `misclassified` card to a person.** Safe and simple, and the fallback if the rewrite misbehaves. It
puts a person in front of a decision the design and worked run make without one.

**Quarantine past the free limit for `check_unavailable`.** Clause (b) accepts a quarantined descendant, so a broken
oracle would release dependents over unchecked work.

**Halt the run on `check_unavailable`.** ADR-0011 halts only on unambiguous signals, and a failure to start a rung
may be one card's problem. R63 records the cost.

**Make `lease_expired` free.** Weakens the crash-loop bound, as ADR-0011 argued.

**Count `stalled` as evidence.** Busy loops keep stamping, so "too hard" is not silence. What silence shows is a
hung tool or a long check, and the oracle now stamps between rungs.

**Enforce the oracle in a `pre_commit` hook.** A misconfigured hook list would silently reopen the hole.

## Consequences

**Good.** No card reaches `done` unchecked, and the database says so. A crash no longer discards a card's cached
work. Late commits cannot strand `integrate`. The lessons queries survive a rerun.

**Costs.**
- **`tasks.kind` is no longer permanent.** The attempt row records what the card was. A content-derived id still
  reflects the original kind, so re-emitting the original no-ops, which is the wanted behaviour.
- **A broken oracle spends each card's free retries before anyone notices (R63).**
- **Three more statements and two more columns,** plus a sweep exemption for kept workspaces.
- **Worked runs show older routes.** They are read-do-not-edit, and policy takes precedence.

**Not measured.** The SQL is exercised in `tests/ledger/` on Postgres 16. No worker, model or container has run
any of it.

## What would change our mind

- **Rewritten cards are hard to read in the tree** → return to a person-gated `split`.
- **Ten runs with no late commit, and no revocation that saved a live worker** → rule 148 is margin; principle 8 applies.
- **Identical retries after a crash reproduce the crash in most cases** → stop serving them from cache, or escalate sooner.
- **A card repeatedly fails hidden checks it could fix with the output** → that rung should be visible, per rule 91.
- **`check_unavailable` parks cards from an outage that later clears** → raise the limit, or build ADR-0011's circuit breaker.
