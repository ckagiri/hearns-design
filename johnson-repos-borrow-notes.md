# Ian Johnson's four repos — what the code adds to the book note

**Subject:** the author's public repos, read as a follow-up to `johnson-harness-engineering-borrow-notes.md` ("the note").
Corrected the same day after reading seven later repos: see `johnson-later-repos-borrow-notes.md`.
Paths are relative to each repo's root. Read against this repo's commit `1e293f2`. Written 2026-11-06.

| Repo | What it is | Commit, last date | Size | State |
|---|---|---|---|---|
| `tacoda/keystone` | Charter framework, Go | `62ccdac`, 2026-07-01 | 21k lines, 5.8k of tests, 536 markdown files | v4.0.0, four majors in 23 days. 44 stars, no outside use visible |
| `tacoda/sigma` | Coding-agent CLI, Go | `3ca5e35`, 2026-07-15 | 6.9k lines, 3.1k of tests | v0.0.1. The book's "reference harness" and, by its own word, an experiment (p.818) |
| `tacoda/open-refinery` | Factory control plane, Python on SQLite | `daf65a8`, 2026-09-28 | 14k of src, 9.2k of tests | 3.0 held and unreleased. "No live model call has been exercised" in its suite (`LIMITATIONS.md:125`) |
| `tacoda/constraint-engineering` | Seven skills distilled from the book | `9906bb2`, 2026-09-15 | 4.2k lines of markdown | Two commits, no evals |

