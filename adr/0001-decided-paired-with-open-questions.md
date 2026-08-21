# ADR-0001: Commission drift is surfaced by a paired signal, not by self-report

**Status:** Accepted, frame widened 2026-08-17
**Date:** 2026-08-13 (amended 2026-08-17)
**Supersedes:** —
**Superseded by:** —
**Guarded by:** E2 arm C (§18.2); the `decided`/`open_questions` mismatch metric (§15.2)

## Context

The verify gate reads sibling summaries against the root intent and asks *what is missing*. That
reliably catches **omission**. It cannot, in principle, catch **commission**: a leaf whose summary
reads "replaced calls in invoice.py, tests pass" is indistinguishable from a correct one when the
replacement was semantically wrong in a way its own tests do not cover.

This matters because §1.1's compounding-fidelity argument — the justification for the whole
verification layer — is a commission argument. There is a gap between the problem stated and the
mechanism proposed.

A first attempt added a `decided` field to `result_summary`: the executor records what it resolved
that its contract did not specify, on the theory that commission drift lives in unspecified
choices.

That reasoning is sound and the fix is incomplete. §19 states that a model handed an ambiguous
instruction does not stop and ask — it resolves toward the modal answer, confidently. This is as
true of an executor as of a splitter. **Drift is resolving an ambiguity you did not register as
one**, so the cards most likely to have drifted are precisely the cards least likely to populate
`decided`. An empty array reads as "no choices were made" and is indistinguishable from "no
choices were noticed."

`decided` alone is therefore self-report from the party whose blind spot is the thing being
reported, and it has no detector — which violates rule 62.

## Decision

We will pair `decided` (executor-side) with `open_questions` (splitter-side): the split jig emits,
per child, the places it knows it underspecified the contract. The **set difference between them
is a detector requiring no model call** — a card whose splitter flagged an ambiguity and whose
`decided` is silent about it is a mechanically detectable commission-drift candidate.

The pair works not because either party is reliable, but because their blind spots are
**uncorrelated**: two parties, at different times, with different context.

We will not treat this as a settled mitigation. E2 arm C measures whether `decided` arrives when
it matters, and that arm is the only one that can falsify the decision.

## Alternatives considered

**`decided` alone.** Rejected: self-report from the party with the blind spot, and no detector.
Would have looked like a mitigation while leaving R25 open, which is worse than an acknowledged
gap.

**Verify reads a sample of bodies rather than summaries.** Not rejected — **deferred as the
fallback if E2 fails all arms.** It would work, at the cost of the context economics that justify
splitting in the first place. Entering it knowingly, after measurement, is different from adopting
it pre-emptively.

**Verify reads the card's `touch_set` diff rather than its summary.** *(Added 2026-08-17.)*
Distinct from body sampling above — it is not a sample, it is the diff of exactly the paths the card
declared, which the harness already knows and already checks at commit. Its cost is bounded by
`touch_set` size rather than by subtree size. **This is the configuration a shipped comparable tool
uses**, at leaf level, on a mid-tier model, with the diff handed over as a file path so it never
enters the controller's context.

The framing in the original decision was wrong in a way worth naming: the axis is not
cold-versus-informed review. Their reviewer is given the report *and* the diff and told explicitly to
treat the report as unverified claims — a stated rationale never downgrades a finding. They found
the ratification failure and patched it. The real difference is **summary-versus-artifact**, and they
never gave up the artifact.

Which means `decided`/`open_questions` is **a proxy for information the diff contains directly.**
Not rejected — this decision stands until measured — but the alternative is now on the record and
verify's input is a config axis (`summaries | touch_set_diff | both`) rather than a constant.

**A dedicated `audit` card re-reading each leaf's diff against its contract.** Rejected for now: it
doubles the leaf-level card count and strong-tier spend, and it is the same commission question one
level removed — the auditor also sees only what it is shown.

**Accept the gap and narrow scope** to work where leaf checks carry semantic weight — where a
passing check means the thing is *right*, not merely that it runs. Not rejected; recorded in §8.3
as the honest response if E2 fails all arms. If commission drift cannot be caught from summaries,
that is a property of the problem, not a flaw in this design.

## Consequences

**Good.**
- A model-free detector where previously there was none, satisfying rule 62.
- `open_questions` is independently useful: it is direct feedback on splitter quality, and E1 can
  measure whether splitters populate it before anything is built.
- The mismatch rate becomes a metric (§15.2).

**Accepted costs.**
- Two extra fields in the split and execute jig schemas, and prompt space in both.
- **A residual with no detector:** where *both* parties fail to notice the ambiguity, nothing
  catches it. This is recorded as failure mode §16.3 and is the honest limit of §8.3.
- A new degradation to watch: an executor echoing `open_questions` back into `decided` without
  resolving anything. Detected structurally (near-verbatim overlap with no added specifics), but it
  is a mechanism that did not previously exist.

**Follow-on work required.**
- `open_questions` in the split jig **before E1 runs** — E1 is the cheapest place to learn whether
  splitters populate it usefully.
- Set-difference check as a `pre_commit` hook.
- Echo detection.
- E2 arm C.

## What would change our mind

- **E1 shows splitters do not populate `open_questions` usefully** → the pair collapses to a single
  weak signal. Fall back to §8.3's two options rather than pretending the mechanism holds.
- **E2 arm C shows `decided` reliably arrives without the splitter-side prompt** → `open_questions`
  is optional polish; keep it for splitter feedback, drop it as a detector.
- **E2 arms A and B show no delta** → the gate cannot use the field at all, and the whole approach
  is wrong regardless of whether the field arrives. Go to body sampling or scope narrowing.
- **The mismatch rate proves uninformative in practice** — high mismatch on cards that turn out
  fine — → demote the check from a gate to a warning surfaced in the digest, per the same caution
  applied to `touch_set`.
- **E2 arm D shows diff-reading detects commission at a rate summary-reading cannot approach**, at a
  cost the leaf `touch_set` bounds → the pair demotes from detector to splitter feedback, and
  diff-reading becomes the design rather than the fallback. *(Added 2026-08-17.)*
- **A computed oracle exists for the domain** — schema-conformance introspection against a declared
  anchor, in SQL, no model call → the pair is **redundant on the structural half** and kept only for
  behavioural cards. Observed in the Odoo adaptation: this is not a retreat to a weaker position, it
  is a stronger one wherever it is available. *(Added 2026-08-17.)*

## Amendments of 2026-08-17

**1. `open_questions` entries carry an optional `closed_by`.**

The set-difference detector produced a **false positive on the first structural card** of the worked
run. An open question closed upstream by an approved `spec_revision` remains in the child's stored
contract and can never be matched by any `decided` entry, because the executor had nothing left to
decide. The hook cannot know that.

`closed_by` is written when a spec revision citing the question is approved. The set difference
excludes closed entries.

**2. §15.2's metric reports *unresolved* mismatches only.**

Without this the raw rate reads as alarming from run one, on good work — which is precisely the
condition this ADR lists above as grounds for demoting the check. The detector would have been
demoted on bad evidence.

**3. What the worked run showed about the case this ADR exists for.**

On the specimen that mattered — a record rule whose domain inverted a regulatory constraint —
`decided` was **empty**, and accurately so: the executor had not registered that it was choosing.
Five mechanisms passed the card, including this pair. The catch came from a test written by a
separate card that the implementing card could not edit.

That is this ADR's own reasoning observed rather than argued: *drift is resolving an ambiguity you
did not register as one*, so the cards most likely to have drifted are the least likely to populate
`decided`. The pair did not save it. Recorded here rather than in the consequences, because it is
evidence about the decision rather than a cost of it.
