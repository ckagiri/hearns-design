# Harness Engineering (Ian Johnson) — ideas worth borrowing

**Subject:** *Harness Engineering: Building Reliable Workflows Around Non-Deterministic Agents*, Ian Johnson, Leanpub,
the version published 2026-07-22. It has 844 numbered pages. Page numbers here are the book's own: in the PDF, a book
page is 22 pages later. Read against commit `1e293f2`. Written 2026-11-06, and corrected the same day after reading the
author's repos: see `johnson-repos-borrow-notes.md` and `johnson-later-repos-borrow-notes.md`.

**Basis.** Six subagents read about 680 pages closely, in two passes:
- **Read closely:** Ch 3–9, 12–16, 19–24, 27–41, 44–50, 53–62, and Appendices A and D.
- **Skimmed:** the Preface and Introduction, Ch 1–2, 10–11, 17–18, 25–26, 42–43, 51–52, and Appendices B, C and E.

Each idea was checked against this repo. The main thread then rechecked the decisive claims against the sketch, the SQL,
the tests and a sample of the book's quotes. Items marked *(unchecked)* rest on one subagent's reading. Nothing was run,
and every trace through `jig-sketch.py` or the SQL comes from reading it. "Not found" means by keyword search, which is
not proof of absence.

**The book's evidence is thin, and it says so.** The author calls their own tools "watched evidence, before-and-after
observation with no control arm" (p.386), and goes on: "The suite in this chapter is the instrument that upgrades them. I am
building it now". `charter-workshop` is the nearest thing to it read so far, and it lacks the repeats that chapter requires. Its stories are anecdotes, and one is admitted to be a composite (Ch 15). Its
numbers come from other people or are labelled illustrative. The workshop later calls its numbers real, "produced by
bin/capture rather than typed" (`71de64d`), but those records don't show independent arms. Some of its sample terminal output matches no code: the
`charter show --path/--topic` output on pp.140-143 is one case (`cmd/keystone/charter.go:124-143` parses neither flag). It
is most useful as a source of questions to put to this design. Most of its own mechanisms confirm what this repo already
has.

**Rule 133.** That rule allows three places for findings, and this is the sixth borrow note outside them. It follows the
precedent of the other five: it records what was read, and nothing here is adopted until it moves into a document, an ADR,
`rules-and-risks.md` or code. Whether borrow notes get a carve-out in rule 133 or move into ADRs is still open.

---

## Words

The book's vocabulary does not match this repo's. Keep this repo's words.

- **Charter** is wider than jigs and skills. It includes the checks, hidden rungs, host hooks, layer 1, the root intent and
  its CONSTRAINTS, the anchor, role config and the failure-class policy (pp.39, 52: "the retry policy is charter").
  `rules-and-risks.md` is not charter. No card reads it: it is a register for the people building the system.
- **Skill** in the book is a multi-phase workflow the agent picks for itself (p.745). Rules 113–115 forbid that inside a
  card. This repo's skill is closer to the book's rule or idiom. The author's published skills are reference bundles with
  routing, which are closer to this repo's layer 2 than the book's definition is.
- **Harness** comes at two levels (p.742). The single-agent harness is the card runtime plus `render()`, `dispatch_tool`,
  `run_oracle` and the container. The fleet harness is the board and the workers.
- **Orchestrator** is inconsistent in the book. It calls one queue with one source of truth "orchestration" (p.669), and
  workers pulling from a shared queue "choreography… Not: orchestration" (p.470, p.759). Here the board is the state, the
  readiness predicate is the book's "derivation function" (p.752), and nothing decides.
- **Also collide:** layer, gate, contract, policy, and the book's Verifier (which refutes a reviewer's finding).

## Worth borrowing

Ranked. The first two are defects in what is already drafted.

**1. Test-first pairing has no gate.**
- **Book:** Ch 14, pp.138–143, on locks and required declarations: "If a project rule contradicts it, the engine picks
  the locked rule, logs the conflict, and surfaces it" (p.139). An iron law is "enforced by a gate, not by goodwill"
  (p.746). Keystone does not implement that lock, so this item rests on R35 and policy §3.8, not on the book's mechanism.
