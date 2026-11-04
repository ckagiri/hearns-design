# H3 — the todo prototype (v3)

**Date:** 20 August 2026
**Status:** Live. **This file is deleted when Phase C ends.**
**Supersedes:** prototype v2, which is deleted, not archived.
**Lives at the repo root**, beside `PLAN.md`, not in `docs/`. It is a plan, not a design document.

## 0. Filing

Rule 63 and rule 133 name three landing places and there is no fourth. This file is a **scoped,
disposable plan** and obeys PLAN.md's own precedent — v1 deleted when v2 arrived — including
against itself. That is why this is v3 rather than a second root-level document: two plans is the
same failure as two design documents, and the material below is additions to the prototype plan,
not a new subject.

> **Deleted at the end of Phase C.** What survives goes to three places: findings become RED
> captures or numbered risks in `docs/rules-and-risks.md`; decisions become ADRs; corrections to the
> design become in-place edits.

**Nothing here is filed under `docs/`.** §14 lists the register entries that are, ready to paste.

### What changed from v2

- **Phase C added** (§7) — splitter and jigs, running *after* Phase B. The todo app hands you a
  ground-truth decomposition that expires the moment you move to pharmacy.
- **Two new emit-time gates** (§8) — the dual of the touch-set collision check, and the dep
  predicate. The second is ADR-0006.
- **Layer 2 gets a rule** (§9) — what belongs in skills versus retrieval, and where `skills.yaml`
  comes from.
- **Library survey extended** to tools, hooks, checks, shapes (§10). One adoption, one pattern
  borrow, two write-your-owns, and one genuine gap: canonical serialization.
- **DSPy reframed** (§11) — not a rejected library but an unrun E2 arm, and my earlier rejection of
  it was the lazy argument.

---

## 1. What the prototype is

A Python terminal todo application, TodoMVC-style: a workload whose specification is small, fixed,
boring and public, so every run is comparable and none of the interest lives in the workload.

**It is a workload, not a component.** The harness is the thing being built. The todo app is
disposable.

### What it answers

| Question | Answered by |
|---|---|
| Does the substrate survive crash and contention against a real workload? | Gate A |
| Is the cache key computable *before* dispatch, over bytes we assembled? | P1-24 |
| What do execute and verify actually fail at, in this repo? | Phase B's RED corpus |
| Does the splitter cover a spec without inventing or dropping work? | Phase C, against the frozen board |
| Does verify catch what the check ladder cannot? | Phase C's seeded traps |

### What it does not answer

- **Whether the output is good.** Core §11 keeps three problems separate. This addresses the first,
  gathers evidence for the second, is silent on the third.
- **Whether the harness beats a single-agent session.** E3 is Phase 3's job on a real workload.
- **Whether the jigs earn their cost** (R-new-2). Phase C measures mechanisms, not content.
- **Whether jigs transfer across workloads.** Needs two workloads.
- **R44.** No schema anchor here. Still owed, against the pharmacy spec.
- **Most of the ⚖ axes.** Correct for a prototype; to be written into `PLAN.md` by name at the end.

---

## 2. Repository layout

One directory, thrown away as a unit. **Two `git init`s, and that is not tidiness.**

```
h3-proto/                       ← no .git at this level
  harness/                      ← its own .git; the kit lives here
  workload/todo/                ← its own .git; disposable, resettable, NO HOOKS
  spec/todo-flat.md             ← twelve frozen behaviours. the board's oracle.
  spec/todo-capabilities.md     ← the same system as three capabilities. splitter input.
  scripts/reset-workload.sh
  scratch/
```

`git worktree add` operates on whichever repository the directory belongs to. If the workload sits
inside the harness repo, a card's worktree is a worktree *of the harness*, and every property Gate A
establishes — source isolation, reset on requeue, a stale writer's edits being absent — is tested
against the wrong tree. A single `.git` at the top is the version that looks most like a monorepo
and silently invalidates Gate A.

