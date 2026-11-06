# Borrow notes

**What this is.** A reading record of other harnesses and one book, plus the open items from that reading, organised by
what would change in this design. It consolidates seven per-source notes.

**Status.** Nothing here is adopted until it moves into a document, an ADR, `rules-and-risks.md` or code. When an item
moves or is rejected it leaves this file, so the file should shrink. Ids are stable and not reused. Rule 133 names three
places for changes and this file is outside them, which is an open question for the owner.

## Basis

Subagents read the sources, and the main thread rechecked the decisive claims against the source and this repo. Nothing
was run, neither the sources nor this design: every trace through `jig-sketch.py` or the SQL comes from reading.

- "Not found" means by keyword search, which is not proof of absence.
- *(unchecked)* means one subagent's reading. *(docs)* means that project's READMEs, notes or postmortems, not its code.
  "Inferred" means reasoned, not traced.
- `repo:path:line` is another project's path, using the prefixes below and the notes' abbreviations (sigma under
  `internal/`, open-refinery under `src/open_refinery/`). `repo:hash` is a commit. Plain paths are this repo's. `p.N` is
  a book page: the PDF page is N + 22.

The sources' evidence is thin, and the book's author says so of their own tools: "watched evidence, before-and-after
observation with no control arm" (p.386). Read every item as a question to put to this design, not as proven practice.

## What was read

| Source (prefix) | Commit | Date | What it is | What its evidence is worth |
|---|---|---|---|---|
| DeepSeek Harness (`dsh`, code under `packages/`) | `8bd07339` | 2026-11-03 | Plugin-built TypeScript harness | Source, four strands. Postmortems most useful per line. Has run |
| `dsh-superagent-prototype` (`superagent`) | `8c32a9dc` | 2026-10-31 | Prototype beside it | A few items, all *(unchecked)*. Its article was not read |
| Pi (`pi`) | `1bc7076` | 2026-11-03 | TypeScript coding agent 1.5.0 | Loop in source; `pi-durable` and evals from docs; provider tests by name |
| Jig (`jig`) | `d9740470`, glossary `986c1f70` | 2026-11-03, 11-04 | Plugin and templates | Docs and glossary only. Modules and `drive-pr` not reviewed |
| OpenCode (`opencode`, under `packages/`) | `93f30ca` | 2026-11-04 | TypeScript agent v1.19.5 | Source, two strands. Serialization, compaction body not read. Has run |
| *Harness Engineering*, Ian Johnson (`p.N`) | none | 2026-07-22 | Leanpub, 844 pages | About 680 read closely. Anecdotes, one a composite. Its numbers are others' or illustrative |
| `tacoda/keystone` | `62ccdac` | 2026-07-01 | Charter framework, Go, 21k lines | v4.0.0, four majors in 23 days. No outside use visible |
| `tacoda/sigma` | `3ca5e35` | 2026-07-15 | Coding-agent CLI, Go, 6.9k lines | v0.0.1, "an experiment" (p.818). Two cases, one repeat, no model |
| `tacoda/open-refinery` | `daf65a8` | 2026-09-28 | Factory control plane, Python, 14k | "No live model call has been exercised" (`LIMITATIONS.md:125`) |
| `tacoda/constraint-engineering` (`ce`) | `9906bb2` | 2026-09-15 | Seven skills from the book | Two commits, no evals, model-assisted. Weak evidence of later judgement |
| `iii-harness-layers-and-promotion` (`iii-layers`) | `933a7bb` | 2026-08-21 | One rule at six rungs | An afternoon, 40-line seed. 12 live runs, gitignored, can't be recomputed |
| `iii-blackboard` | `ada9d48` | 2026-08-26 | Blackboard built two ways, 430 lines | One commit, against a stub |
| `ladder` | `a5725b6` | 2026-08-29 | Constraints and capabilities on one ladder | No model calls and no run data |
| `learn-harness` | `5a40fa3` | 2026-09-15 | Study path through LangChain | Mostly vendor-doc summaries |
| `hands-on-iii` | `3b9566b` | 2026-10-11 | Code for a second book, on iii | 13 commits in 87 minutes, a recut. That book and iii not read |
| `pi-config` | `9a5d975` | 2026-10-20 | The author's config for pi | Looks used; "daily" is inferred. 15 installed packages not read |
| `charter-workshop` (`workshop`) | `81a2851` | 2026-10-28 | Workshop measuring a charter | 16 forks in 15 minutes. No arm has repeats. One fork read (`singularityhacker`, `cde7f2e`) |
| `tacoda/ghola` | `e536a9a` | 2026-09-02 | Harness and factory on iii's stock worker | Read for one question: real runs. Code not reviewed |

**1. The book describes more than the code does.** Read its mechanisms as arguments, not reports of practice, and no
item below can cite the author's practice as support. Keystone and sigma stopped before publication and open-refinery
was rewritten after it, so whether each claim held in July was not checked.

| Book | Code |
|---|---|
| "the engine picks the locked rule, logs the conflict, and surfaces it" (p.139) | Not implemented: the project wins, `strict` unread (`keystone:internal/framework/charter/charter.go:166-173`) |
| Open-refinery "does not run a lease-based retry queue" (p.675) | Reversed by `open-refinery:bbdc9af`: a claim, a 900-second stale takeover, no fence |
| "checked before the call that would cross it" (p.529) | The crossing call fires, and a test asserts spent 12 of limit 10 (`sigma:agent/modelstack_test.go:50-60`) |
| Rooting is "the same defense" as a `realpath` check (pp.494, 496) | `rooted()` is lexical, and an empty root is unconfined (`sigma:internal/tools/paths.go:12-23`) |
| Sandbox read-only "except the working directory" (p.496) | The model picks it: `{"dir":"/"}` makes everything writable (`sigma:tools/bash.go:35,62`) |

**2. Only two jobs were traced end to end, and both changed a README.** `tacoda/fawlty` PR #1 (+66 −1) and PR #2 (+12,
one reviewer-driven rework) ran under `ghola`, on iii's stock `harness` worker, not the author's own loop. The author is
the commenter and the merge account. There is no cost or turn data, and nothing shows a harness catching a real problem.
What the jobs found is in B48.

**3. The author's own daily config is thin.** `pi-config` is a stock agent, Claude Code on a subscription
(`pi-config:agent/settings.json:3-4`), and 172 lines of instruction, against 10.2k in Keystone's charter. No budget
ceiling, sandbox, contract or daemon was found. It is one public config for one person at a keyboard, so it doesn't
answer the background-execution case.

## Before the first run

In this order. All are small. The first and fourth can't be recovered afterwards.

1. **`rung_results` with stable rung ids:** B1, ADR-0015.
2. **`expect: FAIL`'s right-reason check,** or B13's gate is hollow: B9, ADR-0016.
3. **Config that can't reach `done` unchecked:** B10, ADR-0016.
4. **Stored wire requests:** B2, ADR-0015.
5. **The declared-things test,** which finds the remaining holes: B45.
6. **The base-tree check:** B11, ADR-0016.
7. **The empty-diff check,** the only change the `ghola` data forces: B12, ADR-0016.
8. **Depth:** B28.
9. **Unknown cost:** B68.