- **Here:**
  - Policy §3.8 marks pairing "✓ — load-bearing" and says a split that breaks it "is a hard rejection, not a warning"
    (`harness-policy-v3.md:476-491`).
  - The emit gates check fan-out, `check_spec`, empty rung selection, touch sets and edges, but nothing pairs a test card
    with its implementation card (`jig-sketch.py:750-757`).
  - `odoo-adaptation.md:285-286` says the splitter "must justify omitting rung 2", and no field carries that.
- **Why it matters:** R35 says this pairing was the only mechanism of five that caught the inverted security rule. The
  `split` model writes `check_spec`, so the policy is enforced only if the model cooperates.
- **The gate:** lock a rung in `checks.yaml` when the card cites an anchor key carrying `semantic:` or `test:`
  (`odoo-adaptation.md:343-344,404`; rule 89 covers citing the key, and rule 101 names `semantic:`). Then reject a split
  unless each implementation card citing such a key depends on an `expect: FAIL` test card for the same key. Keying on paths
  would wrongly reject structural cards.
- **Open hole:** `expect: FAIL` cannot yet tell the right failure from a broken import, so this gate could pass vacuously.
  See New 1 in the follow-up.
- **Fits:** ADR-0010, because the trigger is a declared field. Rule 31 ("never opt-in") and rule 137 (`check_spec` picks
  the rungs) read against each other here, and this settles which one wins.

**2. Failure routes end in dead ends.**
- **Book:**
  - Ch 34, p.449: "decide, per stage, what a failure routes to rather than what it raises."
  - Ch 54, pp.659–665, has the checklist on p.665: "every loop has a BOUND checked at its header", "every loop has an EXIT
    HATCH when the bound is hit".
  - Ch 55, pp.666–671: "abort has a defined meaning".
  - Ch 57, p.688: "build it first, and pull it on purpose".
- **Here:**
  - **A quarantined sibling holds its gates forever.** Gates depend directly on all siblings (rule 22). Clause (a) of
    the claim requires every direct dependency to be `done` (`harness/ledger/sql/claim.sql:8-9`). Core's "a quarantined
    descendant is acceptable" (`harness-core-v3.md:396-400`) covers grandchildren only. In the flat shape that ships,
    rule 132's "degrade, never hang" fails.
  - **Clause (b) does the opposite one level down.** A quarantined grandchild releases every card that depends on its
    split, gate or not (`harness/ledger/sql/claim.sql:10-12`). `tests/ledger/verify_schema.py:168` tests for this as intended. ADR-0013:23
    named the hole. A misclassified `execute` card becomes a `split` on its own row, so the hole reopens once that split
    commits: a sibling that `consumes` its interface is released against one that does not exist *(unchecked)*.
  - **Nothing leads out of `quarantined`.** `requeue` runs through `review_return.sql`, which matches only
    `state='awaiting_review'`. ADR-0011 wrote `requeue` for a card out of free retries, and `release.sql` sends that card
    to `quarantined`. So `requeue` matches nothing in the case it was written for, and no statement moves a card out of
    `quarantined`.
  - **A failing `integrate` cannot emit a gap card.** New cards are inserted only inside `commit()`, which only reaches
    `done` (`jig-sketch.py:817-851`). A retry re-merges the same branches, fails the same way, and quarantines.
  - **Gap fixes are never re-integrated.** `verify` emits gap cards as siblings, and the one `integrate` was pinned at split
    time *(unchecked)*.
  - **Unfinished verbs:** six of the ten allowed verbs have no statement under `harness/ledger/sql/`: `kill`, `promote`,
    `reset`, `clear_halt`, `raise_budget` and `abandon` (`001_initial.sql:224-225`). No file there inserts into `reviews`,
    though core requires the record (`harness-core-v3.md:750-752`). Nothing writes `runs.outcome`. The claim never reads
    it, so an abandoned run stays claimable.
