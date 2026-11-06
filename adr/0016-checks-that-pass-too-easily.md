# ADR-0016: Four ways a check can pass without meaning anything

**Status:** Proposed. Draft for the owner's review.
**Date:** 2026-11-06
**Would amend:** core §4.1, §6, §8.1, §10, §11 (additions; no core §13 trigger applies); policy §3.8, §4.1;
`odoo-adaptation` §4, §8.3; rules 83, 145; ADR-0013 decision 3; `jig-sketch.py`; `harness/ledger/sql/`
**Would add:** rules 153–156; R65
**Guarded by:** the tests under each decision, none written yet
**Informed by:** `johnson-repos-borrow-notes.md` New 1, 2; `johnson-later-repos-borrow-notes.md` New 2, 3, 7.
The argument rests on this design's own paths. Probed here: pytest 9.2.0, and git 2.50.1 through rule 150's
runner. No Odoo or container.

## Context

Each of these satisfies the letter of rule 145.

- **RED has no reason.** The test "runs and **fails**" (`harness-policy-v3.md:478-479`, rule 83), and the
  inversion is "elided" (`jig-sketch.py:676-677`). A broken import satisfies it, and the implementation card,
  barred from the test (policy:480), quarantines (inferred).
- **Config errors fail open.** A kind with no rungs, or a typo in `kinds`, gives `not_applicable`
  (`jig-sketch.py:680-682`), then `done` (`001_initial.sql:92-93`). `rungs_for` drops a chosen rung that does
  not exist (`:669-671`). `validate_roles` never reads the ladder (`:245-255`), and `narrowed_rungs` has no
  definition (`:754`).
- **Nothing scores the base tree.** A touch set bars the fix, so a rung red on untouchable code fails every
  card selecting it.
- **An empty diff has no defined fate.** Confirmed, though partly because the path is unwritten. Any payload
  without a refusal is `ok` (`jig-sketch.py:626-632`), `commit()` is SQL only (`:836`), and the sketch has no
  `git commit`. In the probe, committing nothing exits 1. A build either raises (`harness_bug`, the wrong
  name) or swallows it and reaches `done`, unless a chosen rung sees the absence. `ghola`'s empty branch
  (`2866476`) motivates this and proves no rate.

## Decision

### 1. RED must be the right failure (rule 153)

`check_spec` stays `{rungs, expect}` (`harness-core-v3.md:163`). A rung's spec in `checks.yaml` says what
counts:

```yaml
red: {exit: [1], report: junit, reject: [ImportError, ModuleNotFoundError, NameError]}  # absent: no expect: FAIL
```

With `expect: FAIL`, such a rung holds if the run completes, its exit is listed, at least one test in a file
the card's diff changed reports `failure`, and those files report no `error` and no message starting with a
`reject` name. One is enough: the worked run's test card has a test that passes on purpose
(`worked-run-odoo.md:596-598`).

| pytest 9.2.0, probed | Exit | JUnit |
|---|---|---|
| Assertion fails | 1 | `failure` |
| Top-level broken import; no tests; named test missing | 2; 5; 4 | `error`; none; none |
| Import or `NameError` inside the test body | 1 | `failure`, message names it |
| Missing or raising fixture | 1 | `error` |
| Skip, xfail | 0 | `skipped` |

**Exits alone do not separate these,** so `red` is an allow-list plus a report, and an unlisted exit fails
closed. `red` is for visible `command` rungs. Startup refuses it elsewhere (rule 91).

**The timeout path does not invert.** `except (Timeout, BrokenPipe)` (`jig-sketch.py:692-695`) stays `failed`
and `SpawnFailure` stays `unavailable`, whatever `expect` says. The worked run's rung 2 has no
`--stop-after-init` (`worked-run-odoo.md:114`). If that leaves the server up, a naive inversion passes every
test card.