Three more cost little now and can't be recovered after: frozen attempt inputs (B3), repeat samples (B50) and where tool
calls execute (B36). Two are defects in what is already written: the test-first gate (B13) and the failure routes
(B23-B27). As soon as a jig exists, before any experiment: a real job of this size (B48).

## Open items

Ranked within each area. "There" is the source; other citations are this repo.

### The record

- **B1. No record of which rung failed: `rung_results` with stable rung ids → ADR-0015 (draft), decision 1.**
  `CheckResult` has no rung (`jig-sketch.py:695-697`), and the column was lost after `initial_plan.md:279`. One inserted
  rung cost the author a remap (`iii-layers:77cb5f1`).
- **B2. The record doesn't keep what the model saw: stored wire requests → ADR-0015 (draft), decision 2.** `prompt_ref`
  is written before the turn loop (`jig-sketch.py:560`). There:
  `ce:skills/agent-orchestration/references/templates.md:306` *(unchecked)*. Secrets stay open: B56.
- **B3. Frozen attempt inputs → ADR-0015 (draft), decision 3.** "Did a person loosen the check before this went green?"
  can't be answered (`001_initial.sql:106-121`). There: pp.699-702. A point it might miss: `downgraded_from` on a
  persisted result (`open-refinery:pipeline/contracts.py:88-93`).
- **B4. Nothing records which tree was checked.** `task_attempts` has `check_ref` and `diff_ref`, with no tree or
  counts; when `tasks.result_sha` is written was not traced. There: Jig's evidence record (command, exact tree, exit
  code, test counts; a later edit voids it), and a dirty-tree capture with a separate git dir
  (`opencode:core/src/snapshot.ts:95-97`), whose failed capture only warns (`:146`). Change: hash the exact tree through
  rule 150's runner.
- **B5. A hung tool leaves no row,** because the sketch audits after `t.fn` returns. There: flush before `tools/execute`
  (`dsh:session/session-checkpoint-policy/src/index.ts:70-75`). Change: insert at dispatch, update at finish. An
  `allowed` row with a NULL `duration_ms` then means unknown. No new column.
- **B6. Immutability is prose.** Rules 94, 96 and 151 have no `CREATE TRIGGER` or `REVOKE` behind them. There: p.699.
- **B7. A `Card:` commit trailer** for human edits outside the board (`worked-run-odoo.md:284`). There: pp.422-423
  *(unchecked)*. Already drafted in `files/intake-and-review.md`.
- **B8. A "nothing needed" outcome.** `superagent:prompts/work.md:45` has `dropped` *(unchecked)*. Decide in policy §4.1
  whether the record should tell it from `ok`.

### Checks and oracle

- **B9. `expect: FAIL` can't tell the right failure → ADR-0016 (draft), decision 1.** There:
  `ce:skills/agent-primitives/references/skeletons.md:40-42`, p.767, and "a timeout killed Vite"
  (`dsh:docs/postmortem/0003-web-agent-gui-feedback-loop.md:36`).
- **B10. Config errors fail open → ADR-0016 (draft), decision 2.** There:
  `ce:skills/agent-harness-building/SKILL.md:178` *(unchecked)*, `pi-config:agent/extensions/preset.ts:437-446`
  *(unchecked)*.
- **B11. A new rung can fail on code no card may touch → ADR-0016 (draft), decision 3.** There:
  `iii-layers:docs/RESULTS.md:275`, the workshop fork's C8.
- **B12. An empty diff may pass → ADR-0016 (draft), decision 4.** There: the workshop's scorer gives one 8/8
  *(unchecked)*; `ghola:2866476`.
- **B13. Test-first pairing has no gate.** Policy calls it "✓ — load-bearing" and "a hard rejection, not a warning"
  (`harness-policy-v3.md:476-491`), but the emit gates pair nothing (`jig-sketch.py:750-757`), and the `split` model
  writes `check_spec`. R35 says this pairing alone caught the inverted security rule, on a walkthrough. Keystone lacks
  p.139's lock, so this rests on R35 and policy §3.8. Change: lock a rung in `checks.yaml` when a card cites an anchor
  key carrying `semantic:` or `test:` (`odoo-adaptation.md:343-344,404`; rule 101). Reject a split unless each
  implementation card citing such a key depends on an `expect: FAIL` test card for that key. Not on paths, which would
  reject structural cards. `odoo-adaptation.md:285-286` says the splitter "must justify omitting rung 2", and no field
  carries that. For rule 31 against rule 137, rule 31 and the lock are a floor that "may go higher, never
  lower", and departures are flagged (`ladder:src/load.py:274,287`, `src/parse.py:103-115`). One sentence in rule 137.
  Needs B9.
- **B14. A rung that runs no tests passes.** Rule 145 stops an empty selection, but `run_oracle` reads only `r.ok`, so
  zero tests reporting ok reaches `done`. There: Jig's skip tripwire. Change: a check fails if it ran zero tests,
  reporting `started`, `exit_code`, `timed_out` and `tests_ran` separately.
- **B15. A restart mid-rung is charged as `failed`.** `run_oracle` returns `unavailable` only for `SpawnFailure`, so
  `BrokenPipe` is charged, against ADR-0011. There: `dsh:subprocess/subprocess-local/src/linux-scope.ts:261-282`
  *(unchecked)*. Change: a harness-owned shim could record the start, on a mount the card can't write.
- **B16. An existing test can be rewritten to pass.** Rules 82-83 cover paired cards only. There: "11 passed, gate
  clean, `done`" (`iii-layers:docs/RESULTS.md:299`), n=2. Change: in the test-file guard
  (`jigs-layers-skills-v2.md:103`), a commit hook rejects a behavioural card whose diff edits a test that existed at
  base. A few lines.
- **B17. The cheap check runs after the expensive one.** The touch-set hook (`jig-sketch.py:872`) runs after the oracle
  (`:571`), though policy calls that hook among the highest-firing and cheapest (`harness-policy-v3.md:441-442`). With
  no class, a raising hook lands on `HARNESS_BUG` (inferred). There:
  `ce:skills/harness-engineering/SKILL.md:62`. Change: run it first, give it a class, add it to B27.
- **B18. Hooks decide outcomes but sit outside the pin** (`jig-sketch.py:134-135`), though core hashes hidden rungs for
  that reason (`harness-core-v3.md:864-865`). There: pp.226, 240. Change: the role's hook list and versions go in
  `kind_hash` and the pin, with a hash-stability test.
- **B19. The hook runner has no timeout, verdict shape or test at its exit.** Part of R64: a hook hanging on a card's
  file strands a worker. There: pp.243-244 fail closed. Copy `{code, stdout, stderr, timedOut}` and a pure
  `verdict(runs)` (`pi-config:agent/extensions/claude-charter/charter.ts:385,424`) at `run_hooks`
  (`jig-sketch.py:868,872`), about 30 lines, inverting its policy, since a timeout passes there. Kill the process group
  (inferred). One test: a failing or hung `pre_commit` hook leaves the card not `done`, since Keystone's sensors could
  not block and the suite stayed green (`keystone:cmd/keystone/hook.go:68-70`, `keystone:08ab8a3`).
- **B20. The pressure will be to loosen rungs.** There: false alarms were fixed by weakening the check, as in
  `go vet ./... || true` (`keystone:6d79e37`, `open-refinery:0615b2e`). Change: protect `CHECK_UNAVAILABLE`
  (`jig-sketch.py:65`), and track false-fire rate per rung.