The kit is harness-repo-only: `guard_invariants.py` keys on `harness/ledger/**` and blocks new
`docs/*.md`. In the workload repo it enforces nothing and blocks the wrong things.

The workload repo gets a thin `CLAUDE.md` or none. If a card succeeds only because the workload had
a helpful project-memory file, the prototype tested something other than the harness.

`scripts/reset-workload.sh` re-inits the workload at a known commit and asserts no hooks. Every run
starts identical, or two runs are not comparable.

---

## 3. Postgres, not JSON

The todo application stores its data in Postgres. Artificial for a terminal app; the reason
overrides it.

The workspace is a triple — worktree, container, **and a database cloned per attempt**. Flat files
degenerate it to a pair: the template-build-and-clone path never runs, workers never contend on
environment construction, and Gate A's clone-collection assertion is vacuous. P1-9 is the largest
overrun risk in `PLAN.md`, and a file-backed workload prototypes it in the one configuration that
hides its hard part.

Two Postgres instances from day one per invariant 8 — the ledger, never deleted, and the workspace
instance whose clones are dropped per attempt. Assert the separation in a test; it is easier to get
wrong when both are on localhost.

**The ledger's store is not swappable.** The claim depends on `FOR UPDATE SKIP LOCKED`,
transactional status transition, and fencing compared inside the transaction. Adjacent projects
expose pluggable state stores as flexibility; a pluggable store means the weakest backend sets the
guarantee. If core does not say this, it is a one-line in-place edit.

---

## 4. Scope cuts

| Cut | Why |
|---|---|
| `digest`, tree renderer | Anti-milestone: a dashboard before the queries are painful |
| Ledger backup/restore (P1-18) | The prototype's ledger is disposable. Re-add before anything is kept |
| Five review verbs → `approve`, `kill` | The others have nothing to act on until Phase C |
| `EXPLAIN ANALYZE` at realistic size | Twelve cards is not realistic size. R15 stays unaddressed |
| Most of Phase 0 | `introspect.py`, `schema_lint.py`, `generate.py`, the Odoo spike. For a Python workload, rung 3 is `pytest` |

Kept from Phase 0: P0-0 (the kit), P0-7 (`make check-static`), P0-10 (the RED corpus).

**One query survives the `digest` cut:** cards pending with a `blocked` or `failed` ancestor. See §8.

---

## 5. Phase A — substrate, fake cards, Gate A

Core §12's build order, unchanged. **The cards are fake** — a card body is
`sleep 30 && echo hi > file.txt`. Core §11: nothing above Gate A needs a model call. Twelve fake
cards with real dependencies exercise the predicate, contention, fencing and the reaper as well as
twelve real ones, and better, because a fake card fails on demand.

1. Fix the kit's dangling reference. `CLAUDE.md` and `.claude/skills/task/SKILL.md` point at
   `docs/h3-project-breakdown.md`; the plan is `PLAN.md` at the root and says so in its own header.
2. Run INSTALL.md's verification, including both `guard_invariants.py` probes. Do not trust a hook
   that has not been seen to block something.
3. Freeze `spec/todo-flat.md` by hand in an hour — add, list, complete, uncomplete, rename, delete,
   filter active, filter completed, clear completed, remaining count, persistence, empty state.
   **Then stop touching it.** Improving the spec mid-prototype ends comparability.
4. Hand-write the board. Twelve cards, dependencies on paper. This is also Phase C's oracle.
5. **Run one card by hand, end to end, before writing harness code.** Play the harness: write the
   contract, paste the execute prompt into a session, run the checks, paste verify, record it in
   `worked-run-catalog`'s format. An afternoon, no code, and it tests the card contract's shape
   while changing it is still free.
6. P1-0 → P1-1 → P1-2 → P1-3 → P1-9 → P1-5, one task per session. The four DRIVE tasks stay DRIVE.
7. **P1-24 as DRIVE, before Gate A** (§12).
8. Gate A.

### The worktree hook hazard