**A wrong-reason RED is `check_failed`,** charged and evidence, on the card that can fix it. Layer 7 shows the
rung's normalized output after one line from the classification: `expected a failing test; rung 2 exited 2,
allowed [1]`. Reports are never rendered.

**Odoo gets no `red` until a spike,** so its test cards are rejected at emit until then, deliberately. The
spike answers: does rung 2 exit by itself, and does its exit separate a failed test from a load error? Where
do per-test results come from (a log parser needs a rule 144 normalizer)? Is a missing model
(`odoo-adaptation.md:343-344`, §8.3) a failure or an error, and the wanted RED (open item 1)? Does a test
module with a broken import fail, log, or silently not run?

**Replay.** `red` renders in layer 8 and hashes through `check_ladder(k)` (`harness-core-v3.md:842`), so **it
moves `execute`'s prompts once, before any run exists,** then only on a config bump. Layer 7's line derives
from what replay re-executes (§8 point 2).

**Test:** each row classifies as shown. Timeout, and a pass, under `expect: FAIL` are `failed`.

### 2. Config cannot reach `done` by being wrong (rule 154)

**At startup, beside `validate_roles`, `ConfigError` unless:** every kind a role claims has rungs or is named,
and not both, in a new `not_applicable: [...]` in `checks.yaml`; every name in a rung's `kinds` is a claimed
kind; and `post_claim`, `pre_commit` and `post_commit` each have an implementation. Pluggy catches a
misspelled hook, not an absent one (`jig-sketch.py:132-133`). Hooks are global here, so New 7's "a role"
becomes "the process".

**At emit, in `plan_emissions` so every shape is covered,** `SplitRejected` (`malformed_output`, as now)
unless every rung in a `check_spec` exists for that kind, and `expect: FAIL` chose a rung with `red`.
`narrowed_rungs(k)` is that check followed by `rungs_for(k, "pre_commit")`, so gate and oracle cannot
disagree. A person's `edit` passes the same check.

`run_oracle` does not change: after startup, an empty ladder and a declared one are one fact, so the list adds
nothing to `kind_hash` and no bytes. `rungs_for`'s docstring (`:667-668`) changes: a `check_spec` may be
absent, a ladder may not.

**Test:** an undeclared kind, a typo in `kinds` and an unregistered hook each stop the process. An absent
rung, or another kind's, is rejected.

### 3. The base tree is scored once, at pin, and a red rung refuses the run (rule 155)

At run start, after the template is built and before any row (inferred: the pin is elided). Pin alone is
enough: neither the ladder (`harness-core-v3.md:815-817`) nor the root's base changes inside a run. It covers
every `pre_commit` rung of every kind, once each, hidden included. `split` and `verify` cards can never fix a
red rung, so theirs count. `post_tool_call` rungs cannot fail a card (`jig-sketch.py:537-539`). Cost: one
container, one clone, no model, about one ladder (`odoo-adaptation.md:273-276`).

**Red or `unavailable` refuses,** with a `ConfigError` printing the rung's output to the person. They fix the
tree, narrow the rung's file set to the card's diff, or remove it. There is no known-red ledger.

**A rung that cannot run on a base declares it:** `base: skip` or `base: {if_exists: <path>}`. The default
runs, so forgetting refuses loudly. Rung 3 compares against the whole schema, so it skips. Odoo's rungs 1 and
2 take `if_exists`: a new module's first run scores nothing, correctly, and a later run scores it. A skipped
rung that is red burns attempts as today, and the pin shows it.

**A test card does not collide.** The check ignores `expect` and `red`, on a tree holding no card's test. RED
is judged later, on the card's tree. **Recorded** in `runs.config_pin` as `base_check: {base_sha, rung id →
passed | skipped}`, ids per ADR-0015, with no output. No layer renders the pin, so hidden stays hidden
(principle 5).

**Replay does not run it.** It reuses the recorded pin, and a flaky rung must not refuse a replay. It enters
no prompt, `kind_hash` or cache key. **Not covered:** a rung red only on a tree earlier cards built, and
`odoo-adaptation`'s new-module assumptions, so the note's Odoo item is answered only in part.

**Test (Gate A):** a red rung refuses with no row. Red and `skip` starts, and the pin says so. `if_exists`
follows the path. A replay on a now-red base still runs.

### 4. An `execute` card must change the tree, or say why not (rule 156)

**`base_sha` is written by nothing.** `emit_task.sql:4` takes it and `shape_children` never supplies it
(`jig-sketch.py:733-745`). So provisioning stamps it, fenced, in one new statement: the commit the attempt's
worktree started at. On an `execute` card a NULL is `harness_bug`.

**The check** runs in `run_jig`, before the oracle and hooks, so it costs no clone and ignores a regenerated
manifest. On `ok` and `done_with_concerns`, through rule 150's runner: `add -A; write-tree`, compared with
`rev-parse <base_sha>^{tree}`. That settles how the harness stages (ADR-0014:199). In the probe a self-commit
with changes reads empty against `HEAD`, and its `git commit` exits 1, while this form reports it correctly,
as it does a planted `.git` and a commit-then-revert. `diff_paths()` should read against `base_sha` too. It is
not a rung or hook: it names no command (rule 137), and either can be left out (ADR-0013).

**Equal raises `HarnessFailure(NO_DIFF)`.** `no_diff` joins `FailureClass` and `EVIDENCE`, charged through the
existing handler (`jig-sketch.py:880-886`). Layer 7 shows the class and `no change against the card's base`,
moving the retry's key like other evidence.

