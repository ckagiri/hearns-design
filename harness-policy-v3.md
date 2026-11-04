# Harness Policy — v3

**Supersedes:** `harness-design-v2` §6–§10, §13, §16–§21, §24.
**Requires:** `harness-core-v3` — the substrate this sits on.
**Also live:** `odoo-adaptation` (the domain instantiation), `change-register` (rules 1–104, risks
R1–R46, numbering authority), ADR-0001, `worked-run-odoo`.

**Why this is separate from core.** Everything here has been amended at least once, and several
things here are **not yet decided** — they are config axes with a named experiment beside them.
Baking an unmeasured decision into prose is how v2's compounding-fidelity argument became
load-bearing without evidence. Core is what you build; this is what you measure.

**Rule of this document.** No new content. Every section carries **what would change it**.

**Reading it.** Sections marked ⚖ are contested — a live axis with a deciding experiment. Sections
marked ✓ are settled by evidence. Everything else is a working assumption.

---

## 1. Roles, kinds and jigs

### 1.1 The kinds

| Kind | Does | Emits |
|---|---|---|
| `split` | decomposes an intent | children + gates, one transaction; + preflight if E1 justifies it |
| `execute` | does leaf work | a diff, a summary |
| `verify` | compares against the root intent | gaps, unverifiable, minors |
| `re_verify` | verdicts prior findings | ADDRESSED / NOT ADDRESSED per finding |
| `preflight` | cross-sibling conflict table | findings or `spec_conflict` |
| `integrate` | merges sibling branches | a merged branch, checked |
| `digest` | the human-facing output | three queries |
| `spec_revision` | proposes an anchor change | `awaiting_review` |

`judge` is not on this list. See core §3.4.

### 1.2 Gates are pinned by the splitter ✓

**A card never emits its own reviewer.** In a controller-based tool this had to be said in every
dispatch template, with escalating psychological pre-emption, because a persistent agent will
helpfully add a review seat. Here a card cannot spawn anything — it emits rows, and gates are pinned
at split time.

### 1.3 The worker loop and roles

A role is config: kinds, tiers, model, effort, jig, hooks, lease TTL. A worker runs one role for its
lifetime. Ten workers on `execute_cheap` are ten processes with the same config.

**No default tier anywhere.** Absence is a config validation error, not a fallback.

**One job each** (ADR-0008, rule 136). A kind says what type of work a card is. A role says who claims
it and how hard they try. A jig says how the work is done. Each kind has exactly one jig, each kind and
tier is claimed by exactly one role, and every kind in a role shares that role's jig. Startup
validation enforces this, and a card whose kind and tier no role claims is rejected at emit time.

| Role | Kinds | Tiers | Jig |
|---|---|---|---|
| `split` | `split` | strong | `split` |
| `execute_cheap` | `execute` | cheap | `execute` |
| `execute_middle` | `execute` | middle | `execute` |
| `execute_strong` | `execute` | strong | `execute` |
| `verify_middle` | `verify` | middle | `verify` |
| `verify_strong` | `verify` | strong | `verify` |
| `re_verify` | `re_verify` | middle | `re_verify` |
| `integrate` | `integrate` | middle | `integrate` |
| `digest` | `digest` | middle | `digest` |

Models and effort are in §2.0. `verify_middle` reads summaries and `verify_strong` reads diffs, set
through the jig's `verify_input` slot; E2 arm D decides whether both survive ⚖. `preflight` has no role
until E1 justifies it (§11), and `spec_revision` has none while a human writes it.

**Open ⚖:** Odoo's structural verify (`odoo-adaptation` §10.1) reads a third input, rung 3's diff, and
has no role yet. It gets `verify_cheap` once that document's open question 2 confirms cheap is enough.

### 1.4 Jigs

Prompt template + tools + output schema + allowed outcomes, bound per kind, versioned with the config
pin.

**A jig names no check command** (rule 137). Check definitions live only in `checks.yaml`, a card's
`check_spec` picks the rungs, and layer 8 renders only rungs marked visible.

**A jig is written against observed failures, captured before the jig existed.** The method:

1. **RED** — run the scenario with no jig. Document what the model does and how it justifies it,
   **verbatim**.
2. **GREEN** — write the minimum that addresses those observed failures. Not hypothetical ones.
3. **Pressure-test** — realistic scenarios combining three or more pressures, forcing a concrete
   choice with no option to defer.
4. **REFACTOR** — each new rationalization gets an explicit negation in the rule, a row in the
   rationalization table, and a red-flag entry.

A jig with no RED pass behind it is untested, regardless of how many golden files it passes. Golden
files test the *shape* of the output; they do not test whether the jig prevents the behaviour it was
written to prevent.

**Jig source material.** Roughly two-thirds of this is already written, MIT-licensed, by people who
ran it: implementer, task-reviewer, re-reviewer and final-reviewer prompt templates map onto
`execute`, `verify`, `re_verify` and root-level `verify`. Attribution goes in the jig file.

**Jig count is bounded by kind, not by domain × kind.** Domain knowledge lives in layer 2, so a new
domain is a swappable skill set in config rather than a new set of jigs. Six jigs ship flat; ten is
the ceiling worth defending. If jigs begin multiplying to encode which card gets which treatment, a
router has been rebuilt in the config directory — and it does not become acceptable by being YAML.
Sizing, placement and skill selection are worked through in `jigs-layers-skills-v2`.

**What would change this:** nothing observed so far. This is the cheapest high-value section in the
document and it is currently the largest unbuilt risk.

### 1.5 Multi-prompt jigs ⚖

A jig is already a function of several things, and two of them are settled:

- **Turns are not prompts.** An executor makes many model calls per attempt — read, edit, run the
  check, read the failure, edit again. That is one prompt template driving a tool loop.
- **Attempt-keyed variation exists.** Layer 7 carries the previous attempt's check output, and the
  fresh-eyes framing at the tier ceiling (§2.2) is a different prompt for the same jig.

The live question is **staged prompts inside one attempt**: call A produces something, call B
consumes it, both within one card.

#### The test

> **If the stages have different checks, and a reviewer could accept one and reject the other, they
> are two cards. If they share one check and one acceptance decision, they may be one jig with
> several prompts.**

This is §3.2's leaf criterion applied one level down. It matters because a jig that sequences
prompts is a small controller inside the card, and once its stages carry independent acceptance
decisions the architecture's central move has been undone locally.

**The failure is not correctness.** A card dying mid-sequence retries cold, which is fine. The
failure is that a decision made in stage A and consumed in stage B **never becomes a row** — so it
cannot be a Ruling, cannot be verified, and cannot be read in the tree a year later. Intermediate
state invisible to the ledger is the one thing this design is built to prevent.

#### Permitted

**Schema repair.** Malformed output, re-prompted with the validation error. Same template, bounded
to one or two retries, no new decision. Worth having: the alternative is burning a whole attempt on
a parse error.

**Extraction under a fixed rubric.** A small cheap call in front of the main one where a
deterministic parser genuinely cannot do it — pulling the relevant traceback out of a 4,000-line
log. Deterministic wherever possible, per principle 3; a model only where the format varies.

**Self-review before returning.** A pass against the card's own contract as a cheap first filter.
Legitimate **only** because an independent check follows. It catches sloppiness and its verdict is
never trusted. A self-review that establishes correctness is the ratification failure at card scale
(§4.6).

#### Not permitted

**Plan-then-execute inside one card.** If the card needs a plan, the plan is a decomposition and
belongs in the ledger as children. This is `split` in disguise, and it is how depth stops being
visible in the tree.

**Triage of your own findings.** A verifier producing gaps and then ranking them in a second call is
grading its own output. Triage comes from something the verifier did not write — `cost_if_wrong`,
`done_with_concerns`, a computed diff.

#### Two constraints

1. **A jig has one output schema and one check.** Intermediate prompts produce material for the
   final output, never a separate deliverable.
2. **A jig is stateless across attempts.** Stage outputs live in the attempt and die with it.
   Nothing carries forward except through the ledger.

#### The schema consequence — a Phase 1 decision

`model_used`, `effort_used`, `tokens_in`, `tokens_out`, `reasoning_tokens` and `cost_usd` are single
columns per task. Three calls per attempt makes `model_used` ambiguous and forces silent summing,
which breaks cost-by-tier and reasoning-tokens-against-attempts-saved.

Two options:

| Option | Shape | When |
|---|---|---|
| Roll up on the task, with a `model_calls` jsonb carrying the breakdown | one table | if multi-prompt jigs stay rare |
| A `model_calls` table keyed `(task_id, attempt, seq)`; the task's columns become a view | two tables | if they become common |

**Take the second if there is any doubt.** Retrofitting means every early run has unattributable
costs, and cost attribution is one of the few things the record is unambiguously for. Caching is
unaffected either way — each call keys independently on its own rendered prompt.

**What would change this:** if the permitted patterns turn out to cover everything anyone wants, the
`model_calls` table is over-build and the jsonb was right. If a jig grows a stage that fails the
test, that is the signal to split the card, not to relax the rule.

### 1.6 The card runtime ⚖

*(Added 2026-08-18. Adoption decision in ADR-0004; cache mechanics in core §8.)*

§1.5 says turns are not prompts — an executor makes many model calls per attempt, reading, editing,
running the check, reading the failure, editing again. **Nothing until now said what runs that
loop.** It was treated as an implementation detail of the executor, which it is not: the loop
decides what the model sees, what it can touch, and what the ledger learns about the attempt.

#### Settled

**The runtime lives below the card boundary and nothing above it.** It makes model calls, runs the
tool loop, and validates output against the jig's schema. It does not schedule, does not retry
across attempts, does not persist between cards, and does not know that other cards exist. Anything
it offers above that line — durable workflows, session resumption, orchestration — is a controller
under a different name, and core §3.4 deletes those by name rather than by category.

**The tool set is enumerated per kind, in the jig, and absence is a gate** (rule 135). A `verify` card
constructed without a write tool cannot edit what it is reviewing. A `digest` card without a shell
cannot run anything. This is rule 25 available at the cheapest possible price: not an instruction
the card is asked to honour, but a capability it was never given. It also puts layer 3 on the same
footing as layer 2, which had a selection discipline (rules 119–122) while tools had none.

**Command output is normalized before the model sees it** (rule 144, ADR-0012). A tool or check type
without a normalizer is a type error. Core §8 gives the reason, and `tool_audit` keeps what it removes.

**The runtime is part of `config_hash`.** It assembles the prompt, so a version change changes what
cards saw whether or not any jig moved. It is pinned in the lockfile and an upgrade is a run
boundary (R60).

#### Contested ⚖

**Does a narrower tool set change behaviour, or only price?** The context argument says every tool
schema costs window and adds a wrong choice to pick from. That is R50's argument moved from skills
to tools, and R50 is exactly the risk where every visible metric can improve while the thing being
measured degrades. **Deciding experiment:** the per-set ablation already scoped for layer 2, run a
second time over tool sets — give a kind the full set and the narrow set on cards written for
neither, and compare. Until then the narrow set is justified *structurally*, as a gate, and the
attention claim is unmeasured.

