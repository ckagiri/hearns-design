# Borrow notes

**What this is.** A reading record of other harnesses and one book, plus the open items that came out of the reading,
organised by what would change in this design. It consolidates seven per-source notes.

**Status.** Nothing here is adopted until it moves into a document, an ADR, `rules-and-risks.md` or code. When an item
moves or is rejected it leaves this file, so the file should shrink. Ids are stable and are not reused. Rule 133 names
three places for changes and this file is outside them, which is an open question for the owner.

## Basis

Subagents read the sources, and the main thread rechecked the decisive claims against the source and this repo.
Nothing was run, neither the sources nor this design: every trace through `jig-sketch.py` or the SQL comes from
reading.

- "Not found" means by keyword search, which is not proof of absence.
- *(unchecked)* means one subagent's reading. *(docs)* means that project's READMEs, notes or postmortems, not its
  code. "Inferred" means reasoned, not traced.
- `repo:path:line` is another project's path, with the prefixes below and the notes' abbreviations (sigma under
  `internal/`, open-refinery under `src/open_refinery/`). A bare hash is a commit in the repo just named. Plain paths
  are this repo's. `p.N` is a book page: the PDF page is N + 22.

The sources' evidence is thin, and the book's author says so of their own tools: "watched evidence, before-and-after
observation with no control arm" (p.386). Read every item as a question to put to this design, not as proven practice.

## What was read

| Source (prefix) | Commit | Date | What it is | What its evidence is worth |
|---|---|---|---|---|
| DeepSeek Harness (`dsh`) | `8bd07339` | 2026-11-03 | Plugin-built TypeScript harness, MIT | Source, in four strands. Postmortems were the most useful per line. Has run |
| `dsh-superagent-prototype` (`superagent`) | `8c32a9dc` | 2026-10-31 | Prototype beside it | A few passing items, all *(unchecked)*. Its article was not read |
| Pi (`pi`) | `1bc7076` | 2026-11-03 | TypeScript coding agent 1.5.0, MIT | Loop in source; `pi-durable` and evals from docs; provider tests by filename only |
| Jig (`jig`) | `d9740470`, glossary `986c1f70` | 2026-11-03, 11-04 | Plugin and templates, Apache-2.0, MIT-0 | Docs and glossary. Modules and `drive-pr` not reviewed |
| OpenCode (`opencode`, under `packages/`) | `93f30ca` | 2026-11-04 | TypeScript agent, v1.19.5, MIT | Source, in two strands. Serialization and compaction body not read. Has run |
| *Harness Engineering*, Ian Johnson (`p.N`) | none | 2026-07-22 | Leanpub, 844 pages | About 680 pages read closely. Anecdotes, one a composite; numbers from others or illustrative. A source of questions |
| `tacoda/keystone` | `62ccdac` | 2026-07-01 | Charter framework, Go, 21k lines | v4.0.0, four majors in 23 days. No outside use visible. Templates sampled |
| `tacoda/sigma` | `3ca5e35` | 2026-07-15 | Coding-agent CLI, Go, 6.9k lines | v0.0.1, "an experiment" (p.818). Its one experiment: two cases, one repeat, no model |
| `tacoda/open-refinery` | `daf65a8` | 2026-09-28 | Factory control plane, Python, SQLite, 14k | "No live model call has been exercised" (`LIMITATIONS.md:125`). Rewritten after the book |
| `tacoda/constraint-engineering` (`ce`) | `9906bb2` | 2026-09-15 | Seven skills from the book | Two commits, no evals, model-assisted compression. Weak evidence of later judgement |
| `iii-harness-layers-and-promotion` (`iii-layers`) | `933a7bb` | 2026-08-21 | One rule at six rungs | An afternoon on a 40-line seed. 12 live runs, gitignored, so nothing can be recomputed |
| `iii-blackboard` | `ada9d48` | 2026-08-26 | Blackboard built two ways, 430 lines | One commit, against a stub |
| `ladder` | `a5725b6` | 2026-08-29 | Constraints and capabilities on one ladder | No model calls and no run data |
| `learn-harness` | `5a40fa3` | 2026-09-15 | Study path through LangChain | Mostly vendor-doc summaries |
| `hands-on-iii` | `3b9566b` | 2026-10-11 | Code for a second book, harness and factory on iii | 13 commits in 87 minutes, a recut, not a history. That book and iii were not read |
| `pi-config` | `9a5d975` | 2026-10-20 | The author's config for pi | Looks used; "daily" is inferred. 15 installed packages not read |
| `charter-workshop` (`workshop`) | `81a2851` | 2026-10-28 | 90-minute workshop measuring a charter | 16 forks in 15 minutes on 2026-11-02. One cell per arm. One fork read (`singularityhacker`, `cde7f2e`) |
| `tacoda/ghola` | `e536a9a` | 2026-09-02 | Harness and factory on iii's stock worker | Read for one question: real runs. Code not reviewed |

**1. The book describes more than the code does.** Read its mechanisms as arguments, not as reports of practice.
Keystone and sigma stopped before publication, and open-refinery was rewritten after it. Whether each claim held in
July was not checked. No item below can cite the author's practice as support.

| Book | Code |
|---|---|
| "the engine picks the locked rule, logs the conflict, and surfaces it" (p.139) | Not implemented. The project wins and `strict` is never consulted (`keystone:internal/framework/charter/charter.go:166-173`) |
| Open-refinery "does not run a lease-based retry queue" (p.675) | Reversed by `bbdc9af`: a claim and a 900-second stale takeover, no fence (`open-refinery:pipeline/workers.py:40,69-86`) |
| "The ceiling has to be checked before the call that would cross it" (p.529) | sigma's crossing call fires, and its test asserts spent 12 of limit 10 (`sigma:agent/modelstack.go:89`, `agent/modelstack_test.go:50-60`) |
| Rooting is "the same defense" as a `realpath` check (pp.494, 496) | `rooted()` is lexical, and an empty root is unconfined (`sigma:internal/tools/paths.go:12-23`) |
| Sandbox read-only "except the working directory" (p.496) | The model picks it: `{"dir":"/"}` makes everything writable (`sigma:tools/bash.go:35,62`, `exec/sandbox.go:35,65-66`) |
| `charter show --path/--topic` output (pp.140-143) | Parses neither flag (`keystone:cmd/keystone/charter.go:124-143`) |

**2. Only two jobs were traced end to end, and both changed a README.** `tacoda/fawlty` PR #1 (+66 −1) and PR #2 (+12,
one reviewer-driven rework) ran under `ghola`, on iii's stock `harness` worker, not the author's own loop and not
Claude Code. The author is the commenter and the merge account. There is no cost or turn data on real work, and stated
figures can't be traced *(unchecked)*. Nothing shows a harness catching a real problem. What those jobs found is in
B48.

**3. The author's own daily config is thin.** `pi-config` is a stock agent, Claude Code on a subscription
(`pi-config:agent/settings.json:3-4`), and 172 lines of instruction, against 10.2k in Keystone's charter. A word
search for their own frameworks finds nothing, and the only tool of theirs it installs is the `ce` skills
(`pi-config:skills.txt:9`). No budget ceiling, sandbox, contract or daemon was found. It is one public config, for one
person at a keyboard, so it does not answer the background-execution case. The one target repo seen dropped its
Keystone block (`tacoda/fawlty`, `adbe43d`).

## Before the first run

In this order. All are small. The first and fourth can't be recovered afterwards.

1. **`rung_results` with stable rung ids:** B1, ADR-0015.
2. **`expect: FAIL`'s right-reason check,** or B13's gate is hollow: B9, ADR-0016.
3. **Config that can't reach `done` unchecked:** B10, ADR-0016.
4. **Stored wire requests,** which can't be recovered afterwards: B2, ADR-0015.
5. **The declared-things test,** which finds the remaining holes: B45.
6. **The base-tree check:** B11, ADR-0016.
7. **The empty-diff check,** the one change the `ghola` data forces: B12, ADR-0016.
8. **Depth:** B28.
9. **Unknown cost:** B68.

Three more cost little before the first run and can't be recovered after it: frozen attempt inputs (B3, ADR-0015),
repeat samples in the cache (B50) and where tool calls execute (B36). Two are defects in what is already written: the
test-first gate (B13) and the failure routes (B23-B27). As soon as a jig exists, and before any experiment: a real job
of this size (B48).

## Open items

Ranked within each area. "Here" is the citation in this repo, "there" the source.

### The record

**B1. No record of which rung failed: `rung_results` → ADR-0015 (draft).** `CheckResult` has no rung
(`jig-sketch.py:695-697`), and the column was lost after `initial_plan.md:279`. Rule 121's ablation, B31, B78 and B81
all need it. Points to keep: list every rung *reached*, since `run_oracle` "Stops at the first failure"
(`jig-sketch.py:676`). Key on a stable `id`, not `Rung.rung: int` (`jig-sketch.py:232`): inserting one rung cost the
author a remap (`iii-layers:77cb5f1`). `post_tool_call` output is not recorded either (`jig-sketch.py:537-539`). Don't
port `iii-layers:scripts/promotion.py:133-161`, which pools across rules, has an underived 20 and counts advisory
events as catches. A person decides (rule 95). About 20 lines.