Hook resolution across worktrees — `core.hooksPath`, worktree-local config, inherited settings — is
fiddly, and the failure is nasty: **a card's commit behaves differently inside its worktree than on
the main checkout, so nondeterminism enters through git config rather than through the model.** It
presents as a flaky card. DeepSeek Harness's `scripts/install-lefthook.mjs` wrapper solves a different
problem, installs overwriting contributors' shared hooks. If P1-9 hits this, read its runtime runner instead,
`packages/experimental/worktree/src/process.ts` and `index.ts`, which disables hooks.

Three responses: rule 150's runner turns hooks off and scrubs host config on every host git call (ADR-0014); the
workload repo has no hooks, asserted by `reset-workload.sh`; and Gate A asserts the hook configuration a card sees
inside its worktree.

### Manufacture the unhappy paths

If every card succeeds, verify never rejects, the reaper never fires and `attempts` never climbs,
the prototype proves nothing — and by principle 8 a mechanism that never fires is a deletion
candidate, so a conclusion from an empty audit is actively wrong. Seed deliberately, labelling each
synthetic in the ledger: an ambiguous spec line; two overlapping touch sets; a card that sleeps past
its lease; one killed mid-write; one that exhausts its turn limit.

### Exit criteria

- Kill tests green: container killed mid-write, clean requeue, worktree removed, clone collected,
  stale process's writes absent.
- Contention: N workers, twelve cards, each claimed exactly once.
- Replay: same run twice from cache, identical terminal graph.
- P1-24 answered in writing, recording-proxy test kept.
- Two-Postgres separation asserted.
- Worktree hook configuration asserted.

---

## 6. Phase B — one crude model pass, three-day timebox

**The deliverable is the RED corpus, not working code.**

Crudest possible execute prompt: card contract, spec fragment, "make the checks pass." No negations,
no rationalization-blocking, no structure. Crudest verify: here is the diff and the contract, did it
do what was asked. Run the twelve cards. Watch what breaks.

**Why crude.** A careful prompt written now is written from *imagined* failure modes, and suppresses
exactly those while leaving the real ones invisible under fluency — R51 through the front door.
A crude prompt fails loudly and unpredictably, which is the point.

**And it cannot be promoted by accident.** Name the files `prompts/execute-v0.md`, not
`jigs/execute.md`, headed *this is a probe, not a jig; every rule in the real jig traces to a RED
case.* Otherwise v0 gets tuned until the todo app passes, starts to look like a jig, and enters
Phase 2 carrying rules that trace to guesses about a toy.

**v0 is also the control arm.** If declarative contracts really do replace prompt engineering, a
bare contract with no accumulated rules is the null hypothesis for the whole policy layer — and
Phase B runs it first by accident. Record its pass rate. Not as a result; twelve cards on a toy
settles nothing. As the number Phase 2's first real jig has to beat. See R-new-2.

### Exit criteria

- A RED corpus with a real number, and an honest note on manufactured versus observed.
- `execute-v0`'s pass rate, with the caveat attached.
- The register entries in §14 filed.

---

## 7. Phase C — splitter and jigs, after Phase B

### Why after, and why at all

Running Phase C after Phase B is what preserves the oracle. The hand-written board from §5 step 4 is
the correct decomposition; if the splitter produced the board, there would be nothing to compare
against.

**Splitter quality is normally unfalsifiable.** "Is this a good decomposition?" has no ground truth,
so evaluation degrades to eyeballing trees. The todo app is the one workload where you have the
answer written down in advance — and that asset expires the moment you move to pharmacy, which is
the argument for spending the days here rather than later.

### Two specs

`spec/todo-flat.md` is the frozen twelve. `spec/todo-capabilities.md` is the same system stated as
three lumpy capabilities — item lifecycle, views and filtering, persistence — and nothing else
differs.

The splitter gets the capabilities version, for two reasons. The pharmacy spec will arrive as
capabilities, not as cards; nobody hands you a pre-decomposed board, and if they did you would not
need a splitter. And twelve atomic behaviours give the splitter no work — **depth 1 only**, while
every interesting splitter failure needs depth 2 or 3: infinite regress, a gap that appears only at
the third level, sibling overlap discovered after both children are in flight, a child that should
have been merged with its sibling.