**What bounds the loop.** The lease and `deadline_at` bound wall clock, host-side, which is stronger
than a step cap — a cap is a guess about how many steps a task needs, and the model already signals
completion by returning text instead of a tool call. But neither bounds **context exhaustion**. A
card that fills its window and then produces a confident summary is a commission-drift generator of
precisely the shape ADR-0001 exists for, and no detector currently exists for it. Recorded as R61.

#### What would change this section

- **The runtime cannot expose the exact request bytes** → it cannot satisfy core §8, and the
  adoption in ADR-0004 is reversed regardless of what else it offers.
- **The ablation shows no behavioural delta from tool-set width** → keep narrow sets as gates, drop
  the attention claim, and stop treating tool selection as a tuning surface.
- **Context exhaustion is observed producing a passing summary** → R61 becomes a mechanism question
  rather than a residual, and the first response is a bound, not a check.

---

## 2. Tiering and effort ⚖

### 2.0 Two axes, one derivation

Tier selects a model. **Reasoning effort is a separate axis**, and v2 did not have it — effort was
whatever the SDK defaulted to, which is the same silent-inheritance failure as a missing tier.

```yaml
execute_cheap:   {model: haiku,  effort: minimal, temperature: 0}
execute_middle:  {model: sonnet, effort: medium}
execute_strong:  {model: opus,   effort: high}
split:           {model: opus,   effort: high}
verify_middle:   {model: sonnet, effort: medium}
verify_strong:   {model: opus,   effort: high}
re_verify:       {model: sonnet, effort: low}
integrate:       {model: sonnet, effort: minimal, temperature: 0}
digest:          {model: sonnet, effort: minimal, temperature: 0}
```

**No default effort**, for the same reason there is no default tier. A cheap model at high effort
and a strong model at low effort are genuinely different points, and which is better depends on the
card rather than on the SDK.

**Effort tracks contract completeness, exactly as tier does** — so it is one derivation, not two.
The splitter's declared completeness sets both.

| Kind / contract shape | Effort | Why |
|---|---|---|
| `split`, `preflight` | high | Search over partitions satisfying four tests at once. One call per subtree — the cheapest place in the system to think hard. |
| `execute`, complete contract | minimal | The edit is enumerated. Thinking is pure cost. |
| `execute`, prose contract | medium | The edit is derived from intent. |
| `execute`, constraint contract | high | Deriving a rule domain from a stated semantic **is** the reasoning task. |
| `verify` on summaries | medium | Comparison. |
| `verify` on diffs | high | Holds intent against code. |
| `re_verify` | low | Verdicting specific claims against specific evidence. |
| `integrate`, `digest` | minimal | Mechanical. |

### 2.0.1 Why effort matters more here than in a chat

**Reasoning substitutes for turns**, and turns are unusually expensive in this architecture.

R28 says weak models take two to three times the turns. R36 says the real cost is turns × check
latency, and the worked run put check latency at 42% of compute wall clock — where a single turn
costs a container, an environment clone and a module install.

So the trade is more tokens inside one call against fewer trips through an expensive check loop.
**In an interactive session a turn is nearly free and that trade is marginal. Here it is
favourable.** R28's mitigation should therefore read *raise effort first, tier up second* rather
than *tier up*.

### 2.0.2 The risk nobody has measured ⚖

A model handed an ambiguous instruction does not stop and ask — it resolves toward the modal answer,
confidently. That premise sits under ADR-0001 and under refusal being a first-class outcome.

**More reasoning may make this worse.** A model with room to think can construct a better
justification for a plausible-but-wrong reading rather than surfacing the ambiguity. If so, high
effort would depress both the refusal rate and `decided` population — degrading the two signals the
design most depends on, while every visible metric improves.

Cheap to test: E2 arm C already measures whether `decided` arrives when it matters. Run it at two
effort levels. One extra prompt, and if effort suppresses refusal it is worth more than the rest of
E2.

### 2.0.3 Reasoning traces

Bulky, never queried, so they go to the content store under core §4.3's truncation policy — but
**asymmetrically: keep the full trace only for non-`ok` outcomes.** The reasoning behind a refusal
or a `needs_context` is exactly what the record wants, and those are a small fraction of cards. A
successful transcription's trace is noise.

### 2.1 Tier on contract completeness, not propagation

v2 tiered on how far a mistake propagates. That is right for `split` and `verify`. For `execute` it
is incomplete, because the cost model assumed cheap leaves are cheap and measurement says a cheap
model on a prose contract takes two to three times the turns — costing more overall.

| Contract shape | Tier |
|---|---|
| Names the exact edit — signatures, values, sites enumerated | cheap |
| Prose describing intent; the executor derives the edit | middle |
| Requires judgement across files, or is a constraint rather than an instruction | strong |

**Second-order benefit:** the splitter has an incentive to write complete contracts, because a
complete contract is a cheaper child.

**Behavioural is not a contract shape** (ADR-0008, rule 138). Shape asks how much of the edit the
executor must derive, and sets tier and effort. Behavioural asks whether correctness needs a test, and
is answered by `check_spec`. The two often coincide, but neither decides the other: a QWeb layout is
prose with no test, and a behavioural implementation behind a pre-written test can be cheap. A test
card is `execute` with `expect: FAIL`; its implementation card is `execute` with `expect: PASS`.

**The declaration is checkable.** A child declared complete whose contract contains a placeholder
fails a mechanical scan. A child declared complete that then takes eleven turns is a metric row.