- **B21. An already-red base charges each card `check_failed`;** no class for it was found. There: Jig's fresh-base
  probe reruns a failing test on the base before blaming the change. Only for tests already on the base.
- **B22. Allowlists can go stale.** There: Jig's entry fails the gate once it no longer suppresses anything.

### Failure routes and exits

There, for B23-B27: p.449, pp.659-665 ("every loop has a BOUND", "an EXIT HATCH"), the best single chapter for this
repo, pp.666-671, p.688. The author's code is no precedent: `failed` has no exit in open-refinery or `hands-on-iii`
*(unchecked)*.

- **B23. Quarantine holds gates and releases everything else.** Gates depend directly on siblings (rule 22) and clause
  (a) requires `done` (`harness/ledger/sql/claim.sql:8-9`), so a quarantined sibling holds its gates forever and rule
  132 fails in the shape that ships: core's "a quarantined descendant is acceptable" (`harness-core-v3.md:396-400`)
  covers grandchildren only. Clause (b) releases every card depending on a split with a quarantined child, gate or not
  (`claim.sql:10-12`), and `tests/ledger/verify_schema.py:168` tests for this as intended. ADR-0013:23 named the hole.
  Change: a gate kind whose check fails parks instead of retrying. Gate kinds accept
  `quarantined` on both clauses, and everything else requires `done` on both. Needs an ADR under core §13.
- **B24. Nothing leads out of `quarantined`.** `requeue` runs through `review_return.sql`, which matches only
  `state='awaiting_review'`, while `release.sql` sends a card out of free retries to `quarantined`. So `requeue` matches
  nothing in the case ADR-0011 wrote it for. Change: one fenced statement out.
- **B25. A failing `integrate` can't emit a gap card.** New cards are inserted only inside `commit()`, which only
  reaches `done` (`jig-sketch.py:817-851`), so a retry re-merges and quarantines. Gap fixes are never re-integrated: the
  one `integrate` was pinned at split time *(unchecked)*. No fix was proposed beyond B23's parking.
- **B26. Six of ten verbs have no statement:** `kill`, `promote`, `reset`, `clear_halt`, `raise_budget`, `abandon`
  (`001_initial.sql:224-225`). Nothing writes `runs.outcome`, so an abandoned run stays claimable. Change: add them,
  plus an operator halt, which is cheap: `halt_run.sql` exists and `claim.sql:19-20` refuses a halted run. The `reviews`
  row is in ADR-0015 (draft), decision 3.
- **B27. No table of loops, bounds and exits.** Change: a table in policy §9, with R31's round cap, and rows shaped like
  `on_refusal: {goto, max, stop_when_identical}` (`hands-on-iii:pipeline.yaml:37`), behind a pure
  `route(kind, outcome, attempts)` (`open-refinery:pipeline/graph.py:96-160`). Test it through the runner: those pure
  tests pass for routes dead in the product *(traced, not run)*.
- **B28. Nothing bounds depth.** `shape_children` caps width only (`jig-sketch.py:750`), and only the nullable budget
  (`001_initial.sql:133`) stops execute→split→execute→split. Core calls this free (`harness-core-v3.md:394`), and policy
  treats it as a feature (`harness-policy-v3.md:385-387`). `max_depth` not found. There:
  `ce:skills/agent-harness-building/SKILL.md:84-91`. Change: derive depth from the hierarchical id in `shape_children`,
  and park at the limit. A few lines, plus a row in B27.
- **B29. Rule 44 promises what core forbids.** "An owner, an alert and a triage path" (`rules-and-risks.md:138`) against
  "Poll only" (`harness-core-v3.md:654-655`). `queries/stalled.sql:6-9` misses a budget refusal or a halted run. Change:
  rewrite rule 44, and add a query for "pending, none claimable, and why". Cheap. There: "Never claim a rung you do not
  carry" (`pi-config:agent/AGENTS.md:58`).
- **B30. Cause fingerprint and flood breaker.** There: Jig gives a failure a stable identity (check, scope, normalized
  signature) and stops repeat alerts after N from one cause, and only confirmed recovery resets it. Fits R63, more
  precise than ADR-0011's breaker.
- **B31. Stop on an identical failure, low rank.** There: `open-refinery:pipeline/graph.py:104-107`. B23 already parks
  gate kinds, and for others it would skip the positional tier-up (`harness-policy-v3.md:361-362`). Query the last two
  `check_ref` values first; naming the rung needs B1.
- **B32. Restart Postgres in Gate A.** Past one lease TTL every lease expires and the reaper charges `lease_expired`,
  which is not free. There: p.643 *(unchecked)*. The single point of failure moved to Postgres, and nothing tests it.
- **B33. Shadow-run automatic decisions.** `superagent:src/policy.ts:55-58` *(unchecked)*. The reaper could log
  would-stall rows, to test ADR-0007's guard.
- **B34. Dead-man's switch** (Jig). An alarm if the reaper itself stops, once runs are unattended.
- **B35. Name how a run ends.** `quiescent` and `stalled` (`iii-blackboard:scratch/blackboard.py:112-134`) fit the
  unwritten `runs.outcome`.

### Tool boundary and containment

- **B36. No document says where tool calls execute.** `dispatch_tool` runs `t.fn(**call.args)` with no container handle
  (`jig-sketch.py:504,528`), core has the card work inside the container (`harness-core-v3.md:669-673`), and the worker
  makes model calls. If file tools run on the host, a symlink planted by `bash` lets `read` reach host files. If the
  runtime runs in the container, `bash` can read the provider key and network deny can't hold. ADR-0003's enforcement
  depends on this. There: pp.494-496; `ghola`'s scope defaulted to the engine's directory until the model refused
  (`ghola:b4f2fff`). Change: a paragraph in core §6, and a per-attempt `make_tools(workspace)` with the workspace
  required, about 20 lines (`sigma:agent/subagent.go`). Gate A cases: a planted symlink and absolute path; the model
  can't choose what a sandbox treats as writable; a card can't write what judges it
  (`hands-on-iii:workers/ladder/src/rules.py:119-121`).
- **B37. A deny test can pass because the plant never fired.** Gate A's "no marker appears" (`harness-core-v3.md:1096`,
  ADR-0014:78) has no control. There: `pi-config:verify.ts:60-75`, `hands-on-iii:tests/live/test_ladder.py:16-17`.
  Change: one sibling case per deny case, showing that the plant fires when nothing stops it.
- **B38. A tool timeout may not kill the tool.** Killing a `docker exec` client may leave it running beside the next
  call (inferred, not run). Change: kill the process tree.
- **B39. R22 checks only that a container exists.** There: `dsh:sandbox/sandbox-local/src/index.ts:70,87` *(unchecked)*.
  Change: a provisioning canary for outbound network and for a write to a read-only mount.
- **B40. No cap on tool results was found in `dispatch_tool`,** though ADR-0012 says "normalize first, then truncate".
  There: head, tail and an exact omitted count, `read` exempt (`dsh:spill/spill-policy/src/index.ts:113-119,136`)
  *(unchecked)*. Not a generated spill path, which would move the key (`dsh:spill/spill-local/src/store.ts:110`).