### Score coverage, not shape

Did every frozen behaviour land in some leaf card, and did the splitter invent cards with no basis
in the spec? Both falsifiable. Whether its tree *looks like* yours is a judgment call, and a
different-but-valid decomposition would score badly on shape while being fine. Gaps and inventions
are the failure modes worth catching anyway.

### Verify needs an eval set, because the workload is bad for it

Verify exists to catch what the check ladder cannot. On a todo app `pytest` catches nearly
everything, because the spec is fully expressible as tests. So verify has almost no residue, will
rubber-stamp, and you would learn that verify *runs* rather than that verify *works*.

**Pre-write the traps.** Cards whose checks pass while the work is wrong, with known signatures, so
verify's detection rate is a number:

- `clear_completed` implemented as delete-everything, passing a weak test
- the remaining-count hardcoded to match the fixture
- a test that asserts nothing but is named as though it does
- the test edited to match the bug rather than the bug fixed
- a card satisfying its contract while silently touching a file outside its touch set

Five to eight, hand-written, a couple of hours. It converts verify from unobservable to measurable
and gives `re_verify` something to do — the round counter is untestable until verify rejects once.

### The contamination rule

A jig is twenty *observed* failures compressed. On a toy you will not get twenty organically, so the
temptation is to write jig rules from the manufactured ones. Don't, and the reason falls out of
rule 25: a manufactured failure is one you already understand well enough to construct, and
understood failures belong in code.

> **Manufactured failure → a gate in the check ladder. Observed failure → a candidate jig rule.**

The assertion-free test becomes a static check. The touch-set violation becomes a post-attempt gate.
Neither becomes a line in `execute.md`. Otherwise Phase 2 starts with a jig full of rules tracing to
your own guesses — R51 one level up from where PLAN.md §5 currently watches for it.

### What Phase C can and cannot teach

**Can:** the emit path end to end — split produces children, gates fire, children land on the board
and become claimable. Prompt assembly and context economics. Output schema shape and
`summary_schema_version`. That verify is structurally unable to write. Round-counter mechanics.
Splitter coverage against a real oracle.

**Cannot:** whether accumulated jig rules earn their cost. Whether jigs transfer. Whether verify
catches enough to justify a second model call.

**Framing, same as Phase A: a mechanism test, not a content test.** The split jig's exit criterion
is "emit works and the gates fire," not "the decomposition was good."

### Cost, honestly

Roughly 4–6 days on top, pushing the prototype past three weeks. That is precisely the elaboration
§4's cuts were protecting against, and the fair question is whether those days beat spending them on
the pharmacy schema anchor — the hour the README calls the highest-leverage in the project, still
unspent.

---

## 8. Two gates and one predicate

### The edge that carries nothing

`reject_if_touch_sets_collide` catches **false independence**: two cards claiming they can run
together when they would collide. Nothing catches **false dependence**: a card claiming it must wait
when no data crosses.

A splitter that emits `B.deps=[A]` and `C.deps=[B]` because that is the order it thought of them has
serialized three independent cards, and the board will faithfully execute the mistake forever. The
predicate cannot catch it — a dep is a dep.

The test, borrowed: *does the next step read the last step's output?* If not, there is no edge and
the wait is wasted. The card shape already has the field — `interfaces` — so require every dep to
name what it consumes:

```python
def reject_if_edge_carries_nothing(kids):
    for k in kids:
        for d in k.deps:
            if not k.consumes.get(d):          # names an interface the parent exposes
                raise SplitRejected("edge_carries_no_data", k.id, d)
```

Same emit-time, one-pass, never-false-rejects character as the collision check. Fails loudly at
split rather than silently costing wall-clock on every run after. **Add it regardless of Phase C.**

### Terminal is not `done` — ADR-0006

A parent that ended `blocked` is terminal, but its summary describes work that did not happen.