**B2. The record does not keep what the model saw: stored wire requests → ADR-0015 (draft).** `prompt_ref` is written
before the turn loop (`jig-sketch.py:560`). Tool calls keep `args_digest` only (`001_initial.sql:210`). There:
`ce:skills/agent-orchestration/references/templates.md:306` *(unchecked)*. Points to keep: `content.put(wire)` at
`jig-sketch.py:477` plus `model_calls.request_ref`; it carries secrets (B56) and B54 depends on it.

**B3. Frozen attempt inputs → ADR-0015 (draft).** "Did a person loosen the check before this went green?" can't be
answered (`001_initial.sql:106-121`; `review_return.sql` and `commit.sql` overwrite). There: pp.699-702, p.664. This
is narrower than the whole-task revisions ADR-0014 rejected. Points to keep: `edit` keeps the old `check_spec` in
`reviews.detail`. One ref per prompt block, because `join_for_audit(blocks)` loses the layer boundaries
(`jig-sketch.py:560`). Copy `downgraded_from` on a persisted result (`open-refinery:pipeline/contracts.py:88-93`).
Neither source is a model: their prompts are overwritten or re-read live *(unchecked)*.

**B4. Nothing records which tree was checked.** `task_attempts` has `check_ref` and `diff_ref`, and no tree or counts.
`tasks.result_sha` may cover part, and when it is written was not traced. `write-tree` was not found, and ADR-0014
says staging is unspecified. There: Jig's evidence record keeps command, exact tree, exit code and test counts, and a
later edit voids it. `opencode:core/src/snapshot.ts:95-97` and `core/src/git.ts:644-647,771-774` capture a dirty tree
with a separate git dir and temporary index. Change: hash the exact tree through rule 150's runner, which may also
answer staging. Don't copy its failure handling: a failed capture only warns (`snapshot.ts:146`), and untracked files
over 2MB are skipped (`:141`).

**B5. A hung tool leaves no row.** The sketch audits after `t.fn` returns. There: flush before `tools/execute`
(`dsh:packages/session/session-checkpoint-policy/src/index.ts:70-75`), and repair separates `TOOL_NOT_STARTED` from
`TOOL_OUTCOME_UNKNOWN` (`dsh:packages/core/session/src/repair.ts:15-18`). Change: insert at dispatch, update at
finish. An `allowed` row with a NULL `duration_ms` then means the outcome is unknown. No new column.

**B6. Immutability is prose.** Rules 94, 96 and 151 have no `CREATE TRIGGER` or `REVOKE` behind them. There: p.699.
Change: enforce it in the database.

**B7. Human edits outside the board leave no link.** The worked run has the human update the schema directly
(`worked-run-odoo.md:284`). There: pp.422-423 *(unchecked)*. Change: a `Card:` commit trailer, already drafted in
`files/intake-and-review.md`.

**B8. A "nothing needed" outcome.** `superagent:prompts/work.md:45` has `dropped` *(unchecked)*. Decide in policy §4.1
whether the record should tell it from `ok`.

### Checks and oracle

**B9. `expect: FAIL` can't tell the right failure → ADR-0016 (draft).** A broken import or a crash satisfies RED
(`harness-policy-v3.md:478-480`; inversion "elided", `jig-sketch.py:676-677`), and the implementation card then burns
its attempts (inferred). There: `ce:skills/agent-primitives/references/skeletons.md:40-42`, p.767, and a test that
passed when "a timeout killed Vite" (`dsh:docs/postmortem/0003-web-agent-gui-feedback-loop.md:36`). Points to keep:
report `started`, `exit_code`, `timed_out` and `tests_ran` separately. Name non-counting failures by runner exit code.
Odoo needs a spike, since a missing-model error is the expected failure there.

**B10. Config errors fail open → ADR-0016 (draft).** A missing kind or typo gives an empty ladder, then
`not_applicable`, then `done` (`jig-sketch.py:680-682`, `001_initial.sql:92-93`). `rungs_for` drops an unknown rung
(`jig-sketch.py:669-671`). There: `ce:skills/agent-harness-building/SKILL.md:178` *(unchecked)*. Point to keep: refuse
a role at startup if its hooks did not register. `pi-config:agent/extensions/preset.ts:437-446` drops a tool when its
ceiling can't load *(unchecked)*, while `claude-charter`'s throw is caught and ignored (`charter.ts:170-171`,
`index.ts:89-95`).

**B11. A new rung can fail on code no card may touch → ADR-0016 (draft).** A touch set bars the fix, so it fails
attempts until quarantine (inferred). No baseline for this was found. There: `iii-layers:docs/RESULTS.md:275`,
`4f10c54`, and the workshop fork's C8. Point to keep: run new rungs on the base tree at pin, refuse or list known-red
ones, and add a Gate A case.