- **B41. `verify`'s tool set has no current listing.** `worked-run-catalog.md:121` gives `[read, grep, glob]` and no
  `bash`, but that file is stale on purpose and rule 135 puts tool sets in the jig. Carry it over. There: OpenCode's
  read-only `explore` has `shell` and coaching (`opencode:core/src/plugin/agent.ts:15,80-84`), rule 25's failure.
- **B42. In-scope injection is unnamed.** Layers 5-7 interpolate model-authored text unmarked. There: pp.501-508. Name
  it as a risk, and seed a labelled trap before keeping any prompt line.
- **B43. Name the sweep's three objects.** Directory, registration and branch fail separately, and rule 141 says
  "worktrees".
- **B44. Edit-miss hints.** `opencode:core/src/tool/plugin/edit.ts:199-241` *(unchecked)*. Nothing measures whether this
  saves a turn.

### The runtime and its tests

- **B45. Test that every declared thing has a reader and a statement.** Six verbs have none (B26), and `gate` on `Role`
  has no `gated()` (`jig-sketch.py:226,741`). There: `open-refinery:tests/test_route_coverage.py`, after a deleted
  router left every test green (`open-refinery:b5585d2`). Change: a test in `tests/ledger/`, derived from the schema,
  that every verb and state in `001_initial.sql` has a statement, and every role and `checks.yaml` key a reader. Under a
  day. Under an hour more: every prompt field has a filler (`hands-on-iii:tests/test_rework.py:71-77`).
- **B46. A `ScriptedModel` and a runtime test file.** `tests/` holds only `tests/ledger/`, and P2-13 is sized as if
  delegated (`PLAN.md:192`) *(unchecked)*. There: pp.526-534. The most copyable thing read: a one-method port
  (`sigma:agent/agent.go:60-62`) and a strict double (`sigma:agent/fakes_test.go:14-35`). Do better than sigma: assert
  what was sent, fake at the model and not above the runner, and script tool-use replies and `HarnessFailure`. First
  cases: the rendered prompt, every terminal state through the runner, a crash at each commit boundary, and the defects
  below.
- **B47. Nothing walks the pipeline before the kill tests.** A jig can't run until P2-13 (`PLAN.md:192`), behind Gate A.
  There: `hands-on-iii:tests/test_factory.py:176-181`. Change: after P1-6, stub jigs walk split, execute, verify and
  integrate to `done`. About half a day. It exercises B23-B27, but wouldn't have found `ghola`'s defects, hence B48.
- **B48. Run a real job of this size on a real repo as soon as a jig exists, before any experiment.** `ghola`'s first
  job's six defects were "invisible to 240 passing tests and cost a real run" (`ghola:b4f2fff`), and the rework hit four
  more (`ghola:2866476`). That was on a stock harness, so the gap with P2-13 is partly the substrate and doesn't justify
  reordering the plan.
- **B49. Assert tool pairing before computing the key.** Otherwise our own bug becomes `PROVIDER_REFUSED`, so layer 7
  tells the card. There: `dsh:llm/llm-deepseek/src/serialize.ts:131-146`. Change: duplicate ids, orphan results and
  unresolved calls raise `HARNESS_BUG`.

### Replay and the cache

- **B50. Repeat samples collapse in the cache.** It is read before the mode check (`jig-sketch.py:476-482`) and the key
  is global (`001_initial.sql:166-171`). Policy's "three samples at one config" (`harness-policy-v3.md:726-733`) then
  returns the same bytes at $0, so rule 121 could delete a skill on one sample. There: pp.380-384. Change: a sample
  value in the key, never sent on the wire. Withhold an arm if any call it scored was `served_from_cache`. Core §8 is
  settled, so this needs an ADR.
- **B51. The kept proxy test may fail as designed → ADR-0015 (draft), decision 2.** `CachedModel` hashes `wire`, but
  `complete` posts `body`, so the SDK serializes what is sent (inferred from a sketch). Send `wire` verbatim, and
  compare over `observed body + identity`.
- **B52. Replay equality proves determinism, not correctness.** Eight DSH scenarios passed while replaying
  `UNKNOWN_TOOL` (`dsh:docs/postmortem/0002-js-expression-disabled-filesystem-tools.md:19`). Change: core §11 also
  asserts the ordered `cache_key` per attempt, and no `out_of_scope` denials in a baseline run.
- **B53. Test that each call extends the last.** `dsh:core/agent-loop/tests/request-reconstruction.spec.ts:69-74`
  compares values, not bytes. No runtime detector of what broke a prefix was found. Add it to P1-22.
- **B54. A miss should name what changed.** `ReplayMiss` carries only the key. There:
  `opencode:http-recorder/src/http/matching.ts:40-57`. Needs B2.
- **B55. The key ignores headers.** There: `opencode:http-recorder/src/http/matching.ts:8-16`, and `anthropic-beta` is a
  header (`opencode:ai/src/protocols/anthropic-messages.ts:1535-1542`). Whether any setting here does this was not
  checked. If one does, add it through an allow-list.
- **B56. Refuse to store secrets.** No rule was found for what `model_cache` and `content.put` may store, and B2 stores
  every tool result. There: a key pattern or environment secret fails the write
  (`opencode:http-recorder/src/cassette/store.ts:132-135`). Cover any fixture the proxy test keeps.
- **B57. Carry thinking through the port as an opaque envelope.** `as_assistant()` is undefined in the sketch. There:
  `dsh:llm/llm-deepseek/src/replay.ts:29,48-64` *(unchecked)*. Whether the provider needs thinking blocks returned is
  unchecked API knowledge, so confirm that first.

### Provider and model handling

- **B58. Read the stop reason, and fail closed on an unknown one.** `_turn_loop` never reads one, so truncated text gets
  `schema_repair_prompt` and `CachedModel` stores it. There: `dsh:llm/llm-deepseek/src/translate.ts:90-97`. Change:
  `Response.stop` and an `OUTPUT_TRUNCATED` class with no repair. Fail every tool call in a truncated response, because
  truncated arguments can pass the schema (`pi:packages/agent/src/agent-loop.ts`); check what the SDK returns. Test
  cases: `model_context_window_exceeded` should be `CONTEXT_EXCEEDED`
  (`opencode:ai/src/protocols/anthropic-messages.ts:1023`) and `refusal` goes to schema repair (`:1025`), both in 200s
  that ADR-0011 misses; a 429 can mean quota, so `billing_exhausted` spends free retries instead of halting
  (`opencode:ai/src/provider-error.ts:141-145,239-244`).
- **B59. Honour `retry-after`.** `not_before` ignores provider hints (core §5), and a long rate limit can exhaust free
  retries (ADR-0011). There: the longer of backoff and hint, capped at 15 minutes
  (`opencode:core/src/model-retry.ts:12-20,31-35`), plus `MAX_TIMEOUT_RETRIES = 3` (`:40`). ADR-0005 gives retries to
  the SDK, so settle how the layers combine.
- **B60. Record the served model.** `validate_roles` never looks at the model (`jig-sketch.py:245-255`), and roles use
  aliases, so when one moves, hits and misses within a run get different models under one string. There: p.514.
- **B61. Provider tests as a checklist.** There: `pi:packages/ai/test` has 194 files, read by name only, which can test
  `CONTEXT_EXCEEDED`. An adapter conformance table waits for a second provider: sigma's swap kept the loop, but caching
  and stop-reason semantics leaked (`sigma:0b5c418`) *(unchecked)*.