**What would change this:** turn count by tier and contract completeness, measured from run one. If
declared completeness does not predict turn count, the declaration is decoration and tiering falls
back to card shape.

### 2.2 Retry escalation — three rungs, not two

With effort as an axis, escalation gains a cheaper middle rung than rule 68 currently has:

```
attempt 1 → base model, base effort
attempt 2 → same model, RAISED EFFORT          ← new; cheaper than a tier bump
attempt 3 → tier up + fresh-eyes framing       ← the current rule 68
```

Rung 2 is the one that follows from §2.0.1: if turns are the expensive thing, buy fewer turns before
buying a bigger model.

Effort and layer 7 count **evidence** attempts only: those whose failure says something about the work (rule 147,
ADR-0013). An outage, a dead worker, a stall or a parked outcome should not raise effort, and a retry after one keeps a
byte-identical prompt. **The tier-up rung is positional:** the last delivery escalates whatever came before, because
identical retries of a work-caused crash would otherwise repeat exactly. A free flip never escalates.

**At the tier ceiling, escalation becomes a fresh-eyes framing in the retry context** — prior
attempts' check output plus *two prior attempts; read their failures; you own this now*. Without
that, rule 68 is a no-op for exactly the cards that needed it most. A kind's ceiling is the highest
tier a role claims for it (§1.3), so `re_verify`, `integrate` and `digest` start at theirs, and a
raised card never lands on a tier nothing claims.

**What would change this:** reasoning tokens against attempts saved (core §9.2). If raised effort
does not reduce attempts, rung 2 is pure cost and the ladder returns to two rungs.

---

## 3. Decomposition

### 3.1 Depth ⚖ — ship flat

A comparable shipped tool runs a one-level plan and handles multi-week work by writing more plans,
each producing working software.

Depth here exists to serve the compounding-fidelity argument, and **the per-level fidelity rate is
assumed, not observed, anywhere in this design.** So: ship flat.

This costs nothing to un-cut, because recursion is a **behaviour**, not a structure — an executor
that refuses and becomes a `split` (ADR-0013) deepens the tree with no new structure. Depth arrives the
first time a card genuinely refuses.

Consequences: `verify_at` becomes `[leaf, root]` rather than a ladder; the too-deep problem
disappears; the vanishing-subtree and silent-sequencer failure modes shrink to sibling scope.

**What would change this:** a measured per-level fidelity rate on real subtrees. Until that number
exists, depth is unjustified.

### 3.2 The leaf criterion

The operational test is not *is the check stateable* — a model can pretend to answer that. It is:

> **Could a reviewer sensibly accept one and reject its neighbour?**

If the acceptance decision is the same for both, they are one card. Fold setup, configuration,
scaffolding and documentation into the card whose deliverable needs them.

### 3.3 Patterned work is one child ✓

When the same small edit repeats across sites — one constant, one import, one field, one call
signature — that is **a single child whose contract enumerates every site.** Not one child per site,
and not levels of grouping to satisfy a child limit.

This is also the cleanest answer to the too-deep problem: a child limit stops forcing artificial
depth, because patterned breadth never reaches it.

### 3.4 The four tests a split must pass

1. **Independence** — declared touch sets are disjoint (§3.5).
2. **No talking** — no contract refers to a sibling. The executor cannot read it. Everything a
   sibling needs is written into its own contract.
3. **Retry safety** — a failed attempt leaves nothing a retry would corrupt, or the card is marked
   `retry_safe: false`.
4. **Coverage** — the children account for exactly the parent.

Test 4 is the splitter checking its own work in the call that produced it — which is the
configuration that produces ratification. `preflight` (§3.7) is the adversarial version.

### 3.5 Declared independence, checked twice

**Emit-time**, in the split gate, no model call:

- touch-set intersections
- namespace ownership collisions — id prefixes, declared names, declared fields
- every `consumes` symbol resolves to some sibling's `produces`, with an edge
- placeholder scan over contracts and check specs
- single-`execute`-child splits rejected (the kind ratchet, §4.1)

**Commit-time**, host-side, unreachable from the card: the diff's actual paths and namespaces
against what was declared.

The commit-time half reports fact rather than prediction, so it cannot false-reject and stays a gate
even if the emit-time half is demoted to a warning.

**The commit-time touch-set hook was among the highest-firing mechanisms in the worked run and one
of the cheapest in the design.** That ratio is the argument for principle 4 of core.

### 3.6 `interfaces` — the third model-free detector

Each child declares `consumes` and `produces` in exact symbols. Nothing in this design ever holds
two sibling contracts at once after the splitter walks away, so sibling incoherence otherwise
surfaces at `integrate` — late and expensive, which is exactly what declared independence prevents
for paths and leaves unprevented for symbols.

The check is string membership plus a reachability check.

**What would change this:** if declared symbols are wrong often enough to false-reject valid splits,
demote to a warning. Unlike touch sets there is no commit-time version that reports fact, so this
one has to earn its place at emit time or not at all.

### 3.7 `preflight` ⚖

Built only if E1 shows conflicts the mechanical checks miss (§11). A card emitted with the children,
which the children depend on. Its output is a **table, not a
verdict**: one row per sibling pair sharing a path or a symbol, naming what one produces against
what the other consumes and what was found. A clean verdict without rows is not a scan that ran.

It catches semantic mismatch that path and symbol checks cannot: sibling A produces what sibling B
consumes, with matching names and types, in an incompatible shape.

**The cost is real and must be stated:** it serialises the fan-out behind one card. In the worked
run it found something genuine and blocked eleven children behind a human gate for twenty minutes.

**Amendment:** preflight blocks only the children implicated in a finding, not all of them. That is
a `deps` change, not a new mechanism.

