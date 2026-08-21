# ADR-0006: A dependency is satisfied only by `done`, not by any terminal state

**Status:** Accepted
**Date:** 2026-08-20
**Amends:** core's readiness predicate — makes explicit something the design left ambiguous
**Guarded by:** rule 25; core §3.4 (no component holds a plan); principle 8

## Context

The readiness predicate makes a card claimable when its dependencies are complete. "Complete" was
never defined against the outcome vocabulary, and the two plausible readings diverge.

A card can reach a terminal state without having done its work. `blocked` means the executor could
not proceed without something outside its ownership. `failed` means it proceeded and the checks did
not pass. Both are terminal for the worker — the lease is released, the row stops being leased —
and both leave a `result_summary` describing an intention rather than an outcome.

If terminal is what satisfies a dependency, a child of a blocked parent becomes claimable and is
handed a summary of work that did not happen. `dep_summaries` renders `Exposes:` for an interface
that does not exist.

This surfaced while writing `dep_summaries`, not while writing the predicate, which is why it was
missed: the predicate reads a status column and the renderer reads a summary, and neither one is
where the contradiction is visible.

## Decision

**A dependency is satisfied only when its state is `done`.**

```python
SATISFIES_DEP = {"done"}   # not every terminal state
```

`blocked`, `failed`, `refused` and `exploration_cap` are terminal for the worker and **do not**
satisfy a dependency. Children of such a parent remain `pending` and unclaimable until the parent
is resolved.

`misclassified` does not arise here: it routes to `needs_review`, which is not terminal.

**A transitive-stall query ships with this**, because the decision is only safe if the stall is
visible:

```sql
-- cards pending with a blocked or failed ancestor
```

Written in Phase A of the prototype despite `digest` being cut, because without it the record cannot
answer *how much is this block costing*, which is the question the decision creates.

## Why the predicate rather than the renderer

**The child cannot recover.** A card whose parent is blocked is a card whose interface does not
exist. There is no useful attempt: the best available outcome is that it blocks too — after a
workspace build, a container spin-up, a template clone and a model call. Execute-card prices to
rediscover what the board already knew at claim time.

**Loud rendering is rule 25's anti-pattern.** Making `dep_summaries` print a warning is an
instruction the card is asked to honour rather than a state it was never given. The predicate is the
same gate for free, and it cannot be talked out of. This is the same argument that makes rule 135's
tool sets structural.

**It composes correctly.** Children left `pending` are exactly the set of work the block is costing,
visible in one query, and made claimable in a single transaction when the parent is resolved. Under
the permissive reading each would instead have been claimed and failed, consuming `attempts` on
failures that were structural rather than about the card — and `max_attempts` could quarantine them
before the parent was ever looked at.

**It is the cheaper mistake.** Requiring `done` and being wrong costs a stalled card a human
notices. Allowing terminal and being wrong costs money, an attempt, and a plausible summary built on
an interface that does not exist — which then propagates to that card's own children.

## Alternatives considered

**Terminal satisfies, and `dep_summaries` renders the difference loudly.** Rejected on the rule 25
argument above, and on a second: the loud rendering has to be *believed*, and a model reading
`Exposes: TodoStore.connect(dsn)` next to a warning has been given contradictory evidence about
whether the interface exists.

**Terminal satisfies, and the child's jig is told to check parent states.** Worse. It moves a gate
into prompt text and makes every card pay attention tokens for a condition the board can evaluate
in SQL.

**A per-dep policy — `hard` versus `soft` dependencies.** Genuinely tempting, and rejected as
premature. It is a real generalisation, but nothing in the design currently needs a soft dependency,
and adding the field now means every splitter must choose a value with no evidence about which. If a
concrete case appears, this is the shape to reach for.

**Let the splitter mark dependencies as optional.** Rejected: it is the per-dep policy with the
choice delegated to a model, which is a chooser, which is core §3.4's deleted router in miniature.

## Consequences

**Good.**
- A card never sees a dependency summary for work that did not happen.
- The cost of a block is a query rather than an inference.
- `attempts` stops being consumed by structurally-doomed cards, so the number keeps meaning what
  core says it means.

**Accepted costs.**
- **Partial blocks stall unnecessarily.** A parent that built its interface and then blocked on
  something unrelated has produced what its child needs, and the child waits anyway. This is the
  real cost and it is accepted deliberately: the alternative is asking the board to reason about
  *how much* of a parent's work landed, which it has no way to know. The right resolution is a human
  verb — review the blocked parent and either unblock it or split off what did land as a separate
  `done` card. A partial block deserves a person.
- **A blocked card can strand a subtree.** Mitigated by the transitive-stall query, not eliminated.
- **One more reason the review verbs matter earlier than planned.** The prototype cuts three of the
  five; a partial block is the first concrete case for one of the cut ones.

## What would change our mind

- **Partial blocks turn out to be common** rather than rare, and the human verb becomes routine
  work. That is the evidence for the per-dep policy, and it should be measured before it is built:
  count blocked parents whose children were later unblocked without any change to the parent's
  output.
- **The transitive-stall query is not enough to make stalls visible in practice** — then the
  decision is safe but unusable, and the fix is in the digest layer, not the predicate.
- **A dependency kind appears that is genuinely advisory** — a card that would benefit from a
  parent's summary but does not require it. That is a soft dependency and it reopens this.
