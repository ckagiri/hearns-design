# `thin-orchestration-fat-discipline` — where it fits

**Subject:** `thin-orchestration-fat-discipline.md`, 1,300 lines, dated 30 August 2026. Untracked
in git; absent from the README index. A curated skill library for coding agents, assembled from
four public packs.

**Question asked:** where does it fit relative to `harness-core-v3` and `harness-policy-v3`.

**Answer in one line:** it is **a different project against a different substrate**, whose live
relationship to h3 is that it is a refined version of **h3's own E3 baseline** — so it should be
kept separate, cross-referenced from policy §7.4, and not merged.

**Status of this document:** an assessment. It proposes no new mechanism. Every claim below is
either a quotation from one of the documents or a comparison between two of them.

---

## 1. The relationship

Four framings are available. One is the answer; two are partly true; one is false.

**"Two unrelated projects sharing a directory" — false, and policy refutes it.** §7.4 defines the
E3 baseline as:

> Not "a coding agent". A specific shipped pipeline: brainstorm → plan → subagent-driven
> development, with worktrees, test-driven development, task reviews, a bounded fix loop and a
> final whole-branch review.

That is a description of `obra/superpowers` — thin-orch's pack #1, whose pipeline thin-orch §2.1
renders as "brainstorm → worktree → plan → subagent execution → TDD → review → finish", and from
which §2.3 takes "pressure testing; verification gate; subagent execution; hook *mechanism*". The
two documents are joined at h3's control arm, and neither says so.

This is the load-bearing observation in this assessment. Policy §7.1 says **run E3 first**. Policy
§10 states the uncomfortable version: *"If most of the value comes from disciplined skills,
test-driven development, review gates and worktree isolation — all of which they ship — then the
ledger is buying crash-safety and the record, and nothing else."* Thin-orch is a design for making
that baseline better. Every improvement it lands raises the bar h3 must clear at step 7.

**"An inner layer of h3" — the weakest framing.** The instinct is that thin-orch describes what
goes in policy §5.1's layers 1, 2 and 8. It does not survive contact with the layer contract.
Layers are per-**kind**, pinned by hand at config-pin time, hashed into `config_hash`, and every
skill file ships paired with the RED case that motivated it (jigs P5). Thin-orch's skills are
per-**session**, human-invoked, description-triggered, and derived from curation. §5's denominator
below is what this framing actually buys.

**"A rival answer to the same problem" — partly true, but not a fair fight.** Core §1 puts
"anything that fits in one context window — use one window" out of scope. That window is
thin-orch's entire domain. They answer adjacent questions, not the same one.

**"Sibling documents, shared epistemics, incompatible substrates" — true, and the finding.** The
convergences in §3 are real, numerous, and were reached independently.

---

## 2. The zero-overlap fact, and why it is evidence

Thin-orch contains no h3 vocabulary at all: no card, jig, ledger, predicate, `config_hash`, tier,
or reference to either v3 document. Its every use of the word "harness" means an eval harness or a
host tool ("~12 harnesses", "one harness to start"). Core and policy never mention it. No document
in the repo mentions both.

The isolation is not a defect in the filing. It is what makes §3 worth reading. Independent
derivation is a different evidentiary class from consistency — which is the standard policy §10
applies to itself: *"recorded because* observed *is a different evidentiary class from* argued".
Two documents that never cite each other, built on incompatible substrates, arriving at the same
eight principles, is a stronger signal about those principles than either document arguing for
them alone.

*Aside, on the register.* The README index lists core at 852 lines; it is 898. It omits thin-orch,
both OpenDev documents, and `files/thin-orchestration-fat-discipline-v2.md`. Nothing since the
24 August commit is tracked. The index is stale, which is part of why this question needed asking.

---

## 3. Where they converge

Graded, because grading is most of the value. Listing eight convergences as equals would overstate
the case.