**What would change this:** if three sampled decompositions show no conflicts that the path and
symbol checks miss, record it as considered-and-declined with the numbers attached.

### 3.8 Test cards before implementation cards ✓ — load-bearing

Where a behaviour has a stateable semantic, the split emits **a test card, then an implementation
card depending on it**. The test card's check is that the test runs and **fails**. The
implementation card must not name the test file in its touch set, and the commit-time hook enforces
that.

This gives the property nothing else provides: the check was written by a different card, at a
different time, with different context, and the implementing card cannot edit it.

**Why this is marked settled rather than assumed.** In the worked run, a security rule with an
inverted domain passed the static check, the load check, introspection, the summary read **and** the
`decided`/`open_questions` pair. Five mechanisms, five passes, on a rule that inverted a regulatory
constraint. Only the separately-written test caught it.

**Therefore:** a split that fails this is a hard rejection, not a warning.

---

## 4. Refusal, drift and verification

### 4.1 Refusal is a first-class outcome ✓

The terminal outcomes:

| Outcome | Means |
|---|---|
| `ok` | done as contracted |
| `done_with_concerns` | done; self-flagged doubt or an out-of-scope observation |
| `expanded` | decomposed rather than executed |
| `misclassified` | wrongly typed or wrongly sized; the card becomes a `split` on the same row |
| `needs_context` | correctly sized and typed; **missing facts** |
| `spec_conflict` | the specification cannot work as described, or the contract mandates a defect |

The sketch's `blocked` and `refused` are refusals too, and the harness assigns `exploration_cap` and `schema_violation`.
Each lands in one state (ADR-0013):

| Outcome | State |
|---|---|
| `ok`, `expanded`, `done_with_concerns` | `done`, if the oracle allows it (rule 145) |
| `needs_context`, `spec_conflict`, `blocked`, `refused` | `awaiting_review` |
| `misclassified` | back to `pending`, as a `split`. A `split` reporting it goes to `awaiting_review` |
| `exploration_cap`, `schema_violation` | `failed` |

`needs_context` and `done_with_concerns` are the two additions, and both earn their place cheaply.

**`needs_context`** is categorically different from `misclassified`. Conflating them sends a
re-split where a re-dispatch with two extra sentences was needed. Its count per root intent is also
the only direct measurement of root-intent quality available — the one outcome that is feedback on
the human rather than on the system.

**`done_with_concerns`** is a one-bit commission signal that arrives **without** `decided`'s blind
spot: an executor that noticed it was unsure is exactly the executor `decided` catches, but the bit
costs one enum value instead of a schema, a prompt section, a splitter counterpart, a set-difference
check and an echo detector. It does not replace the pair; it is the free lower bound on it.

In the worked run it routed a correct out-of-scope observation into a gap card, where without it the
observation would have been either a silent omission or an out-of-scope edit.

**The kind ratchet.** A card's kind ratchets toward `split` and never away. A splitter emitting
exactly one `execute` child carrying the parent's intent is the same misclassification laundered
through a level, and it is a structural detector: one row count and a similarity check.

### 4.2 Verify's input is a config axis ⚖ — the central open question

```yaml
verify:
  input: summaries | touch_set_diff | both
```

**The framing v2 got wrong.** The axis is not cold-versus-informed review. A comparable tool's
reviewer is given the report *and the diff*, and is explicitly told to treat the report as unverified
claims — including that a stated rationale never downgrades a finding. They found the ratification
failure and patched it. The real difference is **summary-versus-artifact**, and they never gave up
the artifact; they bought the context economics back with out-of-band file handoff, which is this
design's content store arrived at independently.

**Consequence for ADR-0001.** The `decided`/`open_questions` pair is a proxy for information the
diff contains directly. The ADR is not reversed — its frame is widened, and diff-reading is added as
an alternative and as a mind-changer.

**What would change this:** the arms in §7.2. If diff-reading detects commission at a rate
summary-reading cannot approach, at a cost the leaf touch set bounds, the pair demotes to splitter
feedback and this axis is decided.

### 4.3 Where a computed oracle exists, it beats both

Where a domain admits schema-conformance introspection — a declared anchor diffed against what was
actually built, in SQL, with no model call — commission drift on the structural half is mechanically
detectable, and the pair is redundant there.

This is worth stating plainly because v2 framed it as a fallback: **the fallback position is
stronger than the general mechanism, wherever it is available.** Which is why core §1 states what
this is for as a property rather than a domain.

### 4.4 Three output channels ✓

| Channel | Becomes | Resolved by |
|---|---|---|
| `gaps` | ordinary cards | the harness |
| `unverifiable` | notes, surfaced at the digest and the human gate | whoever holds cross-card context |
| `minor` | a deferred list carried to the root gate | the final gate, which must take it as input |

**A verifier never widens its own scope.** A verifier with one output channel will widen scope to
fill it. In the worked run the `unverifiable` channel immediately prevented a card asking an
executor to prove something about a third-party library's concurrency semantics with a touch set of
one file.

### 4.5 `re_verify` ✓

A gap becomes a card; without a re-verification shape either nothing re-checks it, or a fresh cold
verifier re-reads the whole subtree — which is expensive and **non-convergent**, because a cold
verifier over a subtree that already passed will find new things.

Scoped:

- verdict **each prior finding** — ADDRESSED or NOT ADDRESSED, with evidence. *Attempted is not
  addressed.*
- inspect **only the fix diff** for new breakage
- anything outside it goes to observations — ledgered, non-blocking, never extending the loop

Emitted by the `verify` gate alongside the gap cards, depending on them, in the same transaction.

