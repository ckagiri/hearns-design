# ADR-0005: The card runtime is hand-written, behind a provider port

**Status:** Accepted (an implementation reversal; the boundary is unchanged)
**Date:** 2026-08-20
**Amends:** ADR-0004 — the boundary stands, the adopted implementation does not
**Guarded by:** core §8's cache guarantee; core §11's hash-stability tests; rules 72, 107, 134, 135;
R60, R59
**Informed by:** a survey of pydantic-ai, LiteLLM, DeepSeek Harness and Flock, 20 August 2026

## Context

ADR-0004 decided two things and was explicit that they were separable: **the boundary** — a library
runs the card's tool loop, below the card boundary and nothing above it — and **the implementation**,
pydantic-ai. It said of the second: *the choice of library is the weakest part of this decision and
the easiest to reverse. What is being decided is the boundary.*

It also recorded the fallback: writing the loop from scratch, 2–4 days, reached cleanly if the
disqualifying test failed.

This ADR takes that fallback, and not because the disqualifying test failed. It has not been run.
It reverses on an argument ADR-0004 recorded as an accepted cost rather than a blocker, having
concluded that the cost is avoidable rather than accepted.

## Decision

**The card's tool loop is written here, in `harness/runtime/`, behind a provider port.**

Three layers, three owners:

| Layer | Owner |
|---|---|
| HTTP, retries, rate limits, error surfacing, request and response types | The provider SDK |
| Output schema definition and validation | pydantic v2 |
| Assemble → dispatch → append result → terminate → validate | This repository |

The boundary from ADR-0004 is unchanged. In scope: the model call, the tool loop, per-role tool
registration, validation against the jig's schema. Out of scope, unchanged and unchanged for the
same reasons: scheduling, retry across attempts, persistence between cards, session resumption,
durable workflow.

**The cache remains the runtime's model interface** — a cache-backed implementation of the port,
wrapping the real adapter. Replay's guarantee stays structural because a call path bypassing the
cache would have to bypass the port, which the loop has no way to do. This is ADR-0004's mechanism,
preserved.

**The port is neutral and typed, not shaped after a provider's wire format.** The adapter builds the
provider-native request; the loop above the port sees canonical types only.

**The cache key is hashed over the adapter's serialized output**, below the port, not over the
canonical request handed to it. Normalize the envelope; never hash the envelope.

**One adapter ships.** The second is written when something concrete requires it.

## Why the boundary survives and the library does not

**A dependency inside `config_hash` is avoidable, not merely costly.** R60 recorded it as an accepted
price: a library upgrade changes prompt assembly, therefore changes what cards saw, with nothing in
the design moving. Core §11 fails the build on a hash change with no version bump — so the defence
is pinning the library into the pin, after which upgrading invalidates every prior run's
comparability. That is a permanent hostage to another project's release cadence, at the exact layer
this design's replay guarantee rests on. Assembling the request here makes the rendered prompt a
local variable that moves when we move it.

**Retry semantics collide with `attempts`.** A library retrying on validation failure means
`attempts` — which counts deliveries and is bounded by `max_attempts` — undercounts real model calls,
cost accounting drifts, and a card that appears to have failed once failed four times. Retry is a
harness concern. Absent is easier to guarantee than configured-off.

**Rule 135 becomes structural rather than asserted.** Owning the dispatch table means a `verify`
card has no write tool because the table has no `write` key. There is no code path to test. Through
a library it is a constructor argument, which is a weaker claim.

**The portability being paid for has already been declined.** `roles.yaml` names one provider
family; the libraries' central value is breadth across many.

**P1-24 dissolves as a risk.** Its failure mode — hashing what was handed to the library rather than
what the library sent — has no analogue when the bytes are assembled here. The half day is not
skipped; it is repointed at the harder question, below.

**What ADR-0004 got right and this ADR keeps:** the boundary, the exclusion list, the cache as the
model interface, and the rejection of CLI harnesses and durable-execution capabilities. Those
arguments are untouched and they are the load-bearing half.

## Alternatives considered

**Keep pydantic-ai, run the disqualifying test first.** The orthodox move, and it was close. Rejected
because a passing test would not address the `config_hash` coupling — the test asks whether the bytes
are *visible*, not whether they are *stable across upgrades*, and the second is the problem. Passing
would have licensed the adoption on evidence that does not bear on the actual objection.

**LiteLLM as the transport.** Its canonical form is an existing provider's wire format, so one
provider is structurally privileged and everything the others express uniquely gets flattened.
Lossy normalization sitting exactly where the cache key is taken is the worst possible placement:
one key could map to two different provider requests. Its version bumps would move keys for the
same reason a library's would. **Its error taxonomy is borrowed; its translation layer is not.**