| Convergence | thin-orch | h3 | Depth |
|---|---|---|---|
| A mechanism must beat its baseline or be deleted | §4.4, §12.6, failure mode 17 | core principle 8: *"A mechanism that never fires in practice is a candidate for deletion, not a safety margin"*; policy §11 anti-milestones, "any mechanism that has never fired" | **Deep.** Both apply it reflexively to their own favourite mechanism — thin-orch §15.1 on the tripwire, policy §11's standing caution on its own most elaborate machinery |
| No router | §3, seven subsections | core §3.4 deletes Router by name; policy §5.1: *"Nothing computes them: a chooser is core §3.4's deleted router returning"* | **Deep.** Near-identical arguments — single point of failure, the error of the mechanism versus the error it replaces — from opposite substrates |
| Mechanical beats a model call | §4.2, §6.2 | core principle 4: *"Where a mechanical check and a model call cover the same ground, the mechanical check wins"* | **Deep**, and the same empirical shape: thin-orch's glob against policy §3.5's commit-time touch-set hook, *"among the highest-firing mechanisms in the worked run and one of the cheapest in the design"* |
| No self-grading | §8.9's EXTRACT step; failure mode 15, "adversarial theatre" | core principle 6: *"No party grades work done under its own instruction"*; policy §1.2, §4.6 | **Deep** — and thin-orch's EXTRACT (*"the reviewer must not inherit the chain of thought it is meant to attack"*) is a sharper statement of the mechanism than h3 has anywhere |
| Knowledge is never auto-promoted | §9.5, "deliberate and rare" | core §4.5: *"Nothing is promoted automatically… automatic promotion is how a lessons store fills with noise and stops being read"* | **Medium.** Same conclusion, but h3 ships `NullMemory`, so it is agreement about a thing one side does not build |
| Escalate on observation, not prediction | §4.3, §6.1 | policy §3.5, the commit-time half *"reports fact rather than prediction, so it cannot false-reject"* | **Medium.** Same principle, opposite placement: h3 host-side, thin-orch in-session |
| No compaction layer | §9.4, index not corpus — *"injecting bodies does not scale past ~30"* | core §3.4 deletes Compactor: *"Context is managed by splitting, not compressing"* | **Medium.** Different mechanism, same instinct about what context pressure does to trust |
| Anti-rationalization tables | §7.6 — **twelve rows, shipped** | policy §1.4 REFACTOR, policy §5.1 layer 2, jigs P3, rule 118 — **required in four places, instantiated nowhere** | **Asymmetric.** See §6 |

---

## 4. The real conflict: curation versus RED-derivation

The genuine disagreement is not architectural. It is epistemological, it is about how skill content
earns its place, and it lives in a document neither the question nor the obvious reading names:
`jigs-layers-skills-v2.md` is h3's *own* skill-library document, and it takes the opposite position.

jigs §3.6, "Your skills will not look like the 114", distinguishes the marketplace genre (pattern
documentation, tutorial-shaped, complete, "may change no output") from the RED-derived genre
(correction-shaped, short, specific, "changes a known output, provably"), and rules:

> The 114 files are a map of which failures a real Odoo shop hit often enough to write down. Worth
> reading for that signal. **Not worth pasting — inherited elaboration is still elaboration, and
> principle 8 applies to content you did not write.**

P10 states it as law: *"Version-delta content may be imported. Pattern documentation is derived
from a RED pass or not adopted."* P5: every skill file ships paired with its RED case. P6: a skill
whose RED case no longer reproduces on ablation is deleted, not kept as margin.

Thin-orch §1 states the opposite thesis in one line: **"The value proposition is curation, not
invention."** Eighteen skills assembled from four packs whose RED corpora, where they exist, belong
to other people and other repositories.

Both positions are defensible; they cannot both be house policy. The honest trade:

- h3's rule is safer and much slower, and it has so far produced **zero shipped jigs** — both
  drafts carry `0.1.0-GREEN-PENDING-RED` (jigs §3, line 129).
- thin-orch's rule is fast and produces a working library, and it accepts unmeasured content —
  which is precisely the failure R24, R43 and R56 name.