**The predicate requires `done`.** A card whose parent is blocked is a card whose interface does not
exist; the best possible attempt blocks too, after a workspace build, a container spin-up, a clone
and a model call. Loud rendering in `dep_summaries` would be rule 25's anti-pattern — an instruction
the card is asked to honour rather than a state it was never given.

```python
SATISFIES_DEP = {"done"}   # not every terminal state
```

Children of a blocked parent stay `pending` and unclaimable: visible, costing nothing, and made
claimable in one transaction when the parent is unblocked. Full argument, alternatives and the
partial-block objection in ADR-0006.

**This needs one query alongside it**, or the stall is silent: cards pending with a `blocked` or
`failed` ancestor. Without it you see one blocked card and not the eleven waiting behind it, and
*how much is this block costing* is exactly what the record should answer trivially. Write it in
Phase A despite the `digest` cut.

---

## 9. Layer 2 — where skills come from and what belongs there

### Where `skills.yaml` comes from

You write it. By hand, once per pin, about six lines. §P5.1: nothing computes it, because a chooser
is core §3.4's deleted router returning.

```
harness/config/skills.yaml         # kind → skill names        ← the mapping
skills/pytest-failure-reading.md   # the skill itself          ← the prose
```

Both the mapping's hash and each file's hash enter `config_hash`, which is what makes *what did this
card see* answerable from the ledger.

**On day one it is empty and correct:**

```yaml
execute: []
verify: []
split: []
```

Skills come from Phase B. Each ships paired with the RED case that motivated it — which assigns its
kind, supplies its ablation test, and makes it removable. Without the pairing a corpus grows by
accretion and nothing records what any file was for.

### The rule

> **Layer 2 is not what this task needs. It is what every card of this kind needs. Anything narrower
> is retrieval.**

The cost of a broad set is not tokens — layer 2 is kind-scoped, so cache amortises the price. The
cost is R50: telling a model where to look makes it look there and marginally less elsewhere, so a
broad set may degrade the cards it was not written for *while every cost metric looks fine.*

Under the rule, a Postgres-fixture skill fails to be a skill: it is a concern of cards that touch
the store, not of all execute cards. It goes to layer 6 as named-risk retrieval, triggered by the
card's touch set intersecting the store — derived from the board, not chosen by a model, so §3.4's
router stays deleted. **If you cannot state the trigger as a property of the card, it stays a
skill.**

Three things this buys: R50 shrinks by construction; §P5.2's structural detector (retrieval with no
named risk) gets something to detect for the first time; and the demotion is falsifiable — if it is
wrong, the DB cards fail in a way that names the missing knowledge, and *that failure* is the RED
case for promoting it back.

**More than one skill per kind is fine.** The discipline is per-skill, never a count: does this one
have a RED case, and does the ablation still justify it. `verify`'s set stays shortest.

### A sketch fix this exposes

`Role.kinds` is a list, `Role.jig` is one jig, `Jig.skills` is one set — so a role serving two kinds
gives both the same skills, contradicting skills being per-kind. Key the lookup off the card:

```python
Block(2, "kind", load_skills(SKILLS[task.kind]))    # not j.skills
```

Scope stays `kind`, the prefix survives, and the manifest stops lying about its granularity.

### The free ablation

Any skill that applies to only some of the twelve will be in the prompt for the rest. That is
§P5.1's measurement — the set run against cards it was not written for — on a board small enough to
run both arms in an afternoon. The cheapest look you will ever get at R50, which is the load-bearing
uncertainty in layer-2 sizing.

---

## 10. Libraries, by registry

The bar is not "does this exist." Tool schemas are layer 3 and check definitions are layer 8, so
**both are inside `config_hash`** — a library supplying them puts a third party's version inside
your hash, the coupling ADR-0005 just removed from the runtime. So: is it library-shaped *and* is it
outside the pin.

| Registry | In the pin? | Answer |
|---|---|---|
| `HOOKS` | No | **pluggy.** Adopt |
| `CHECKS` | Yes (layer 8) | pre-commit as a model; optionally as a rung 0–1 runner |
| `TOOLS` | Yes (layer 3) | No. Write six |
| `SHAPES` | No | Definitionally yours |