**B12. An empty diff may pass → ADR-0016 (draft).** `Outcome.OK` reaches `done` (`jig-sketch.py:809,836`). There: the
workshop's scorer gives an empty diff 8/8 *(unchecked)*, and `ghola` pushed "a branch… with nothing on it"
(`ghola:2866476`). Point to keep: derive the diff from `base_sha` (`harness-core-v3.md:200`), not staged changes,
because a `ghola` turn committed by itself (`tacoda/fawlty` PR
#2), and under ADR-0014 a card can write `.git`. Test both cases.

**B13. Test-first pairing has no gate.** Policy §3.8 calls it "✓ — load-bearing" and "a hard rejection, not a warning"
(`harness-policy-v3.md:476-491`). The emit gates pair nothing (`jig-sketch.py:750-757`),
`odoo-adaptation.md:285-286`'s justification has no field, and the `split` model writes `check_spec`. R35 says this
pairing alone caught the inverted security rule, though its "**Confirmed**" rests on a walkthrough. Keystone doesn't
implement p.139's lock, so this rests on R35 and policy §3.8. Change: lock a rung in `checks.yaml` when a card cites
an anchor key carrying `semantic:` or `test:` (`odoo-adaptation.md:343-344,404`; rule 101 names `semantic:`). Reject a
split unless each implementation card citing such a key depends on an `expect: FAIL` test card for the same key.
Keying on paths would wrongly reject structural cards. It fits ADR-0010, because the trigger is a declared field. For
rule 31 against rule 137, take `ladder`'s form: a derived default, a flagged departure (`ladder:src/parse.py:103-115`)
and a floor that "may go higher, never lower" (`ladder:src/load.py:274,287`). Rule 31 and the lock are the floor, and
rule 137 selects above it (`jig-sketch.py:671`). One sentence in rule 137. Depends on B9.

**B14. A rung that runs no tests passes.** Rule 145 stops an empty selection, but `run_oracle` reads only `r.ok`, so
zero tests reporting ok gives `passed` and `done`. There: Jig's skip tripwire. Change: a check fails if it ran zero
tests.

**B15. A restart mid-rung is charged as `failed`.** `run_oracle` returns `unavailable` only for `SpawnFailure`, so
`BrokenPipe` is charged, against ADR-0011. There: no start is proved from an unconsumed request file
(`dsh:packages/subprocess/subprocess-local/src/linux-scope.ts:261-282`) *(unchecked)*. Change: a harness-owned shim
could record the start, on a mount the card can't write.

**B16. An existing test can be rewritten to pass.** Rules 82-83 cover paired cards only. There: in both rounding arms
the agent rewrote the pinning test, "11 passed, gate clean, `done`" (`iii-layers:docs/RESULTS.md:299`), n=2, no raw
records. Change: add to the test-file guard (`jigs-layers-skills-v2.md:103`) a commit hook rejecting a behavioural
card whose diff edits a test that existed at base. A few lines.

**B17. The cheap check runs after the expensive one.** The oracle runs inside `run_jig` (`jig-sketch.py:571`), and the
touch-set hook after it (`:872`), though policy calls that hook among the cheapest (`harness-policy-v3.md:441-442`).
`FailureClass` has no touch-set class (`jig-sketch.py:60-77`), so a raising hook lands on `HARNESS_BUG` (inferred).
There: `ce:skills/harness-engineering/SKILL.md:62`. Change: run it before the oracle, give it a class, and add it to
B27's table.

**B18. An already-red base charges each card `check_failed`.** No class for it was found. There: Jig's fresh-base
probe reruns a failing test on the base before blaming the change. It works only for tests that already exist on the
base.

**B19. Hooks decide outcomes but sit outside the pin** (`jig-sketch.py:134-135`), though core hashes hidden rungs
because "they decide outcomes" (`harness-core-v3.md:864-865`). There: pp.226, 240, and neither of the author's
harnesses does this. Change: put the role's hook list and versions in `kind_hash` and the pin, with a hash-stability
test. Keystone's `on:` and `run:` in reviewed frontmatter is the one cheap idea.

**B20. The hook runner has no timeout, no verdict shape and no test at its exit.** Part of R64: a hook that hangs
parsing a card's file strands a worker. There: pp.243-244 time out and fail closed. Copy `runHook` returning
`{code, stdout, stderr, timedOut}` and a pure `verdict(runs)`
(`pi-config:agent/extensions/claude-charter/charter.ts:385,424`) at `run_hooks` (`jig-sketch.py:868,872`), about 30
lines. Invert its policy, since a timeout passes there (`charter.ts:422`) to keep a host's contract, and this design
has no host. Kill the process group, and add a compound command to the Gate A case (inferred, `charter.ts:397,405`).
Add one test: a failing or hung `pre_commit` hook leaves the card not `done`. Keystone's sensors can exit 2 but
`hook fire` exits 1, so they can't block (`keystone:cmd/keystone/hook.go:68-70`), and the rewrite that lost the
working gate left the suite green (`08ab8a3`).

**B21. The pressure will be to loosen rungs.** There: false alarms were fixed by weakening the check, as in
`command -v go && go vet ./... || true` (`keystone:6d79e37`, also `e234e32`; `open-refinery:0615b2e`). Change: protect
`CHECK_UNAVAILABLE` (`jig-sketch.py:65`), and track false-fire rate per rung.

**B22. Allowlists can go stale.** There: Jig's entry fails the gate once it no longer suppresses anything.

### Failure routes and exits

There: Ch 34 p.449, Ch 54 pp.659-665 ("every loop has a BOUND", "an EXIT HATCH"), Ch 55 pp.666-671, Ch 57 p.688. Ch 54
is the best single chapter for this repo. B23-B26 have no precedent in the author's code: `failed` has no exit in
open-refinery *(unchecked)* or `hands-on-iii` *(unchecked)*.

**B23. Quarantine holds gates and releases everything else.** A quarantined sibling holds its gates forever: gates
depend directly on siblings (rule 22), clause (a) requires `done` (`harness/ledger/sql/claim.sql:8-9`), and core's
"acceptable" covers grandchildren only (`harness-core-v3.md:396-400`). So rule 132's "degrade, never hang" fails in
the shape that ships. Clause (b) does the opposite one level down, for gate or not (`claim.sql:10-12`, tested as
intended at `tests/ledger/verify_schema.py:168`). A misclassified `execute` rewritten to `split` reopens ADR-0013:23's
hole once that split commits *(unchecked)*. Change: a gate kind whose check fails parks instead of retrying. Gate
kinds accept `quarantined` on both clauses, and everything else requires `done` on both. That amends core, so it needs
an ADR under core §13.

**B24. Nothing leads out of `quarantined`.** `requeue` runs through `review_return.sql`, which matches only
`state='awaiting_review'`, while `release.sql` sends a card out of free retries to `quarantined`. So `requeue` matches
nothing in the case ADR-0011 wrote it for. Change: one fenced statement out of `quarantined`.

**B25. A failing `integrate` can't emit a gap card.** New cards are inserted only inside `commit()`, which only
reaches `done` (`jig-sketch.py:817-851`), so a retry re-merges the same branches and quarantines. Gap fixes are never
re-integrated: `verify` emits siblings, and the one `integrate` was pinned at split time *(unchecked)*. No fix was
proposed beyond B23's parking.

**B26. Six of ten verbs have no statement:** `kill`, `promote`, `reset`, `clear_halt`, `raise_budget`, `abandon`
(`001_initial.sql:224-225`). No file inserts into `reviews`, which core requires (`harness-core-v3.md:750-752`).
Nothing writes `runs.outcome`, and the claim never reads it, so an abandoned run stays claimable. Change: add the
statements and an operator halt, which is cheap: `halt_run.sql` exists and `claim.sql:19-20` already refuses a halted
run.

**B27. No table of loops, bounds and exits.** Change: a table in policy §9 with a column for R31's round cap, rows
shaped like `on_refusal: {goto, max, stop_when_identical}` (`hands-on-iii:pipeline.yaml:37`), behind a pure
`route(kind, outcome, attempts)` copied from `advance()` (`open-refinery:pipeline/graph.py:96-160`). Test it through
the runner: open-refinery's pure tests pass for routes dead in the product. `merge` reaches `landed` in
`tests/test_pipeline_graph.py:107-111`, while the first poll holds the run and workers skip held runs
(`actions.py:173`, `workers.py:61,81`) *(traced, not run)*.

**B28. Nothing bounds depth.** `shape_children` caps width only (`jig-sketch.py:750`), `rekind_split.sql` stops
split→split on one row, and execute→split→execute→split stays open (`harness-core-v3.md:394`,
`harness-policy-v3.md:385-387`). Only the nullable budget stops it (`001_initial.sql:133`). `max_depth` not found.
There: `ce:skills/agent-harness-building/SKILL.md:84-91`. Change: derive depth from the hierarchical id in
`shape_children`, and park at the limit. A few lines, plus a row in B27.

**B29. Rule 44 promises what core forbids.** It requires "an owner, an alert and a triage path"
(`rules-and-risks.md:138`), and core says "Poll only" (`harness-core-v3.md:654-655`). `queries/stalled.sql:6-9` starts
only from `quarantined` and `awaiting_review`, so a budget refusal or halted run returns nothing. Change: rewrite rule
44 to what is true, and add a query for "pending, none claimable, and why". Cheap. There: "Never claim a rung you do
not carry" (`pi-config:agent/AGENTS.md:58`) is a one-line test for this and R56.

**B30. Cause fingerprint and flood breaker.** There: Jig gives each failure a stable identity (check, scope,
normalized signature) and stops repeat alerts after N failures from one cause, and only confirmed recovery resets it.
It fits R63, and is more precise than ADR-0011's "failures span unrelated cards" breaker.

**B31. Stop on an identical failure, low rank.** `open-refinery:pipeline/graph.py:104-107` fails a stage repeating a
refusal. B23 already parks a failing gate kind, and for other kinds this would skip the positional tier-up
(`harness-policy-v3.md:361-362`). Query the last two `check_ref` values on real runs first. `check_ref` equality can't
name the rung, so it needs B1.

**B32. Restart Postgres in Gate A.** Past one lease TTL every lease expires and the reaper charges `lease_expired`,
which is not free. There: p.643, item 4 *(unchecked)*. The single point of failure moved to Postgres, and nothing
tests it.

**B33. Shadow-run automatic decisions.** `superagent:src/policy.ts:55-58` records `would_accept` and acts on nothing
*(unchecked)*. The reaper could log would-stall rows for early runs, to test ADR-0007's guard directly.

**B34. Dead-man's switch.** There: Jig. An alarm if the reaper itself stops, once runs are unattended.

**B35. Name how a run ends.** `quiescent` and `stalled` (`iii-blackboard:scratch/blackboard.py:112-134`) fit the
unwritten `runs.outcome`.

### Tool boundary and containment

**B36. No document says where tool calls execute.** `dispatch_tool` runs `t.fn(**call.args)` with no container handle
(`jig-sketch.py:504,528`). Core says the card edits and checks inside the container (`harness-core-v3.md:669-673`),
ADR-0004:16 puts the jig's executor there, the container denies network (`harness-core-v3.md:666`), and the worker
makes the model calls. If file tools run on the host, a symlink planted by `bash` lets `read` reach host files. If the
runtime runs in the container, `bash` can read the provider key and network deny can't hold. ADR-0003's enforcement
depends on this. There: pp.494-496, p.271 *(unchecked)*, though the quote is the book's Python and not tested
practice. sigma shows the host branch's holes (`sigma:exec/sandbox.go:40-42`), and `ghola`'s scope defaulted to the
engine's directory, so a turn "would have edited ghola's files" until the model refused (`ghola:b4f2fff`). Change: a
paragraph in core §6. A per-attempt `make_tools(workspace)` with the workspace required and no default, about 20 lines
(`sigma:agent/subagent.go`). Keep the key on the process that runs the model, not the shell
(`hands-on-iii:worker-compose.yaml:33,71`, inferred). Gate A cases: a planted symlink and absolute path, which
`sigma:internal/tools/rooting_test.go` omits *(unchecked)*; the model can't choose what a sandbox treats as writable;
a card can't write what judges it (`hands-on-iii:workers/ladder/src/rules.py:119-121`). Also ask: "Name the one
mechanism that stops the worst outcome if every rule has a bug" (`hands-on-iii:docs/worksheet.md`).

**B37. A deny test can pass because the plant never fired.** Gate A's "no marker appears" (`harness-core-v3.md:1096`,
ADR-0014:78) has no control. There: `pi-config:verify.ts:60-75` fails with "so the plan result above proves nothing",
and `hands-on-iii:tests/live/test_ladder.py:16-17`. Change: one sibling case per deny case, showing that the plant
fires when nothing stops it.

**B38. A tool timeout may not kill the tool.** Killing a `docker exec` client may leave it running in the container
beside the next call (inferred, not run). Lease and deadline bound the attempt, not one tool. Change: kill the process
tree.

**B39. R22 checks only that a container exists.** There: real-profile probes
(`dsh:packages/sandbox/sandbox-local/src/index.ts:70,87`) *(unchecked)*. Change: a provisioning canary for outbound
network and for a write to a read-only mount.

**B40. No cap on tool results was found in `dispatch_tool`,** though ADR-0012 says "normalize first, then truncate".
There: head, tail and an exact omitted count, with `read` exempt
(`dsh:packages/spill/spill-policy/src/index.ts:113-119,136`) *(unchecked)*. Don't copy a generated spill path, which
would move the key (`dsh:packages/spill/spill-local/src/store.ts:110`, `opencode:core/src/tool-output.ts:88-92`).