- **Change:**
  - A gate kind whose check fails parks instead of retrying.
  - Make the bar follow the dependent's kind: gate kinds accept `quarantined` on both clauses, everything else requires
    `done` on both. The predicate amends core, so this needs an ADR under core §13.
  - Add one fenced statement out of `quarantined`.
  - Add statements for the six unfinished verbs, and an operator halt. The halt is cheap: `halt_run.sql` exists, and
    `claim.sql:19-20` already refuses a halted run.
  - Add a table in policy §9 listing every loop with its bound and exit, including a column for R31's round cap.

**3. Freeze what each attempt saw and returned.**
- **Book:** Ch 58, pp.699–702: "frozen — immutable the moment it is created, in code and in intent." Ch 54, p.664: "every
  re-entry is a recorded transition."
- **Here:**
  - `task_attempts` stores no contract, prompt or result (`001_initial.sql:106-121`).
  - `review_return.sql` overwrites `contract` and `check_spec`, and `commit.sql` overwrites `result_summary` and
    `prompt_ref`.
  - So "did a person loosen the check before this went green?" cannot be answered.
  - ADR-0014 rejected whole-task revisions because "the statements read overwrite few fields that any query needs." This
    is narrower, and that query needs them.
- **Change:**
  - Add `input_digest`, `prompt_ref`, `result_ref`, `result_summary` and `rung_results` to `task_attempts`. The last was in
    `initial_plan.md:279` and was lost on the way to the schema. See New 1 in `johnson-later-repos-borrow-notes.md`.
  - Have `edit` keep the old `check_spec` in `reviews.detail`.
  - Store one ref per prompt block. `join_for_audit(blocks)` (`jig-sketch.py:560`) loses the layer boundaries.
- **Why now:** rows never written cannot be recovered, and the record is the one differentiator left (policy §10).

**4. Repeat samples collapse in the cache.**
- **Book:** Ch 30, pp.380–384. "Three runs tell you about luck. Thirty begin to tell you about spread." "Measure the band,
  not the best run."
- **Here:**
  - The cache is read before the mode check, so live runs hit too (`jig-sketch.py:476-482`).
  - The key is the wire bytes plus the adapter identity, and `model_cache.key` is global (`001_initial.sql:166-171`).
  - Policy asks for "three samples at one config" and "the seed-varied set" (`harness-policy-v3.md:726-733`), which
    nothing implements.
  - Repeats at one config return the same cached bytes at $0 and read as perfect stability. Rule 121 could then delete a
    skill on what is really one sample.
  - Rendered card ids may make some cards miss by accident, so the collapse may be partial. It is decided by accident
    either way.
- **Change:** add a sample value to the key that is never sent on the wire. Withhold an arm if any call it scored was
  `served_from_cache`. Core §8 is settled, so this needs an ADR.

**5. Say where tool calls execute.**
- **Book:** Ch 37, pp.494–496: "Resolving first defeats ../ escapes and symlink tricks"; the path "escapes workspace
  root" check. Ch 21, p.271 *(unchecked)*. That quote is the book's Python: the author's Go `rooted()` is lexical
  (`internal/tools/paths.go:12-23`), so it is not tested practice.
- **Here:**
  - `dispatch_tool` runs `t.fn(**call.args)` with no container handle (`jig-sketch.py:504,528`).
  - Core says the card edits and runs checks inside the container (`harness-core-v3.md:669-673`). ADR-0004:16 puts the
    thing that executes a jig inside the container. The container denies network (`harness-core-v3.md:666`). The worker
    makes the model calls.
  - **If file tools run on the host:** a symlink planted by `bash` lets `read` reach host files.
  - **If the runtime runs in the container:** `bash` can read the provider key, and network deny cannot hold.
  - ADR-0003's enforcement depends on this answer, and no document gives it.
- **Change:** a paragraph in core §6, a `fn(args, ctx)` signature, and a Gate A case that plants a symlink and an absolute
  path.

**6. Define `gated()`.**
- **Book:** Ch 32, pp.409–418. The mode is "a field on the contract… set during Intake, signed", and "step back hard,
  step forward slow". Ch 62, p.735 warns of the approval slot that exists so someone can say it exists.