**The bridge already exists in thin-orch and h3 should take it.** §12.6's baseline comparison — run
the same fixtures with the mechanism disabled, and *"if the mechanism does not beat the baseline,
it comes out"* — is a cheaper substitute for a RED pass. It is core principle 8 made operational,
which h3 asserts in four places and never specifies how to run.

**A near-miss worth surfacing.** jigs §3.6's single import exception is the 24 version-delta files,
granted because they are a different genre: *"correction-shaped, bounded… asserts a fact"* rather
than a preference. Thin-orch's `references/` layer (§10 — five static, human-authored checklists:
OWASP, WCAG 2.1 AA, RED metrics, definition-of-done, testing patterns) is that same genre and
qualifies under that same exception. Neither document knows this about the other.

---

## 5. Landing sites, with an honest denominator

| Thin-orch part | h3 site | Verdict |
|---|---|---|
| `references/` checklists §10 | layer 2, or layer 1 house preamble | **PORTS** — same genre as jigs §3.6's version-delta exception |
| Anti-rationalization tables §7.6 | layer 2 beside their skill (jigs P3, rule 118) | **PORTS** — h3 has the slot specified four times and empty |
| Baseline comparison §12.6 | policy §7 experiments; core principle 8 | **PORTS as method** — principle 8 made runnable |
| `blast-radius.sh` §6.2 | core `pre_commit`, host-side | **SURGERY, then probably deleted.** Must move host-side to satisfy principle 5. On arrival it meets policy §3.5 — a touch set *declared per card* and checked twice, emit-time and commit-time — which is strictly stronger than a repo-wide glob, so it likely fails principle 8 immediately |
| `verification-before-completion` §8.6 ★ | layer 8 check ladder, commit hook | **REDUNDANT.** Core §5.7 makes commit a harness operation, not a card operation; the card structurally cannot claim done. Thin-orch's version is a table asking a model not to lie |
| `tdd` + `tdd_scope` §8.7 ★ | policy §3.8 | **ALREADY THERE, STRICTLY STRONGER.** §3.8 emits a *separate test card* the implementing card may not name in its touch set, enforced by the commit-time hook. Marked ✓ load-bearing on a worked-run incident where a security rule with an inverted domain passed five mechanisms and *"only the separately-written test caught it"* |
| Knowledge layer §9, three tiers | `notes` (ships as `NullMemory`) | **NO SITE as built** — see §6 |
| Orchestrators `align`/`plan`/`build`/`handoff` | — | **NO SITE.** `align` ≈ policy §8's root-intent lint plus the human gate; `plan` ≈ the `split` card; `build` ≈ the board itself; `handoff` is structurally unnecessary once the ledger exists — it is the problem core §1 claim 1 says the ledger solves |
| Session-start hook §5.1 | — | **NO SITE.** There is no session |
| Tiered escape hatch + `overrides.log` §11 | — | **REFUSED BY NAME.** Policy §6 lists "in-card approval" among what is *"absent, not deferred… speculative elaboration of a sound principle"* |
| Escalation table rows 2–6 §6.3 | — | **NO SITE.** In-card judgement; core principle 5 keeps trust-establishing checks hidden from the card |
| Three-tier eval harness §12.1–12.5 | policy §7's E1/E2/E3 | **RIVAL, not portable.** Different objects — skills versus jigs. Tier-2 description-collision detection has no h3 analogue and needs none: routing is `WHERE kind = ANY($1)`, so there are no descriptions to collide |

**Of eighteen skills, two port** — and both port as `references/` content rather than as skills.
Plus three mechanisms, one of which is likely deleted on arrival. That denominator is the strongest
available statement that these are different projects.

---

## 6. What each reveals about the other

Stated in both directions, because a one-way critique is advocacy.