**B41. `verify`'s tool set has no current listing.** `worked-run-catalog.md:121` gives `[read, grep, glob]` and no
`bash`, but that file is stale on purpose and rule 135 puts tool sets in the jig. Carry it over when `verify`'s jig is
written. It names `glob`, where the sketch's six tools name `ls`. There: OpenCode's read-only `explore` has `shell`
and prompt coaching (`opencode:core/src/plugin/agent.ts:15,80-84`), rule 25's failure.

**B42. In-scope injection is unnamed.** Layers 5-7 interpolate model-authored text unmarked. There: pp.501-508;
spotlighting "is not a wall" (p.506). Change: name it as a risk, and seed a labelled trap before keeping any prompt
line.

**B43. Name the sweep's three objects.** Directory, registration and branch fail separately, and rule 141 says
"worktrees". DSH has no sweep *(docs, unchecked)*, so ours is ahead.

**B44. Edit-miss hints.** A failed edit returns "already applied" or the closest lines
(`opencode:core/src/tool/plugin/edit.ts:199-241`) *(unchecked)*. Nothing measures whether this saves a turn.

### The runtime and its tests

**B45. Test that every declared thing has a reader and a statement.** Six verbs have none (B26), and `gate` on `Role`
has no `gated()` (`jig-sketch.py:226,741`). No such check in `tests/ledger/` by keyword search. There: `keystone`'s
`manifest.Strict` has no reader, which is why a lock is inert *(unchecked for that policy)*;
`open-refinery:tests/test_route_coverage.py` came after a deleted router left every test green (`b5585d2`); and
`pre_trigger` "registers without error and never fires" (`hands-on-iii:tests/test_hooks.py:2`) *(unchecked)*. Change:
a test deriving from the schema that every verb and state in `001_initial.sql` has a statement, and every role and
`checks.yaml` key a reader. Under a day. Then, under an hour: every prompt field has a filler
(`hands-on-iii:tests/test_rework.py:71-77`).

**B46. A `ScriptedModel` and a runtime test file.** `tests/` holds only `tests/ledger/`, ADR-0005 admits these tests
are now the repo's job, and P2-13 is sized as if delegated (`PLAN.md:192`) *(unchecked)*. There: pp.526-534,
pp.212-213. The most copyable thing read: a one-method port (`sigma:agent/agent.go:60-62`), a strict double that
errors when exhausted (`sigma:agent/fakes_test.go:14-35`), and one that repeats, for bounds
(`sigma:agent/agent_test.go:15-27`) *(unchecked)*. Do better than sigma: assert what was sent, fake at the model and
not above the runner, and script tool-use replies and `HarnessFailure`, with `build` and `identity`. First cases: the
rendered prompt, every terminal state through the runner, a crash at each commit boundary, "an ambiguous check fails
closed" (`ce:skills/agent-harness-building/SKILL.md:231-237`) *(unchecked)*, and the defects listed below. Each test's
docstring names the failure it guards against.

**B47. Nothing walks the pipeline before the kill tests.** A jig can't run until P2-13 (`PLAN.md:192`), behind Gate A.
There: `hands-on-iii:tests/test_factory.py:176-181`. Change: after P1-6, stub jigs walk split, execute, verify and
integrate to `done`. About half a day. It exercises B23-B27. It would not have found `ghola`'s defects, hence B48.

**B48. Run a real job of this size on a real repo as soon as a jig exists, before any experiment.** `ghola`'s first
job's six defects were "invisible to 240 passing tests and cost a real run" (`ghola:b4f2fff`), the rework hit four
more (`ghola:2866476`), and the first real audit log failed its own verification (`ghola:dfa099a`). Its job landed the
day the repo was created, on a stock harness, so the gap with P2-13 is partly the substrate and doesn't justify
reordering the plan. Tracing has yielded findings but is no substitute for running.

**B49. Assert tool pairing before computing the key.** Without it our own bug becomes `PROVIDER_REFUSED`, which is in
`EVIDENCE`, so layer 7 tells the card. There: `dsh:packages/llm/llm-deepseek/src/serialize.ts:131-146` rejects
duplicate ids, orphan results and unresolved calls. Change: raise `HARNESS_BUG`. ADR-0005 names ordering as ours to
test.

### Replay and the cache

**B50. Repeat samples collapse in the cache.** It is read before the mode check (`jig-sketch.py:476-482`), and the key
is global (`001_initial.sql:166-171`). Policy asks for "three samples at one config" (`harness-policy-v3.md:726-733`),
which then return the same bytes at $0 and read as perfect stability, so rule 121 could delete a skill on one sample.
Rendered card ids may make the collapse partial. There: pp.380-384; the `ce` advice "Re-run the same prompt" walks
into this trap (`ce:skills/harness-engineering/SKILL.md:119`). Change: a sample value in the key, never sent on the
wire. Withhold an arm if any call it scored was `served_from_cache`. Core §8 is settled, so this needs an ADR.

**B51. The kept proxy test may fail as designed.** `CachedModel` hashes `wire` plus the adapter identity, but
`complete` calls `provider.post(body)`, so the SDK serializes what is sent. ADR-0005's test compares the key with a
hash of the observed body, which differ on two counts (inferred from a sketch). Change: send `wire` verbatim, and
compare over `observed body + identity`.

**B52. Replay equality proves determinism, not correctness.** Eight DSH scenarios passed while replaying
`UNKNOWN_TOOL` (`dsh:docs/postmortem/0002-js-expression-disabled-filesystem-tools.md:19`). Core §11 asserts only an
identical terminal graph. Change: also assert the ordered `cache_key` per attempt, and no `out_of_scope` denials in a
baseline run.

**B53. Test that each call extends the last.** `expectPrefixExtension` compares values, not bytes
(`dsh:packages/core/agent-loop/tests/request-reconstruction.spec.ts:69-74`). No runtime detector of what broke a
prefix was found. Add it to P1-22.

**B54. A miss should name what changed.** `ReplayMiss` carries only the key. There: `requestDiff` reports by JSON path
(`opencode:http-recorder/src/http/matching.ts:40-57`). Depends on B2.

**B55. The key ignores headers.** There: the recorder matches method, URL, headers and sorted JSON
(`opencode:http-recorder/src/http/matching.ts:8-16`), and `anthropic-beta` is a header
(`opencode:ai/src/protocols/anthropic-messages.ts:1535-1542`). Whether any setting here does this was not checked. If
one does, add it to the key through an allow-list.

**B56. Refuse to store secrets.** No rule was found for what `model_cache` and `content.put` may store, and B2 stores
every tool result. There: a key pattern or environment secret fails the write
(`opencode:http-recorder/src/cassette/store.ts:132-135`, `http-recorder/src/redaction/secrets.ts`). It should cover
any fixture the proxy test keeps.

**B57. Carry thinking through the port as an opaque envelope.** `as_assistant()` is undefined in the sketch. There:
`dsh:packages/llm/llm-deepseek/src/replay.ts:29,48-64` *(unchecked)*. Whether the provider needs thinking blocks
returned is unchecked API knowledge, so confirm that first, then test that replayed call 2 has the same bytes as live
call 2.

### Provider and model handling

**B58. Read the stop reason, and fail closed on an unknown one.** `_turn_loop` never reads one, so truncated text gets
`schema_repair_prompt` and `CachedModel` stores it. There: `dsh:packages/llm/llm-deepseek/src/translate.ts:90-97`.
sigma is the warning: `length` and `content_filter` read as success (`sigma:internal/openai/stream.go:110-115`).
Change: `Response.stop` and an `OUTPUT_TRUNCATED` class with no repair. Fail every tool call in a truncated response,
because truncated arguments can pass the schema (`pi:packages/agent/src/agent-loop.ts`,
`failToolCallsFromTruncatedMessage`). Its comment blames the streaming parser, so check what the SDK returns. Test
cases, which ADR-0011's "status and typed errors" misses when they arrive in a 200: `model_context_window_exceeded`
should be `CONTEXT_EXCEEDED`, not truncation (`opencode:ai/src/protocols/anthropic-messages.ts:1023`), and `refusal`
with no parseable text goes to schema repair (`:1025`). Also a 429 can mean quota, so `billing_exhausted` spends free
retries instead of halting (`opencode:ai/src/provider-error.ts:141-145,239-244`), and Cerebras's
`token_quota_exceeded` is a throttle that reads as quota.

**B59. Honour `retry-after`.** `not_before` ignores provider hints (core §5), and a long rate limit can exhaust free
retries (ADR-0011). There: the longer of backoff and hint, capped at 15 minutes
(`opencode:core/src/model-retry.ts:12-20,31-35`), plus a separate `MAX_TIMEOUT_RETRIES = 3` (`:40`), because a
timed-out call has already spent minutes. This is harness retry, so ADR-0005's loop exclusion holds, but ADR-0005
gives retries to the SDK: settle how the layers combine.

**B60. Record the served model.** `validate_roles` never looks at the model (`jig-sketch.py:245-255`), and the role
table uses aliases. When an alias moves, hits and misses within one run get different models under one string. There:
p.514.

**B61. Provider tests as a checklist.** There: `pi:packages/ai/test` has 194 files, by name only, such as
`tool-call-without-result`, `openai-responses-empty-tool-result` and `context-overflow`. Copy the cases, which can
test `CONTEXT_EXCEEDED`. OpenCode's 40 or so overflow regexes (`opencode:ai/src/provider-error.ts:16-58`) are test
cases, and an adapter conformance table waits for a second adapter too: sigma's swap changed no loop code, but caching
and stop-reason semantics leaked (`sigma:0b5c418`) *(unchecked)*.

