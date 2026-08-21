# Depth — an amendment to policy §3.1

**Status:** proposal. In-place edit to `harness-policy-v3.md` §3.1 plus two register entries. Not a
new design document; nothing here is a new mechanism.

**What it changes:** §3.1's conclusion mostly survives. Its *reasoning* does not, and the reasoning
is what determines what you measure. It also supersedes an earlier version of this argument I made
before the epic/story/card vocabulary existed — that version said ship flat and let depth arrive
from below. With three named tiers, that is no longer right as a default.

---

## 1. The compounding-fidelity frame measures the wrong variable

§3.1 rests on `p^d`: each level is a lossy retransmission, so depth multiplies error. That treats
every level as the same operation. It isn't.

A level that **partitions an already-crisp specification** loses almost nothing — it is bookkeeping.
A level that has to **invent structure the spec does not contain** loses a lot. The lossy operation
is resolving an ambiguity, not descending a level, and the two correlate only loosely.

Consequences:

- Two levels below a schema anchor can be *safer* than one level below a vague paragraph.
- A per-level fidelity rate averaged across both describes neither.
- The number §3.1 asks for — "a measured per-level fidelity rate on real subtrees" — is not
  measurable in the form it asks for it, because "level" is not the thing that varies.

**What to measure instead:** attempts-to-green and verify-gap count per card, against *how much the
parent contract had to invent*. Depth then falls out as a correlate rather than being the axis.

**The rule this gives you, which is a bound rather than a number:**

> **A split may go as deep as the specification supports, and not one level deeper.** A card that
> cannot be split without inventing facts is not a card that needs a deeper split. It is
> `needs_context` or `spec_conflict`.

---

## 2. Depth is given by the vocabulary, not chosen

This is the part that changes with epic / story / card.

The tiers are not three iterations of a generic split. They are three **named** tiers with different
semantics, and the difference is what a reviewer does at each:

| Tier | Emitted by | Review semantics | Artifact |
|---|---|---|---|
| Epic | the human, at intake | intake gate; you approve its stories | a milestone |
| Story | `split` on the epic | **you accept or kill it** | one branch, one PR-sized diff |
| Card | `split` on the story | `verify`, no human | one commit |

Depth 3 is therefore the *normal* shape, not an exception to be justified. And the too-deep problem
disappears structurally rather than by a cap: **below the card tier there is no name.** A splitter
asked to go a fourth level has no vocabulary for what it would produce and no reviewer semantics to
attach, so the correct outcome is refusal, not a smaller card.

That is a better guard than an integer, because an integer is a config axis someone will want to
tune, and this is a consequence of what the tiers mean.

**The cap still exists** — hard stop below card tier, `blocked` with a reason, loud. But it is a
circuit breaker against runaway emit, not a design position, and it should not be argued as one.

---

## 3. Depth-by-refusal survives, as the escape hatch

§3.1's observation stands and is the cheapest mechanism in the area: an executor that refuses and
emits a `split` replacement deepens the tree with no code change. With named tiers it has a narrower
job — it is what happens when a *story* was mis-sized, producing more cards, or when a *card* turns
out to be a story in disguise.

The justification is better than "it costs nothing to un-cut." It is the same asymmetry the design
already commits to in §3.5:

> A splitter choosing depth is **predicting** difficulty before contact with the repo. An executor
> refusing is **reporting** it after. Emit-time gates predict and can false-reject; the commit-time
> hook reports fact and cannot.

Depth-from-refusal is the commit-time version of the same idea. It should be argued that way,
because then it is a consequence of a principle rather than a convenience.

### The bias that has to be counterweighted

**Models are bad at refusing.** Attempting and producing something plausible is the lower-energy
path — the design worries about this elsewhere (R47). Left alone, refusal fires rarely, and you will
misread the resulting flat trees as the work being flat.

So the *absence* of refusal needs a detector, and the parts already exist:

> **A card that fails verify twice on gap-type findings is a refusal that did not happen.** Point
> the round-counter breaker at `split` rather than at a third attempt.

That converts a mechanism already being built into the thing that makes refusal actually fire.

---

## 4. Depth is the ledger's friend, and the design never says so

§1.5 makes this argument about multi-prompt jigs: a decision made in stage A and consumed in stage B
never becomes a row, and **intermediate state invisible to the ledger is the one thing this design
exists to prevent.**

That argument runs upward too. A card that is too big has its internal decisions invisible for
exactly the same reason. So flatness is not free — it buys fidelity at the cost of the record, which
is the *primary* claim, traded against a secondary one.

Which means the leaf criterion — *could a reviewer sensibly accept one and reject its neighbour?* —
is really a **ledger criterion**. Push depth to wherever separately-judgeable decisions stop
existing, and stop there. Not to a number.

Stated once, in §3.1, this also explains why the story tier is the review boundary: a story is the
smallest unit a human accepts or rejects, so it is the smallest unit whose acceptance is worth a row.

---

## 5. What to write into the design

**In-place edits to policy §3.1:**

1. Replace the `p^d` framing with §1 above. Keep the honesty about the number being unobserved;
   change what the number is.
2. State that depth is given by the epic/story/card vocabulary, and that depth 3 is the default
   shape rather than an exception.
3. State that the cap is a circuit breaker, not a position.
4. Keep depth-by-refusal, re-argued as predict-versus-report per §3.
5. Add the ledger argument from §4, cross-referencing §1.5.
6. Replace "what would change this" with: *a measured relationship between invention and fidelity*,
   not a per-level rate.

**Two register entries:**

- **R-new-7 — refusal may never fire, and flat trees will be misread as flat work.** Depth-from-
  refusal depends on a model admitting it was mis-sized, which is the same self-report R47 says is
  unreliable. Mitigation: the breaker-to-split rule in §3. Detector: count of `misclassified`
  outcomes per epic; a zero is a finding, not a success.
- **R-new-8 — "level" is not the variable, so a per-level fidelity rate would be a measurement of
  the wrong thing.** Mitigation: instrument per card against invention, per §1. Watch for: anyone
  proposing to measure depth directly.

**One ADR, if it is adopted:** *depth is bounded by the tier vocabulary, not by a configured
integer.* The alternatives — a config axis, a model-chosen depth, an unbounded splitter — each have
a named failure, and the decision is worth keeping its argument after the cap becomes invisible.

---

## 6. What would change this

- **Refusal essentially never fires against real work.** Then bottom-up is a nonstarter and you need
  a top-down splitter with an explicit depth budget. Worse, because it is prediction — but a worse
  mechanism that fires beats a better one that does not. Cheap to watch for: it is one count.
- **A fourth tier turns out to be needed** — something between story and card, or above epic. Then
  the vocabulary argument in §2 weakens and the bound has to come from somewhere else.
- **Invention and fidelity turn out not to correlate.** §1's whole replacement frame goes, and
  `p^d` was closer to right than this note claims.
- **Hierarchical integration proves more expensive than flat.** My instinct is that depth *reduces*
  merge pressure — conflicts scale with concurrent siblings, and a tree with fixed leaves has fewer
  siblings per parent — but this is genuinely uncertain and the pilot's day 3 is what would answer
  it.