**An in-process CLI wrapper or RPC-driven harness** (Claude Agent SDK, `deepseek-harness-sdk`,
Codex CLI as a subprocess). Rejected — but **the obvious argument for rejecting them is wrong and
should not be used.** It is tempting to say the rendered prompt is invisible behind an RPC boundary.
It is not: DeepSeek Harness's Python SDK inherits `DEEPSEEK_BASE_URL`, so a local OpenAI-compatible
proxy sees the exact request bytes. Any opaque harness can be observed this way.

The correct argument is about predictability, not visibility. **The cache needs the key before
dispatch; a proxy only produces it after.** With an opaque runtime there is nothing to look the key
up *with*, so replay degrades from a guarantee to a recording. Compaction makes it worse: there is
not one rendered prompt per card but N, chosen by logic we do not control, so there is not even a
stable thing to key on. A proxy buys observation. It cannot buy determinism.

*(Narrowed 2026-11-04.)* This describes an opaque runtime, and not every CLI harness is one. OpenCode at `93f30ca` can
turn automatic compaction off, and a plugin hook sees each request before it is sent, so a key could probably be
computed before dispatch, with a proxy serving the hits. That was read and not run. Rejecting such a harness rests
on the other arguments here: its releases move the prompt (R60), its retries are on by default against `attempts`,
and its tool sets are permission rules rather than an absent table key.

The proxy technique is kept, repurposed — see the follow-on work below.

**A prompt-compiling framework** (Flock, and DSPy beneath it). Rejected, and worth recording because
it is the closest published architecture to this design — a blackboard with type subscriptions and
automatic parallelization, reached independently. The runtime half is still disqualifying: the
rendered prompt is compiler output that moves when the optimizer runs, when a signature changes, or
when the library version moves, stacked on LiteLLM's normalization underneath. Two layers of prompt
assembly we do not own, at the exact layer §8's guarantee rests on. Its architectural convergence is
recorded separately in the register; it is not an argument for adopting the runtime.

**Defer and decide at P2-13.** Rejected on ADR-0003's argument that deferred is not a state a design
can hold. The port is needed in Phase A regardless — the error taxonomy feeds `failure_class` — so
something gets decided implicitly if nothing is decided explicitly.

## Consequences

**Good.**
- `config_hash` has no third-party dependency in it. R60 is closed rather than mitigated.
- R59 is closed by construction: there is no cross-vendor effort abstraction to be trapped by. Rule
  134 is enforced by there being nowhere else for effort to live but resolved provider parameters.
- Rule 135 becomes a structural property.
- P1-24 becomes a one-off assertion with a kept test rather than a gating spike.
- The error taxonomy is ours, which core §10's `failure_class` allow-list already required.

**Accepted costs.**
- **2–4 days instead of 1–1.5.** Expect nearer 2–3 with the SDK handling transport; budget 3–4 and
  treat the difference as luck.
- **Behaviour the library had tested now needs our tests** — tool-result ordering, turn limits,
  malformed-output repair, schema validation failure paths.
- **A standing scope-creep risk.** Reimplementing 60% of a framework badly over six months, one
  defensible improvement at a time, is R43 through a door `guard_invariants.py` does not watch. The
  exclusion list below is the mitigation and it is written before the code.
- **We inherit provider quirks directly.** Tool-result blocks must precede text in the content array
  or the request is rejected; stop-reason vocabularies differ. Fiddly, and now ours.

**The exclusion list, which is the operative half.** The loop has: no streaming; no retry of any
kind; no provider abstraction beyond the port; no conversation state beyond the single card; no
sub-agents, delegation or capabilities; no memory; no compaction. Anything added later needs an
argument against this list.

**Follow-on work required.**
- The port and one adapter, in Phase A — the error taxonomy is needed before Gate A.
- **A kept test using a recording proxy, not a transport hook.** Point the adapter at a local
  OpenAI-compatible proxy, run one card, and assert the pre-dispatch cache key equals a hash of the
  body the proxy observed. Captured outside the process, so nothing the SDK does internally can fool
  it. This is what P1-24 becomes: not *are the bytes visible* — assembling them here makes that
  trivial — but *is the key computable before dispatch and stable across upgrades*.
- `failure_class` enumerated from the taxonomy, with turn-limit exhaustion distinct and never a
  success.
- A typed `ProviderSettings` per adapter, validated at config load, so `effort` has a home.
- Adapter identity into `kind_hash`, with a hash-stability test when the second adapter lands.

## What would change our mind

- **A third provider becomes necessary**, or the loop passes roughly 500 lines. Breadth stops being
  a cost paid for nothing, and the library becomes the right answer after all.
- **Provider quirk handling turns out to be a recurring maintenance cost** rather than a one-time
  translation — that is the case for someone else's if/else statements.
- **The exclusion list needs a third exception in a quarter.** That is the framework arriving by
  accretion, and the honest response is to adopt one deliberately rather than to keep growing this.
- **Subscription billing becomes economically decisive.** Then core §8 is amended by ADR before any
  runtime changes, and determinism and replay are what is being traded away — explicitly, not
  quietly.