**It applies to every `execute` card,** including a test card, where an old failing test could otherwise
satisfy RED. `split`, `verify`, `re_verify` and `digest` are exempt because their output is the payload, and
`integrate` because its check is the merged tree (`odoo-adaptation.md:913`).

**When no change is right: `no_change`,** a new outcome on `execute` only. It is a refusal: no oracle, parked
by `park.sql`, `check_result` NULL, so it cannot read as a pass. Core §7 has no verb that reaches `done`:
`approve` returns to `pending`, and `kill` leaves dependents held. So a person's `edit` changes the contract
or sets `check_spec.allow_empty: true`. The card runs once more and returns `ok`, the ladder must pass, no
commit is made, and `result_sha` is `base_sha`. It lands through fenced `commit.sql`, with no new verb.
Emission rejects `allow_empty`, so a splitter cannot grant it.

**Replay.** `no_change` and its rule enter layer 0 (policy:619), **moving `execute`'s prompts once, before any
run exists.** `allow_empty` moves layer 5, as any `edit` does. ADR-0014 left replay of a person's actions
open.

**Test:** empty diff is `no_diff`, charged. Self-commit, not empty, passes. Commit-then-revert is `no_diff`.
`no_change` parks. `allow_empty` by `edit` reaches `done` with the ladder run, and at emit is rejected.

## Open for the owner

1. **What tree does a dependent card start from?** Found while tracing. The test card depends on the model's
   card (`worked-run-odoo.md:217`), and its partner must pass that test, yet the worked run provisions at
   `<base-sha>` (`:304`), and two siblings each "saw only its own branch" (`:701`). No document says how deps'
   commits arrive. This decides whether Odoo's RED is a missing model or a behaviour. Recommend merging `done`
   deps at provision and stamping after, which decision 4 allows. It needs its own trace before the spike.
2. **`no_change`, or `refused` with a detail?** Recommend new: `Outcome` exists so reasons don't fragment
   (`jig-sketch.py:612-615`). An `accept` verb would spare a model call, but opens a route to `done` around
   the fence.
3. **Refuse a red base, or list it known-red?** Recommend refuse. A loud linter on an existing codebase is the
   case against, and narrowing its file set answers it.
4. **Keep `reject`?** It can over-reject. Recommend keeping it for pytest, and letting the spike decide for
   Odoo.

## Not decided here

The test-first pairing gate (the note's item 1), depth limits, unknown cost, the declared-things test,
ADR-0010 item 6, the amendments ledger, and a green summary surviving a failed rework. How a held RED reads in
the record, so it isn't counted a catch, is ADR-0015's.

## Alternatives considered

**Exit codes only,** as the note proposes. A missing fixture and a `NameError` both exit 1. **`no_diff` as
`check_failed`.** It reads as a rung failure with no rung behind it, and spends a clone first. **Base check at
provision.** A ladder per attempt, for one answer. **Only new rungs.** It must diff pins, and misses a base
that moved.

## Consequences

**Good.** A test card answers for its own RED. A config typo stops the process. A rung that cannot pass stops
one run, not a board.

**Costs.** Odoo's pairs wait on a spike. One outcome, one class, one statement, one `checks.yaml` list, two
rung keys. Each run start pays a ladder, and a flaky rung refuses a run.

**R65: RED can still be wrong.** A test can fail on an unrelated assertion or an exception `reject` omits.
This shows it failed in a tested way, not that it is a good test. No mitigation beyond verify and the
implementation card.

**Not measured.** Only the two probes ran. A card's self-commit probably cannot move the real branch here,
since the container has no route to it (inferred), so that test guards the check's form, not a path seen in
this design.

## What would change our mind

- **The spike shows Odoo cannot separate these** → RED there is exit-only, R65 grows, and policy §3.8 says so.
- **`reject` refuses a right failure in the first runs** → drop it.
- **`no_diff` fires mostly on cards right to change nothing** → the splitter's contracts are the problem.
- **No run by step 7 refuses at base or hits `no_diff`** → principle 8: that decision is margin.