### Review gates

- **B62. `gated()` is called and defined nowhere** (`jig-sketch.py:741`). `gate` sits on `Role` as `'depth <= 1'`
  (`jig-sketch.py:226`), and R1's "human gate at depth ≤1" (`rules-and-risks.md:305`) gates every card under ship-flat,
  yet the worked run shows three gates. The closest design is `review_policy` (`files/intake-and-review.md:327-337`).
  There: pp.409-418, p.735. Change: a review level on the run, set by a person (`every_card`, `plan_and_root`,
  `root_only`). Raises only, decided at emit from card facts: touch set against `always_gate`, `retry_safe: false`,
  incomplete contracts, reversibility, falsifiable criteria (`ce:skills/agent-charter-operations/SKILL.md:261-271`).
  Take `gate` off `Role`. A query counts verbs per gate position, and a person changes the level by hand. An unknown
  level falls to the safer one (`open-refinery:pipeline/agent.py:50`) *(unchecked)*.
- **B63. Refusal shape.** There: Jig's framed decision (question, options with costs, recommendation, what was done),
  pp.599-612, p.776 (one question per refusal). `worked-run-odoo.md:531` bundles two. Test in E2 arm C before adopting,
  because a costlier refusal may suppress refusal (R47).
- **B64. Show a gate the latest attempt's result, not the first.** After the rework on `tacoda/fawlty` PR #2 a comment
  reported `prove: unproven`, the summary still said `prove: yes`, and it merged 12 minutes later. No cause is recorded,
  and it may have been a README judged good enough. Its body was cut at 10,000 characters inside the proof text: check
  against rule 97.
- **B65. A downgrade contract for `verify` verdicts.** None was found here. There: unparseable is never a pass, "yes"
  with no evidence becomes `unproven`, an objection needs `file:line` (`open-refinery:pipeline/contracts.py:31-45`).
  Copy it only with a route: "a contract never fails a job" (`hands-on-iii:tests/test_rework.py:167`).
- **B66. Queries over human attention.** There: p.685. The worked run spent 49 of its 94 minutes on gates
  (`worked-run-odoo.md:817`), which is an imagined run.
- **B67. Two small Jig shapes.** `/jig:audit` scores with file-path evidence and changes nothing. A ledger on the pull
  request lets another machine resume a review loop.

### Cost and ceilings

- **B68. Unknown cost reads as free.** `model_calls.cost_usd numeric(12,6) NOT NULL DEFAULT 0` (`001_initial.sql:157`)
  is summed at the claim (`harness/ledger/sql/claim.sql:13`), so an unpriced model never trips the budget. There:
  `hands-on-iii:cost.py:94-108`, and `ghola`'s cost really read $0.00 (`ghola:c1e79c2`). Change: add `cost_source`, and
  let an unpriced live call refuse further claims. Cache hits stay $0 (`jig-sketch.py:483`). A few lines.
- **B69. No token ceiling inside the card.** Budget only refuses new claims (`harness-core-v3.md:450-452`)
  *(unchecked)*, `max_cost_usd` may be NULL (`001_initial.sql:133`), `max_turns` is marked contested
  (`jig-sketch.py:208`), and R61's mitigation is "None"
  (`rules-and-risks.md:380`). There: pp.520, 529. Change: count tokens from the served response, because a dollar limit
  would trip live and not in replay. Copy sigma's decorator, about 25 lines (`sigma:agent/modelstack.go:87-100`),
  outside `CachedModel`, and estimate `spent + last_input + max_tokens` before the call, which sigma doesn't. Put the
  ceiling in `kind_hash`, keep it out of the evidence classes, and make `max_cost_usd` NOT NULL. Measuring the stable
  prefix at pin time can come first: it needs no model.
- **B70. Record provider cache tokens, keeping unknown distinct from zero.** `model_calls` has no cache columns. There:
  `dsh:llm/token-meter/src/turn-usage.ts:136-137` *(unchecked)*. This detects R61, not bounds it.

### Prompt and layers

- **B71. Commit rendered prompts as text.** Hash tests show that something moved, not what. R21 cites golden-file prompt
  tests, and none were found. There: DSH's 101 `system-prompt.expected.md` and 94 `tool-schemas.expected.json` files,
  where one rewording was refused for re-rendering 83 *(docs)*. Deduplicate per kind and tier.
- **B72. Read ADR-0010 item 6, "A check comes first", more narrowly.** There: "Most rules should stay prose forever"
  (`iii-layers:policy/README.md:5-7`), against p.715. Keep it for decidable, consequential checks, and ask for a RED
  case for anything else. One sentence.
- **B73. Exemplar module.** Run N's code becomes what run N+1 copies. There: pp.57-63 *(unchecked)*. The author's later
  texts disagree on whether imitation wins (`iii-layers:docs/RESULTS.md:147-148`,
  `workshop:workshop/narrative.md:80-84`), so assume neither. First tag RED failures as "copied from" versus "model
  prior".
- **B74. Counter-test restriction text in prompts.** Stating read-only caused five of twelve zero-tool-call turns in one
  DSH note (`dsh:.agents/notes/archived/feature/2026-07-06-sandbox.md:159`) *(docs, unchecked)*.

### Experiments and measurement

- **B75. Rule 121 deletes a skill and names no sample size.** There: DSH's 150 requests per arm, 0/150 vs 6/150 and
  0/150 vs 23/150 (`dsh:.agents/notes/implemented/bug-fix/2026-10-21-subagent-end-turn-guidance.md`) *(docs)*, which
  three runs miss 88% and 61% of the time. Change: the RED pairing (`jigs-layers-skills-v2.md` §3.4) names model id,
  base commit, observable event and base rate, and N follows. To delete at a 5% risk of deleting a skill that works, the
  consecutive misses needed are 5 at a base rate of .5, 14 at .2 and 74 at .04. Recomputed: 5/5 vs 0/5 is p=.008, 4/5 vs
  1/5 is .21, and power at n=5 is .38 for .2→.8.
- **B76. An eval protocol that can't report a false result,** for P3-5. There: `pi:packages/evals/README.md`. Runs and a
  protocol digest are fixed first. A missing or errored arm blocks its pair and withholds the headline. Missing
  telemetry stays unavailable, not zero. Saturated controls, no lift and flakiness are flagged. Material is removed
  symmetrically. Not its default of one run per variant.
- **B77. A checklist from the only committed measurement.** Each is a mistake step 7 could make. Two `workshop`
  reference arms are one patch (`a82e6796967f`). The independent variable is null (`workshop:bin/capture:55-70`). In the
  fork, 7/8 in every arm, `lines_added` fell 184 to 62 only because `--numstat` skips untracked files
  (`workshop:tools/scorecard.py:175-184`), and the bare agent probably read the scorer (inferred). Changes, all text:
  compute from the stored diff. In policy §7, tag each arm and separate "not installed" from "removed"
  (`iii-layers:docs/RESULTS.md:332-340`). In E2's reviewer rules, the prompt must not name the specimen. A Gate A case:
  hidden rung definitions and earlier arms' records are unreadable from the container.