### Review gates

**B62. `gated()` is called and defined nowhere** (`jig-sketch.py:741`). `gate` sits on `Role` as `'depth <= 1'`
(`jig-sketch.py:226`), which ADR-0008 doesn't give a role. R1's "human gate at depth ≤1" (`rules-and-risks.md:305`)
gates every card under ship-flat, yet the worked run shows three gates. The closest design is `review_policy` in
`files/intake-and-review.md:327-337`. There: pp.409-418 ("step back hard, step forward slow"), p.735; the author's
`pi-config` enforces no mode (`pi-config:README.md:47-48`). Change: a review level on the run, set by a person
(`every_card`, `plan_and_root`, `root_only`). Raises only, decided at emit from card facts: touch set against
`always_gate`, `retry_safe: false`, incomplete contracts, plus reversibility and falsifiable criteria
(`ce:skills/agent-charter-operations/SKILL.md:261-271`). Its history questions would break replay *(unchecked)*. Take
`gate` off `Role`. Add a query counting verbs per gate position; a person changes the level by hand. An unknown level
falls to the safer one (`open-refinery:pipeline/agent.py:50`) *(unchecked)*. Avoid open-refinery's one `approved_at`
across stages, and its plan gate firing before the plan exists (`open-refinery:pipeline/runner.py:124`).

**B63. Refusal shape.** There: Jig's framed decision (question, options with costs, recommendation, what was already
done), and pp.599-612, p.776 (one question per refusal). `worked-run-odoo.md:531` bundles two. Test it in E2 arm C
before adopting, because a costlier refusal may suppress refusal (R47).

**B64. Show a gate the latest attempt's result, not the first.** After the rework on `tacoda/fawlty` PR #2, a comment
reported `prove: unproven` and `review: unreadable`, the summary still said `prove: yes` and `review: pass`, and it
merged 12 minutes later. No cause is recorded, and this may have been a README judged good enough. Rule 145 covers the
state on paper. Its body was also cut at 10,000 characters inside the proof text, a case to check against rule 97,
which keeps a traceback and tail for check logs, not review text.

**B65. A downgrade contract for `verify` verdicts.** No downgrade was found here. There: unparseable is never a pass,
"yes" with no evidence becomes `unproven`, an objection needs `file:line`
(`open-refinery:pipeline/contracts.py:31-45`). Copy it only with a route: in `hands-on-iii` it is a label, "a contract
never fails a job" (`hands-on-iii:tests/test_rework.py:167`). Avoid `partial` not being in `OBJECTING`
(`open-refinery:pipeline/contracts.py:65`).

**B66. Queries over human attention.** There: p.685. Take the query, not the escalation (§7). The worked run spent 49
of its 94 minutes waiting on gates (`worked-run-odoo.md:817`), which is an imagined run.

**B67. Two small Jig shapes.** An audit that changes nothing: `/jig:audit` scores with file-path evidence and a person
decides. Drive state on the pull request: a ledger there lets another machine resume if the driver dies.

### Cost and ceilings

**B68. Unknown cost reads as free.** `model_calls.cost_usd numeric(12,6) NOT NULL DEFAULT 0` (`001_initial.sql:157`)
is summed at the claim (`harness/ledger/sql/claim.sql:13`), so an unpriced model never trips the budget. There: "a
ceiling that reads $0.00 as safe is no ceiling" (`hands-on-iii:cost.py:94-108`), and `ghola`'s cost really read $0.00
(`ghola:c1e79c2`). Change: add `cost_source`, and let an unpriced live call refuse further claims. Cache hits stay $0
(`jig-sketch.py:483`). A few lines.

**B69. No token ceiling inside the card.** Budget only refuses new claims (`harness-core-v3.md:450-452`)
*(unchecked)*. `max_cost_usd` may be NULL (`001_initial.sql:133`), `max_turns` is contested (`jig-sketch.py:208`), and
R61's mitigation is "None" (`rules-and-risks.md:380`). There: pp.520, 529. Change: count tokens from the served
response, because a dollar limit would trip live and not in replay. Copy sigma's decorator, about 25 lines
(`sigma:agent/modelstack.go:87-100`), outside `CachedModel`, and fix its flaw: estimate
`spent + last_input + max_tokens` before the call. Put the ceiling in `kind_hash`, keep it out of the evidence
classes, and make `max_cost_usd` NOT NULL. A budget refusal bypasses the error route
(`open-refinery:pipeline/runner.py:135-147`) *(unchecked)*. Avoid a fresh budget per sub-agent
(`sigma:agent/subagent.go:84`) *(unchecked)* and uncharged failed turns (`open-refinery:pipeline/agent.py:199,204`)
*(unchecked)*. `max_turns` as `recursion_limit` is no turn cap (`open-refinery:pipeline/agent.py:197`). Measuring the
stable prefix at pin time can come first, because it needs no model.

**B70. Record provider cache tokens, keeping unknown distinct from zero.** `model_calls` has no cache columns, so
`cache_control` is unmeasured. There: `dsh:packages/llm/token-meter/src/turn-usage.ts:136-137` *(unchecked)*. This
detects R61, not bounds it.

### Prompt and layers

**B71. Commit rendered prompts as text.** Hash tests show that something moved, not what. R21 cites golden-file prompt
tests, and none were found in core, `PLAN.md` or `PROTOTYPE_v3.md`. There: DSH keeps 101 `system-prompt.expected.md`
and 94 `tool-schemas.expected.json` files, and one rewording was refused because it would re-render 83 *(docs)*.
Change: add them, deduplicated per kind and tier.

**B72. Read ADR-0010 item 6, "A check comes first", more narrowly.** There: "Most rules should stay prose forever… A
rule earns the next rung only by failing at the one it is on" (`iii-layers:policy/README.md:5-7`), against p.715. Keep
it for decidable, consequential checks, and ask for a RED case for anything else. One sentence.

**B73. Exemplar module.** Every layer is instruction or feedback, and across runs of one project run N's code becomes
what run N+1 copies. There: pp.57-63 *(unchecked)*. The author's later texts disagree on whether imitation wins
(`iii-layers:docs/RESULTS.md:147-148`, `workshop:workshop/narrative.md:80-84`), on thin data, so assume neither. First
tag RED failures as "copied from" versus "model prior".

**B74. Counter-test restriction text in prompts.** Stating read-only caused five of twelve zero-tool-call turns in one
DSH note (`dsh:.agents/notes/archived/feature/2026-07-06-sandbox.md:159`) *(docs, unchecked)*.

### Experiments and measurement

**B75. Rule 121 deletes a skill and names no sample size.** There: DSH ran 150 requests per arm with history ending at
the decision point, 0/150 vs 6/150 on flash and 0/150 vs 23/150 on pro
(`dsh:.agents/notes/implemented/bug-fix/2026-10-21-subagent-end-turn-guidance.md`) *(docs)*, so three runs miss the
effect 88% and 61% of the time. A six-benchmark eval read neutral on another sentence, which stayed on production
evidence (`2026-10-26-read-guidance-line-ranges.md`) *(docs, unchecked)*. Change: the RED pairing
(`jigs-layers-skills-v2.md` §3.4) names model id, base commit, observable event and base rate, and N follows. To
delete at a 5% risk of deleting a skill that works, the consecutive misses needed are 5 at a base rate of .5, 14 at .2
and 74 at .04. Recomputed Fisher p: 5/5 vs 0/5 is .008, 4/5 vs 0/5 .048, 4/5 vs 1/5 .21. Power at n=5 is .38 for .2→.8
and .15 for .3→.7; n=20 gives .96 for .2→.8. 5/5 passes still has a 95% lower bound of 48% (two-sided).

**B76. An eval protocol that can't report a false result,** for P3-5. There: `pi:packages/evals/README.md`. Runs and a
protocol digest are fixed before execution. A missing or errored arm blocks its pair and withholds the headline.
Missing telemetry stays unavailable, not zero. Saturated controls, no lift and flakiness are flagged. Material is
removed symmetrically, including the prompt section pointing to it. Don't take its default of one run per variant.

**B77. A checklist from the only committed measurement.** Each is a mistake step 7 could make. In `workshop`: two
reference arms are one patch (`a82e6796967f`). The independent variable is null (`workshop:bin/capture:55-70`; the
charter was probably not on disk, inferred). The seed held the baseline's answer *(unchecked)* (`workshop:1a07a4b`).
The 8/8 patch may not work, and the scorer has no acceptance test (traced, *(unchecked)*). In the fork, on Codex CLI,
decidable checks scored 7/8 in every arm: `lines_added` fell 184 to 62 only because `git diff --numstat` skips
untracked files (`workshop:tools/scorecard.py:175-184`), every arm holds gates derived from the scorer's markers, so
the bare agent probably read it (inferred; `charter_check.py` *(unchecked)* for the derivation), and hooks never ran.
`iii-layers`' "Deleted by the agent: 3" came from missing arm config (`iii-layers:docs/RESULTS.md:332-340`), and that
file is candid: "These are mechanism demonstrations, not rates" (`:380-382`). Changes, all text: compute from the
stored diff. In policy §7, tag each arm and separate "not installed" from "removed". In E2's reviewer rules, the
prompt must not name the specimen (`workshop:charter-auditor.md:20-21`; 3 of 3 reviews cite charm *(unchecked)*). A
Gate A case: hidden rung definitions and earlier arms' records are unreadable from inside the container. Principle 5
is ahead on paper, and core §11.1 has no such case.