- **Here:**
  - `gated(role, parent)` is called (`jig-sketch.py:741`) and defined nowhere.
  - `gate` sits on `Role` as `'depth <= 1'` (`jig-sketch.py:226`). ADR-0008 gives a role "model, effort, lease,
    parallelism", and not review.
  - R1's "human gate at depth ≤1" (`rules-and-risks.md:305`) gates every card under ship-flat, yet the worked run shows
    three gates.
  - The closest design is `review_policy` in `files/intake-and-review.md:327-337`, which README does not index.
- **Change:**
  - A review level on the run, set by a person, with values along the lines of `every_card`, `plan_and_root` and
    `root_only`.
  - Raises only, decided at emit from card facts: the touch set against `always_gate`, `retry_safe: false`, and incomplete
    contracts.
  - Take `gate` off `Role`.
  - A query that counts verbs per gate position, to say when a level can drop. The person changes the level by hand;
    reading history automatically would break replay.

**7. Hooks decide outcomes, so they belong in the pin.**
- **Book:** Ch 20, p.226: "A new tool is a behavior change." A hook's declaration is charter material, "versioned and
  reviewed like a rule file" (p.240).
- **Here:**
  - Hooks are "Outside the pin, because hooks do not render into prompts" (`jig-sketch.py:134-135`).
  - Core hashes hidden rungs for the opposite reason: "they decide outcomes, so their definitions are hashed anyway"
    (`harness-core-v3.md:864-865`).
  - The `pre_commit` hooks decide outcomes too, so a change to one moves no hash.
- **Change:** put the role's hook list and versions into `kind_hash` and the pin. Add a hash-stability test.

**8. A token ceiling inside the card.**
- **Book:** Ch 40, p.520: "A limit that logs 'budget exceeded' and keeps going is not a budget. It is a bill with
  commentary." Ch 41, p.529: "the ceiling has to be checked before the call that would cross it."
- **Here:**
  - Budget only refuses new claims, and "cards already claimed keep spending" (`harness-core-v3.md:450-452`)
    *(unchecked)*.
  - `max_cost_usd` may be NULL, which means no limit (`001_initial.sql:133`), though `max_free_retries` beside it has no
    default.
  - `max_turns` is marked contested (`jig-sketch.py:208`).
  - R61's mitigation is "None" (`rules-and-risks.md:380`).
- **Change:**
  - Count tokens from the served response, not dollars. A cache hit costs $0, so a dollar limit would trip live and not in
    replay.
  - Put the ceiling in `kind_hash`, because it decides outcomes.
  - Keep it out of the classes that count as evidence.
  - Make `max_cost_usd` NOT NULL.
  - Measuring the stable prompt prefix at pin time can come first, because it needs no model.

**9. A `ScriptedModel` and a runtime test file.**
- **Book:** Ch 41, pp.526–534, which covers routing, bounds, structured-output giving up, and resume not repeating work.
  Ch 19, pp.212–213: "Mock the unmanaged, run the managed."
- **Here:**
  - `tests/` holds only `tests/ledger/`.
  - The 0005 ADR admits these tests are now the repo's job.
  - P2-13 is sized as if it were delegated (`PLAN.md:192`) *(unchecked)*.
- **First cases:** the defects below.

**10. An amendments ledger.**
- **Book:** Ch 28, pp.355–367: the flywheel ledger; "the sensor needs to live in code, not in goodwill" (p.359); "No
  patch" as a signed-off result (p.365). Ch 29, p.375: the repeat-failure rate *(unchecked)*.
- **Here:**
  - No row links a failed card to the change that answered it, or says whether that change worked.
  - `notes` is the only learning table, and "nothing writes here yet" (`001_initial.sql:232-243`).
  - `queries/lessons.sql:95-97` counts review verbs and nothing else.
- **Change:** an append-only, human-written row with these fields:
  - direction
  - the charter artifact changed: rung, hook, layer 1, skill, ADR-0010 row or anchor
  - the source cards
  - the missing guard
  - a decision: `patched`, `no_patch`, `deferred` or `retired`
  - the hash before and after
  - `landed_in`: charter, harness, anchor or contract

  A query then compares the repeat-failure rate across the hash move. Flag a hash move with other than one row, because a
  bundled change cannot be attributed.