**pluggy.** `dict[str, list[Fn]]` has a specific failure: a typo'd hook name registers a function
that silently never fires, and you find out when workspace reset stops happening and cards inherit
each other's state — presenting as flaky cards. pluggy validates implementations against declared
specs at registration, so a misspelled name or wrong signature raises at import. Ordering without a
convention, `firstresult` where one answer wins. Outside the pin because hooks do not render into
prompts. **No entry-point discovery** — a hook that arrives by being pip-installed is a hook that is
not in your config.

**pre-commit.** Checks as data, each pinned to a revision, resolved into isolated environments, run
over a file set — the check ladder's rungs 0–2 with the pinning discipline already solved, and
because every hook carries a `rev`, the check set has a hash, which is what layer 8 needs. Steal the
shape for `checks.yaml`. If you also run it, `.pre-commit-config.yaml` lives in the *workload* repo
and its cache directory must be baked into the image, not mounted, or a card's check environment
differs from the template's.

**Tools: no, and MCP is the trap.** Server schemas land in layer 3 and therefore in `config_hash`,
so a server upgrade changes what every card saw with nothing in the design moving. A server
lifecycle inside the container adds failure modes to the layer Gate A is trying to prove. And
`normalize` has no external equivalent — no tool provider offers a stable-bytes guarantee, so you
would wrap every one anyway and keep the dependency for nothing. The real set is `read`, `write`,
`edit`, `bash`, `grep`, `ls`: a few hundred lines including normalizers, all of it wanting your
`side_effect` classification and your quota keying.

**Shapes: nothing external knows your id derivation, dep resolution, gating or `config_version`
propagation.** The registry is a ten-line decorator. What to watch is not a missing library but
sketch note 2 — `emits`-as-data holds only while shapes stay pure functions of `(task, payload)`.

### The genuine gap: canonical serialization

`canonical_json()` and `canonical_bytes()` are elisions in the sketch and load-bearing for
`config_hash`, `kind_hash` and the cache key. Hand-rolling canonicalization is a classic subtle-bug
generator — key ordering, Unicode normalization form, float representation, escaping, whether `1`
and `1.0` hash alike. Each produces a hash stable on your machine and unstable across a Python
version or locale change, and the symptom is a cache miss you would blame on the model.

**Use an RFC 8785 (JCS) implementation.** `json.dumps(sort_keys=True)` fixes neither float repr nor
Unicode form. Pin it into `config_hash`; a canonicalizer upgrade moves every key you hold. This is
the one place I would add a dependency without hesitation.

### Two free wins

**Derive tool schemas from the function.** Hand-written JSON Schema drifts from `fn`'s signature
silently, and the drift appears as `invalid_args` denials that look like model misbehaviour.
`pydantic.TypeAdapter(fn).json_schema()` makes check 2 in `dispatch_tool` unable to disagree with
check 1 — same argument as `normalize` being non-optional at the type level.

**No templating engine.** Jinja2's version would affect rendered bytes and therefore enter
`config_hash`. Layers 0–3 are files read verbatim, except that a role's slot values are substituted
with `str.replace`; layers 4–7 are five f-strings. That is the whole requirement.

### Measurement: you already have a better eval harness

promptfoo is the leading matrix-eval tool and it is genuinely good. But an ablation here is: same
frozen board, same workload commit, bump `config_version` with a different `skills.yaml`, re-run,
compare. Your substrate gives deterministic replay, per-attempt cost accounting, and a record of
exactly what each card saw — none of which promptfoo has, because it calls the provider itself.
Running ablations through it would bypass the cache and the ledger, so the measurement would not be
reproducible by the mechanism whose reproducibility is the project's main claim.

Borrow its **assertion vocabulary** — the taxonomy of deterministic versus model-graded checks — as
input to `checks.yaml`. Skip the runner. Same posture as LiteLLM's error taxonomy.

---

