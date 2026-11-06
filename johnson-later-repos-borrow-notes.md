# Seven more of Ian Johnson's repos — what the later work adds

**Subject:** seven of the author's public repos, read as a second follow-up. The earlier notes are
`johnson-harness-engineering-borrow-notes.md` ("the note", on the book) and `johnson-repos-borrow-notes.md` ("the repos
note", on Keystone, sigma, open-refinery and constraint-engineering). Paths are relative to each repo's root. Read against
this repo's commit `1e293f2`. Written 2026-11-06.

| Repo | What it is | Commit, last date | Size | State |
|---|---|---|---|---|
| `iii-harness-layers-and-promotion` | One rule at six rungs, with a promotion report | `933a7bb`, 2026-08-21 | 1.9k lines, 301 of tests | An afternoon experiment on a 40-line seed |
| `iii-blackboard` | Blackboard architecture, built two ways | `ada9d48`, 2026-08-26 | 430 lines | One commit, against a stub |
| `ladder` | Constraints and capabilities on one ladder | `a5725b6`, 2026-08-29 | 2.2k lines, 594 of tests | No model calls and no run data |
| `learn-harness` | Study path through the LangChain stack | `5a40fa3`, 2026-09-15 | 8.3k of markdown, 2.3k of examples | Mostly vendor-doc summaries |
| `hands-on-iii` | Companion code for a second book: a harness and factory on iii | `3b9566b`, 2026-10-11 | 3.9k lines, 4.4k of tests | Tagged by chapter. All 13 commits fall within 87 minutes, so it is a recut, not a history |
| `pi-config` | The author's configuration for the pi coding agent | `9a5d975`, 2026-10-20 | 1.9k lines, 224 of tests | Looks used. "Daily" is inferred |
| `charter-workshop` | A 90-minute workshop that measures a charter | `81a2851`, 2026-10-28 | 2.9k lines, 1k of tests | Used: 16 forks within 15 minutes on 2026-11-02 |

**Basis.** Four subagents read the repos in four strands. The main thread rechecked the decisive claims against the source,
including the record tallies and the statistics, which it recomputed. Items marked *(unchecked)* rest on one subagent's
reading. No repo code was run, and every trace comes from reading. "Not found" means by keyword search, which is not proof of
absence.

- **Not read:** the *Hands-on iii* book, the iii engine, the 15 third-party packages `pi-config` installs, and
  parts of `hands-on-iii`'s tests and `learn-harness`'s docs. Upstream pi, LangChain and deepagents were read through `gh` only.
- **`tacoda/ghola` was added later, for one question:** does it hold evidence of real runs? See [ghola](#ghola). Its code was not reviewed.
- **The book is no help here.** None of the seven appears in it, so this note compares the later work with what the book
  says, rather than checking the book's claims about the code.

**Rule 133.** This is the eighth borrow note outside the rule's three places. Nothing here is adopted until it moves into a
document, an ADR, `rules-and-risks.md` or code.

**A correction to an earlier note, already made.** The repos note said open-refinery's inside-turn ceiling limit "comes from
running on a framework", and that this gave ADR-0005 an argument. That was an inference in that note, and it was wrong. LangChain
1.4.2 has `before_model` and `wrap_model_call` (`langchain/agents/middleware/types.py:455,503`), and open-refinery chose
`wrap_tool_call`. The passage is fixed.

---

## Words

"Rung" collides. In these repos a rung is a place a rule is enforced: 0 prose, 1 grant, 2 hook, 3 tool call, 4 stage gate, 5 CI
(`RUNGS.md`, `workers/ladder/src/rules.py:22-26`). Here a rung is an entry on a kind's check ladder in `checks.yaml`. Keep this
repo's word, and call the author's "enforcement points".

## What the later work changes

**1. The author's own setup is the best evidence yet on scope.** `pi-config` is a stock agent, stock Claude Code on a
subscription (`agent/settings.json:3-4`), and a small first-party layer: 172 lines of instruction (`agent/AGENTS.md`,
`agent/APPEND_SYSTEM.md`), against 10.2k in Keystone's charter. A word search for keystone, sigma, open-refinery, ladder, iii,
charter-workshop, bastion, deepagents, langchain and langgraph finds nothing. The only tool of their own it installs is the
constraint-engineering skills (`skills.txt:9`). No budget ceiling, sandbox, contract or daemon was found.

The limits matter. This is one public config, for one person at a keyboard. It does not answer the background-execution case,
and it installs 15 packages that were not read. It does show the author not using their fleet layer for this work. The one target
repo seen points the same way: `tacoda/fawlty` dropped its Keystone block because it pointed at a missing file, "so every session
opened with a failed read" (`adbe43d`).

**2. Evidence of a working harness is thin: two README jobs.** See [ghola](#ghola). The other repos add little:
- The first live runs reported are the 12 in `iii-harness-layers-and-promotion`, but `runs/` is gitignored (`.gitignore:7`), so
  no number can be recomputed. The summary spans code versions: "Earlier provenance was migrated rather than re-run" (`77cb5f1`).
- `charter-workshop` commits records, but its three reference runs are two distinct patches (see [Measurement](#measurement)).
- `hands-on-iii`'s test docstrings claim real runs: "ghola's first reconciler spun 2,020 history entries in 75 seconds"
  (`tests/test_factory.py:209`). In `ghola` the fix and its test are traced, and the number is not.

**3. The first outside data exists, and it says little.** One fork of `charter-workshop` (`singularityhacker`, `cde7f2e`) ran all
five arms on Codex CLI. Decidable checks scored 7/8 in every arm: no movement. See [Measurement](#measurement).

**4. The author's position on promotion narrowed.** See [Later positions](#later-positions). This one bears on ADR-0010.

**5. The later work exposes six more holes in this design.** See [New](#new). The first cannot be recovered after a run.

## New

Ranked. Items 1–6 are holes in this design. Items 7–10 are smaller.

**1. This repo cannot say which rung failed, though an earlier draft could.**
- **Here:**
  - `CheckResult` has a state, `detail` and `hidden`, and no rung (`jig-sketch.py:695-697`).
  - `check_ref` is an output hash, and `hidden_check_ref` adds only one bit (`001_initial.sql:114-115`).
  - `post_tool_call` output is appended to tool text and not recorded (`jig-sketch.py:537-539`).
  - `rung_results jsonb` was in `initial_plan.md:279`, `files/PILOT.md:90` and `files/state-command.md:101`. `PILOT.md:226` says
    "Write results per rung". Word search finds it nowhere in core, policy or the schema.
- **Why it matters:** the promotion question, rule 121's ablation, the repos note's New 9 and 11, and a step-7 scorecard all need it.
- **Change:** one column on `task_attempts` listing every rung *reached* and its result, so that a rung behind an earlier failure
  shows as unreached: `run_oracle` "Stops at the first failure" (`jig-sketch.py:676`). Update `end_attempt.sql` and `commit_attempt.sql`.
  About 20 lines. Then one query is the promotion report:
  ```sql
  select a.kind, r.key, count(*) reached, count(*) filter (where r.value = 'failed') caught
    from task_attempts a, jsonb_each_text(a.rung_results) r group by 1, 2;
  ```
- **Key it on a stable name.** `Rung.rung: int` (`jig-sketch.py:232`) is what `check_spec` selects. Inserting one rung cost the
  author a remap of their record (`77cb5f1`) and left stale docs (`RUNGS.md:100-113` *(unchecked)*). Add a stable `id`.
- **Don't port the thresholds.** `scripts/promotion.py:133-161` is deterministic, but it pools across rules, its 20 has no
  derivation, and advisory events count as catches: `attributable: False` is written (`gate_worker.py:164-172`) and never read
  (`promotion.py:49-50`). A person decides (rule 95).

**2. A new rung can fail on code no card may touch, and nothing scores the base tree.**
- **Source:** two repos reached this separately. "The gate was attributing the tree's pre-existing state to a job" (`docs/RESULTS.md:275`),
  and "a rule that is new to an existing codebase is violated by code that was already there" (`4f10c54`). The workshop fork's C8 is
  red in every arm, which the fork attributes to the base tree.
- **Here:** worse (inferred). A touch set bars the fix, so a rung added at a config bump fails attempts until quarantine on every
  card whose tree trips it. No baseline for this was found: the word search hits only E3.
- **Change:** at pin, run new rungs on the base tree, and refuse or list known-red ones. A few lines, plus a Gate A case. This also
  answers the note's Odoo-in-an-existing-codebase item.

**3. An empty diff may pass.**
- **Source:** the workshop's scorer gives an empty diff 8/8 on a green toolchain *(unchecked)*.
- **Here:** no rejection of an empty `execute` commit was found. `Outcome.OK` reaches `done` (`jig-sketch.py:809`), and rung selection
  can be narrow.
- **Field case:** `ghola` pushed "a branch… with nothing on it" (`2866476`). No rejection appears in `commit()` either (`jig-sketch.py:836`).
- **Change:** reject an `execute` commit with no diff, and give it a class. Derive the diff from `base_sha` (`harness-core-v3.md:200`), not from
  staged changes, because a turn in `ghola` committed by itself ("Committed clean: `8e3f381`", `tacoda/fawlty` PR #2), and under ADR-0014 a card can
  write `.git`. Add both cases to the test.

**4. Unknown cost reads as free.**
- **Source:** "an unpriced turn counts as over: a ceiling that reads $0.00 as safe is no ceiling" (`hands-on-iii`, `cost.py:94-108`).
- **Here:** `model_calls.cost_usd numeric(12,6) NOT NULL DEFAULT 0` (`001_initial.sql:157`), summed at the claim
  (`harness/ledger/sql/claim.sql:13`). An unpriced model reads as $0, so the budget never trips.
- **Change:** add `cost_source`, and let an unpriced live call refuse further claims. Cache hits stay $0 (`jig-sketch.py:483`). A few lines.

**5. A deny test can pass because the plant never fired.**
- **Source:** `pi-config/verify.ts:60-75` runs the refused case, then the allowed one, and fails the second with "so the plan result above
  proves nothing". `hands-on-iii/tests/live/test_ladder.py:16-17` has the same idea: "A model that declines on its own also leaves no file."
- **Here:** Gate A's "no marker appears" (`harness-core-v3.md:1096`, ADR-0014:78) has no such control. "Positive control" not found.
- **Change:** one sibling case per deny case, showing that the plant fires when nothing stops it.

**6. Nothing walks the pipeline before the kill tests.**
- **Source:** `hands-on-iii`'s `ch08` is a stage graph of stubs, with `test_stub_job_walks_to_waiting_with_four_history_entries`
  (`tests/test_factory.py:176-181`).
- **Here:** in `PLAN.md`, a jig cannot run until P2-13 (`PLAN.md:192`), behind Gate A. No such step was found.
- **Change:** after P1-6, stub jigs walk split, execute, verify and integrate to `done`. About half a day. It would exercise the note's item 2
  routes early and make New 4 of the repos note concrete.

**7. A guard that cannot load should remove the capability.** `pi-config`'s `preset.ts:437-446` drops the `subagent` tool when its ceiling
cannot load *(unchecked)*. Its `claude-charter` shows the opposite failure: `loadHooks` throws "A guard that silently vanishes is worse than
none" (`charter.ts:170-171`), and `index.ts:89-95` catches the throw, notifies, and carries on. Here, refuse a role at startup if its hooks did
not register. It extends the repos note's New 2.

**8. A hook shape, with the policy inverted.** `runHook` returns `{code, stdout, stderr, timedOut}`, and a pure `verdict(runs)` decides
(`charter.ts:385,424`). Copy that at `run_hooks` (`jig-sketch.py:868,872`), about 30 lines. Invert the policy, because a timeout passes there
(`charter.test.ts:193-195`). That adapter keeps a host's contract, and this design has no host to match. Also kill the process group: bash alone
leaves grandchildren holding the pipes (inferred, `charter.ts:397,405`). Add a compound command to the Gate A case. This is part of R64.

**9. An existing test can be rewritten to pass.** In both rounding arms the agent rewrote the test pinning half-up: "11 passed, gate clean, `done`"
(`docs/RESULTS.md:299`). That is n=2, with quoted diffs and no raw records. Rules 82–83 cover paired cards only. Add the existing-test case to the
test-file guard (`jigs-layers-skills-v2.md:103`): a commit hook rejects a behavioural card whose diff edits a test that existed at base. A few lines.

**10. Small, when needed.**
- **Every prompt field has a filler:** `tests/test_rework.py:71-77`, written after "ghola's review prompt carried a `$diff` that nothing wrote".
  Under an hour here, and it extends the repos note's New 4.
- **A premise test per specimen:** assert that the fixture still opposes the rule (`test_charter_gate.py`, *(unchecked)*). For E2's specimen, not Gate A.
- **Name how a run ends:** `quiescent` and `stalled` (`iii-blackboard/scratch/blackboard.py:112-134`) fit the unwritten `runs.outcome`.
- **A written prediction per arm** (`workshop/index.html`). Trivial, and the same discipline as step 7.
- **"Refuse a rule claim nothing carries":** see [Against the earlier notes](#against-the-earlier-notes).

## Measurement

The only repo that claims to measure a charter's effect, and the most instructive about how such a measurement goes wrong.

**Recomputed from the committed records:**

| Run | Decidable | Lines added | Patch `+` lines | `charter` field |
|---|---|---|---|---|
| Reference `00-bare` | 1/8 | 49 | 49 | null |
| Reference `01-reads` | 8/8 | 102 | 102 | null |
| Reference `02-checks` | 8/8 | 102 | 102 | null |
| Fork `00-bare` | 7/8 | 140 | 179 | null |
| Fork `01-instruction` | 7/8 | 182 | 227 | `CLAUDE.md` 652 words |
| Fork `02-constraint` | 7/8 | 184 | 222 | plus 4 in `.claude` |
| Fork `03-capability` | 7/8 | 62 | 200 | plus 10 in `.claude` |
| Fork `04-check` | 7/8 | 58 | 241 | plus 12 in `.claude` |

**What the reference runs show:**
- **Two arms are one patch.** Excluding run records, `01-reads` and `02-checks` hash identically (`a82e6796967f`).
- **The independent variable is null.** `bin/capture:55-70` records it, and all three reference scorecards show no charter. So the charter was
  probably not on disk at capture (inferred).
- **The baseline's seed already held its answer** *(unchecked)*. `1a07a4b`, subject "fix: bin/ imports tools.scorecard", also changed `handlers.py`,
  `http.py`, `legacy/tables.py` and two test files. A near-identical bare patch scored 4/8 at an earlier commit, so the gate looks tuned against the
  baseline (inferred).
- **The 8/8 patch may not work.** It reads a module global nothing populates, so real requests get empty results (traced, *(unchecked)*). The scorer has
  no acceptance test.

**What the fork shows:**
- **A metric moved because of the instrument.** `lines_added` falls from 184 to 62, which reads like a charter tightening the agent. `diff_size` uses
  `git diff --numstat`, which skips untracked files (`tools/scorecard.py:175-184`). Actual patch size rose. **Compute from the stored diff.**
- **The control was contaminated.** Every arm, bare included, contains both `authority-gate` and `provenance-gate`, which derive from the scorer's own
  escape markers (`charter_check.py`, *(unchecked)* for the derivation). The scorer sits in the agent's tree. So the bare agent probably read it (inferred).
- **It tests an adapter.** Codex reads no `.claude/`, so rules arrived through a generated `AGENTS.md` and hooks never ran. Levers 2–4 weren't tested as designed.
- **An anecdote worth one test.** Attempts stopped on the ticket-versus-rule conflict in 3 of 4 tries at levers 3–4, against 0 of 3 at levers 0–2, in prose only
  (two-sided Fisher p=.14). Policy lines 299 and 776 say a model "does not stop and ask". Test it in E2 arm C, and don't edit on this.

**What n can support.** Each cell has one run, so no arm has repeats. Yet the page's stated claim is "the charter alone narrows the band". The author's page is
candid about this: "Today was not a measurement… Do not quote any of it as a rate" (`workshop/index.html:2914-2916`). Recomputed:

| Comparison | Two-sided Fisher p |
|---|---|
| 5/5 against 0/5 | .008 |
| 4/5 against 0/5 | .048 |
| 4/5 against 1/5 | .21 |

- **Power at n=5:** .38 for .2→.8, and .15 for .3→.7. Reaching .96 for .2→.8 takes n=20.
- **5/5 passes** still has a 95% lower bound of 48% (two-sided).
- **Rule 121 needs a sample size.** To delete a skill at a 5% risk of deleting one that works, the consecutive misses needed are 5 at a base rate of .5, 14 at .2 and
  74 at .04. The two bare columns above disagree on six of eight checks, so a single RED reproduction, or a single failure to reproduce, says little.

**Changes here, all text:**
- Add to the RED pairing (`jigs-layers-skills-v2.md` §3.4): model id, base commit, observable event, base rate.
- Add to policy §7: tag each arm, and separate "not installed" from "removed". The author's "Deleted by the agent: 3" came from missing arm config
  (`docs/RESULTS.md:332-340`): "the instrument produced exactly the dramatic result the project was looking for, and it was an artifact."
- Add to the reviewer rules for E2: the prompt must not name the specimen. `charter-auditor.md:20-21` names "charmed", and 3 of 3 reviews cite charm *(unchecked)*.
- Add a Gate A case: from inside the container, hidden rung definitions and earlier arms' records are unreadable. Principle 5 is ahead on paper, and core §11.1 has no
  such case. It adds to the Pi note's arm-integrity protocol.
- **Raise the note's one-window arm.** It is this kind of run, and the fork's took 20 seconds to 2 minutes each. Run it first under policy §7.1.

**Step 7's scorecard.** Copy the shape: one row per check, one column per config, each cell tied to evidence. Don't copy the nine checks. Add `queries/scorecard.sql` by hand beside
step 7's thresholds (`PLAN.md:52,236`). Cells are pass, fail and not-reached counts per `config_hash`, plus policy §7.4's numbers. It needs New 1.

## ghola

`tacoda/ghola` at `e536a9a` (39 commits, 2026-08-29 to 09-02) was read for one question, because it is where `hands-on-iii` says real runs happened. Its answer changes this note's
earlier conclusion. **The harness did run end to end on real pull requests.** It is the only such case in the twelve repos read, and it is two small jobs.

| Target | Change | What happened |
|---|---|---|
| `tacoda/fawlty` PR #1 | README only, +66 −1, one commit | Opened by `ghola`, merged 8 minutes later |
| `tacoda/fawlty` PR #2 | README only, +12, two commits | A reviewer comment drove a rework on the same branch, with three machine comments marked `<!-- ghola -->`. Merged |

**What it ran on.** Not the author's own loop, and not Claude Code. Each phase is a `harness::send` to iii's stock `harness` worker, pinned at 1.8.7 (`worker-compose.yaml:84-85`, `workers/ghola-core/src/turn.py:3-5`), with models through `llm-router` and `provider-anthropic`. "Nothing here owns a loop, a
transcript, a retry, or a token budget." `claude-code` and `codex` workers are in the compose file, and no reference to them was found in `workers/`, `settings/` or `scripts/`.

**What this does not show.** Neither job changed code. The author is the commenter and the merge account, on their own repo. Nothing shows the harness catching a real problem, and there is no cost or turn data on real work. `state/`, `runs/` and `audit/` are gitignored, and `evals/*.json` are requests rather than results *(unchecked)*. Stated figures, such as 232 audit entries (`e926527`) and "control 1/1, treatment 0/1"
(`855ee06`), can't be traced *(unchecked)*.

**What the first real jobs found.** This is the most useful part.
- **Fakes missed what a real job hit at once.** The first job's six defects were "invisible to 240 passing tests and cost a real run" (`b4f2fff`). The worst was a filesystem scope that defaulted to the engine's directory, so a turn "would have edited ghola's files". The plan turn noticed and refused, so the model caught it, not the
  harness. That is item 5's "workspace required, no default" in the field. The rework then hit four more: "Four defects stood between it and working, none of which any test caught" (`2866476`). One was a shell string passed as a program name: "THE COMMIT NEVER RAN and a branch was pushed
  with nothing on it". Separately: "The first real job produced an audit log that failed its own verification, and nothing had tampered with it" (`dfa099a`).
- **Green stayed on the surface while the checks failed.** After the rework, a comment on PR #2 reported `prove: unproven` and `review: unreadable`. The PR's own summary still says `prove: yes` and `review: pass`, and it merged 12 minutes later. No cause is recorded. A person merged it by design, and this may have been
  a README judged good enough. Rule 145's `done_means_checked` covers the state on paper. **The lesson for a gate:** show the latest attempt's result, not the first.
- **A record was cut where it mattered.** The body was truncated at 10,000 characters inside the proof text. This is a case to check against rule 97, which keeps a traceback and tail for check logs, not review text.
- **Cost read $0.0000** in the one surviving raw turn (`.logs/m2turn.log` at `9399c40`): "Cost still reads $0.00 because the router prices these models at null" (`c1e79c2`). This is New 4, seen in practice.

**For this repo.** Add New 3 to the pre-run list, the only change the data forces. It also qualifies New 6: a stub walk exercises the routes, and it wouldn't have found these. `ghola`'s first real job landed the day the repo was created, on a stock harness. Here, in `PLAN.md`, a jig can't run until P2-13. That difference
is partly the substrate, so it doesn't justify reordering the plan. It does argue for a real job of this size, on a real repo, as soon as a jig exists, and before any experiment.

## Later positions

Where the later work moves from the book. Each row is the author's text. None comes with enough data to settle it.

| Topic | Book | Later | For this repo |
|---|---|---|---|
| Promotion | "Every technique in this book is one move… push it down a ladder toward determinism" (p.715) | "Most rules should stay prose forever… A rule earns the next rung only by failing at the one it is on, in a way you can point at" (`policy/README.md:5-7`) | **Cuts against ADR-0010 item 6, "A check comes first".** Keep it for decidable, consequential checks. Ask for a RED case for anything else, as skills already must. One sentence |
| What separates rungs | Decreasing inference (pp.715-716) | "differ in **what they can see**, not in how hard they push" (`ladder/src/gate.py:8`) | Use as values for "enforced by". Also "who can switch it off" |
| Instruction and imitation | "Why instruction loses to imitation" (p.59) | "prose loses to the imitation surface only when it is *redundant*" (`docs/RESULTS.md:147-148`), against "imitation beats instruction every time the two disagree" (`workshop/narrative.md:80-84`, later) | **Unsettled.** The author's own texts disagree. Keep the note's "tag RED failures first", and drop any implication that imitation wins |
| Scope test | Three questions, "Two or more" (p.442) | Six properties, "fewer than three yes, stop here and write it as one agent" (`hands-on-iii/docs/worksheet.md:9`) | **Doesn't settle it.** This design passes: runtime graph, nondeterminism, state outlives compute, a person inside. Same caveat as the note's scope section: the answers describe the design, not the need |
| Hook failure | "killed and treated as a non-zero exit", failing closed (pp.243-244) | "Any other exit is a non-blocking error" (`charter.ts:422`) | Keep the book's, because this design has no host contract |
| Modes | "belongs on the contract" (p.415) | "Paired is the default… nothing enforces it" (`pi-config/README.md:47-48`) | Item 6 can't cite the author's practice |
| Orchestration | "a queue, not an agent" (p.673) | "It starts turns and never runs one" (`hands-on-iii`, *(unchecked)*) | Sharpened, and consistent with this repo |
| Runtime control | Not stated | Blackboard "genuinely fits agents better than a pipeline" (`iii-blackboard/README.md:120-125`), and six weeks later a drawn stage graph, with no blackboard mentioned | No reason given. See below |
| Enforcement claims | Various | "Never claim a rung you do not carry" (`agent/AGENTS.md:58`) | Sharper than anything in the book. A good one-line test for this repo's rule 44 and R56 |

**On the blackboard.** It neither supports nor undercuts this repo's board, because the repo offers no evidence. The iii half has no agents: every knowledge source binds to `publish`
(`bb/knowledge-sources.yaml:29`). The scratch half's preconditions are mutually exclusive (`scratch/blackboard.py:185-216` *(unchecked)*), so it is a pipeline written as predicates. A conflict
pays for the model call and then drops the result (`:165-171`). There is no fence, and in-process state dies with the worker. Keep ADR-0005:118 as a resemblance only: this board adds the exclusive claim
a blackboard lacks.

## Against the earlier notes

**The note's items:**

- **Item 1 gains its first observed case and a settled shape.** See New 9. For rule 31 against rule 137, `ladder` gives the form: a derived default, a declared departure that is flagged
  (`declared_rungs`, `src/parse.py:103-115`), and a floor that a specialisation "may go higher, never lower" (`src/load.py:274,287`). Here, rule 31 and item 1's lock are the floor, and rule 137 selects above it.
  `rungs_for` already has `r.always or r.rung in chosen` (`jig-sketch.py:671`). Record a narrowing as a departure. One sentence in rule 137.
- **Item 2.** Copy `on_refusal: {goto, max, stop_when_identical}` (`hands-on-iii`, `pipeline.yaml:37`) as the row shape for policy §9's table. `hands-on-iii` also fixed open-refinery's `waiting` dead end
  by polling through the queue, but `failed` stays terminal *(unchecked)*.
- **Item 3.** Add `rung_results` to what `task_attempts` lacks. `hands-on-iii` is not a model: sections are replaced, and graph, prompts and rules are re-read live *(unchecked)*.
- **Item 5.** Copy the key split: `env_file` only on `llm-router` and `github` (`worker-compose.yaml:33,71`), so the process that runs the model holds the key, and the shell does not (inferred). That matches the worker
  making model calls here. Also ask the worksheet's question: "Name the one mechanism that stops the worst outcome if every rule has a bug" (`docs/worksheet.md`). Item 5 exists because this design can't yet answer it.
  **Add a Gate A case:** a card cannot write what judges it. In `hands-on-iii`, a turn can write a rule file that the ladder then executes (`workers/ladder/src/rules.py:119-121`, `ladder.py:133-139`). `pi-config` fixes no sigma hole, because
  it has no confinement to fix (`agent/extensions/bash-spawn-hook.ts:17-26` *(unchecked)*).
- **Item 8.** No later shape to copy, and sigma's decorator stands. `hands-on-iii` still checks before each stage, though it now charges errors (`test_budget.py:155-170` *(unchecked)*).
- **Item 9.** Stands, and now with support. `hands-on-iii`'s `FakeWorker` sits at the engine seam with real git, so tests drive the runner, which fixes open-refinery's dead routes *(unchecked)*. But the loop is stock, so tool use is never scripted. That leaves
  `ScriptedModel` as this repo's own job. Copy one habit: each test's docstring names the failure it guards against.
- **Item 10.** `ladder`'s `Plan(was, now, steps, notes)` (`src/lifecycle.py:52-62` *(unchecked)*) is close, but it is returned and discarded, and a move changes no hash. Here a rung change moves `kind_hash`, which is ahead. Add `rule_id` to the note's row. From `pi-config`'s `/learn`, take
  "No lesson, nothing recurred" as a correct result (`agent/prompts/learn.md:21` *(unchecked)*), which matches `no_patch`.
- **"Enforced by" column (Smaller).** Derive it and don't write it. Hand prose rotted within hours in the author's repo (`RUNGS.md:100-113` *(unchecked)*). Add `rule:` to `Rung`, and have the repos note's New 4 test generate the column. `hands-on-iii` is a working example: `CARRIED` and `ELSEWHERE`
  (`workers/ladder/src/rules.py:22-26`), which refuse a rule claiming a rung nothing carries (`:85-97` *(unchecked)*). `ladder`'s `measured_share` is the warning: "a script exists" is not "it ran".
- **ADR-0005.** It stands on its own arguments and needs them, now that the ceiling argument is gone.
  - **For:** the wire bytes. `ModelRequest` holds messages, not wire bytes, so the cache key would need a chat-model wrapper *(unchecked)*. And deepagents always adds summarization and tool-call patching (`graph.py:805-806` at 0.7.19, *(unchecked)*), which bears on R60.
  - **For:** even on a substrate, the author keeps the record out of it: "Plain files, not the state worker: a record must survive the thing it records" (`workers/audit/src/index.ts:11`). One Postgres statement also avoids `hands-on-iii`'s file-then-message dual write.
  - **Against:** a full factory in about 3.6k lines on iii, a substrate the ADR's survey omits (`:8`). Only replay still justifies hand-writing, which is the note's existing verdict.
- **Policy §10 and replay.** Upstream LangGraph docs say "Replay re-executes nodes… LLM calls… fire again" (`use-time-travel.mdx:14,22` *(unchecked)*), so checkpoint replay is not this design's cache replay. That supports the differentiator. `learn-harness`'s own summary says the opposite.
- **ADR-0004.** Its CLI rejection gains a reason: "pi-claude-bridge starts Claude Code with project settings and no trust check", so a cloned repo's hooks run (`8ca4dc8`). `dd3834e` adds that a charter "mostly never reached the model" under the bridge.

**Corrections to the earlier notes, applied 2026-11-06:**

1. **Repos note, Rule table columns:** "No working example in any repo" is now wrong. See above.
2. **Repos note, New 9:** add the shadow caveat. "a rung whose idleness is caused by a removable rung above it has not demonstrated anything" (`RUNGS.md:62-63`). Ablate the earlier rung in replay, not the idle one.
3. **Repos note, New 10:** "Unparseable is never a pass" is only a label in the later code: "a contract never fails a job" (`tests/test_rework.py:167`). Copy the downgrade only together with a route.
4. **Repos note, New 11:** `check_ref` equality cannot name the rung. It needs New 1 here.
5. **Repos note, correction 2:** "fenced is the difference" holds against open-refinery. `hands-on-iii` has no claim or lease at all, by word search of `workers/`, `config/` and `scripts/`, so p.675 fits it again.
6. **Repos note, "Why they stopped":** "followed by a new one rather than by use" is too strong, because `charter-workshop` had an audience. The sequence also omits the August iii series, `ghola`, `audit-log`, `workers` and `anchor`.
7. **Repos note, trailers:** a Claude trailer is still evidence of model assistance, but its absence isn't evidence of hand-writing from here on. `pi-config`'s `agent/AGENTS.md:101-103` bans it.
8. **Note, exemplar module (Smaller):** see "Instruction and imitation" above.
9. **Note, p.386 quote:** it stops short. The next lines say "I am building it now". `charter-workshop` is the nearest thing read so far, and it lacks the repeats that chapter requires.
10. **Note, "numbers… labelled illustrative":** `71de64d` says the workshop's reference numbers are real ones. They may be literally produced by `bin/capture`, but the records don't show independent arms.
11. **Open-refinery's `max_turns`:** it is passed as `recursion_limit`, which counts super-steps, so it isn't a turn cap (`pipeline/agent.py:197`).

Also applied: `rung_results` in the note's item 3, and p.244 no longer marked *(unchecked)*.

**One proposed correction rejected.** A subagent reported that `hands-on-iii` does the opposite of "an unknown level falls to the safer one". `scripts/turn.py:60-66` sends an unknown level to `supervised`, the same as open-refinery, and `tests/test_oversight.py:26-29` asserts it. The repos note stands.

## Field evidence

- **A charter can silently fail to reach the model.** "a repo's `.claude/` charter mostly never reached the model", because bridged tool names never match `Edit|Write` matchers (`pi-config` `dd3834e`). A brief never reached the model either (`preset.ts:456-458` *(unchecked)*). This is what `render()` and the pin exist to prevent, so it supports them.
- **Silent mis-wiring is the substrate's price.** `pre_trigger` "registers without error and never fires" (`hands-on-iii`, `test_hooks.py:2` *(unchecked)*), and `ladder/src/main.py:39-41` calls that "the exact failure this worker exists to prevent". Yet `ladder` itself has it: the hook calls rung 3 only (`main.py:295-296`), so a rule that defaults to rung 2 is skipped, and `generate-hook` returns a "TODO" string
  (`:439-444`). "Dropping the `.py`… moves the rule from prose to hook" (`README.md:40-42`) therefore changes a number (traced).
- **The author measures their own instrument too generously, then says so.** `docs/RESULTS.md:380-382`: "These are mechanism demonstrations, not rates." `:392`: "I designed the rules to produce the effect." This self-criticism is real and worth copying, and it is stronger than anything in the book. It does not reach the README, or `policy/README.md:7`, "This one clears all three tests", when recurrence is "not established for anything here".
- **A gate's limit, observed.** "A gate enforces only the decidable shadow of a rule" (`docs/RESULTS.md:213`). The agent hardcoded `"USD"` past a gate *(unchecked)*.
- **Tests that pass over the thing they name.** `loadHooks`'s test is named "instead of dropping its guards", while its caller drops them (New 7). `ladder`'s "asserted by a live test" (`src/main.py:41`) has no such test (`README.md:287-288`). This repeats the repos note's pattern.

## Here is ahead

On paper, since none of it has run.

- **Claim and fence.** `iii-blackboard` uses content-hash CAS on a slot's value, optionally: 3 of 4 writes are blind *(unchecked)*. `hands-on-iii` has an epoch check. Neither guards who owns the work.
- **The record.** `iii-harness-layers-and-promotion` omits model and commit from each run, so denominators are lost *(unchecked)*. `config_hash` is ahead. It stops short on rungs (New 1).
- **Grants.** Fixed on the jig here. There, a planner model's `writes_code` decides, and an empty grant falls back to all four tools (`planner_worker.py:117-118`, `coder_worker.py:244`, *(unchecked)*).
- **Hidden checks.** Principle 5 has no counterpart in any of the seven. The workshop's scorer is in the agent's tree.
- **Escape markers.** Model-writable in `ladder` (`gate.py:84-86`, *(unchecked)*), `hands-on-iii` and the workshop. None found here, and that should stay true.

## Not borrowing

| The repos have | Why not |
|---|---|
| iii as a substrate | No borrow needs it, and `check()` and `gate.decide` are plain code. Postgres avoids the dual write. See ADR-0005 above |
| Capabilities on one ladder | Two tables, one verb and an early branch (`src/lifecycle.py:140` *(unchecked)*). The rungs are ownership layers, which one project lacks. The jig's tool list already is the grant |
| Promotion thresholds and the verdict printer | Pooled, underived. See New 1 |
| Layers, locking, specialisation | One project |
| Agent-writable escape markers | They would defeat hidden rungs |
| "A check that raises is a finding" | It collapses what `CHECK_UNAVAILABLE` separates |
| Hot-reloaded graph, prompts and rules | Directly against the pin |
| Worktree snapshot and restore | Cards have per-attempt workspaces |
| The blackboard vocabulary | No evidence behind it, and this repo's words are settled |
| Tarrasque, the nine checks, AST rules keyed on variable names | Specific to the workshop. Take the shape of the scorecard |
| `bin/promote` | Pools reference and own runs, so one bare failure reads as earned *(unchecked)* |
| `hands-on-iii`'s chapter order as a build plan | A teaching order from a recut tree. `ch11` adds the record, and here rows never written can't be recovered. Take the stub walk only (New 6) |
| `learn-harness`'s curriculum | Vendor docs, one commit, and no result beyond three inline examples |
| Presets, trust files, collision renaming | Stock-agent concerns. No repo charters load here |

## Where to look first

| For | Read |
|---|---|
| What the author runs themself | `pi-config/agent/AGENTS.md`, `agent/APPEND_SYSTEM.md`, `README.md` Known limits |
| Honest self-assessment of an experiment | `iii-harness-layers-and-promotion/docs/RESULTS.md`, §5.6 and §7 |
| Mistakes to avoid in measuring | `charter-workshop/tools/scorecard.py`, `bin/capture`, `runs/reference/`, and the fork's `RESULTS.md` |
| Positive controls | `pi-config/verify.ts:60-75` |
| Hook runner shape | `pi-config/agent/extensions/claude-charter/charter.ts:385-424` |
| A floor plus declared departures | `ladder/src/parse.py:103-115`, `src/load.py:274-287` |
| Stub walk | `hands-on-iii/tests/test_factory.py:176-215` |
| The only real runs | `tacoda/fawlty` PRs #1 and #2, and `ghola`'s `2866476` and `dfa099a` |

## Verdict

The author's own practice is the strongest thing in this batch. Three months after the book, their own config is a thin layer on a stock agent, and their sharpest later sentence on rules is "Most rules should stay prose forever". That supports the note's caution on scope, and argues for a narrower reading of ADR-0010. It doesn't settle whether this design should be built, because a helper running unattended is not one person at a keyboard, and this design's reason to exist, the replayable record, is one no repo here attempts.

The measurement work shows how hard this is. The only committed numbers contain an arm that duplicates another, a null independent variable, a contaminated control and a metric that moved because of the instrument. Each is a mistake this repo could make at step 7, so take them as a checklist.

**Before the first run,** combining all three notes, in this order: `rung_results` (New 1 here), `expect: FAIL`'s right-reason check, config that can't reach `done` unchecked, stored wire requests, the declared-things test, the base-tree check (New 2 here), the empty-diff check (New 3 here), depth, and unknown cost (New 4 here). All are small. The first and fourth can't be recovered afterwards.

**The next step probably isn't another repo.** These three notes now total over 1,100 lines, outside rule 133, about a system that has not run. That is R56 in this repo's own words, and it's what the author's history warns about. `ghola` was the one remaining lead that could change a conclusion, and it changed one by a small amount. The useful move now is to turn this list into ADR amendments and tests.