## Smaller

- **Enforce immutability in the database** (p.699). Rules 94, 96 and 151 are prose only. No `CREATE TRIGGER` or `REVOKE`
  exists.
- **Restart Postgres in Gate A** (Ch 50, p.643, item 4) *(unchecked)*. Past one lease TTL, every lease expires and the
  reaper charges `lease_expired`, which is not free.
- **Time out host hooks, and fail them closed** (Ch 20, pp.243–244). A hook that hangs while parsing a file a card wrote
  strands a worker, which is part of R64. The author's newest code does the reverse (`pi-config`, `charter.ts:422`), because
  that adapter keeps a host's contract. This design has no host to match.
- **Record the served model** (Ch 39, p.514: "A model version is a dependency — pin it"). `validate_roles` never looks at
  the model (`jig-sketch.py:245-255`), and the role table uses aliases. When an alias moves, hits and misses within one run
  get different models under one string.
- **Add three columns to the rule table** (Ch 12, pp.110–116) *(unchecked)*: audience, enforced by, and evidence (paper,
  test or run id). Add a precedence order. The conflicts it would settle:
  - rule 147's "byte-identical" against rule 68's escalation on the last delivery
  - rule 65 against `re_verify` being emitted by `verify`
  - rule 31 against rule 137

  R35's "**Confirmed**" rests on a walkthrough.
- **Add a one-window arm to E3** (Ch 9, p.79, where the bitter-lesson objection is "mostly right" for harnesses)
  *(unchecked)*. Core says "Anything that fits in one context window. Use one window." (`harness-core-v3.md:53`), and
  nothing measures it. Rerun it on each major model release.
- **Keep an exemplar module** (Ch 7, pp.57–63: "instruction loses to imitation") *(unchecked)*. The author's later texts
  disagree on whether imitation wins (`docs/RESULTS.md:147-148` in `iii-harness-layers-and-promotion`, against
  `workshop/narrative.md:80-84` in `charter-workshop`), on thin data, so assume neither. Every layer is instruction
  or feedback. Across runs of one project, run N's code becomes what run N+1 copies. Tag RED failures as "copied from"
  versus "model prior" first.
- **Odoo in an existing codebase** (Ch 23, pp.286–292) *(unchecked)*. `odoo-adaptation.md` targets a new module only.
  Characterization tests must pass on arrival, which clashes with `expect: FAIL`, and the introspection "extra" list would
  flag every existing model.