- **B78. Write step 7's scorecard first.** There: p.712. Add `queries/scorecard.sql` beside step 7's thresholds
  (`PLAN.md:52,236`): one row per check, one column per config, as pass, fail and not-reached counts per `config_hash`,
  plus policy §7.4's numbers. Needs B1.
- **B79. Add a one-window arm to E3, and run it first under policy §7.1.** Core says "Use one window."
  (`harness-core-v3.md:53`), and nothing measures it. There: p.79 *(unchecked)*. The fork's runs took 20 seconds to 2
  minutes each. Rerun on each major model release.
- **B80. An amendments ledger.** No row links a failed card to the change that answered it, and "nothing writes here
  yet" (`001_initial.sql:232-243`), and `queries/lessons.sql:95-97` counts review verbs and nothing else. There: pp.355-367; Keystone's prose pipeline holds only `.gitkeep`. Change: an
  append-only, human-written row with direction, `rule_id`, the charter artifact changed, source cards, the missing
  guard, a decision (`patched`, `no_patch`, `deferred`, `retired`), hash before and after, and `landed_in`. A query
  compares the repeat-failure rate across the hash move.
- **B81. A hidden rung can be measured from the cache.** The key excludes `kind_hash` (`jig-sketch.py:478`) and hidden
  rungs never render, so changing one replays free until the first card diverges (inferred). One paragraph in policy §7,
  no code. Ablate the earlier rung, not the idle one (`iii-layers:RUNGS.md:62-63`). Needs B1.
- **B82. Odoo in an existing codebase.** `odoo-adaptation.md` targets a new module only. Characterization tests must
  pass on arrival, against `expect: FAIL`, and the "extra" list would flag every existing model. There: pp.286-292
  *(unchecked)*. B11 answers part.
- **B83. An anecdote worth one test.** In the fork, attempts stopped on the ticket-versus-rule conflict in 3 of 4 tries
  at levers 3-4, against 0 of 3 at levers 0-2, in prose only (p=.14). Policy lines 299 and 776 say a model "does not
  stop and ask". Test in E2 arm C, and don't edit on this.
- **B84. Small queries, when step 7 needs them.** Same stage failing across runs, revision churn, stalled holds
  (`open-refinery:improve.py:149-230`) *(unchecked)*. Tools each kind never calls (p.232 *(unchecked)*). `lessons.sql`
  at the final gate and each config bump, not on a calendar (p.732 *(unchecked)*).
- **B85. Small habits for specimens.** A premise test that the fixture still opposes the rule
  (`workshop:tests/test_charter_gate.py`, *(unchecked)*). A written prediction per arm (`workshop:workshop/index.html`).
- **B86. Four papers the book cites, unopened.** arXiv 2503.13657 (E2, E3), 2602.16873 (E1), 2607.12227 (E3, step 7),
  2605.29682 (E2 arm C′, tool width).

### Rules and docs

- **B87. Add three columns to the rule table:** audience, enforced by, evidence (paper, test or run id), plus a
  precedence order. There: pp.110-116 *(unchecked)*. It would settle rule 147 against rule 68, rule 65 against
  `re_verify` emitted by `verify`, and rule 31 against rule 137. Derive "enforced by", because hand prose rotted within
  hours (`iii-layers:RUNGS.md:100-113` *(unchecked)*): add `rule:` to `Rung`, and have B45 generate the column, as
  `hands-on-iii:workers/ladder/src/rules.py:22-26,85-97` does *(unchecked)*.
- **B88. Two glossary habits from Jig.** "Avoid" lines name each term's rival words, and ADR-0008 exists because docs
  described one concept differently. "Tally versus constraint" tests which numbers in prose will drift.

## Positioning and scope

**B89. Narrow policy §10, and say "no controller process".** "The record survives the controller dying" no longer
separates this design: `pi-durable` resumes after a crash, though experimental with one process per store; DSH fsyncs
batches and repairs torn tails *(docs, unchecked)*; OpenCode's record survives process death, as §10 already says. Both
have run, and this has not. "There is no controller" (`harness-policy-v3.md:812`) reads too strongly: the book's daemon
holds no state (p.624). That holds for deciding, not doing, since open-refinery's worktree is state outside the row
*(unchecked)*; this repo should test that it doesn't inherit this. What remains, for §10 to name as typed questions
across runs, listed for step 7 and recorded under core §13's clause:

- **The fence.** DSH has no lease plus fencing across processes *(docs, unchecked)*. Open-refinery claims with no fence.
  OpenCode resumes a controller and assumes an orphan's owner is dead
  (`opencode:core/src/session/execution/restart.ts:16-17,56-60`). `hands-on-iii` has no claim or lease, by word search.
- **The typed keys.** No equivalent of `project`, `intent_digest`, `config_hash` or an oracle verdict was found in DSH
  (`dsh:session-query/session-query/src/types.ts:205-221`), `pi-durable` or OpenCode.
- **Replay.** LangGraph's "Replay re-executes nodes" (`use-time-travel.mdx:14,22` *(unchecked)*) isn't this design's
  cache replay.
- **The refused question.** Core §4.3 never queries content, so "have we hit this error before?" has no answer here,
  where DSH has one. Name it.

**B90. Have ADR-0005 name the files in "the loop passes roughly 500 lines".** No trigger fired.
`dsh:core/agent-loop/src` is 2,127 lines and its driver functions 448 *(unchecked)*, including streaming and
cancellation that ADR-0005 excludes. Counting assembly and dispatch takes it far past that *(unchecked: about 4,856)*.

**B91. Add evaluator-backed certification as a re-check trigger in core §13.** Trusted "done" elsewhere supports
ADR-0013: `update_goal`'s `complete` runs no evidence check (`dsh:goal/tool-goal/src/index.ts:294-295`), and superagent
checks nothing itself on completion *(unchecked)*.

**ADR-0005 holds, on its own arguments.** Its narrowing against OpenCode is already in the ADR.

- **For.** A seam you can't outsource, such as the audit trail (pp.540-541). A plugin boundary's cost: DSH's ACP server
  crashed on first connection "despite 178 green unit tests and 100% line coverage"
  (`dsh:docs/postmortem/0001-acp-default-export-drops-inject.md:13`). Even on a substrate the author keeps the record
  out (`hands-on-iii:workers/audit/src/index.ts:11`). OpenCode's prompt moves with its releases (R60), and its retries
  are on by default.
- **Against.** A full factory in about 3.6k lines on iii, a substrate the ADR's survey omits, leaves only replay
  justifying hand-writing. The retry argument is half wrong *(unchecked)*: only "absent is easier to guarantee than
  configured-off" survives. "No retry of any kind" reads against schema repair *(unchecked)*.
- **No argument from ceilings.** Open-refinery's inside-turn limit comes from the seam it chose, `wrap_tool_call`
  (`open-refinery:pipeline/agent.py:60-62`). LangChain 1.4.2 also has `before_model` and `wrap_model_call`.
- **ADR-0004's CLI rejection gains a reason.** "pi-claude-bridge starts Claude Code with project settings and no trust
  check" (`pi-config:8ca4dc8`).

**Should this be built at all? The checklist on p.442 does not settle it.** It asks about background execution,
multi-model routing, and determinism or durability, and "Two or more" means "you are building an agent system". This
design answers yes to all three as drawn, and passes `hands-on-iii:docs/worksheet.md:9`'s six properties, but the
answers describe the design, not the need. The caution comes from elsewhere:

- p.442 closes on building "only when the stock one runs out of road". Policy §10 concedes queues, tiering and
  worktrees, leaving replay plus the typed record. That count is a judgement, not the checklist's.
- pp.570, 819: "A two-person team on a small repo with one item in flight does not need a daemon, contracts, or
  touchpoints; it needs a charter."
- "Build one when the workflow you need is one no stock harness can express"
  (`ce:skills/agent-harness-building/SKILL.md:25-27`).
- The author's own config (conclusion 3), though a helper running unattended is not one person at a keyboard, and the
  replayable record is one no repo here attempts.

That supports core §12's substrate and replay, and warns against the policy above them: preflight, `re_verify`, `digest`
and multi-prompt jigs. Learning is a legitimate aim, but not one of the book's triggers.

## Where the sources disagree with this design

| Topic | Source | Here | Judgement |
|---|---|---|---|
| Failure routing | Per-stage routes and exits (Ch 34, 54) | Retry, then quarantine | **Source.** B23-B27 |
| What bounds the loop | Four ceilings (pp.520-521) | Lease and deadline | **Source.** B69 |
| Splitting a coherent feature | Keep one context once pieces must fit (pp.463-465) | Split, `interfaces`, merged-tree check | **Source on the risk.** No repair route yet (B25) |
| Promotion | "Most rules should stay prose forever" (B72) | "A check comes first" (ADR-0010 item 6) | **Source, narrowly** |
| What separates rungs | "what they can see" (`ladder:src/gate.py:8`), against decreasing inference (pp.715-716) | Not stated | Use as values for "enforced by" (B87), with who can switch it off |
| Fresh clone per run | p.627, though pp.466 and 621 recommend worktrees | Worktree plus pinned host git | **Here.** ADR-0014 traced the attacks |
| Resume from an interrupt | A pointer back into the work (p.602) | Cold retry | **Here.** Cards are small |
| Escalation on an SLA | Unsigned gates escalate (pp.683-684) | No notification (ADR-0003) | **Here,** for a helper. Take the query (B66) |
| Caching for determinism | Listed among frustrations (p.27) | The determinism mechanism | **Here,** but see B50 |
| Compaction | Safe eviction (pp.481-482) | Excluded (ADR-0005) | **Here.** sigma compacts only at a turn boundary (`sigma:internal/agent/turnstack.go:36-47`), and a card is one turn |
| Inner contract wins | "More specific wins" (p.137) | The model-written contract loses | **Here.** The book assumes a human inner author |
| Rule of three | pp.351-352 | One RED case, then ablation | **Here** for skills |
| Auto-promotion | p.725 | Rule 95 | **Here.** Later: "The agent proposes; the human approves" (`ce:skills/agent-charter-operations/SKILL.md:66`) |
| Mode enforced inside the card | p.416, though `pi-config:README.md:47-48` says "nothing enforces it" | A gate is a row state | **Here** |
| MCP as the default | p.251 | In-process registry | **Here.** A live query breaks reproducibility unless pinned (p.332) |
| Hook failure | "Any other exit is a non-blocking error" (`pi-config:agent/extensions/claude-charter/charter.ts:422`) | Fail closed (B19) | **Here.** No host contract to keep |
| Runtime control | Blackboard "fits agents better" (`iii-blackboard:README.md:120-125`), then a stage graph, no reason given | The board | **No evidence either way.** This board adds the exclusive claim a blackboard lacks |

**The book contradicts itself,** which shows how much of it is settled.

| Topic | One place | Another | The author's later work |
|---|---|---|---|
| Fresh clone or worktree | p.627, p.628 rejects a long-lived tree | pp.466, 621 on parallel mutators, so partly scale | Skill says clone, both harnesses use worktrees (`open-refinery:pipeline/workspace.py:23`) |
| When to check the budget | After spending (p.520) | Before the call (p.529) | Neither harness checks first. B69 stands on argument |
| What a shared queue is | Orchestration (p.669) | Choreography (p.470) | Claiming workers, consistent with here |
| Promoting rules | Automatic (p.725) | Human approval (Ch 32) | No automatic promotion found in Keystone. Supports rule 95 |
| Where behaviour lives | "Up the rings" (p.830) | Knowledge toward determinism (p.715) | Keystone's Go grew from 4 files to 169 |

**Where this design is ahead,** on paper only, since none of it has run: the fence (`commit.sql`, `rekind_split.sql`);
`FailureClass` and `CHECK_UNAVAILABLE`, the distinction both of Keystone's weakened sensors lost; core's pin and hash,
with no match in Keystone or sigma; `render()`'s scope check and a fixed tool order (`jig-sketch.py:561`), against Go's
map order (`sigma:internal/tools/tools.go:55`); layer 7, where open-refinery's `last_refusal` is never rendered
*(unchecked)*; ADR-0010's table; tool lists fixed on the jig; and principle 5, which has no counterpart in the later
seven repos. Their escape markers are model-writable (`ladder:gate.py:84-86`, *(unchecked)*). None were found here, and
that should stay true.

## Not borrowing