**It also supplies a round counter, and therefore a cap.** Without it the verify loop is unbounded.
Adjudicate only at the cap; adjudicating earlier is pre-judging under another name.

### 4.6 No party grades work done under its own instruction ✓

The verifier compares against the **root intent**, not the contract — so a contract that mandated
something wrong cannot excuse the result. That is held for free here and is worth recording.

The executor-side half: a card whose **contract** mandates something its own check spec or the house
preamble treats as a defect emits `spec_conflict` rather than complying quietly. A defect the plan
itself mandated is still a defect; the plan does not grade its own work.

---

## 5. Context

### 5.1 The layer stack

| Layer | Content | Cache scope |
|---|---|---|
| 0 | role, output contract, refusal rules, the outcome enum | kind |
| 1 | house preamble — conventions, banned patterns | house |
| 2 | skills for this kind, with their rationalization tables | kind |
| 3 | tools | kind |
| 4 | **generated** orientation + the root intent's CONSTRAINTS **verbatim** | run |
| 5 | the card's contract, ownership and interfaces | card |
| 6 | dependency summaries + retrieved artifacts | card |
| 7 | previous attempt's check output, on retry | attempt |
| 8 | definitions of the rungs the card may see | kind |

**Layer 4 is a query, not prose**, wherever the domain permits it — generated from the environment
rather than summarised. More accurate than any prose summary, cacheable per run, costs a script.

**The CONSTRAINTS block is copied verbatim and never paraphrased.** It is the verify jig's attention
lens.

**Layer 2 sizing ⚖.** Cache scope amortises **price**, not **attention**: a pinned skill set is
written once per pin and read by every call of that kind. Telling a model where to look makes it
look there and, plausibly, marginally less elsewhere — so a large set may degrade the cards it was
not written for while every cost metric looks fine (R50). Every kind's set is therefore kept
minimal, `verify`'s shortest. The measurement is per-set ablation against cards the set was not
written for, and it is the load-bearing uncertainty in layer-2 sizing.

**Skill sets are per-kind, chosen by hand at pin time**, in a file of about six lines that joins
`config_hash`. Nothing computes them: a chooser is core §3.4's deleted router returning. Each skill
ships paired with the RED case that motivated it, which assigns its kind, supplies the ablation
test, and makes it removable — without the pairing a corpus grows by accretion and nothing records
what any file was for.

### 5.2 Named-risk retrieval ✓

Retrieval must **cite the risk that justified it**, one focused check per named risk, and the
citation lands in the summary. This makes just-in-time retrieval auditable — you can query which
cards retrieved what and why — and it supplies a structural detector: retrieval with no named risk.

**The harness may also add a file to layer 6**, but only from a hand-written table keyed by kind, on a
trigger that is a declared field of the card, with the table and files in `config_hash` and each firing
recorded with its risk (ADR-0010, rule 139). It is built when a RED case asks for it.

### 5.3 Two-tier reporting

Full report to a file at a path the harness names; status, a one-line check summary and concerns
come back inline, under fifteen lines. This makes the ceiling a contract rather than an aspiration.
Elsewhere, a dispatch that accumulated pasted history reached 42k characters of which almost all was
history — the failure this prevents structurally.

### 5.4 What is banned from context

Prior-task summaries beyond declared dependencies. Session history. Anything a card did not need to
do its own job. The intent size cap in core §4.1 enforces the floor.

---

## 6. Enforcement

**Reduced to one section, deliberately.**

The principle survives: **enforce structurally rather than trust a declaration.** The elaboration
does not.

What ships: **container + network deny + read-only mounts + host-side commit hooks.** A comparable
tool's entire isolation story is a git worktree, and it has survived a large user base. The container
adds a pinned runtime and a kill handle, which core §5.4 needs.

What is **absent, not deferred**: per-tool quota, side-effect layer, in-card approval, fail-closed
table. These were speculative elaboration of a sound principle, and elaboration-without-evidence is
the failure the whole v2 rewrite was correcting.

`tool_audit` stays: what was attempted, including denials.

**What would change this:** a card writing outside its workspace. That is a containment failure and
it reopens the section — with evidence attached.

---

## 7. Experiments

Three problems stay separate: **the harness worked**, **the jigs worked**, **the output is good.**

### 7.1 Sequencing — E3 first

Run the baseline before the paper experiments. It is a five-minute install, it resolves the
overkill risk on real work rather than in argument, and it is the cheapest way to observe
diff-reading review in operation — which is what E2's decisive arm is trying to simulate.

### 7.2 E2 — the verify axis ⚖

| Arm | Verifier input | Measures |
|---|---|---|
| A | summaries, `decided` empty | baseline |
| B | summaries, `decided` populated | whether the field helps |
| **D** | **the card's `touch_set` diff** | **what summary-reading costs** |
| E | a computed oracle diff, structural specimen | whether triage works when detection is free |
| C | real executor, ambiguous contract | whether `decided` arrives |
| C′ | **same, at a second effort level** | **whether reasoning suppresses refusal (§2.0.2)** |
| Control | clean set through each | false-positive rate per input type |

**Arm D is the control the design has been missing.** Without it, a poor result in A and B is
uninterpretable — you cannot tell whether commission is undetectable *in principle from this
subtree* or merely *from summaries*.

**Use a real specimen**, small and well-framed: a security rule whose domain is inverted by one
operator. Four lines of diff, one sentence of intent. If arm D fails on that, summary-reading verify
is decoration on the behavioural half and the design should say so.

### 7.3 E1 — the splitter

Add two things v2's version lacks:

- **A RED pass**: run the root intent with no split jig, three samples, record what a strong model
  does unprompted. That is the baseline the jig is written against.
- **State what is varying across the samples, and why.** Three samples at one config measures
  *sampling stability* in the jig. Three samples across different models or effort levels measures
  *agreement*. These are different experiments and E1 currently does not distinguish them. Vary the
  model; if you also want the stability number, run the seed-varied set separately and label it.
- **A human-authored control**: run a plan-writing tool on the same intent and diff its
  decomposition against the splitter's. E1 currently scores three model samples against each other
  with nothing independent to anchor on.

Measure: check-spec executability · touch-set intersections · ownership collisions · symbol
resolution · whether behavioural cards are paired with test cards · whether contracts cite the
anchor or paraphrase it · `open_questions` populated.

### 7.4 E3 — the baseline

Not "a coding agent". A specific shipped pipeline: brainstorm → plan → subagent-driven development,
with worktrees, test-driven development, task reviews, a bounded fix loop and a final whole-branch
review.

**Record three numbers separately**: end-to-end wall clock, per-task quality, intervention count.
That tool never dispatches implementers in parallel — so a wall-clock win proves only parallelism,
which nobody disputes.

**The by-product may exceed the experiment.** A plan-writing tool's output carries Files, Interfaces
and a Global Constraints header. Run the emit-time gates against a **human-reviewed decomposition
that actually executed**. If they reject it, the gates are wrong — and that is far stronger evidence
than three model samples.

---

## 8. Writing root intents

The five headings: INTENT · DONE MEANS · OUT OF SCOPE · WHAT YOU SHOULD KNOW · SHAPE · CONSTRAINTS.

**DONE MEANS is a file where the domain permits** — an anchor that a check can be run against, not a
description.

**The lint**, mechanical, before the split:

- every CONSTRAINTS line names something the anchor can express or test
- no CONSTRAINTS line rests on a design section still marked open
- OUT OF SCOPE is populated
- the anchor passes its own lint and installs as a generated stub

In the worked run, both human gates on the critical path were foreseeable at authoring time. A
mechanical check moved earlier removes a human gate from the middle of a run.

**A model handed an ambiguous instruction does not stop and ask** — it resolves toward the modal
answer, confidently. That is as true of a splitter as of an executor, and it is why the lint exists
and why ambiguity has to be closed before the run rather than discovered during it.

---

## 9. Policy-level failure modes

Substrate modes are in core §10.

| Mode | Tell | Response |
|---|---|---|
| Quiet scope creep | diff touches paths outside the declared set | commit-time hook, host-side |
| Refusal loop | `misclassified` chains | none can form: a `split` reporting it goes to `awaiting_review` (ADR-0013) |
| Verify loop | gaps producing gaps | `re_verify` round counter and breaker |
| Echo | `decided` restates `open_questions` with no added specifics | structural: near-verbatim overlap detection |
| **Detector false positive** | mismatch flagged on a question closed upstream by an approved revision | `closed_by` on `open_questions`; the metric reports **unresolved** mismatches only |
| Second source of truth | a contract restates the anchor rather than citing it | a contract containing a field list that also appears in the anchor is a finding |
| Assembled-only breakage | each card passed alone; the whole does not | `integrate`'s check is a real check on the merged tree, not a clean merge |
| Oracle coverage bug | a computed check passes something it should catch | mutation tests on the oracle: mutate the anchor, assert it notices |

**The detector false positive is worth its own note.** In the worked run, ADR-0001's set-difference
detector fired incorrectly on the *first structural card*, because an open question closed by an
approved spec revision stays in the child's contract and can never be matched by any `decided`. The
raw metric would have read as alarming from run one, on good work — which is precisely the condition
the ADR lists as grounds for demoting the check. The fix is a join, not a judgement.

---

## 10. Positioning

**The honest comparison.** A shipped tool with a large user base does most of this today with a
controller: fresh implementer per task, task review after each, whole-branch review at the end,
model tiering, a bounded fix loop, worktree isolation, and a progress ledger file. Same problem,
same decomposition, opposite answer on who holds the plan. **It has run**; this has not.

**The genuine differentiator, stated narrowly:** the record survives the controller dying, because
there is no controller.

**Parallelism is no longer a differentiator.** *(Corrected 2026-08-18.)* It was, against the
sequential controller this section was first written about. It is not against Gas Town, whose
reconciler spawns one executor per routed work item up to a cap, each in its own worktree, claiming
atomically from a shared SQL store. Same shape as the claim protocol here, reached by a different
route. Parallelism is table stakes in this class of tool and should be argued as a *requirement
met*, never as an advantage held.

**The uncomfortable version, stated once.** If most of the value comes from disciplined skills,
test-driven development, review gates and worktree isolation — all of which they ship — then the
ledger is buying crash-safety and the record, and nothing else. Those are worth something. The
step-7 checkpoint decides whether they are worth the build.

**It got more uncomfortable, not less.** *(2026-08-18.)* With parallelism removed from the list,
one differentiator remains, and it is the one the first build is *for*. That is the correct
alignment — the primary hypothesis and the sole differentiator are now the same claim — but it
removes the fallback. If the record turns out not to answer questions the baseline's cannot, there
is no second thing this bought.

