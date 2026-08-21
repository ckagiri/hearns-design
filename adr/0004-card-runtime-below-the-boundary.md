# ADR-0004: A library runs the card's tool loop, below the card boundary

**Status:** Accepted (an adoption, scoped by what it excludes)
**Date:** 2026-08-18
**Supersedes:** —
**Guarded by:** the disqualifying test below; core §8's cache guarantee; policy §1.6; R60

## Context

Policy §1.5 states that turns are not prompts: an executor makes many model calls per attempt —
read, edit, run the check, read the failure, edit again — and that is one prompt template driving a
tool loop.

**Nothing said what runs that loop.** Core specifies the board, the claim, the lease, the workspace
and the cache. Policy specifies jigs, tiering, effort, context and verification. Between the two
sits the thing that actually executes a jig inside the container, and no section owned it. It was
treated as an implementation detail of the executor role.

It is not a detail. The loop decides what the model sees, what it is able to touch, and what the
ledger learns about the attempt. Three of this design's load-bearing claims run through it:
`config_hash` answers *what system did this card run under*, core §8 promises replay with zero
outbound calls, and rule 25 wants gates in code rather than instructions in prompts.

Writing it from scratch is a real cost — provider handling, schema generation and validation, retry
semantics, streaming, tool dispatch — and none of that cost buys anything this project is trying to
learn. The substrate is the interesting part; the tool loop is table stakes that several libraries
already implement.

## Decision

**A library runs the card's tool loop. It lives below the card boundary and is used for nothing
above it.**

In scope: the model call, the tool loop, tool registration per role, and validation of output
against the jig's schema.

Out of scope, and this is the operative half of the decision: scheduling, retry across attempts,
persistence between cards, session resumption, and any durable-workflow capability the library
offers. Those are a controller under a different name. Core §3.4 deletes the router and the
controller by name; adopting one as a dependency would reintroduce it by category.

**The cache is implemented as the library's model interface**, not as a wrapper around the library —
a cache-backed implementation of the interface, wrapping the real one. Core §8 now records why: a
call path that bypassed the cache would have to bypass the model interface itself, which the runtime
has no way to do. Replay's guarantee stays structural.

**Pydantic AI is the adopted implementation.** It fits three requirements unusually well: the agent
is stateless with message history passed in explicitly, which is compatible with the board being the
only place state lives; `Model` is an abstract base class intended for subclassing, which is the
cache integration point; and structured output validation maps directly onto jig contracts, so
`summary_schema_version` becomes a version on a real schema rather than a convention. Tools are
registered per agent, which makes rule 135's per-role tool sets a constructor argument rather than a
mechanism to build.

**The choice of library is the weakest part of this decision and the easiest to reverse.** What is
being decided is the boundary. The implementation behind it is replaceable.

## The disqualifying test

**The runtime must expose the exact request bytes sent to the provider.** Core §8 keys the cache on
the rendered prompt, which means what the provider received — including the library's assembled
system prompt and its generated tool schemas — not the inputs handed to the library. This is rule
127's principle one layer down: hash the rendered artifact, not the thing that renders it.

If the runtime cannot expose that, it cannot satisfy §8, and no other property compensates.

**This is verified before Gate A, not assumed.** The `CachedModel` spike is scheduled ahead of the
substrate's gate precisely because a negative result invalidates the adoption while it is still
cheap to reverse.

## Alternatives considered

**Write the loop from scratch.** Not rejected on principle — it is 2–4 days and it removes a
dependency from `config_hash`. Rejected on what the days buy: provider handling and retry semantics
are solved problems that teach nothing about the substrate, and a hand-written loop would need its
own tests for behaviour the library already has. **This is the fallback if the disqualifying test
fails**, and the decision reverses to it cleanly because the boundary, not the library, is what was
decided.

**Shell out to a CLI coding harness** (Claude Code headless, or similar) as the executor. Rejected,
and it is worth saying why, because it is superficially attractive — an executor *is* a tool loop,
and these harnesses are good ones. Handing prompt assembly to a third-party CLI means no longer
knowing what the model saw, and `config_hash` exists to answer exactly that. It would also break the
cache as the determinism mechanism, remove control of the layer stack, and put the output contract
at the mercy of whatever the harness chooses to print. The context economics in policy §5 presume
this design renders the prompt.

**Adopt the library including its durable-execution capabilities.** Rejected. Those capabilities are
well built and solve a real problem — for someone whose durability story is not already a Postgres
ledger with leases and fencing. Taking them would mean two durability mechanisms with overlapping
responsibilities, which is worse than either alone, and the plan would move back inside a component.

**Defer the decision and keep the loop unspecified.** Rejected on the argument ADR-0003 makes at
length: deferred is not a state a design can hold. The loop is going to be built either way, and
leaving it unowned means it gets built implicitly, by whoever writes the executor first, with no
section to check it against.

## Consequences

**Good.**
- The gap between core and policy is closed, and policy §1.6 owns it.
- Rule 135's per-role tool sets become nearly free, which puts layer 3 on the same footing as layer
  2 and gives rule 25 a cheap structural win: a verify card that cannot write cannot fix what it
  reviews.
- Output validation against a real schema, with malformed output re-prompted — which §1.5 already
  permits as schema repair, now with an implementation.
- Roughly 2–4 days of executor-runtime work becomes 1–1.5 days plus the spike.

**Accepted costs.**
- **A dependency inside `config_hash`** (R60). A library upgrade changes prompt assembly, therefore
  changes what cards saw, with nothing in the design moving. Pinned in the lockfile; upgrades are
  run boundaries. This is a genuine new coupling and the honest price of the decision.
- **The library's effort abstraction is a trap** (R59). It normalises reasoning effort across
  vendors, which is convenient and is exactly the label whose meaning varies by provider. Rule 134
  applies unchanged: the resolved provider parameters enter the pin, never the abstract level.
- **A category of failure now belongs to someone else.** When the loop misbehaves the first question
  is whether it is our jig or their dispatch, and that is a slower question than it would be in code
  we wrote.
- Determinism still comes from the cache, not from the library. Its own documentation notes that
  temperature zero with a fixed seed is not fully deterministic, which is the correct expectation
  and the reason §8 does not rely on sampling settings.

**Follow-on work required.**
- `CachedModel` spike **before Gate A** — it tests core §8's guarantee, and that belongs before the
  substrate's gate.
- Executor runtime task in Phase 2, sized against the spike's result.
- Per-role tool sets as a sibling of `skills.yaml` (rule 135).
- Runtime version into the config pin and `config_hash` (R60).

## What would change our mind

- **The runtime cannot expose the exact request bytes** → adoption reversed, fall back to writing the
  loop. This is the disqualifying test and it is checked first.
- **A library upgrade silently changes prompt assembly and is not caught by the pin** → R60 is not
  mitigated, and the coupling is worse than the days it saved. Vendor the assembly or write the loop.
- **The durable-execution capabilities start being useful** → that is the signal that something has
  moved above the card boundary, and the thing to fix is whatever moved, not the boundary.
- **Per-role tool sets show no behavioural effect in ablation** → keep them as gates, which is their
  structural justification, and drop the attention claim. Recorded in policy §1.6 as the contested
  half.
