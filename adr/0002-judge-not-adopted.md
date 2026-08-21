# ADR-0002: `judge` is not adopted

**Status:** Accepted (a deletion)
**Date:** 2026-08-17
**Supersedes:** `harness-design-v2` §7.6
**Guarded by:** the trigger in *What would change our mind*; core §3.4's list of absent roles

## Context

v2 §7.6 proposed a `judge` role: given several candidate artifacts for one card, select the best.
Its natural application was best-of-N generation — sample several decompositions or several
implementations, pick one — which is the standard use for sampling variation.

It was written as conditional from the start, gated on E1 showing structural disagreement between
splitter samples. E1 has not run. So the role was in the design as a plan rather than a decision,
and it was shaping other sections — the tiering table, the roles vocabulary, the config surface —
on the strength of an experiment nobody had performed.

Three further facts arrived after v2 was written.

**No comparable shipped tool has an analogue.** The reviewed controller-based system resolves ties
by a **recorded human ruling**, carried into the final message with what it costs if wrong. That is
a person deciding and being accountable, not a model selecting.

**It is the role most likely to become a router.** v2 said so itself. A component whose job is
choosing between things, given a growing set of things to choose between, is one refactor away from
choosing *which card gets which treatment* — and core §3.4 deletes the router explicitly, because
routing is `WHERE kind = ANY($1) AND tier = ANY($2)`, inspectable in SQL, with no model call.

**It never fired.** In the worked run, across twenty-two cards including a refusal, a
`needs_context`, a reap and three retries, there was no point at which two candidate artifacts
existed and something had to choose. The mechanism costs design surface whether or not it fires
(core principle 8), and this one fired at zero.

## Decision

`judge` is **not adopted**. It leaves the roles table, the vocabulary and the tiering discussion.
It is not deferred and it is not a stub; the design does not carry it.

Best-of-N generation goes with it, since `judge` was the only thing that made it coherent. This also
removes the last live use for per-card temperature variation, which is recorded in core §8.1.2.

## Alternatives considered

**Keep it deferred.** Rejected. A deferred section still costs reading attention on every pass,
still shapes schema decisions, and still gets built in month four on the strength of being written
down. The v2 rewrite existed to correct exactly this pattern.

**Keep it, gated on E1.** Rejected on ordering. E1 is now scoped around a RED pass and a
human-authored control, and its purpose is measuring splitter quality — not producing candidates for
a selector. If E1 shows disagreement, that is a finding about the split jig, and the first response
is to fix the jig, not to add a component that picks between its outputs.

**A human ruling instead.** **This is what is adopted**, and it already exists: the human gate's
five verbs, plus `decided` with `cost_if_wrong`, plus the Rulings query in the digest. A tie is a
decision made on the human's behalf, and the design's existing answer is that such decisions are
recorded exhaustively and surfaced. That is strictly better than a model selecting silently.

## Consequences

**Good.**
- One fewer role, one fewer tier row, one fewer config surface.
- Temperature stops being a live knob (core §8.1.2), which removes a parameter nobody could reason
  about and everybody would have fiddled with.
- The roles table stays short enough that adding to it is visibly a decision.

**Accepted costs.**
- Where two plausible decompositions exist and neither is obviously better, the harness has no
  automatic answer. It goes to the human gate. On a helper-shaped system that is acceptable; on an
  unattended one it would not be.
- Genuine quality gains from best-of-N, if any exist, are foregone unmeasured.

## What would change our mind

- **E1 shows splitter samples disagreeing structurally *and* the disagreement is not fixable in the
  jig** — i.e. the variance is irreducible rather than a prompt defect. Then selection is a real
  problem and this ADR is revisited. Fixing the jig is tried first.
- **A human gate becomes a measured bottleneck on ties specifically** — not on approvals generally,
  which are expected on a helper.
- **Best-of-N is measured to help.** It has not been. Measuring it does not require the role: sample
  N, have a human pick, and see whether the picked one beats the first one often enough to matter.
  That experiment is cheap and it is the honest precondition for reopening this.