**Against thin-orch: the tripwire is weaker than it looks.** Five of the seven rows in §6.3 require
in-session model judgement — scope surprise, recall hit, repeated failure, unverifiable assertion,
guidance conflict. Core principle 5 predicts these get argued away, and policy §10 records the same
thing observed rather than predicted: *"coaching in the prompt where a gate belongs in code —
observed in a shipped tool rather than predicted."* Only row 1 (the glob) and row 7 (test weakened
to pass) are mechanical, and thin-orch §15.1 already flags row 1 as possibly not beating baseline.
Compounding this, §8.8 makes `escalate` non-binding except row 7, and §11's anti-nag rule means a
waved-off signal does not re-raise for that class in the session — a documented bypass on the
mechanism that §15.4 admits is the only thing standing between `/build autonomous` and silent drift.

**Against h3: it specifies content it has never written.** Four places require anti-rationalization
tables — policy §1.4's REFACTOR step (*"each new rationalization gets an explicit negation in the
rule, a row in the rationalization table, and a red-flag entry"*), policy §5.1's layer 2, jigs P3,
and rule 118. The corpus contains no instantiated table; jigs line 210 shows a single illustrative
row inside a different discussion. Thin-orch ships twelve rows across two tables — and the last row
of its verification table (*"I'll run it once more to be sure"* → verification theatre as **padding**
rather than skipping) is a failure mode h3 has nowhere and would not have gone looking for, because
h3's entire design pressure runs toward enforcement. More broadly: thin-orch ships instantiated
content — twelve rows, five checklists, a config schema, a script — against h3's `PENDING-RED`, and
its stage 1 is "two skills, two checklists, and a free CI harness." By core principle 8, that is the
more disciplined document.

**On knowledge, both are right about different things.** Thin-orch §4.8 — *"Capture is worthless
without retrieval. A knowledge base nobody reads is a slower way of forgetting"* — correctly
identifies that h3's advisory memory is under-specified: `notes` ships as `NullMemory` with no
retrieval story. But h3's real answer is not `notes`. It is core §9.3: *"the card tree **is** the
plan, retroactively — structural rather than maintained, permanent rather than compacted, and
spanning runs because `project` is on every row"*, plus §9.4's lessons queries, which retrieve
across runs by SQL with `intent_digest` held fixed. Measured against that, `.agent/learnings/*.md`
is **a file maintained by discipline** — the exact artifact core §1 claim 1 says the ledger
replaces. h3 gets structurally, from `project` + `caused_by` + content-derived ids, a weaker-looking
version of what thin-arch builds by hand with confidence fields, decay windows and a noise-rate
metric. And h3 never has to ask thin-orch's §15.2 (does recall clear the noise bar), §15.9 (when
does the overlap check get expensive) or §15.10 (`.agent/` or `docs/`).

**h3 answers thin-orch's largest open question.** §15.11: *"Does any of this hold for teams?
Everything assumes one repo and one person's judgment. A learning written by one engineer and
surfaced to another has a trust dimension this document does not address. **Still the largest
gap.**"* h3 answers it structurally: every human action is a row in `reviews` recording what they
had open, what they chose and why; a note carries the task it came from *"so the derivation is
always recoverable"* and is *"superseded, never edited"*; multi-node claiming under `SKIP LOCKED`
is a team model. The trust dimension is provenance in a shared ledger — which is exactly what a
markdown file in one engineer's repo cannot supply. Thin-orch §15.10 is settled by core §4.4: never
deleted, because *"old runs are the asset."*

---

## 7. What to do

1. **Add one line to policy §7.4** naming thin-orch as the refined form of the E3 baseline. This is
   rule-63-legal: it specifies something being built now, since §7.1 runs E3 first. Not applied here
   — proposed.
2. **Keep thin-orch out of the h3 register**, as a separate project with its own README. **Rule 63
   does not reach it.** Core §1 puts "anything that fits in one context window" out of scope, and
   that is thin-orch's whole domain; it is not an h3 design document, so the rule against new h3
   design documents does not apply to it. Settled — not reopened here.
3. **Port the three items marked PORTS in §5** — the checklists, the rationalization tables, and
   §12.6's baseline comparison. Small, specific, and each fills a slot h3 has already specified.
   **§7A specifies how, in what order, and what would make each one fail.**