- **Refusal shape** (Ch 48, pp.599–612: the skill "refuses to file if a field is empty, if more than one question sits in
  the…"; the Appendix B interrupt template, p.776). Use one question per refusal and options with costs.
  `worked-run-odoo.md:531` bundles two. Test it in E2 arm C before adopting, because a costlier refusal may suppress
  refusal (R47).
- **Queries over human attention** (Ch 57, p.685: "If you cannot enumerate the places your system stops for a human…").
  The worked run spent 49 of its 94 minutes waiting on gates (`worked-run-odoo.md:817`), which is an imagined run.
- **Write step 7's scorecard first** (Ch 59, p.712: "a metric you defined after the change is a metric you chose to make
  the change look good").
- **Add a `Card:` commit trailer** for human edits outside the board (Ch 32, pp.422–423) *(unchecked)*. The worked run has
  the human update the schema directly (`worked-run-odoo.md:284`). The trailer is already drafted in
  `files/intake-and-review.md`.
- **Run `lessons.sql` at the final gate and at each config bump,** not on a calendar (Ch 62, p.732) *(unchecked)*.
- **Find tools each kind never calls** (Ch 20, p.232) *(unchecked)*. `lessons.sql` groups `tool_audit` by tool only.
- **Name in-scope injection as a risk** (Ch 38, pp.501–508; spotlighting "lowers the hit rate; it is not a wall", p.506).
  Layers 5–7 interpolate model-authored text unmarked. Seed a labelled trap before keeping any prompt line.

## Defects found while checking

Each was traced, not run.

- **A split's refusal lands on `HARNESS_BUG`.**
  1. A refusal returns its payload (`jig-sketch.py:624`).
  2. `plan_emissions` runs on any truthy payload (`:871`).
  3. `payload["children"]` raises KeyError (`:745`), which the generic handler catches (`:888-889`).
  4. So a split never reaches `awaiting_review`.
- **`HARNESS_BUG` says "quarantine, do not retry"** (`jig-sketch.py:77`). `reaper_flip.sql` has no branch for it, and
  retries until `max_attempts`.
- **An unknown refusal reason carries no `failure_class`** (`jig-sketch.py:619-623`). `reaper_flip.sql` then relabels it
  `stalled` or `lease_expired`. This is inferred: `JigResult` has no definition.
- **`detail=` has no column** (`jig-sketch.py:620`, `:878`, `:889`). `fail.sql` cannot store it, so a `SplitRejected`
  reason never reaches layer 7.
- **`tree.sql` undercounts subtree cost.** It sums `tasks.cost_usd`, which only `commit.sql` writes, and in the sketch
  that is the last response's cost (`jig-sketch.py:631`). A quarantined card shows $0. Read `model_calls` instead.
- **The `Model` protocol declares only `complete`** (`jig-sketch.py:432-433`). `CachedModel` also calls `build` and
  `identity` (`:477-478`).
- **`dispatch_tool` still runs the quota, side-effect and approval checks** (`jig-sketch.py:515-526`) that ADR-0003
  voided. `NeedsApproval` has no handler.

## Against the positioning

- **"There is no controller"** (`harness-policy-v3.md:812`) reads more strongly than it should. The book's daemon is a
  function of stored state, so it "can crash, be restarted, be redeployed, or skip a tick, and on its next tick it derives
  exactly the action the previous instance" would have (p.624; also pp.638–641). A controller can exist and hold no
  state. That holds for deciding, not doing: in open-refinery the worktree is state outside the row, so a retry after a
  crash can behave differently *(unchecked)*. This repo provisions a workspace per attempt and should not inherit that, but
  it should test it.
  - Say "no controller process".
  - The narrower claim is the fenced worker pool plus the typed comparison keys. Open-refinery no longer contrasts on
    leases: p.675 says it "does not run a lease-based retry queue", but `bbdc9af` added claiming workers with a stale
    takeover and no fence (`pipeline/workers.py:40,69-86`). Against open-refinery, the fence is the difference. The author's
    later `hands-on-iii` has no claim or lease at all, by word search, so p.675 fits that one again.
  - The single point of failure moved to Postgres, and nothing tests it.
- **Should this be built at all?** Ch 33's checklist (p.442) does not settle it. It asks about background execution,
  multi-model routing, and determinism or durability, and "Two or more" means "you are building an agent system". This
  design answers yes to all three as drawn. The caution comes from elsewhere:
  - p.442 closes on building "only when the stock one runs out of road". Policy §10 concedes the comparables have queues,
    tiering and worktrees, which leaves replay plus the typed record as what a stock engine lacks. That count is this
    note's judgement, not the checklist's.
  - Part VI's intro (p.570) and Appendix D (p.819): "A two-person team on a small repo with one item in flight does not need
    a daemon, contracts, or touchpoints; it needs a charter."
  - The author's distilled form: "Build one when the workflow you need is one no stock harness can express — not because
    building one sounds interesting" (`skills/agent-harness-building/SKILL.md:25-27` in `constraint-engineering`).
  - That supports core §12's substrate and replay. It warns against the policy above them: preflight, `re_verify`,
    `digest` and multi-prompt jigs.
  - Learning is a legitimate aim, but it is not one of the book's triggers.
- **ADR-0005 holds.** "Build vs buy, one layer up" (pp.540–541) supports it, since its third sign is a seam you can't
  outsource, such as the audit trail. Two qualifications *(unchecked)*:
  - The retry argument is half wrong. With the cache as the library's model interface, library retries would land in
    `model_calls` anyway, so only "absent is easier to guarantee than configured-off" survives.
  - "No retry of any kind" reads against schema repair.
- **The book independently supports** "the orchestrator is a queue, not an agent" (p.673) and "I never found a sequencing
  decision that deserved a model" (p.674).

## Where the book disagrees

| Topic | Book | Here | Judgement |
|---|---|---|---|
| Failure routing | Per-stage routes and exits (Ch 34, 54) | Retry, then quarantine | **Book.** See item 2 |
| Splitting a coherent feature | Keep one context once the pieces must fit (pp.463–465) | Split, with `interfaces` and a merged-tree check | **Book on the risk.** The merged-tree check has no repair route yet (item 2) |
| Fresh clone per run | p.627, though pp.466 and 621 recommend worktrees | Worktree plus pinned host git | **Here.** ADR-0014 traced the attacks |
| Resume from an interrupt | A pointer back into the work (p.602) | Cold retry | **Here.** Cards are small |
| Escalation on an SLA | Unsigned gates escalate (pp.683–684) | No notification (ADR-0003) | **Here,** for a helper. Take the query |
| Caching for determinism | Listed among frustrations (p.27) | The determinism mechanism | **Here,** but see item 4 |
| What bounds the loop | Four ceilings (pp.520–521) | Lease and deadline | **Book.** See item 8 |
| Compaction | Safe eviction (pp.481–482) | Excluded (ADR-0005) | **Here.** sigma compacts only at a turn boundary (`internal/agent/turnstack.go:36-47`), and a card is one turn. Item 8 still gives R61 its bound |
| Inner contract wins | "More specific wins" (p.137) | The model-written contract loses | **Here.** The book assumes a human inner author |
| Rule of three | pp.351–352 | One RED case, then ablation | **Here** for skills |
| Auto-promotion | p.725 | Rule 95 | **Here.** The book contradicts itself in Ch 32 |
| Mode enforced inside the card | p.416 | A gate is a row state | **Here** |
| MCP as the default | p.251 | In-process registry | **Here.** Ch 26 says a live query breaks reproducibility unless pinned (p.332) |

**The book contradicts itself** in several places. These show how much of it is settled:

| Topic | One place | Another |
|---|---|---|
| Fresh clone or worktree | p.627, and p.628 rejects a long-lived tree | pp.466 and 621, on parallel mutators, so this is partly scale |
| When to check the budget | After spending (p.520) | Before the call (p.529) |
| What a shared queue is | Orchestration (p.669) | Choreography (p.470) |
| Promoting rules | Automatic (p.725) | Human approval (Ch 32) |
| Where behaviour lives | "Up the rings" toward markdown (p.830) | Ch 60 pushes knowledge down a ladder toward determinism (p.715). This is milder than it looks, since p.830 also puts reacting behaviour in the binary. Keystone's Go grew from 4 files to 169 |

The budget-breach pair is not a contradiction. p.268 is a per-session budget where "the human decides", p.525's run scope is
`halt_fleet` where "a human decides what resumes", and `fail_item` is a separate per-item scope.

## Not borrowing

| The book has | Why not |
|---|---|
| Autonomy ladder L0–L4 (Ch 58) | This is a helper by design |
| n≥30 as a number (pp.380–381) | No derivation. Use the DeepSeek note's base-rate sizing |
| Vector store, reranker, staleness budgets (Ch 36) | No prose corpus. Knowledge files are hand-written and hashed |
| MCP and charter-as-a-service (Ch 20, 26) | Cards deny network. The in-process registry gives the typed schema, scope, fixed output and audit log that p.250 credits to MCP |
| Dashboards | Core §9.3's static page is enough |
| SemVer, changelog, forward-only patching for the charter (Ch 31) | No consumers of a shared charter. The pin and rule 128 are enough |
| Curator calendar and daily rhythm (Ch 32, pp.424–427) | Built for a team reviewing a stream of PRs. The event trigger is under Smaller |
| Hash chain over the record (p.678) | The book's own threshold is "the second harness or the first auditor" (p.704) |
| Judge panel (p.620) | ADR-0002. The book offers no evidence for it |
| Dual-LLM quarantine (pp.504–505) | An executor must read code to edit it |
| Experiment engine with z-tests (Ch 58) | One project cannot power it. `(config_hash, intent_digest)` covers the tagging |
| Framework builds (Ch 42–43, 51–52) | ADR-0005 |

## Sources to read first-hand

These are cited by the book, unverified, and none was opened. Each bears on a ⚖ experiment.

| Source | Book's account | Bears on |
|---|---|---|
| Cemri et al., MAST, arXiv 2503.13657 | 1,600+ annotated traces, 14 failure modes | E2, and coding E3's intervention count |
| Yu, AdaptOrch, arXiv 2602.16873 | 12–23% from matching topology to dependency structure | E1, policy §3.1 depth |
| Wang et al., *Rethinking the Evaluation of Harness Evolution*, arXiv 2607.12227 | No consistent gain over budget-matched test-time scaling | E3 and step 7 method |
| Zhang et al., *Effective Feedback Compute*, arXiv 2605.29682 | Predicts failure better than token or tool-call counts | E2 arm C′, tool-width ⚖ |

## Doc drift noticed

- **`README.md` is stale.**
  - It still cites `change-register.md` as the numbering authority. `rules-and-risks.md:3-5` replaced it, and core:5 and
    policy:5 cite it too.
  - It lists `pharmacy.schema.yaml` and the archive files, none of which are in the repo.
  - Its line counts are wrong, and it says "Rules 1–130, R1–R53" where there are now 152 rules and 64 risks.
  - Its ADR index omits 0005–0007, and 0005 and 0006 sit at the root rather than in `adr/`.
- **E3's baseline conflicts.** Policy §7.4 says a sequential pipeline (`harness-policy-v3.md:742-750`).
  `rules-and-risks.md` §6 item 8 names Gas Town, which policy §10 calls parallel.
- **`odoo-adaptation.md:1081` cites rule 96,** which now means "a note is superseded". The generator text belongs to rule
  104.
- **`rules-and-risks.md:483` says "133 rules and 56 risks"** *(unchecked)*.

## Reading list

The pages behind the items above. In the PDF, add 22. ✓ means the main thread found the quoted passage on that page.

| For | Book pages | Checked |
|---|---|---|
| Item 2, and the best single chapter for this repo | **Ch 54, 659–665** | ✓ 664, 665 |
| Items 5, 8, 9: test shapes for the runtime | **Ch 41, 526–534**; Ch 19, 212 | ✓ 212, 529 |
| Item 2: failure as an edge | Ch 34, 449; Ch 50, 640; Ch 55, 666–671; Ch 57, 688 | ✓ 449, 670, 688 |
| Item 1: locks and tiers | Ch 14, 138–143; Ch 12, 110–116; App A, 746 | ✓ 139, 746 |
| Item 3: the frozen record | Ch 58, 699–702 | ✓ 699, 702 |
| Item 4: samples and the band | Ch 30, 380–384; Ch 3, 33–34 | ✓ 380, 381, 384 |
| Item 5: tool boundary | Ch 37, 494–496; Ch 21, 271 | ✓ 494, 496 |
| Item 6: modes | Ch 32, 409–418 | ✓ 415, 416 |
| Item 7: hooks as charter | Ch 20, 226, 239–245 | ✓ 226, 240 |
| Item 8: ceilings | Ch 40, 518–525 | ✓ 520 |
| Item 10: flywheel and post-mortems | Ch 28, 355–367; Ch 29, 375 | ✓ 359, 365 |
| Positioning | Ch 49, 623–626; Ch 56, 673–675 | ✓ 624, 673, 674, 675 |
| Should this be built | Ch 33, 433–442; p.570; App D, 819 | ✓ 442, 819 |
| Vocabulary | Ch 4–6, 38–56; App A, 741–762 | ✓ 52, 742, 752 |
| One-window objection | Ch 9, 78–80 | ✓ 79 |
| Odoo in an existing codebase | Ch 23, 286–292 | |
| The author on their own evidence | Ch 30, 386 | ✓ |

## Verdict

Borrow the questions and keep this repo's words. Items 1 and 2 are defects in what is already written, and items 3–5
cost little before the first run but cannot be recovered after it. The book's strongest challenge is scope. Its checklist
would pass this design, but its prose asks what a stock engine cannot do, and the clearest answer here is the replayable
record. That argues for the substrate and against much of the policy above it.