**Basis.** Four subagents read one repo each, and one of them ran a review checklist from the skills against this design.
The main thread then rechecked the decisive claims against the source: the Keystone merge, the verify and hook paths, the
sigma tool, budget and stop-reason code, the open-refinery claim, routes and contracts, the traces through this repo in
[New](#new), and a sample of the book quotes. Items marked *(unchecked)* rest on one subagent's reading. Nothing was run, and every trace comes from
reading. "Not found" means by keyword search, which is not proof of absence.

- **Not read:** Keystone's templates (sampled), `web/`, `eval/` and migrations; sigma's `tui/`, `scaffold`, `commands`,
  `rules` and most of `mcp`; open-refinery's frontend, auth, packs and most routers. `deepagents` is not vendored in
  open-refinery, so its behaviour is inferred.
- **Timing matters.** Keystone's and sigma's last commits predate the book's publication on 2026-07-22, so a mismatch with
  those two existed when the book came out. open-refinery was rewritten afterwards: its 09-27 and 09-28 commits are
  +27.7k/−13.6k lines. Whether each book claim held in July was not checked.

**Rule 133.** This is the seventh borrow note outside the rule's three places, and it follows the same precedent: nothing
here is adopted until it moves into a document, an ADR, `rules-and-risks.md` or code.

---

## What the code changes

**1. The book describes more than the code does.** The note's top item, the lock, is unimplemented in Keystone. The
"no lease" claim was reversed in open-refinery. Several sigma claims were already false when the book was published. Read
the book's mechanisms as arguments, not as reports of practice. The note's ten items mostly survive, but on their
reasoning: none can cite the author's practice as support.

**2. None of the four offers field evidence of a working harness.**
- open-refinery has never exercised a live model call in its suite. Its own review calls the July code "a product that
  still cannot open a pull request" (`docs/PLAN-3.0.md:1299-1302`).
- sigma's only experiment is two cases, one repeat and no model. Its result sits in a commit message, which says it "proves
  the plugin shapes the agent" (`0aacd3f`). What it shows is that a regex blocks the string it was written for.
- The skills are mostly model-assisted compression of the book: both commits carry a Claude trailer, and one subagent's
  phrase-overlap test gave 62% *(unchecked)*. Treat any side they take as weak evidence of the author's later judgement. A
  trailer is evidence of model assistance, but its absence is not evidence of hand-writing: `pi-config` later bans it
  (`agent/AGENTS.md:101-103`).

**3. What the history does give us is failure patterns,** which the book could not. See [Field evidence](#field-evidence).

**4. The review pass found holes the note missed,** and the worst of them undercuts the note's own item 1. See
[New](#new).

## Book against code

Only the claims that bear on the note.

| Book | Code | Bears on |
|---|---|---|
| "the engine picks the locked rule, logs the conflict, and surfaces it" (p.139); `CONFLICT` output (p.143) | **Not implemented.** `mergeCascade` lets the project win and never consults `strict` (`internal/framework/charter/charter.go:166-173`). `findShadowing` compares filenames only (`internal/framework/loader/cascade.go:229-259`). `verify` exits 1, by hand, and nothing changes what is indexed. It is the only strict check found | Item 1 |
| Policies lock what the agent receives | They never reach the agent. `scanRoots` derives from `canonicalDirKind`, which has no `policies` (`primitive/primitive.go:97-111`, `primitive/walk.go:51-58`). Only the dashboard walks them (`web/cache.go:126`) | Item 1 |
| Required declarations with values at session start (p.141) | File existence only (`cascade.go:299-314`). `HasGaps` has no caller outside tests | Item 1 |
| "Keystone's reconciler is the reference" (p.417); "Sixty seconds is the default Keystone installs today" (p.627) | No reconciler at HEAD. The Go hit is a comment (`migrations/migrations.go:72`) | Positioning |
| Open-refinery "does not run a lease-based retry queue" (p.675) | **Reversed** by `bbdc9af`: a claim plus a 900-second stale takeover (`pipeline/workers.py:40,69-86`). It has no fence, heartbeat or attempt bound | Positioning |
| A quota refuses before the call (pp.677, 687) | Deleted. "Checked before a stage, charged after it" (`budgets.py:11-16`) | Item 8 |
| "The ceiling has to be checked before the call that would cross it" (p.529) | sigma checks `spent >= limit`, so the crossing call fires, and its test asserts that: spent 12 of limit 10 (`agent/modelstack.go:89`, `agent/modelstack_test.go:50-60`) | Item 8 |
| Rooting is "the same defense" as a `realpath` check (pp.494, 496) | `rooted()` is lexical, and an empty root is unconfined (`internal/tools/paths.go:12-23`). `EvalSymlinks` not found | Item 5 |
| Sandbox read-only "except the working directory" (p.496) | The model picks that directory: `dir` in the bash schema reaches `writableDirs` (`tools/bash.go:35,62`, `exec/sandbox.go:35,65-66`). `{"dir":"/"}` makes everything writable | Item 5 |
| `ReadOnly()` is the most reviewed line, under deny-by-default (p.493) | A nil policy allows everything (`agent/toolstack.go:123`). `code_health` declares `ReadOnly` and runs shell (`plugins/codehealth/codehealth.go:85-89`) | Item 5 |
| sigma "needs no API key" (pp.435, 818) | `OPENAI_API_KEY` required since `0b5c418` (`cmd/sigma/main.go:213-216`) | Basis |
| Silent empty reply fixed (p.455) | Every finish reason but `tool_calls` becomes `end_turn` (`internal/openai/stream.go:110-115`). `length` and `content_filter` read as success | Stop-reason cases, OpenCode note |

**Holds:** sigma's 50-iteration cap and one level of sub-agents; open-refinery's audit hash chain and digest record
*(unchecked)*; Keystone's `on:` in the reviewed file, and `DepthViolation`.

## Corrections to the note

All eleven were applied to the note on 2026-11-06. The line numbers here refer to the note before those edits.

1. **The scope verdict misapplies p.442 (lines 294-296, 408-410).** The checklist asks about background execution,
   multi-model routing, and determinism or durability, and "Two or more" means "you are building an agent system". This
   design answers yes to all three as drawn. The note's "one yes" comes from discounting against the comparables, which the
   checklist does not ask. The caution still has support: p.442's closing "when the stock one runs out of road", p.570,
   App D p.819, and the distilled form, "Build one when the workflow you need is one no stock harness can express — not
   because building one sounds interesting" (`skills/agent-harness-building/SKILL.md:25-27`). Rest it on those, and drop
   "by its own test".
2. **Remove the p.675 contrast (lines 291-292).** Against open-refinery, "fenced" is now the whole difference: its HEAD is
   claiming workers (`pipeline/workers.py:8-19`), the same shape as here, without the fence. The author's later `hands-on-iii`
   has no claim or lease at all, by word search, so p.675 fits that one again.
3. **"Function of stored state" (line 287) holds for deciding, not doing.** In open-refinery the worktree is state outside
   the row. Three traces *(unchecked)*: a crash after commit makes the retry see a clean tree and fail; a crash mid-`prove`
   ships the check's edits; a crash after `open_pr` fires it again. This repo provisions a workspace per attempt, so it should not inherit these. Test it
   anyway (item 9).
4. **Item 2's unfinished verbs are six, not two (lines 89-90).** Under `harness/ledger/sql/`, `review_return.sql` covers
   approve, edit, split and requeue. `kill`, `promote`, `reset`, `clear_halt`, `raise_budget` and `abandon` have no statement,
   and no file there inserts into `reviews`, though core requires the record (`harness-core-v3.md:750-752`).
5. **"Add an operator halt" is cheaper than it reads (line 96).** `halt_run.sql` exists, and `claim.sql:19-20` already
   refuses a halted run.
6. **Item 1 cites rule 89 for `semantic:` and `test:` (line 59).** Rule 89 names neither (`rules-and-risks.md:202`). The keys
   are at `odoo-adaptation.md:343-344,404`, and rule 101 names `semantic:`. Item 1 also leans on p.139 as a mechanism. Justify
   it from R35 and policy §3.8 instead.
7. **The contradictions table overstates three rows.**
   - **Hold or fail (line 334):** p.268 is a per-session budget where "the human decides". p.525's run scope is `halt_fleet`,
     "a human decides what resumes", and `fail_item` is a separate per-item scope. They agree, and this design's split fits.
   - **Clone or worktree (line 332):** partly scale. pp.466 and 621 cover parallel mutators and p.627 per-dispatch, though
     p.628 still rejects a long-lived tree.
   - **Where behaviour lives (line 337):** pp.829-830 also put reacting behaviour in the binary, and Ch 60 pushes *knowledge*
     down (p.715). The real conflict is in the code: p.830 says the "default direction of change is up the rings", while Keystone's Go grew
     from 4 files at v0.1.0 to 169 at v4.0.0.
8. **Compaction (line 321) is stronger for "Here".** sigma compacts only at a turn boundary (`internal/agent/turnstack.go:36-47`),
   so it never fires inside a one-shot run. A card is one turn.
9. **Item 5's quote (line 131) is the book's Python.** The author's Go lacks it. The item stands, and its Gate A case is
   exactly what sigma's suite omits (`internal/tools/rooting_test.go`) *(unchecked)*.
10. **Add to "the book's evidence is thin" (line 16):** some of its sample terminal output matches no code, such as the
    `charter show --path/--topic` output on pp.140-143 (`cmd/keystone/charter.go:124-143` parses neither).
11. **"Skill" in Words (line 34)** holds for the book's definition. The published skills are reference bundles with routing,
    closer to this repo's layer 2.

## Against the note's items

Where the code bears on an item. Items 1 and 5 lose an implied precedent, and 2, 8 and 9 gain a shape to copy.

**Item 1: the lock.** This repo's gate, at emit on a declared field, would be stronger than anything Keystone has. There is
nothing to copy except the split between hard errors and advisories in `VerifyResult` (`loader/cascade.go:20-31`). It also
has a hole: see New 1.

**Item 2: routes.**
- **Copy the shape:** a pure `advance(run, graph, result) -> Move` (`pipeline/graph.py`), here as
  `route(kind, outcome, attempts)` behind the table in policy §9.
- **But test it through the runner.** Those pure tests pass for routes that are dead in the product: `merge` reaches `landed`
  in `tests/test_pipeline_graph.py:107-111`, while the first poll with no event holds the run (`actions.py:173`,
  `graph.py:158`) and workers skip held runs (`workers.py:61,81`). No forge webhook was found, so a run cannot land unattended
  *(traced, not run)*.
- **`failed` has no exit in that code either,** and rework has no bound *(unchecked)*. No state or verb table exists in code.
  This repo's `park.sql` already beats a `held` flag.
- **Repair context:** `last_refusal` is stored and never rendered *(unchecked)*. Layer 7 is well ahead.

**Item 3: frozen attempts.** The note goes further than the author's code does. There, immutability is "no update route exists" and a comment, the audit chain
detects tampering rather than preventing it, and prompts are overwritten in place *(unchecked)*. Copy one small thing:
`downgraded_from` on a persisted result (`pipeline/contracts.py:88-93`). See also New 5.

**Item 4: samples.** Absent from all four. sigma's `Repeats` averages with no spread, and transcripts overwrite
*(unchecked)*. Its live mode never reads recordings, but that cure does not transfer, because rule 147 needs live hits. The
skills advise "Re-run the same prompt" (`skills/harness-engineering/SKILL.md:119`), which walks straight into
this repo's cache trap. The note's sample value stands.

**Item 5: where tools execute.** Both harnesses are the note's "file tools on the host" branch, so they show the predicted
holes and offer no model. In sigma a symlink planted by bash makes `write_file` escape, and bash inherits the provider key
(`exec/sandbox.go:40-42`, no `cmd.Env`).
- **Copy the factory, not `fn(args, ctx)`:** `make_tools(workspace)` per attempt, with the workspace required and no empty
  default (`agent/subagent.go`, `NewTools func(root string)`). About 20 lines. An unset workspace then cannot silently mean
  unconfined.
- **Add a Gate A case:** the model must not be able to choose what a sandbox treats as writable.

**Item 6: `gated()`.** open-refinery's `Repository.oversight` has five levels and is set per repo. It is not on a contract,
not set at intake and not signed, and no raises-only logic was found *(unchecked)*.
- **Copy:** an unknown level falls to the safer one (`pipeline/agent.py:50`) *(unchecked)*.
- **Avoid:** one `approved_at` shared across stages, so one approval opens every later gate. Its plan gate also fires before
  the plan stage runs (`pipeline/runner.py:124`, `graph.py:192`, `spec.py:320`), so the person approves an unwritten plan.
- **Take two inputs** from the rubric at `skills/agent-charter-operations/SKILL.md:261-271`: reversibility and falsifiable
  criteria are card facts. Its history questions would break replay *(unchecked)*.

**Item 7: hooks in the pin.** Neither harness does it. sigma ignores `.sigma/` in git, despite p.240's "versioned and
reviewed", and hashes nothing *(unchecked)*. The item rests on core's own hidden-rung argument, which is enough. Keystone's
one cheap good idea is `on:` and `run:` declared in reviewed frontmatter.

**Item 8: token ceiling.**
- **Copy:** sigma's decorator (`agent/modelstack.go:87-100`), about 25 lines, placed outside `CachedModel` so it counts
  served tokens and trips alike in live and replay. Fix its flaw: estimate `spent + last_input + max_tokens` before the call.
- **Avoid three bugs:**
  - A fresh budget per sub-agent, though config says session (`agent/subagent.go:84`) *(unchecked)*.
  - open-refinery's ERROR and interrupt returning `units=0`, so a failed turn goes uncharged (`pipeline/agent.py:199,204`
    *(unchecked)*).
  - open-refinery's only in-turn bound is not a turn cap: `max_turns` is passed as `recursion_limit` (`pipeline/agent.py:197`),
    which counts super-steps, and a model-and-tool round takes at least two (inferred).
- **Copy:** a budget refusal bypasses the error route, so `on_error: continue` cannot walk past it (`pipeline/runner.py:135-147`)
  *(unchecked)*.
- **ADR-0005 gains no argument here.** open-refinery says an inside-turn ceiling "cannot" work, because its seam "sees a tool
  call rather than a model call" (`pipeline/middleware.py:7-11`). That is true only of the seam it chose, `wrap_tool_call`
  (`pipeline/agent.py:60-62`). LangChain 1.4.2, the version it locks, also has `before_model` and `wrap_model_call`
  (`langchain/agents/middleware/types.py:455,503`). An earlier version of this note called this a framework limit. That was
  an inference, and it was wrong. See `johnson-later-repos-borrow-notes.md`.

**Item 9: `ScriptedModel`. The most copyable thing in the four repos.**
- **Port:** one method (`Stream(ctx, req, onText)`, `agent/agent.go:60-62`).
- **Doubles:** `fakeStreamer` is strict and errors when exhausted (`agent/fakes_test.go:14-35`). `fakeClient` repeats its last
  result, for testing bounds (`agent/agent_test.go:15-27`) *(unchecked)*.
- **Do better than sigma:**
  - **Assert what was sent.** sigma's `reqs` is written and never read. open-refinery's `tests/test_harness.py:314-328` uses
    `requires=("spec",)` while shipped review has `requires: ["work"]`, so review reads the implementer's summary, against
    its own comment *(unchecked)*.
  - **Fake at the model, not above the runner.** open-refinery fakes `phase_runner`, and its bugs sit underneath that seam.
  - **Script tool-use replies and `HarnessFailure`.** `ScriptedModel` also needs `build` and `identity`.
- **First cases:** assert the rendered prompt, drive every terminal state through the runner, crash at each commit boundary,
  and "an ambiguous check fails closed" (`skills/agent-harness-building/SKILL.md:231-237`) *(unchecked)*.

**Item 10: amendments ledger.** Keystone is the negative result. It has a full prose amendment pipeline, and its
`.charter/learning/{inbox,promoted,rejected}` hold only `.gitkeep`. Its pruner concedes "Effectiveness... needs telemetry we
don't have yet" (`web/prune.go:38-39`). That supports "the sensor needs to live in code". Take the
`Source` and `Evidence` columns from `skills/agent-charter-operations/references/templates.md:12-37`, and keep the note's
hash-before-and-after and `no_patch`, which it lacks.

**Rule table columns (Smaller).** No working example in these four repos. `hands-on-iii` has one:
`workers/ladder/src/rules.py:22-26,85-97`. sigma's prompt labels a rule "(guarded)" when code backs it
(`plugins/canon/canon.go:4-5`) *(unchecked)*, which is a small argument for the "enforced by" column.

## New

Ranked. Items 1–7 are defects in this design that the note missed. Items 8–12 are smaller ideas.

**1. `expect: FAIL` cannot tell the right failure from a broken import.**
- **Source:** "Confirm the new tests fail for the behavioral gap, not for a missing import" (`skills/agent-primitives/references/skeletons.md:40-42`; p.767).
- **Here:** policy says only that the test "runs and **fails**" (`harness-policy-v3.md:478-479`), the inversion is "elided"
  (`jig-sketch.py:676-677`), and no field carries the distinction.
- **Why it matters:** a broken import satisfies RED, the implementation card may not edit the test (policy:480), and it burns
  its attempts and quarantines (inferred). **Item 1's gate would then enforce a pairing that can pass vacuously, on the one
  mechanism R35 calls load-bearing.**
- **Change:** the rung spec names failure kinds that do not count, by runner exit code. Odoo needs a spike first, since a
  missing-model error is the expected failure there.

**2. Config errors fail open.**
- **Source:** *(unchecked)* `skills/agent-harness-building/SKILL.md:178`, and the lights-out checklist in
  `skills/agent-orchestration/references/templates.md`.
- **Here:**
  - A kind missing from `checks.yaml`, or a typo in a rung's `kinds`, gives an empty ladder, then `not_applicable`
    (`jig-sketch.py:680-682`), then `done` (`001_initial.sql:92-93`). Rule 145 only covers a kind that has a ladder.
  - `rungs_for` silently drops a chosen rung that does not exist (`:669-671`), so a card can pass on the always-on rungs alone.
  - `validate_roles` never reads the ladder (`:245-255`), and `narrowed_rungs` has no definition (`:754`).
- **Change:** at startup, every kind must have a ladder or be declared `not_applicable` by name, and every rung a `kinds`
  entry names must exist. At emit, every rung in a `check_spec` must exist. A few lines, and it closes a route to `done`
  without a check.

**3. Nothing bounds depth.**
- **Source:** "Recursion limit — depth of delegation", one of five bounds to "wire all of"
  (`skills/agent-harness-building/SKILL.md:84-91`).
- **Here:** `shape_children` caps width only (`jig-sketch.py:750`). `rekind_split.sql` stops split→split on one row, but
  execute→split→execute→split stays open. Core calls this free (`harness-core-v3.md:394`), and policy treats it as a feature
  (`harness-policy-v3.md:385-387`). Only the nullable budget stops it (`001_initial.sql:133`). `max_depth` not found.
- **Change:** derive depth from the hierarchical id in `shape_children`, and park at the limit. A few lines, plus a line in the
  note's item 2 table.

**4. Test that every declared thing has a reader and a statement.**
- **Source:** Keystone's `manifest.Strict` is schema-documented with no reader, which is why the one real policy's lock is
  inert *(unchecked for that policy)*. open-refinery's `tests/test_route_coverage.py` was written after a review deleted a
  router and every test stayed green (`b5585d2`, `d68a79e`), and `repo.max_revisions` is still never read *(unchecked)*.
- **Here:** six of ten verbs have no statement (correction 4), and `gate` on `Role` has no `gated()` (`jig-sketch.py:226,741`).
  `tests/ledger/` has no such check by keyword search.
- **Change:** a test in `tests/ledger/` that every verb and state in `001_initial.sql` has a statement, and every role and
  `checks.yaml` key has a reader. Under a day, and it finds item 2's holes mechanically. Derive it from the schema, where
  open-refinery's is a hand list.

**5. The record does not keep what the model saw.**
- **Source:** `skills/agent-orchestration/references/templates.md:306` *(unchecked)*.
- **Here:** `prompt_ref` is written before the turn loop (`jig-sketch.py:560`), despite the comment "store what the model SAW",
  so turn messages, tool results and repair prompts are not stored. Tool calls keep `args_digest` only (`001_initial.sql:210`),
  and `raw_ref` is written only if the normalizer changed the bytes (`jig-sketch.py:535`).
- **Change:** `content.put(wire)` at `:477`, plus `model_calls.request_ref`. The DeepSeek note says "consider" this for cache
  misses, and the OpenCode note depends on it. Move it to item 3's "before the first run" list: the wire contains every tool
  result, so one column answers all of the above. Secrets belong with it, per the OpenCode note.

**6. Rule 44 promises what core forbids.**
- **Here:** rule 44 requires "an owner, an alert and a triage path" (`rules-and-risks.md:138`). Core says "Poll only" and
  notification is absent, "not deferred" (`harness-core-v3.md:654-655`). No owner field was found. `queries/stalled.sql:6-9`
  starts only from `quarantined` and `awaiting_review`, so a budget refusal or a halted run returns nothing, and that stall
  shows up only as an absence.
- **Change:** rewrite rule 44 to what is true, and add a query for "pending, none claimable, and why". Cheap.

**7. The cheap check runs after the expensive one.**
- **Source:** "Run coarse filters before fine ones" (`skills/harness-engineering/SKILL.md:62`).
- **Here:** the oracle runs inside `run_jig` (`jig-sketch.py:571`), and the touch-set hook runs after it (`:872`), though policy
  calls that hook among the highest-firing and cheapest (`harness-policy-v3.md:441-442`). So a violation pays for a container
  first. `FailureClass` has no touch-set class (`:60-77`), so a raising hook lands on `HARNESS_BUG` (`:888-889`) (inferred).
- **Change:** run the touch-set check before the oracle, give it a class, and add it to item 2's table.

**8. Test a gate at its outermost exit.** Keystone's sensors can exit 2, but `hook fire` turns any failure into an error and
`main` exits 1 (`cmd/keystone/hook.go:68-70`, `main.go:27-29`), and the host treats that as non-blocking. So those hooks cannot
block. v2.4.1 had a working version, with a 5-second default timeout and "Exit 2 blocks" (`adapters/claudecode/hooks.go` at that tag). Here, add one test: a failing or hung `pre_commit` hook leaves the
card not `done`.

**9. A hidden rung can be measured from the cache.** The key excludes `kind_hash` (`jig-sketch.py:478`), and hidden rungs never
render. So changing one replays free until the first card diverges (inferred). sigma's replay A/B has this shape, though its
run proves little (`internal/eval/replay.go:30-33` *(unchecked)*). Not found in policy §7. One paragraph, no code. Beware the
shadow: "a rung whose idleness is caused by a removable rung above it has not demonstrated anything" (`RUNGS.md:62-63` in
`iii-harness-layers-and-promotion`). `run_oracle` stops at the first failure, so ablate the earlier rung, not the idle one.

**10. A downgrade contract for `verify` verdicts.** Copy it only together with a route: in the later `hands-on-iii` this is a
label, because "a contract never fails a job" (`tests/test_rework.py:167`). Unparseable is never a pass, and "yes" with no evidence becomes
`unproven` (`pipeline/contracts.py:31-45`). An objection needs `file:line`. No downgrade was found here. Avoid its leak:
`partial` is not in `OBJECTING`, so it passes (`contracts.py:65`).

**11. Stop on an identical failure, with a caveat.** open-refinery fails a stage that repeats the same refusal
(`pipeline/graph.py:104-107`). The subagent ranked this first. It ranks low here: the note's item 2 already parks a failing
gate kind, which covers `integrate`, and for other kinds an early stop would skip the positional tier-up (`harness-policy-v3.md:361-362`)
that exists for this exact case. Query the last two `check_ref` values on real runs before adding a branch. `check_ref` equality
cannot name the rung, so this needs New 1 in `johnson-later-repos-borrow-notes.md`.

**12. Detectors as queries.** The same stage failing across runs, revision churn and stalled holds (`improve.py:149-230`)
*(unchecked)*. Add them to `queries/lessons.sql` when step 7 needs them, and not before.

## Field evidence

What the histories show. These are the most useful things here, because nothing in the book says them.

- **False alarms got fixed by weakening the check.** Warnings fired "on every hook fire", so unknown sensors now exit 0 and
  soft-skip (Keystone `e234e32`). Noise from a missing tool became `command -v go && go vet ./... || true`, so a failing vet
  passes too (`6d79e37`, `.charter/guides/computational/go-vet.md:5`). open-refinery's content filter refused emails and
  13-digit literals on ordinary work, and was scoped back (`0615b2e`). **For this repo:** `CHECK_UNAVAILABLE` already separates
  "could not start" from "failed" (`jig-sketch.py:65`), and it needs protecting. Track false-fire rate per rung, because the
  pressure will be to loosen rungs.
- **A rewrite lost the working gate, and the suite didn't notice.** `08ab8a3` moved blocking to a dispatcher, which cannot
  block (New 8). `e1b198e` repaired nav 404s and a dead SSE topic that had shipped with the "full test suite green".
- **Green tests, unreachable product.** `b5585d2` deleted a router carrying features whose tests drove the modules directly
  (`tests/test_route_coverage.py:3-7`). `3680879` says of the process engine that "a run completely ignored it", and `0ff4bb4` says of the
  executor that "The factory never used it". Those two engines are the subject of Ch 56.
- **Tracing found what the suite didn't.** The auditor grant was not read-only (`f6bcfc4`), a failed downgrade could corrupt the
  database (`aa40966`), and a no-op typecheck hid type errors (`46a8548`). How each was found comes from their commit messages
  and one subagent's reading *(unchecked)*. The route defects under item 2 survive at HEAD with a large suite passing. Tracing
  is no substitute for running this design, but it has yielded findings in the author's repos and in these notes.
- **Prose answered by more prose.** Agents "could complete bootstrap by narrating", so the fix added an iron law and a grep
  check (`49ee731`). Precedence was misdescribed twice, each time claiming "the code has always" done it
  (`64fb53e`, `84eb08d`), and no resolver reads policies, so nothing could settle it *(inferred)*.
- **R56 happens fast.** Keystone's `.charter` is 175 files and 10.2k lines by one author in weeks, and a `severity: must` guide
  cites a tool and a directory that no longer exist *(unchecked)*. The response to load was lazy loading (`INDEX.lite.json`), not
  cutting, and no commit subject prunes a rule for going unfollowed. `keystone-3.0.0-domain.md` is marked "FROZEN" and defends
  `hook` as a kind, and `e225173` retired that kind for v4.0.0 *(unchecked)*. open-refinery's review went the other way: −2,110 lines, then "the road to 3.0 is
  mostly deletion" (`docs/ROAD-TO-3.0.md:8`). **Prose outran the code that was meant to back it,** in the book author's own project.
- **The provider port survived a real test.** sigma's swap of providers changed no loop code and added a 307-line adapter, but
  caching and stop-reason semantics leaked (`0b5c418`) *(unchecked)*. That supports ADR-0005's port. Add an adapter conformance
  table when a second adapter arrives, not before.

**Why they stopped (inference).** Keystone paused at v4.0.0 while preparing an AAIF submission, and on 07-09 the author pointed
an issue thread at open-refinery as "a more appropriate level". sigma looks finished as a teaching artifact, not superseded:
open-refinery never mentions it. Between open-refinery's two bursts came the August iii series, `ghola`, `ladder`, `audit-log`,
`workers` and `anchor`, and in October `tacoda/bastion`, most of them not read. Most projects were followed by a new one rather
than by use, which is the note's "learning is a legitimate aim" with a warning attached. `charter-workshop` is the exception:
it had an audience.

## The contradictions, against the author's later work

The note listed six places where the book contradicts itself. The skills' sides are book sentences kept or dropped, without
argument, so they are weak evidence. The code column is stronger.

| Topic | Skills pick | Code does | Judgement |
|---|---|---|---|
| Fresh clone or worktree | Clone: "Fresh clones every time" (`agent-orchestration/SKILL.md:240`) | Worktrees in both harnesses (`pipeline/workspace.py:23`) | **Here** stands. The author's practice disagrees with the skill |
| When to check the budget | Silent: "the ceiling has to throw" | Neither checks before the crossing call | Item 8 stands on argument |
| On a breach | Throw (`agent-harness-building/SKILL.md:84-85`) | sigma errors. open-refinery refuses the next stage | Not a real contradiction (correction 7) |
| What a shared queue is | "The orchestrator is a queue" | Claiming workers | Consistent with here |
| Promoting rules | Human: "The agent proposes; the human approves" (`agent-charter-operations/SKILL.md:66`) | No automatic promotion found in Keystone | Supports rule 95 |
| Where behaviour lives | Up: "Markdown beats code until a trigger forces the code" (`agent-harness-building/SKILL.md:31`) | Keystone's Go grew from 4 files to 169 | The code answers |

**What compression shed.** Ch 54's bound-and-exit checklist, abort, the kill switch, "before the call" and every story are gone
from the skills. Don't read that as retraction. It does mean that items 2 and 8 have to be read in the book, not the skills.

## Here is ahead

Worth knowing before borrowing anything. None of these has run either, so "ahead" means ahead on paper.

- **Fence.** `commit.sql` and `rekind_split.sql` match on holder and attempt. open-refinery has no fence, so a live turn slower
  than 900 seconds gets a second worker in the same worktree (inferred).
- **Typed failures.** `FailureClass` against sigma's two sentinels and untyped `fmt.Errorf`. "Check could not start" is already a
  class here (`CHECK_UNAVAILABLE`), which is the distinction both of Keystone's weakened sensors lost.
- **Run identity.** Core's pin and hash, against no charter digest in Keystone or sigma. Keystone's `verify` also deletes a
  drifted policy and exits 0 *(unchecked)*.
- **The prompt.** `render()`'s scope and contiguity check, against a flat join in sigma (`prompt/prompt.go:26`) *(unchecked)*,
  and Go's map order randomizing sigma's tool list on each call (`internal/tools/tools.go:55`). The p.481 claim of an identical prefix
  therefore fails in the author's code. Here the tool list is built in the jig's fixed order (`jig-sketch.py:561`).
- **Retry context.** Layer 7 reads the failure. open-refinery's `last_refusal` is never rendered.
- **ADR-0010.** The harness adds a file from a table. In Keystone the agent filters globs itself.

## Not borrowing

| The repos have | Why not |
|---|---|
| Keystone's cascade, policy tree and 13 kinds | One project with no outer layer, and the cascade doesn't reach the agent. Open-ended events cut against rule 31 |
| Multi-host projection | One runtime |
| sigma's layer spines, plugin host and 12-event bus | Five kinds and a fixed `dispatch_tool` order need no extension point. Keep this repo's word "layer", and call sigma's "wrappers" |
| sigma's retry layer | Immediate, retries 401s, re-emits streamed text *(unchecked)*. ADR-0005 forbids it |
| sign test and z-test experiments | Too few cases. `experiments.py:11-13` admits the limit *(unchecked)* |
| Stale claim without a fence | This repo's lease is better |
| `held` as a flag | `park.sql` makes it a state |
| Conformance score bands | Invented thresholds |
| Two-signer rules | One operator. No-self-approve could not be passed |
| Importing any skill into layer 2 | Rules 120 and 125, R51. They are usable as a review pass, which is how they earned their place here |
| Dashboards, packs, forge and tracker ports | Out of scope |

## Where to look first

| For | Read |
|---|---|
| The lock that isn't there | Keystone `internal/framework/charter/charter.go:166-173`, `loader/cascade.go:110-120,158-175` |
| Doubles and bounds for item 9 | sigma `internal/agent/fakes_test.go`, `agent_test.go`, `toolstack_test.go`, `agent_golden_test.go` |
| Budget decorator for item 8 | sigma `internal/agent/modelstack.go:80-100` |
| Tool boundary, as a list of what to avoid | sigma `internal/tools/paths.go`, `internal/exec/sandbox.go` |
| Pure route function for item 2 | open-refinery `src/open_refinery/pipeline/graph.py:96-160` |
| Downgrade contract | open-refinery `src/open_refinery/pipeline/contracts.py:31-96` |
| The author's own review | open-refinery `docs/PLAN-3.0.md`, §12; `docs/ROAD-TO-3.0.md`; `LIMITATIONS.md` |
| Questions for a review pass | constraint-engineering `skills/agent-harness-building/SKILL.md`, `skills/agent-orchestration/references/templates.md` |

## Verdict

The code weakens the book as a record of practice and leaves it useful as a source of questions. Nothing in the four repos shows
a harness that works in the field, and the author's most honest documents, `LIMITATIONS.md` and the review in `docs/PLAN-3.0.md`, say as much. Copy
three small shapes: `ScriptedModel`, the budget decorator and the pure route function.

Do the following before the first run, in this order, because each protects something the note's items rely on: New 1 (`expect: FAIL`,
or item 1's gate is hollow), New 2 (config cannot reach `done` unchecked), New 5 (the wire cannot be recovered afterwards), New 4
(the test that finds the remaining holes), New 3 (depth).

The strongest lesson is about this repo's own risk. The author could not keep prose and code aligned over a few weeks, working
alone. This repo's 152 rules and 64 risks describe a system that has not run, which is the position Keystone's charter was in.
The correction that worked in those repos was deletion, after looking hard at what the code actually did.