**OpenCode comes close to the differentiator.** *(Added 2026-11-04. Source: `anomalyco/opencode` at
`93f30ca`, read and not run; see `opencode-borrow-notes.md`.)* Core §13 asks for this to be said. Its
record survives the process dying, and a boot sweep resumes unfinished sessions up to a counted limit.
So "the record survives" no longer separates this design, and "there is no controller" has to carry
the claim. OpenCode recovers by resuming a controller and telling it to continue, and its sweep assumes
every orphaned claim's owner is dead, where attempts here are fenced. No equivalent of `intent_digest`
or `config_hash` was found by keyword search, which is not proof of absence. It has run, and this has
not. That leaves step 7's second question below. The DeepSeek note proposes narrowing this section to
typed questions across runs, and that is still undecided.

**Step 7 decides two questions separately:**

1. Cost and wall clock against the baseline.
2. Does the record answer questions the baseline's record cannot?

These can diverge, and the likely outcome is losing on the first and winning on the second. A single
threshold cannot express that.

**What the comparable's own failure modes show.** *(Added 2026-08-18. Source: Koleczek, "Turning
the Dark Factory Lights On", 17 Apr 2026 — an independent account of building three projects on Gas
City v0.13.4, not the project's own material.)*

Three observations, each landing on a position this design already took by argument. They are
recorded because *observed* is a different evidentiary class from *argued*, and step 7 should weigh
them as such.

1. **The inter-agent handoff protocol is not enforced by code.** A completing executor is
   instructed to stamp metadata and reassign the work item; if it skips a step the integrator
   rejects on a missing field, and if it exits without reassigning, the item sits orphaned in
   progress until a separate watchdog notices. This is rule 25's split — coaching in the prompt
   where a gate belongs in code — observed in a shipped tool rather than predicted. The equivalents
   here are host-side: the commit hooks and the fencing predicate, both unreachable from the card.

2. **Validation is not built in.** The account reports having to instruct the coordinator explicitly
   to confirm that merged work actually functioned. R25 and R29 observed: the gap between *it
   merged* and *it is right* is not closed by having an integrator role. §4's ladder and ADR-0001's
   pair exist for exactly this gap, and the comparable does not appear to carry even a self-report
   layer to fall short of.

3. **The integrator's merge workflow is declarative TOML handed to the agent as text**, with
   dependency and control-flow syntax functioning as prompt engineering rather than as executed
   control flow. The account names making it deterministic as the obvious improvement. That is core
   §3.4's router argument — routing is `WHERE kind = ANY($1) AND tier = ANY($2)`, inspectable in
   SQL, with no model call — arrived at independently from the outside.

**Cost is unresolved on both sides.** The same account names cost as an open problem in this class
of tool, with no numbers. Nothing here informs §8's tiering table or E2. It is a shared gap, not a
finding.

---

## 11. Build order above the substrate

Core §12 is the substrate. This is what follows, and **it is deliberately gated**.

**Before anything here:** core's Gate A.

1. Jig authoring, RED-first, starting with `execute` and `verify`.
2. The check ladder for the target domain, cheapest rung first and runnable standalone.
3. The computed oracle, if the domain has one — **with its own mutation tests.**
4. `split` jig, written against E1's RED pass.
5. `integrate`, whose check is a real check on the merged tree.
6. Gates: `verify`, `re_verify`, `digest`.
7. `preflight`, **only if E1 shows conflicts the mechanical checks miss.**

**Anti-milestones** — none of these is progress:

- a dashboard before the queries are painful
- a router
- notification
- a second content backend before the first is uncomfortable
- **a jig that grew a second stage** — that is a candidate split, not a feature (§1.5)
- depth before a measured per-level rate
- any mechanism that has never fired

**The standing caution.** In the worked run, what fired hardest was cheap and mechanical: the static
rung, the commit-time touch-set hook, the real check on the merged tree, and a test written by a
card that could not edit it. Three of those four are hooks. The most elaborate mechanism in the
design was outperformed on both halves of the work. That is one imagined run and proves nothing —
but it is the shape E2 exists to confirm or refute, and it is the reason principle 4 of core reads
the way it does.

---

## 12. What would change this document

Section by section, since that is the point of it being separate.

| § | Changes if |
|---|---|
| 1.3 Roles | E2 arm D settles verify's input — one `verify` role goes; a kind needs different tools by tier — tools return to the role (ADR-0008) |
| 1.4 Jig count | jigs start needing domain names in their filenames — content is misplaced, not the jig |
| 1.5 Multi-prompt jigs | the permitted patterns cover everything wanted — then `model_calls` is over-build |
| 5.1 Layer 2 sizing | per-set ablation shows a broad set narrows attention on unrelated cards (R50) |
| 2 Tiering | declared completeness fails to predict turn count |
| 2.0 Effort | reasoning tokens fail to buy attempts saved |
| 2.0.2 Effort vs refusal | E2 arm C′ shows high effort depressing refusal or `decided` |
| 2.2 Escalation | raised effort does not reduce attempts — the ladder returns to two rungs |
| 3.1 Depth | a per-level fidelity rate is measured on real subtrees |
| 3.6 Interfaces | declared symbols false-reject valid splits |
| 3.7 Preflight | three sampled decompositions show no conflicts the cheap checks miss |
| 4.2 Verify input | E2 arm D lands, either way |
| 4.3 Computed oracles | a generator can emit what the anchor declares — then the structural half is a hook, not cards |
| 6 Enforcement | a card writes outside its workspace |
| 7 Experiments | E3 resolves the overkill question on real work |
| 10 Positioning | controller-based tools acquire crash-safe records and parallelism |

**And one that applies to the whole document.** The purpose of the first build is learning and a
record. That purpose supplies no external signal to stop, which makes this the document most
vulnerable to elaboration — a mechanism can always be justified as another lesson. Version 1 failed
exactly this way. Rule 63 and the anti-milestones do more work now, not less, and the change register
exists partly to keep the accumulated total visible in one place.