**B78. Write step 7's scorecard first.** There: p.712. Add `queries/scorecard.sql` by hand beside step 7's thresholds
(`PLAN.md:52,236`): one row per check, one column per config, each cell tied to evidence, as pass, fail and
not-reached counts per `config_hash`, plus policy §7.4's numbers. Take the shape, not the workshop's nine checks.
Needs B1.

**B79. Add a one-window arm to E3, and run it first under policy §7.1.** Core says "Anything that fits in one context
window. Use one window." (`harness-core-v3.md:53`), and nothing measures it. There: p.79 *(unchecked)*. The fork's
runs took 20 seconds to 2 minutes each. Rerun on each major model release.

**B80. An amendments ledger.** No row links a failed card to the change that answered it. `notes` is the only learning
table and "nothing writes here yet" (`001_initial.sql:232-243`), and `queries/lessons.sql:95-97` counts review verbs
only. There: pp.355-367, p.375 *(unchecked)*; Keystone's full prose pipeline holds only `.gitkeep`
(`keystone:web/prune.go:38-39`). Change: an append-only, human-written row with direction, `rule_id`, the charter
artifact changed, source cards, the missing guard, a decision (`patched`, `no_patch`, `deferred`, `retired`), hash
before and after, and `landed_in`. Take `Source` and `Evidence` from
`ce:skills/agent-charter-operations/references/templates.md:12-37`. A query compares the repeat-failure rate across
the hash move. Flag a hash move with other than one row, because a bundled change can't be attributed.

**B81. A hidden rung can be measured from the cache.** The key excludes `kind_hash` (`jig-sketch.py:478`) and hidden
rungs never render, so changing one replays free until the first card diverges (inferred). Not found in policy §7. One
paragraph, no code. `run_oracle` stops at the first failure, so ablate the earlier rung, not the idle one: "a rung
whose idleness is caused by a removable rung above it has not demonstrated anything" (`iii-layers:RUNGS.md:62-63`).
Needs B1.

**B82. Odoo in an existing codebase.** `odoo-adaptation.md` targets a new module only. Characterization tests must
pass on arrival, which clashes with `expect: FAIL`, and the introspection "extra" list would flag every existing
model. There: pp.286-292 *(unchecked)*. B11 answers part of this.

**B83. An anecdote worth one test.** In the fork, attempts stopped on the ticket-versus-rule conflict in 3 of 4 tries
at levers 3-4, against 0 of 3 at levers 0-2, in prose only (two-sided Fisher p=.14). Policy lines 299 and 776 say a
model "does not stop and ask". Test it in E2 arm C, and don't edit on this.

**B84. Small queries, when step 7 needs them.** Detectors for the same stage failing across runs, revision churn and
stalled holds (`open-refinery:improve.py:149-230`) *(unchecked)*. Tools each kind never calls, since `lessons.sql`
groups by tool only (p.232 *(unchecked)*). Run `lessons.sql` at the final gate and at each config bump, not on a
calendar (p.732 *(unchecked)*).

**B85. Small habits for specimens.** A premise test asserting the fixture still opposes the rule
(`workshop:tests/test_charter_gate.py`, *(unchecked)*), for E2's specimen. A written prediction per arm
(`workshop:workshop/index.html`).

**B86. Four papers the book cites, unverified and unopened,** bearing on ⚖ experiments. MAST, arXiv 2503.13657 (E2,
E3's intervention count). AdaptOrch, 2602.16873 (E1, policy §3.1 depth). *Rethinking the Evaluation of Harness
Evolution*, 2607.12227 (E3, step 7 method). *Effective Feedback Compute*, 2605.29682 (E2 arm C′, tool width).

### Rules and docs

**B87. Add three columns to the rule table:** audience, enforced by, evidence (paper, test or run id), and a
precedence order. There: pp.110-116 *(unchecked)*. Conflicts it would settle: rule 147's "byte-identical" against rule
68's escalation on the last delivery; rule 65 against `re_verify` being emitted by `verify`; rule 31 against rule 137.
Derive "enforced by" rather than writing it, because hand prose rotted within hours (`iii-layers:RUNGS.md:100-113`
*(unchecked)*): add `rule:` to `Rung`, and have B45 generate the column.
`hands-on-iii:workers/ladder/src/rules.py:22-26` has `CARRIED` and `ELSEWHERE`, which refuse a rule claiming a rung
nothing carries (`:85-97` *(unchecked)*). Values for the column: what a level can see (`ladder:src/gate.py:8`), and
who can switch it off.

**B88. Two glossary habits from Jig.** "Avoid" lines name the rival words for each term; this repo has no glossary,
yet ADR-0008 exists because docs described one concept differently. And "tally versus constraint", a test for which
numbers in prose will drift.

## Positioning and scope

**B89. Narrow policy §10, and say "no controller process".** "The record survives the controller dying" no longer
separates this design. `pi-durable` commits before showing and resumes after a crash, though it is experimental with
one process per store. DSH fsyncs batches and repairs torn tails *(docs, unchecked)*. OpenCode's record survives
process death, which §10 already records, with a write-ahead claim (`opencode:core/src/session/execution.ts:73-80`)
*(unchecked)*, and DSH and OpenCode have run while this has not. "There is no controller" (`harness-policy-v3.md:812`)
also reads too strongly: the book's daemon holds no state and "derives exactly the action the previous instance" would
have (p.624). That holds for deciding, not doing, because open-refinery's worktree is state outside the row
*(unchecked)*; this repo provisions a workspace per attempt and should test that it doesn't inherit this.

What remains is narrower, and §10 should say typed questions across runs, list them for step 7, and record this under
core §13's clause:
- **Fence.** The fenced worker pool: nothing in DSH has lease plus fencing across processes *(docs, unchecked)*.
  Open-refinery has claiming workers with no fence (`open-refinery:pipeline/workers.py:40,69-86`), OpenCode's sweep
  assumes the owner is dead (`opencode:core/src/session/execution/restart.ts:56-60`; no fence between hosts
  *(unchecked)*) and it resumes a controller (`:16-17`), and `hands-on-iii` has no claim or lease, by word search.
- **Typed keys.** No equivalent of `project`, `intent_digest`, `config_hash` or an oracle verdict was found in
  `dsh:packages/session-query/session-query/src/types.ts:205-221`, `pi-durable` or OpenCode. No DSH aggregates were
  found *(unchecked)*, though whole events can be exported over OTLP for a warehouse *(unchecked)*.
- **Replay.** Upstream LangGraph's "Replay re-executes nodes… LLM calls… fire again" (`use-time-travel.mdx:14,22`
  *(unchecked)*) is not this design's cache replay. `learn-harness`'s summary says the opposite.
- **The refused question.** Core §4.3 never queries content, so "have we hit this error before?" has no answer here,
  where DSH can answer it. Name it.

**B90. Have ADR-0005 name the files in "the loop passes roughly 500 lines".** No trigger fired.
`dsh:packages/core/agent-loop/src` is 2,127 lines. Its driver functions are 448 *(unchecked)*, with streaming and
cancellation that ADR-0005 excludes, so about 500 is plausible for the driver alone. Counting assembly and dispatch
takes it far past that *(unchecked: about 4,856)*.

**B91. Add evaluator-backed certification as a re-check trigger in core §13.** Trusted "done" elsewhere supports
ADR-0013: `update_goal`'s `complete` runs no evidence check (`dsh:packages/goal/tool-goal/src/index.ts:294-295`), its
README admits "No independent evaluator" *(docs, unchecked)*, and superagent checks nothing itself on completion
*(unchecked)*.

**ADR-0005 holds, on its own arguments.** Its narrowing against OpenCode is already in the ADR.
- **For.** Pp.540-541's third sign is a seam you can't outsource, such as the audit trail. A plugin boundary has a
  measured cost: DSH's ACP server crashed on first connection "despite 178 green unit tests and 100% line coverage"
  (`dsh:docs/postmortem/0001-acp-default-export-drops-inject.md:13`). `ModelRequest` holds messages, not wire bytes
  *(unchecked)*. deepagents always adds summarization and tool-call patching (`graph.py:805-806` at 0.7.19,
  *(unchecked)*), which bears on R60. Even on a substrate the author keeps the record out: "a record must survive the
  thing it records" (`hands-on-iii:workers/audit/src/index.ts:11`). sigma's provider swap supports the port (B61).
  OpenCode's prompt moves with its releases (R60; `opencode:core/src/instructions/builtins.ts:25-45`), retries are on
  by default (`opencode:core/src/session/runner/retry.ts:45-50`), and tools hide only by a whole-tool deny
  (`opencode:core/src/tool.ts:379-382`).
- **Against.** A full factory in about 3.6k lines on iii, a substrate the ADR's survey omits (`:8`). Only replay still
  justifies hand-writing. The retry argument is half wrong *(unchecked)*: with the cache as the library's model
  interface, library retries would land in `model_calls`, so only "absent is easier to guarantee than configured-off"
  survives. "No retry of any kind" reads against schema repair *(unchecked)*.
