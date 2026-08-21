# ADR-0003: Enforcement collapses to isolation; notification is absent

**Status:** Accepted (two deletions with one shared argument)
**Date:** 2026-08-17
**Supersedes:** `harness-design-v2` §10 entirely; §13.3–13.7
**Guarded by:** the reopening trigger below; core §5.9; policy §6

## Context

Two sections of v2 were marked *deferred*. Both are here deleted, and they share a reason worth
stating once.

**Deferred is not a state a design can hold.** A deferred section still costs reading attention on
every pass, still shapes schema decisions — v2's commit path carried an `outbox` insert for a
notification system nobody had built — and still gets implemented in month four by someone who found
it written down and assumed it was agreed. Version 1 of this design failed by elaboration. Marking
elaboration *deferred* does not remove it; it removes only the obligation to defend it.

### Enforcement (§13.3–13.7)

§13.1's principle is sound and survives: **enforce structurally rather than trust a declaration.**
What followed it was a per-tool quota system, a side-effect layer, in-card approval, and a
fail-closed table — none of which had a triggering incident behind it.

Meanwhile the reviewed comparable tool's entire isolation story is a **git worktree**, plus a rule
that a reviewer is read-only on the checkout. That has survived a shipped 6.x and a large user base.

This design already has strictly more: a container (pinned runtime, cgroup limits, network deny) and
host-side commit hooks that the card cannot reach. The commit hooks matter most — the touch-set and
namespace checks run on the host, after the card returns, so they are unreachable from inside the
workspace. That is the same property that makes the check oracle hidden, applied to the structural
gates.

In the worked run the commit-time touch-set hook was among the highest-firing mechanisms and one of
the cheapest in the design. Nothing in §13.3–13.7 fired at all, because none of it existed.

### Notification (§10)

A notify/relay/outbox path so a completing card could wake a waiting worker rather than waiting for
a poll. It brings a table, a relay process, an at-least-once delivery story, and a new failure mode.
The poll loop it replaces is one query on a timer, and it has never been the bottleneck in anything
measured. `Relay` also occupied a slot in the roles vocabulary for a component with no work to do.

## Decision

**Enforcement is one section.** Container + network deny + read-only mounts + host-side commit
hooks + `tool_audit`. §13.1's principle stated; §13.3–13.7 deleted.

**Notification is absent.** Scheduling is poll-only. The `outbox` insert leaves the commit path, and
`Relay` leaves the vocabulary.

Neither is deferred. If either returns it will be as a new decision with evidence attached.

## Alternatives considered

**Keep both deferred.** Rejected, per the argument above. This ADR *is* the record, which is what
deferral was pretending to provide.

**Keep the fail-closed table only.** Considered seriously — it is the cheapest item in §13.3–13.7
and the most defensible. Rejected because a table mapping tool failures to outcomes is meaningless
without the per-tool machinery it was written against, and the general case is already covered:
`failure_class` plus the policy table plus quarantine.

**Build notification behind a feature flag.** Rejected. A flag is deferral with a code path, which
is worse than deferral with a heading — it has to be maintained and tested, and it will be enabled
by someone chasing latency that was never measured.

## Consequences

**Good.**
- Two fewer subsystems, one fewer role, one fewer table, one fewer insert in the hot commit path.
- The enforcement story becomes short enough to hold in mind, which is what makes it auditable.
- Scheduling has one mechanism, so its behaviour under contention is one thing to reason about.

**Accepted costs.**
- **Poll latency.** A card completing just after a poll waits up to one interval. At the
  contemplated scale this is noise beside model call time and check latency — which the worked run
  put at 42% of compute wall clock, several orders above poll interval.
- **No per-tool granularity.** A card that may write files may write any file inside its workspace.
  The workspace boundary is the granularity, and the commit hooks are what make it enforceable.
- **A card can still burn its own budget wastefully** within its lease. Bounded by the lease and the
  deadline, not by per-tool quota.

## What would change our mind

**Enforcement reopens if a card writes outside its workspace.** That is a containment failure, it is
observable, and the response should be sized to the actual escape rather than to the space of
imaginable ones. The reopening must name the incident.

**Notification reopens if poll latency becomes a measured fraction of run wall clock** — a
comparison against check latency and model time, not an assertion that polling feels wasteful. Given
the worked run's numbers, this would require the check ladder to get roughly two orders of magnitude
cheaper, which would itself be a large enough change to revisit much more than this.

**Neither reopens on the grounds that it would be more complete.** Completeness is the failure mode
this ADR exists to record.

## Amendment of 2026-08-18 — external evidence for §13.1's principle

§13.1's surviving principle is *enforce structurally rather than trust a declaration*. It was argued,
and the supporting evidence was one comparable's worktree isolation plus this design's own commit
hooks. Independent evidence has since arrived, and it is worth recording because this ADR's
reopening triggers are all framed around observation.

Koleczek's account of building three projects on Gas City v0.13.4 reports that its inter-agent
handoff is instructed rather than enforced: a completing executor is told to stamp metadata and
reassign the work item, and if it skips a step the integrator rejects on a missing field; if it exits
without reassigning, the item sits orphaned until a separate watchdog notices. The account names
making the workflow deterministic as the obvious improvement.

That is this ADR's argument observed in a shipped tool rather than derived. It does not change the
decision — the decision was already to enforce structurally — but it moves the claim from *plausible*
to *supported*, and it is the citation to reach for if anyone proposes reintroducing an instructed
step where a host-side hook exists.

**It does not license adding enforcement machinery.** §13.3–13.7 stay deleted. The reopening trigger
is unchanged: a card writing outside its workspace, named as an incident.