## 11. DSPy is an unrun experiment, not a rejected library

v2's §7 disqualified prompt-compiling frameworks because the rendered prompt is compiler output that
moves when the optimizer runs. **That was the lazy argument again** — the same failure as v1's
CLI-runtime claim.

Compilation is a *build step*. A compiled program is a frozen artifact — instructions plus selected
demonstrations — and loading it makes inference as deterministic as any other prompt. The mechanism
is obvious once stated: **compilation is a run boundary**, exactly like a jig edit.
`compiled_program_hash` enters `config_hash`; recompiling is a new `config_version`. Existing
discipline absorbs it unmodified.

And there is a move that removes even the R60 coupling: **use it as an offline prompt compiler, not
as a runtime.** Compile against a metric, export the optimized instructions and demos, commit them
as jig and layer-2 content, render through your own loop, hash your own bytes. A dev dependency that
never appears in `config_hash`.

**What it would buy.** R51 dies structurally — an optimizer cannot rationalize; it selects what
scored. Phase 2's uncompressible calendar time becomes: define a metric, run the optimizer, ship the
artifact. Every prompt change acquires a number, where E2 currently has no measurement apparatus.
And **Phase C already builds the trainset** — a frozen spec, a hand-written board as splitter ground
truth, seeded traps as verify ground truth, a check ladder as execute ground truth.

**What it would cost.** *Goodhart, aimed at the central claim*: the obvious execute metric is "the
checks pass," and the verify layer exists precisely because check-passing is not work-done. Using
`run_oracle` as the metric is the real answer, but then the oracle stops being an independent
measurement of the thing it now shapes, and you need a second held-out oracle. *Provenance dies*:
a searched artifact has no RED pairing, so it cannot be argued with, ablated per-rule, or removed
for a reason — and rule 133, `/drift` and the register all depend on being able to. *Overfitting to
a toy*: selected demonstrations would be todo-app examples embedded in pharmacy prompts.

**So it resolves to an E2 arm.** Hand-authored `execute-v1` against a DSPy-compiled `execute-v1c`,
same board, same oracle, same `config_version` discipline, compared on the ledger. That is exactly
what R-new-2 asks for, and offline-compiler mode makes it runnable without touching the runtime or
the cache. Filed as an arm, not an ADR — there is nothing to decide yet.

---

## 12. Runtime and port — unchanged from v2, restated in brief

**Write the loop, behind a port** (ADR-0005). Provider SDK for transport; pydantic v2 for schema;
200–400 lines of assemble → dispatch → append → terminate → validate here, because a library upgrade
would move every cache key silently, a library retry would make `attempts` undercount real model
calls, and owning the dispatch table makes rule 135 structural rather than asserted.

**CLI-driven runtimes are disqualified on predictability, not visibility.** A local proxy sees the
bytes of any opaque harness. But the cache needs the key *before* dispatch and a proxy produces it
after; with compaction there is not one rendered prompt per card but N, chosen by logic you do not
control. **A proxy buys observation. It cannot buy determinism.**

**The port is neutral and typed, one adapter shipped.** Take the error taxonomy pattern regardless:
core §10's `failure_class` allow-list *is* an error taxonomy, and written against one provider's
exception names it starts meaning different things the moment a second adapter exists. Turn-limit
exhaustion is a distinct class and never a success.

> **Normalize the envelope. Never hash the envelope.**

**P1-24 restated:** not *are the bytes visible* — assembling them here makes that trivial — but *is
the key computable before dispatch and stable across upgrades*. Kept test is a **recording proxy**,
capturing from outside the process so nothing the SDK does internally can fool it.

**Second adapter waits for something concrete:** P0-1's two independent schema drafts (two providers
is the strongest independence available, a real upgrade on effort-level variation for R48), or cost.
Cost is a second-adapter question, never a runtime question.

---

## 13. Timelines

**No reduction from `PLAN.md` v2.** Phase A 12.5–16.5 days; Phase B a three-day timebox; Phase C
4–6 days.