- **No argument from ceilings.** Open-refinery's inside-turn limit comes from the seam it chose, `wrap_tool_call`
  (`open-refinery:pipeline/agent.py:60-62`). LangChain 1.4.2 also has `before_model` and `wrap_model_call`
  (`langchain/agents/middleware/types.py:455,503`).
- **ADR-0004's CLI rejection gains a reason.** "pi-claude-bridge starts Claude Code with project settings and no trust
  check", so a cloned repo's hooks run (`pi-config:8ca4dc8`), and a charter "mostly never reached the model" under the
  bridge (`pi-config:dd3834e`), which is what `render()` and the pin exist to prevent.

**Should this be built at all? The checklist on p.442 does not settle it.** It asks about background execution,
multi-model routing, and determinism or durability, and "Two or more" means "you are building an agent system". This
design answers yes to all three as drawn. `hands-on-iii:docs/worksheet.md:9`'s six properties pass too, and in both
cases the answers describe the design, not the need. The caution comes from elsewhere:
- p.442 closes on building "only when the stock one runs out of road". Policy §10 concedes the comparables have
  queues, tiering and worktrees, which leaves replay plus the typed record. That count is this repo's judgement, not
  the checklist's.
- p.570 and p.819: "A two-person team on a small repo with one item in flight does not need a daemon, contracts, or
  touchpoints; it needs a charter."
- "Build one when the workflow you need is one no stock harness can express — not because building one sounds
  interesting" (`ce:skills/agent-harness-building/SKILL.md:25-27`).
- The author's practice (conclusion 3). It doesn't settle this, because a helper running unattended is not one person
  at a keyboard, and the replayable record is one no repo here attempts.

That supports core §12's substrate and replay, and warns against the policy above them: preflight, `re_verify`,
`digest` and multi-prompt jigs. Learning is a legitimate aim, but not one of the book's triggers, and most of the
author's projects were followed by a new one rather than by use, `charter-workshop` being the exception (inference).
The book independently supports "the orchestrator is a queue, not an agent" (p.673) and "I never found a sequencing
decision that deserved a model" (p.674).

## Where the sources disagree with this design

| Topic | Source | Here | Judgement |
|---|---|---|---|
| Failure routing | Per-stage routes and exits (Ch 34, 54) | Retry, then quarantine | **Source.** B23-B27 |
| What bounds the loop | Four ceilings (pp.520-521) | Lease and deadline | **Source.** B69 |
| Splitting a coherent feature | Keep one context once the pieces must fit (pp.463-465) | Split, with `interfaces` and a merged-tree check | **Source on the risk.** The check has no repair route yet (B25) |
| Promotion | "Most rules should stay prose forever" (`iii-layers:policy/README.md:5-7`) | "A check comes first" (ADR-0010 item 6) | **Source, narrowly.** B72 |
| Enforcement claims | "Never claim a rung you do not carry" (`pi-config:agent/AGENTS.md:58`) | Rule 44, R56 | **Source.** B29 |
| Fresh clone per run | p.627, though pp.466 and 621 recommend worktrees | Worktree plus pinned host git | **Here.** ADR-0014 traced the attacks, and the author's harnesses use worktrees (`open-refinery:pipeline/workspace.py:23`) |
| Resume from an interrupt | A pointer back into the work (p.602) | Cold retry | **Here.** Cards are small |
| Escalation on an SLA | Unsigned gates escalate (pp.683-684) | No notification (ADR-0003) | **Here,** for a helper. Take the query (B66) |
| Caching for determinism | Listed among frustrations (p.27) | The determinism mechanism | **Here,** but see B50 |
| Compaction | Safe eviction (pp.481-482) | Excluded (ADR-0005) | **Here.** sigma compacts only at a turn boundary (`sigma:internal/agent/turnstack.go:36-47`), and a card is one turn. B69 gives R61 its bound |
| Inner contract wins | "More specific wins" (p.137) | The model-written contract loses | **Here.** The book assumes a human inner author |
| Rule of three | pp.351-352 | One RED case, then ablation | **Here** for skills |
| Auto-promotion | p.725 | Rule 95 | **Here.** `ce` says "The agent proposes; the human approves" (`ce:skills/agent-charter-operations/SKILL.md:66`) |
| Mode enforced inside the card | p.416 | A gate is a row state | **Here.** `pi-config:README.md:47-48`: "nothing enforces it" |
| MCP as the default | p.251 | In-process registry | **Here.** Ch 26 says a live query breaks reproducibility unless pinned (p.332) |
| Hook failure | "Any other exit is a non-blocking error" (`pi-config:…/charter.ts:422`) | Fails closed (pp.243-244, B20) | **Here.** No host contract to keep |
| Runtime control | Blackboard "genuinely fits agents better than a pipeline" (`iii-blackboard:README.md:120-125`), then a stage graph six weeks later, no reason given | The board | **No evidence either way.** Its iii half has no agents (`iii-blackboard:bb/knowledge-sources.yaml:29`). ADR-0005:118 is a resemblance only: this board adds the exclusive claim |

**The book contradicts itself,** which shows how much of it is settled. The budget-breach pair is not one: p.268 is
per session, and p.525's run scope and `fail_item` are separate scopes.

| Topic | One place | Another | The author's later work |
|---|---|---|---|
| Fresh clone or worktree | p.627, and p.628 rejects a long-lived tree | pp.466, 621 on parallel mutators, so partly scale | Skill says clone (`ce:skills/agent-orchestration/SKILL.md:240`), code uses worktrees |
| When to check the budget | After spending (p.520) | Before the call (p.529) | Neither harness checks before the crossing call. B69 stands on argument |
| What a shared queue is | Orchestration (p.669) | Choreography (p.470) | Claiming workers, consistent with here |
| Promoting rules | Automatic (p.725) | Human approval (Ch 32) | No automatic promotion found in Keystone. Supports rule 95 |
| Where behaviour lives | "Up the rings" (p.830; it also puts reacting behaviour in the binary) | Pushes knowledge toward determinism (p.715) | Keystone's Go grew from 4 files to 169 |

**Where this design is ahead,** on paper only, since none of it has run:
- **Fence.** `commit.sql` and `rekind_split.sql` match on holder and attempt. In open-refinery a turn slower than 900
  seconds gets a second worker in the same worktree (inferred). `iii-blackboard`'s CAS is optional, 3 of 4 writes
  blind *(unchecked)*, and `hands-on-iii`'s epoch check doesn't guard who owns the work.
- **Typed failures.** `FailureClass`, and `CHECK_UNAVAILABLE`, the distinction both of Keystone's weakened sensors
  lost.
- **Run identity.** Core's pin and hash against no charter digest in Keystone or sigma, and `iii-layers` omits model
  and commit per run *(unchecked)*. It stops short on rungs (B1).
- **The prompt.** `render()`'s scope and contiguity check against a flat join (`sigma:prompt/prompt.go:26`)
  *(unchecked)*, and Go's map order randomizing sigma's tool list (`sigma:internal/tools/tools.go:55`), where here it
  is the jig's fixed order (`jig-sketch.py:561`).
- **Retry context.** Layer 7 reads the failure, and open-refinery's `last_refusal` is never rendered *(unchecked)*.
- **ADR-0010.** The harness adds a file from a table. In Keystone the agent filters globs itself.
- **Grants.** Fixed on the jig. In `iii-layers` a planner model decides, and an empty grant falls back to all four
  tools (`iii-layers:planner_worker.py:117-118`, `coder_worker.py:244`, *(unchecked)*).
- **Hidden checks and escape markers.** Principle 5 has no counterpart in the later seven repos, and the workshop's
  scorer is in the agent's tree. Markers are model-writable in `ladder` (`ladder:gate.py:84-86`, *(unchecked)*),
  `hands-on-iii` and the workshop. None were found here, and that should stay true.

## Not borrowing