**Do not merge.** The substrate incompatibility is total — per-session against per-kind, one context
window against a ledger, a human router against a SQL predicate — and a merged document would be two
documents stapled together.

**Do not read §3 as validation of either design.** Both are unbuilt. Policy §10's discipline
applies: *it has run; this has not.* Two arguments agreeing is still two arguments.

---

## 7A. Executing the three ports

§7 item 3 names three items. This section specifies how each one lands, and what would make it
fail. The order matters: **the third port gates the first two**, for the reason §7A.0 gives.

### 7A.0 The obstacle, named first

All three items arrive from thin-orch **without RED cases**. jigs P5 requires that every skill file
ship paired with the observed failure that motivated it; P6 deletes any skill whose RED case stops
reproducing on ablation; P10 refuses pattern documentation that is not RED-derived. Taken at face
value, P5 and P10 block ports 1 and 2 outright.

They should not be waived, and they do not need to be. **§12.6's baseline comparison is the
substitute, and that is why it ports first.** jigs §3.4 says the RED pairing does three jobs: it
assigns the kind, supplies the ablation test, and satisfies principle 8. A baseline comparison
supplies the second and third directly — remove the content, rerun the fixture, see whether the
failure returns. What it does not supply is the *observed* failure, which is the first job and the
one that makes a RED case evidence rather than a hypothesis.

So the honest sequence is: port the method, use it to manufacture the missing ablation, and let the
result decide whether the content stays. Content that survives its own ablation has earned a
pairing retroactively. Content that does not is deleted under principle 8, which is the correct
outcome and costs nothing but the fixture.

---

### 7A.1 Port `§12.6` baseline comparison — the method