| What | Why not |
|---|---|
| Everything is a plugin (DSH); layer spines, plugin host, 12-event bus (sigma) | The measured cost above, and ADR-0005's exclusion list. Five kinds need no extension point |
| Compaction, in-loop retry, recovery, steering, resume, subagents, continuation, model switching, extensions (DSH, Pi, OpenCode); framework builds (Ch 42-43, 51-52) | ADR-0005, core §3.4, policy §1.6. An attempt that fails simply ends |
| sigma's retry layer | Immediate, retries 401s, re-emits streamed text *(unchecked)*. ADR-0005 forbids it |
| `repeat-tool-reminder` (DSH), doom-loop detection (OpenCode, dead in its code) | `opendev-port-notes` excludes it, and an `args_digest` query gives the signal |
| `blockedAfterConsecutiveRounds` (DSH) | It delays refusals, which we want early |
| `flock` ownership, same-session retries (DSH) | Single host, against stateless workers and identical-prompt retries |
| Event-sourcing the ledger (DSH) | ADR-0014 gets the benefit with three columns |
| Indexing content, model-facing `session_search` (DSH) | Core §4.3 and ADR-0005's small tool surface. Name the refused question (B89) |
| `isContextWindowExceededError`, stderr signatures (DSH); overflow regexes as logic (OpenCode) | Text matching, which ADR-0011 rejected. Test cases at most (B61) |
| Argument coercion, `{}` fallback, tool aliases (DSH, Pi, OpenCode *(unchecked)*) | Port notes §1.2. Pi's comment that models often send these is evidence for their §5 trigger |
| Per-file 100% coverage (DSH) | Postmortem 0001 shows it missed a dead product |
| bwrap, Seatbelt, ACL backends (DSH); permission rulesets, asks (OpenCode) | Weaker than the container. Rules 48-54 are void, and cards have no in-loop approver (ADR-0003) |
| Model-chosen skill loading (DSH) | Policy §5.1's hand-chosen sets |
| DSH's benchmarks | Time, heap and scaling only, not agent quality *(docs)* |
| Code mode, per-tool `replay` flags (Pi) | An interpreter inside the loop; workspace destruction and `retry_safe` already cover this per card |
| "Four tools is enough" (Pi) | A 2025 claim. The ablation settles §1.6's tool-width question |
| Running complete tool calls from a truncated stream (OpenCode) | B58 is stricter, and with no streaming it costs nothing |
| Treating unknown failures as retryable (OpenCode) | ADR-0011: ambiguous stays `provider_refused` |
| In-process recorder as the kept test (OpenCode) | ADR-0005: "a recording proxy, not a transport hook" |
| Autonomy ladder L0-L4 (Ch 58) | This is a helper by design |
| n≥30 as a number (pp.380-381) | No derivation. Use B75 |
| Vector store, reranker, staleness budgets (Ch 36) | No prose corpus. Knowledge files are hand-written and hashed |
| MCP and charter-as-a-service (Ch 20, 26) | Cards deny network. The in-process registry gives what p.250 credits to MCP |
| Dashboards (book, repos); packs, forge and tracker ports | Core §9.3's static page is enough. Out of scope |
| SemVer, changelog, forward-only patching for the charter (Ch 31) | No consumers. The pin and rule 128 are enough |
| Curator calendar and daily rhythm (pp.424-427) | Built for a team reviewing a stream of PRs. The event trigger is B84 |
| Hash chain over the record (p.678) | The book's own threshold is "the second harness or the first auditor" (p.704) |
| Judge panel (p.620); dual-LLM quarantine (pp.504-505) | ADR-0002, and the book offers no evidence. An executor must read code to edit it |
| Experiment engines, sign and z-tests (Ch 58, `open-refinery:experiments.py:11-13` *(unchecked)*) | Too few cases. `(config_hash, intent_digest)` covers the tagging |
| Keystone's cascade and 13 kinds; layers, locking (`ladder`); multi-host projection | One project, one runtime. Open-ended events cut against rule 31 |
| Stale claim without a fence; `held` as a flag (open-refinery) | This repo's lease is better, and `park.sql` makes it a state |
| Conformance score bands; two-signer rules | Invented thresholds. One operator, so no-self-approve could not be passed |
| Importing any skill into layer 2 | Rules 120 and 125, R51. Usable as a review pass, which is how they earned their place |
| iii as a substrate | No borrow needs it, and Postgres avoids the file-then-message dual write |
| Capabilities on one ladder (`ladder:src/lifecycle.py:140` *(unchecked)*) | The rungs are ownership layers, which one project lacks. The jig's tool list is the grant |
| Promotion thresholds, verdict printer (`iii-layers:scripts/promotion.py:133-161`); `bin/promote` *(unchecked)* | Pooled and underived, with advisory events counted as catches. A person decides (rule 95) |
| Agent-writable escape markers; "a check that raises is a finding" | They would defeat hidden rungs. It collapses what `CHECK_UNAVAILABLE` separates |
| Hot-reloaded graph, prompts, rules; worktree snapshot and restore | Directly against the pin. Cards have per-attempt workspaces |
| Blackboard vocabulary; Tarrasque, nine checks, AST rules | No evidence behind it; specific to the workshop (B78 takes the shape) |
| `hands-on-iii`'s chapter order as a build plan | `ch11` adds the record, and rows never written can't be recovered. B47 takes the stub walk |
| `learn-harness`'s curriculum; presets, trust files, collision renaming (`pi-config`) | Vendor docs, no result. Stock-agent concerns, and no repo charters load here |
| Running Jig's `drive-pr` or dispatcher | Not yet. Revisit once other teams use them and its issues #399-#403 are closed |

## Defects and doc drift

Noticed in this repo, and not items above. Each was traced, not run. The first seven are cases for B46.

- **A split's refusal lands on `HARNESS_BUG`.** `plan_emissions` runs on any truthy payload (`jig-sketch.py:871`),
  `payload["children"]` raises KeyError (`:745`), and the generic handler catches it (`:888-889`). A split never reaches
  `awaiting_review`.
- **`HARNESS_BUG` says "quarantine, do not retry"** (`jig-sketch.py:77`), but `reaper_flip.sql` has no branch for it and
  retries.
- **An unknown refusal reason carries no `failure_class`** (`jig-sketch.py:619-623`), so `reaper_flip.sql` relabels it.
  Inferred: `JigResult` has no definition.
- **`detail=` has no column** (`jig-sketch.py:620`, `:878`, `:889`), so a `SplitRejected` reason never reaches layer 7.
- **`tree.sql` undercounts subtree cost.** It sums `tasks.cost_usd`, which only `commit.sql` writes, the last response's
  cost (`jig-sketch.py:631`). Read `model_calls` instead.
- **The `Model` protocol declares only `complete`** (`jig-sketch.py:432-433`), while `CachedModel` also calls `build`
  and `identity` (`:477-478`).
- **`dispatch_tool` still runs the checks ADR-0003 voided** (`jig-sketch.py:515-526`). `NeedsApproval` has no handler.
- **`README.md` is stale.** It cites `change-register.md`, as do core:5 and policy:5, where `rules-and-risks.md:3-5`
  replaced it. It lists files not in the repo, its line counts are wrong, it says "Rules 1–130, R1–R53" where there are
  152 rules and 64 risks, and its ADR index omits 0005-0007, of which 0005 and 0006 sit at the root.
- **E3's baseline conflicts.** Policy §7.4 says a sequential pipeline (`harness-policy-v3.md:742-750`), and
  `rules-and-risks.md` §6 item 8 names Gas Town.
- **`odoo-adaptation.md:1081` cites rule 96,** which now means "a note is superseded". The generator text belongs to
  rule 104.
- **`rules-and-risks.md:483` says "133 rules and 56 risks"** *(unchecked)*.

## Words

Keep this repo's words. The same words mean something else in the sources.

- **Charter** (book) is wider than jigs and skills: checks, hidden rungs, hooks, layer 1, the root intent, the anchor
  and role config (pp.39, 52). `rules-and-risks.md` is not charter: no card reads it.
- **Skill** (book) is a multi-phase workflow the agent picks for itself (p.745), which rules 113-115 forbid in a card.
  **Harness** (book) has two levels (p.742): the card runtime, and the board and workers.
- **Orchestrator** is inconsistent in the book. Here the board is the state, and nothing decides.
- **Rung.** In the author's repos, a place a rule is enforced: call those "enforcement points". In Jig, a step of its
  enforcement ladder. Here, an entry on a kind's check ladder in `checks.yaml`.
- **Jig** the project is unrelated to this repo's jigs. Its `tier`, `kind` and `park` differ too, and it avoids `card`.
- **Layer** in sigma: call them "wrappers". **Also collide:** gate, contract, policy, and the book's Verifier, which
  refutes a reviewer's finding.

## Verdict

Borrow the questions, the failure stories and three small shapes (`ScriptedModel`, B46; the budget decorator, B69; the
pure route function, B27), and adopt no package. The book is a source of questions, not a record of practice, and the
only committed numbers contain an arm that duplicates another, a null independent variable, a contaminated control and a
metric that moved because of the instrument.

The strongest lesson is about this repo's own risk. The author could not keep prose and code aligned over a few weeks,
working alone, and the correction that worked was deletion (`open-refinery:docs/ROAD-TO-3.0.md:8`). This repo's 152
rules and 64 risks describe a system that has not run, which is R56. The next step probably isn't another repo. It is to
turn the list above into ADR amendments and tests, and to run a real job.