PLAN.md §1 argues it: 30% off, not 70%, and the four things dominating the critical path barely
compress. The prototype makes it *worse* — every cut in §4 was DELEGATE work, so what remains is
roughly two-thirds DRIVE and PAIR against about 40% in the full plan. The compressible fraction
shrank; the spine stayed.

**And the spine does not scale with workload size.** P1-9 is Docker, bind mounts,
git-on-host-execute-in-container, template clones — identical whether the card writes a todo app or
an Odoo module. A toy workload bought Phase 0 and the jigs. It bought nothing on the spine.

Phase B's timebox buys observation, and observations accrue in calendar time. Finishing early is
information about the estimate, not a reason to have planned for it.

**The risk that gets worse with speed** is PLAN.md §7's last row: velocity outruns the register. Run
`/drift` at every phase boundary, and add one immediately after Gate A.

---

## 14. Register entries to file in `docs/rules-and-risks.md`

Filed now, not when this file is deleted. Numbers assigned on filing.

**R-new-1 — a pluggable ledger store would set the guarantee to its weakest backend.** The claim
depends on `SKIP LOCKED`, transactional transition, and fencing inside the transaction. Mitigation:
core states the ledger is Postgres, not an interface. Watch for: any proposal to abstract the store.

**R-new-2 — the jigs may not earn their cost.** A deployed, production-focused counter-argument
exists that declarative type contracts replace prompt engineering. Policy §5 bets the opposite.
Both cannot be right; this is the single result that would most change Phase 2's shape. Early
signal: `execute-v0`'s pass rate (§6). Arms: hand-authored versus compiled (§11).

**R-new-3 — nondeterminism can enter through git configuration.** Worktree-local hook resolution can
make a card's commit behave differently inside its worktree than on the main checkout, presenting as
a flaky card. Mitigation: no hooks in the workload repo, asserted; Gate A asserts what a card sees.

**R-new-4 — an edge that carries no data is invisible to the predicate.** A splitter can serialize
independent cards by emitting order-of-thought as dependencies, and the board executes the mistake
forever with no signal. Mitigation: the emit-time gate in §8. Detector: dep count versus
`consumes` count per card.

**R-new-5 — unnormalised tool output breaks replay at the second model call.** Directory ordering,
timings and absolute paths enter turn N+1's key. Symptom is a cache miss attributed to the model.
Mitigation: `normalize` non-optional on `ToolImpl`. Arguably a bigger determinism threat than
sampling, which §C8 already handles at length. *(Promoted to rule 144, ADR-0012.)*

**R-new-6 — hand-rolled canonicalization produces locally-stable hashes.** Key order, Unicode form,
float repr. Mitigation: an RFC 8785 implementation, pinned into `config_hash`.

**Amendment to R60** — recorded as an accepted cost of a runtime dependency inside `config_hash`.
ADR-0005 closes it rather than mitigating it. Point the entry at ADR-0005 and mark closed, not
deleted.

**Amendment to step 7** — the differentiator list standing at one, the record, is now supported by
three named comparables that lack a durable ledger by their own account.

---

## 15. What would change this plan

- **The two-repo split proves unworkable** — the workload boundary needs a different mechanism, not
  a merge; Gate A depends on it.
- **P1-24 shows the key cannot be computed before dispatch** — core §8's cache is not implementable
  as specified. A core edit, not a runtime workaround.
- **The hand-written loop passes 500 lines, or a third provider becomes necessary** — ADR-0005's
  reopening trigger.
- **`execute-v0` passes eleven of twelve** — R-new-2 is live, and Phase 2 needs re-scoping before it
  starts rather than after.
- **Phase B produces fewer than a handful of distinct RED cases** — either the workload is too easy
  even with manufactured failures, or the corpus needs a real workload sooner than planned. Phase
  2's duration depends on this number.
- **Phase C's splitter covers the spec on the first try** — suspect the capabilities spec of being
  pre-decomposed, not the splitter of being good.
- **A cut in §4 turns out to have been load-bearing** — re-add it and record why, rather than
  working around its absence.