**Why first.** It is the gate on the other two, and it is the only one of the three that h3's own
documents already demand without specifying. Core principle 8 (*"a mechanism that never fires in
practice is a candidate for deletion, not a safety margin"*), policy §11's anti-milestone "any
mechanism that has never fired", jigs P6 and jigs §3.4's ablation box all assert the same rule.
None of them says how to run it. Thin-orch §12.6 does.

**Where it lands.** Policy §7, as a fourth subsection beside E1/E2/E3 — *not* as a new document,
and not as a mechanism. It is a procedure that existing rules already oblige.

**What to write.** Thin-orch §12.6's three measures, transposed from skills to h3's objects:

| Measure | thin-orch's question | h3 transposition |
|---|---|---|
| Outcome quality | Does the mechanism-enabled run satisfy more `expectations[]`? | Does the pinned-in run produce fewer non-`ok` outcomes on the same fixture corpus? |
| False-positive cost | How often does it fire where the baseline was already correct? | How often does the check reject a card the unaided run got right? Policy §3.5's emit-time/commit-time split already frames this — the commit-time half *"cannot false-reject"*, so only emit-time content is exposed |
| Token cost | Cost per invocation, amortised across runs where it does not fire | Layer-2 content is read by **every call of that kind** (jigs §2.1), so amortisation runs the other way: the cost is paid always and the benefit is occasional. This is R50 |

**The one line that must survive transposition**, because it is the whole point: *"if the mechanism
does not beat the baseline, it comes out."*

**How this differs from the per-set ablation policy §5.1 already names.** Policy's ablation measures
whether a pinned skill set *degrades cards it was not written for* — an attention question, R50.
§12.6 measures whether content *earns its place on the cards it was written for* — a value question.
Both are needed and they are not the same test. Say so explicitly when writing the subsection, or
the two will be conflated and only the cheaper one will ever run.

**What would make this port fail:** if writing the subsection produces a mechanism rather than a
procedure — a scorer, a harness, a threshold table — it has become elaboration, and policy §12's
warning applies to it directly. It should read as three questions and a rule, not as machinery.

---

### 7A.2 Port the `references/` checklists — content, into layer 1 or 2

**Why.** jigs §3.6 grants exactly one import exception, for the 24 version-delta files, on the
grounds that they are a different genre from pattern documentation: *"correction-shaped, bounded…
asserts a fact"* rather than asserting a preference. Thin-orch §10's five checklists — OWASP Top 10,
WCAG 2.1 AA, RED metrics, definition-of-done, testing patterns — are that same genre. They assert
facts and standards, they are bounded, and they are human-authored rather than model-generalised.
Thin-orch §10 is explicit that this is the distinction: references *"describe how things should be"*,
whereas patterns are *"agent-generalised from what happened here"*.

**Where each one lands — run jigs §2.2's placement tree, do not guess.** The tree asks two
questions in order:

- *Would it still be true if the domain were Terraform?* → **layer 0** (role/contract).
- *True of every repo doing this domain, or only this repo?* → **layer 2** (skills) / **layer 1**
  (house preamble).

Applied to the five:

| Checklist | Placement | Reasoning |
|---|---|---|
| `security-checklist` (OWASP) | **layer 2**, `execute` and `verify` | Domain-general within web/ERP work; true of every repo doing it, not only this one. Note `odoo-security` already occupies this slot in jigs §3.1 — reconcile, do not duplicate |
| `testing-patterns` | **layer 2**, `execute` | Pairs with policy §3.8's test card, which is where its readers are |
| `definition-of-done` | **layer 0**, not layer 2 | It is an output contract, true regardless of domain. jigs §2.2's first branch sends it to layer 0, and policy §5.1 layer 0 already holds "role, output contract, refusal rules" |
| `accessibility-checklist` (WCAG) | **defer** | No current kind consumes it. Importing it now is accretion — it fires on nothing |
| `observability-checklist` (RED) | **defer** | Same. Policy §11's anti-milestone "any mechanism that has never fired" applies before it is written, not after |

**Three of five, and two deferred.** Resist importing all five because they arrived together.

**Strip on the way in — P8 and P9 are mandatory.** Imported material has removed from it: anything
that spawns an agent (P8 — *"a card never emits its own reviewer"*, which kills thin-orch's
`adversarial-check` framing wherever the checklists reference it), and anything requiring network
access, version detection from generated files, or a decomposition decision (P9). Thin-orch's
checklists are pulled by skills that assume a session; that framing does not survive.

**Then run §7A.1 on each.** Ablate the checklist, rerun the fixture, keep what changes an outcome.

**What would make this port fail:** if the checklists arrive intact at tutorial length. jigs §3.6's
genre table is the test — *"complete, tutorial-shaped, long"* is the marketplace genre it refuses;
*"correction, short, specific"* is what may land. A checklist that is imported wholesale has failed
the exception it was admitted under.

---

### 7A.3 Port the anti-rationalization tables — rows, into layer 2

**Why this is the cleanest of the three.** h3 specifies this content in four places and has written
none of it: policy §1.4's REFACTOR step (*"each new rationalization gets an explicit negation in the
rule, a row in the rationalization table, and a red-flag entry"*), policy §5.1's layer 2 (*"skills
for this kind, with their rationalization tables"*), jigs P3, and rule 118. Thin-orch §7.6 has
twelve rows. The slot and the content exist on opposite sides of a directory.

**Where they land.** jigs P3 and rule 118 both say it: **layer 2, beside the skill they belong to,
except rows that survive a domain change** — those go to layer 1 or layer 0 by §2.2's tree. Not
layer 0 wholesale, and not a file of their own.

**Which rows survive the crossing.** Thin-orch's two tables are written for an agent in a session
that can *decline* to run a check. h3 removes that affordance structurally: core §5.7 makes commit a
harness operation, so a card cannot skip verification by rationalizing — there is nothing to
rationalize *to*. Rows that rebut skipping are therefore mostly redundant on arrival. Sort them:

| Thin-orch row | Crossing | Reason |
|---|---|---|
| "The change is straightforward, tests should pass" | **Redundant** | The card does not decide; the commit hook does |
| "I ran them earlier" / "Ten tickets in a row have passed" | **Redundant** | No session, no streak. Each card is fresh context |
| "The user said ship it" | **Redundant** | Policy §6 refuses in-card approval by name |
| **"The failure looks unrelated to my change"** | **PORTS → layer 2, `execute` + `verify`** | Survives. A card *does* triage its own check output, and this is the sentence it produces when it wants to stop |
| **"I'll run it once more to be sure"** | **PORTS → layer 2, `execute`** | Survives, and is the most valuable of the twelve — see below |
| "I'll write tests after the code works" / "too simple to test" / "it's a prototype" | **Redundant** | Policy §3.8 emits the test as a separate card the implementer cannot edit |
| **"The types already guarantee this"** | **PORTS → layer 2, `verify`** | Survives. A verifier comparing against root intent can talk itself out of a check this way |
| "I already know what the test will say" | **Redundant** | Same as §3.8 |

**Four of twelve rows port.** That is the honest number, and it is still four more than the corpus
has.

**The row worth the whole port.** *"I'll run it once more to be sure"* → *"After a clean run with no
intervening edit, re-running adds nothing."* Thin-orch flags it as pointing opposite to the rest:
verification theatre as **padding** rather than skipping. h3 has no equivalent anywhere, and would
not have gone looking, because its entire design pressure runs toward enforcement — every mechanism
in policy §6 and core §5.7 is built to stop a card doing *less*. Nothing is built to stop a card
doing the same thing three times and reporting diligence. That is a real cost with no detector, and
it arrives free with this port.

**Format.** Two columns, rationalization and rebuttal, as thin-orch §7.6 has them. Thin-orch §4.11
gives the reason the format matters and it transposes intact: *"'This is mandatory' is weak. Naming
the exact rationalization the agent is about to generate, and rebutting it, is strong."*

**What would make this port fail:** if the rows are written from thin-orch's table rather than from
observed h3 output. A rationalization table is a record of sentences a model actually produced. Four
rows imported on the strength of another substrate's observations are a hypothesis, and P5 is right
to want the pairing — so mark them as provisional and let §7A.1's ablation confirm or delete them.

---

### 7A.4 Sequence, and what each step costs

| # | Step | Cost | Gate |
|---|---|---|---|
| 1 | Write policy §7.5, the baseline comparison, as three questions and a rule | An afternoon. No tokens | Reads as procedure, not mechanism |
| 2 | Place `definition-of-done` in layer 0; `security` and `testing-patterns` in layer 2, stripped per P8/P9; defer WCAG and RED | A day. Reconcile `security` against the existing `odoo-security` entry | Nothing lands tutorial-shaped |
| 3 | Add four rationalization rows to layer 2, marked provisional | An hour | Rows sit beside their skill, not in a file of their own |
| 4 | Run step 1's comparison against steps 2 and 3 | Tokens, one fixture corpus | Anything that does not beat baseline comes out |

**Total surface added to h3:** one policy subsection, three checklist files, four table rows. Nothing
new in core. No new document, no new mechanism, no new kind — which is what makes the whole of §7A
rule-63-compatible: each item specifies something being built now, and each carries the ablation
that would remove it.

**The order is not negotiable.** Steps 2 and 3 without step 1 is exactly the accretion jigs §3.4
warns about — content in the corpus with nothing recording what it was for, and therefore nothing
that can ever remove it.

---

## 8. What would change this document

- **E3 is run and the baseline wins on all three numbers.** Thin-orch becomes the primary line and
  h3 becomes the experiment, inverting §1's framing entirely.
- **A retrieval story is specified for `notes`.** The knowledge-layer comparison in §6 stops being
  a contrast between a built thing and an unbuilt one, and thin-orch §9's three tiers become a live
  design input rather than a rival.
- **thin-orch acquires a non-interactive mode that is not `/build autonomous`.** The substrate
  incompatibility in §1 narrows, and the landing-site denominator in §5 changes.
- **A rationalization table is instantiated anywhere in the h3 corpus.** §6's asymmetry closes, and
  the second PORTS row in §5 loses its justification.