| What | Why not |
|---|---|
| Everything is a plugin (DSH); layer spines, plugin host, 12-event bus (sigma) | The measured cost in B-section above, ADR-0005's exclusion list. Five kinds and a fixed `dispatch_tool` need no extension point |
| Compaction, in-loop retry, recovery, steering, resume, subagents, output continuation, mid-session model switching, extensions (DSH, Pi, OpenCode); framework builds (Ch 42-43, 51-52) | ADR-0005, core §3.4, policy §1.6. An attempt that fails simply ends |
| sigma's retry layer | Immediate, retries 401s, re-emits streamed text *(unchecked)*. ADR-0005 forbids it |
| `repeat-tool-reminder` (DSH), doom-loop detection (OpenCode, dead in code at `opencode:core/src/v1/config/permission.ts:27`) | `opendev-port-notes` excludes it, and an `args_digest` query gives the signal |
| `blockedAfterConsecutiveRounds` (DSH) | It delays refusals, which we want early |
| `flock` ownership, same-session retries (DSH) | Single host, and contradicts stateless workers and identical-prompt retries |
| Event-sourcing the ledger (DSH) | ADR-0014 gets the benefit with three columns |
| Indexing content for search, model-facing `session_search` (DSH) | Core §4.3 and ADR-0005's small tool surface. Name the refused question (B89) |
| `isContextWindowExceededError`, stderr signatures (DSH); overflow regexes as runtime logic (OpenCode) | Text matching, which ADR-0011 rejected. Test cases at most (B61) |
| Argument coercion, `{}` fallback, tool aliases (DSH, Pi, OpenCode *(unchecked)*) | Port notes §1.2. Pi's comment that models often send these is evidence for the port notes' §5 trigger |
| Per-file 100% coverage (DSH) | Postmortem 0001 shows it missed a dead product |
| bwrap, Seatbelt, ACL backends, `sandbox_permissions` (DSH); permission rulesets, asks, `external_directory` (OpenCode) | Weaker than the container. Rules 48-54 are void, and cards have no in-loop approver (ADR-0003) |
| Model-chosen skill loading (DSH) | Policy §5.1's hand-chosen sets |
| DSH's benchmarks | Time, heap and scaling only, not agent quality *(docs)* |
| Code mode (Pi) | An interpreter inside the loop ADR-0005 keeps small |
| Per-tool `replay` flags (Pi) | Workspace destruction and `retry_safe` already cover this per card |
| "Four tools is enough" (Pi) | A 2025 claim. The ablation settles §1.6's tool-width question. Cite Pi's repo, not its dated posts |
| Running complete tool calls from a truncated stream (`opencode:core/src/session/runner/step.ts:119-131`) | B58 is stricter, and with no streaming it costs nothing |
| Treating unknown failures as retryable (`opencode:ai/src/schema/errors.ts:216`) | ADR-0011: ambiguous stays `provider_refused` |
| In-process recorder as the kept test (OpenCode) | ADR-0005: "a recording proxy, not a transport hook" |
| Autonomy ladder L0-L4 (Ch 58) | This is a helper by design |
| n≥30 as a number (pp.380-381) | No derivation. Use B75 |
| Vector store, reranker, staleness budgets (Ch 36) | No prose corpus. Knowledge files are hand-written and hashed |
| MCP and charter-as-a-service (Ch 20, 26) | Cards deny network. The in-process registry gives what p.250 credits to MCP |
| Dashboards (book, repos); packs, forge and tracker ports | Core §9.3's static page is enough. Out of scope |
| SemVer, changelog, forward-only patching for the charter (Ch 31) | No consumers. The pin and rule 128 are enough |
| Curator calendar and daily rhythm (pp.424-427) | Built for a team reviewing a stream of PRs. The event trigger is B84 |
| Hash chain over the record (p.678) | The book's own threshold is "the second harness or the first auditor" (p.704) |
| Judge panel (p.620) | ADR-0002. The book offers no evidence for it |
| Dual-LLM quarantine (pp.504-505) | An executor must read code to edit it |
| Experiment engine, sign and z-tests (Ch 58, `open-refinery:experiments.py:11-13` *(unchecked)*) | Too few cases. `(config_hash, intent_digest)` covers the tagging |
| Keystone's cascade, policy tree, 13 kinds; layers, locking, specialisation (`ladder`); multi-host projection | One project, one runtime. Open-ended events cut against rule 31 |
| Stale claim without a fence; `held` as a flag (open-refinery) | This repo's lease is better, and `park.sql` makes it a state |
| Conformance score bands; two-signer rules | Invented thresholds. One operator, so no-self-approve could not be passed |
| Importing any skill into layer 2 | Rules 120 and 125, R51. Usable as a review pass, which is how they earned their place |
| iii as a substrate | No borrow needs it, and Postgres avoids the file-then-message dual write |
| Capabilities on one ladder (`ladder:src/lifecycle.py:140` *(unchecked)*) | The rungs are ownership layers, which one project lacks. The jig's tool list already is the grant |
| Promotion thresholds, verdict printer, `bin/promote` *(unchecked)* | Pooled and underived (B1) |
| Agent-writable escape markers | They would defeat hidden rungs |
| "A check that raises is a finding" | It collapses what `CHECK_UNAVAILABLE` separates |
| Hot-reloaded graph, prompts and rules | Directly against the pin |
| Worktree snapshot and restore | Cards have per-attempt workspaces |
| Blackboard vocabulary; Tarrasque, the nine checks, AST rules keyed on variable names | No evidence behind it; specific to the workshop. Take the scorecard's shape (B78) |
| `hands-on-iii`'s chapter order as a build plan | A teaching order, and `ch11` adds the record, where rows never written can't be recovered. Take the stub walk (B47) |
| `learn-harness`'s curriculum | Vendor docs, one commit, no result beyond three inline examples |
| Presets, trust files, collision renaming (`pi-config`) | Stock-agent concerns. No repo charters load here |
| Running Jig's `drive-pr` or dispatcher | Not yet. Revisit once other teams use them and its issues #399-#403 are closed |

## Defects and doc drift

Noticed in this repo while reading, and not items above. Each was traced, not run. All are first cases for B46.

- **A split's refusal lands on `HARNESS_BUG`.** A refusal returns its payload (`jig-sketch.py:624`), `plan_emissions`
  runs on any truthy payload (`:871`), `payload["children"]` raises KeyError (`:745`), and the generic handler catches
  it (`:888-889`). So a split never reaches `awaiting_review`.
- **`HARNESS_BUG` says "quarantine, do not retry"** (`jig-sketch.py:77`), but `reaper_flip.sql` has no branch for it
  and retries until `max_attempts`.
- **An unknown refusal reason carries no `failure_class`** (`jig-sketch.py:619-623`), so `reaper_flip.sql` relabels it
  `stalled` or `lease_expired`. Inferred: `JigResult` has no definition.
- **`detail=` has no column** (`jig-sketch.py:620`, `:878`, `:889`), so a `SplitRejected` reason never reaches layer
  7.
- **`tree.sql` undercounts subtree cost.** It sums `tasks.cost_usd`, which only `commit.sql` writes, the last
  response's cost (`jig-sketch.py:631`). A quarantined card shows $0. Read `model_calls` instead.
- **The `Model` protocol declares only `complete`** (`jig-sketch.py:432-433`), while `CachedModel` also calls `build`
  and `identity` (`:477-478`).
- **`dispatch_tool` still runs the quota, side-effect and approval checks** (`jig-sketch.py:515-526`) that ADR-0003
  voided. `NeedsApproval` has no handler.
- **`README.md` is stale.** It cites `change-register.md`, as do core:5 and policy:5, where `rules-and-risks.md:3-5`
  replaced it. It lists `pharmacy.schema.yaml` and archive files not in the repo. Its line counts are wrong, and it
  says "Rules 1–130, R1–R53" where there are 152 rules and 64 risks. Its ADR index omits 0005-0007, and 0005 and 0006
  sit at the root.
- **E3's baseline conflicts.** Policy §7.4 says a sequential pipeline (`harness-policy-v3.md:742-750`), and
  `rules-and-risks.md` §6 item 8 names Gas Town, which policy §10 calls parallel.
- **`odoo-adaptation.md:1081` cites rule 96,** which now means "a note is superseded". The generator text belongs to
  rule 104.
- **`rules-and-risks.md:483` says "133 rules and 56 risks"** *(unchecked)*.

## Words

Keep this repo's words. The same words mean something else in the sources.

- **Charter** (book) is wider than jigs and skills: checks, hidden rungs, host hooks, layer 1, the root intent and its
  CONSTRAINTS, the anchor, role config and failure-class policy (pp.39, 52). `rules-and-risks.md` is not charter,
  since no card reads it.
- **Skill** (book) is a multi-phase workflow the agent picks for itself (p.745), which rules 113-115 forbid in a card.
  This repo's skill is closer to the book's rule or idiom. `ce`'s skills are closer to layer 2.
- **Harness** (book) comes at two levels (p.742): the card runtime plus `render()`, `dispatch_tool`, `run_oracle` and
  the container; and the board and workers.
- **Orchestrator** is inconsistent in the book (§7). Here the board is the state, the readiness predicate is the
  book's "derivation function" (p.752), and nothing decides.
- **Rung.** In the author's repos a place a rule is enforced (`iii-layers:RUNGS.md`,
  `hands-on-iii:workers/ladder/src/rules.py:22-26`): call those "enforcement points". In Jig, a step of its
  enforcement ladder. Here, an entry on a kind's check ladder in `checks.yaml`.
- **Jig** the project is unrelated to this repo's jigs. It uses `tier` for a model or deploy tier, `kind` for a
  code-stats dimension and `park` for human decision classes, and it avoids `card` in favour of "issue".
- **Layer** in sigma means what should be called "wrappers" here. **Also collide:** gate, contract, policy, and the
  book's Verifier, which refutes a reviewer's finding.

## Verdict

Borrow the questions, the failure stories and three small shapes (B46's `ScriptedModel`, B69's budget decorator, B27's
pure route function), and adopt no package. The book is useful as a source of questions, not a record of practice.
Nothing read shows a harness catching a real problem in the author's work, and the only committed numbers contain an
arm that duplicates another, a null independent variable, a contaminated control and a metric that moved because of
the instrument.

The strongest lesson is about this repo's own risk. The author could not keep prose and code aligned over a few weeks,
working alone (a `severity: must` guide cites a tool that no longer exists *(unchecked)*), and the correction that
worked was deletion: "the road to 3.0 is mostly deletion" (`open-refinery:docs/ROAD-TO-3.0.md:8`). This repo's 152
rules and 64 risks describe a system that has not run, which is R56. The next step probably isn't another repo. It's
to turn the list above into ADR amendments and tests, and to run a real job.
