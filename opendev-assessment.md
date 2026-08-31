# OpenDev — assessment against harness-core-v3 and harness-policy-v3

**Subject:** `github.com/opendev-to/opendev`, MIT, Rust. Read at commit `d32c660`, workspace
version 0.1.9, dated 2026-08-08. Assessed 2026-08-29.

**Question asked:** where does this fit relative to the v3 documents.

**Answer in one line:** it is a candidate for the **card runtime** of policy §1.6, and a weak
secondary data point for §10 positioning. It is not a substrate, not a competitor to core, and
adopting it would not change a line of `harness-core-v3`.

**Status of this document: SUPERSEDED on the operative question.** *(Header added 2026-08-30.)*

**ADR-0005, dated 2026-08-20 — nine days before this assessment — already reversed ADR-0004's
implementation half.** The card's tool loop is hand-written in `harness/runtime/`, behind a provider
port. This document was written as though the adoption were still open. It was not, and no adoption
of OpenDev is proposed or available.

**The central finding does not carry the weight it claims.** §3 establishes that `AdaptedClient`
exposes the exact wire payload before transport. That is a **visibility** result, and ADR-0005
considered running exactly that test and rejected it: *"a passing test would not address the
`config_hash` coupling — the test asks whether the bytes are visible, not whether they are stable
across upgrades, and the second is the problem."* A 0.1.9 Rust workspace inside `config_hash` is
worse on that axis than the library ADR-0004 had adopted. §9's recommended spike is therefore
non-decisive; do not run it on this document's say-so.

**One argument here is one ADR-0005 warns against.** §7 option B rejects wrapping the binary on the
grounds that it forfeits the cache seam. An opaque runtime *can* be observed, via a local
OpenAI-compatible proxy inheriting the base URL. The correct objection is that **the cache needs the
key before dispatch; a proxy only produces it after** — replay degrades from a guarantee to a
recording.

**What survives, and where it went.** The reading itself — what the crates contain, what is above and
below the card boundary, what is refused and by which section — is sound and is the basis of
`opendev-port-notes.md`, which asks the question that is actually live: **which shapes should the
hand-written Python loop borrow, and which must it refuse?** Read that document instead. This one is
kept as the record behind it.

---

**Status as originally written:** an assessment, not a decision. The adoption decision belongs in
ADR-0004, which policy §1.6 already names as its home.

---

## 1. What OpenDev is

A terminal-native coding agent, built as an ensemble rather than a single loop. Work is routed
through five workflow slots — Normal, Thinking, Compact, Self-Critique, VLM — each independently
bound to a configured model across nine providers. Twenty crates: TUI, web UI, MCP integration,
LSP and symbol tooling, plugins, hooks, channels, history, and a ReAct loop driving tool calls.

The README documents no database, no task queue and no crash-recovery story. `opendev --continue`
resumes the most recent session. That is the whole persistence account.

---

## 2. Where it fits — the card runtime, policy §1.6

§1.6 exists because §1.5 established that turns are not prompts — an executor makes many model
calls per attempt, reading, editing, running the check, reading the failure, editing again — and
**nothing until then said what runs that loop**. The card runtime is that thing. It lives inside
one attempt on one card, below the card boundary:

> It makes model calls, runs the tool loop, and validates output against the jig's schema. It does
> not schedule, does not retry across attempts, does not persist between cards, and does not know
> that other cards exist.

OpenDev's ReAct loop, tool registry and provider layer are exactly that job description. Everything
else it ships is either above that boundary or irrelevant to it.

**The layering, for orientation:**

| Layer | What | Home |
|---|---|---|
| Ledger, predicate, claim, fencing, reaper | core §4–§5 | ours |
| Worker loop — claims, provisions the workspace triple, commits | core §5, §6 | ours |
| **Card runtime — drives one attempt's model calls and tool loop** | **policy §1.6** | **the slot in question** |
| Jig — prompt template, output schema, checks | policy §1.4 | ours |

---

## 3. The decisive question: can it satisfy core §8?

Policy §1.6 states the disqualifying condition plainly:

> **The runtime cannot expose the exact request bytes** → it cannot satisfy core §8, and the
> adoption in ADR-0004 is reversed regardless of what else it offers.

### 3.1 It passes the bytes test

The seam is `AdaptedClient` — `crates/opendev-http/src/adapted_client.rs:32` — which holds an
`HttpClient` plus an optional `Box<dyn ProviderAdapter>`. Its `post_json` does:

```rust
effective_owned = adapter.convert_request(payload.clone());   // the wire bytes
```

`ProviderAdapter::convert_request` (`crates/opendev-http/src/adapters/base.rs:22`) is where the
internal Chat Completions payload becomes the provider's actual format — Anthropic's message
shape, cache-control fields, reasoning parameters. That converted `Value` is then serialized by
`HttpClient::post_json` at `crates/opendev-http/src/client.rs:227`.

So the exact request body exists as one materialized `serde_json::Value`, in one function, before
transport. That is core §8.1.1's requirement met — *hash the rendered artifact, not the thing that
renders it* — including the assembled system prompt and the generated tool schemas, which is
precisely the property core §8 says "must be verified rather than assumed."

`Box<dyn ProviderAdapter>` also means the cache can be implemented as a `CachingAdapter` wrapping
the real one. That is ADR-0004's "cache as the model interface" shape, not a wrapper around a
library — the distinction core §8 makes load-bearing.

### 3.2 It fails the chokepoint test as shipped

Core §8's guarantee is meant to be structural: *"a call path that bypassed the cache would have to
bypass the model interface itself, which the runtime has no way to do."* Here it has a way, twice.

Two live paths build their own `reqwest::Client` and post to hardcoded endpoints with keys read
from the environment:

- `crates/opendev-tools-impl/src/vlm.rs:219-230` — hardcoded `https://api.openai.com/v1/chat/completions`
- `crates/opendev-agents/src/attachments/collectors/memory_selector.rs:103-104` — same pattern

Both are model calls. Both would make outbound requests during replay, breaking the
zero-outbound-calls promise.

A third path, `with_curl_transport`, shells out to curl for endpoints that reject reqwest. It
still passes through `convert_request` first, so it is cache-visible — but it shows the transport
layer is not sealed.

### 3.3 The fix, and why the second option is better

**Option A — upstream it.** Route the two bypasses through `AdaptedClient`, add a CI lint banning
raw `reqwest` outside `opendev-http`. Two files, MIT codebase.

**Option B — enforce from outside the process.** Network deny in the container, per policy §6,
with the cache as the only permitted egress. A bypassed call becomes a hard failure rather than a
silent cache miss.

**Take B.** Option A converts a structural guarantee into a maintained one, which is exactly the
distinction policy §10 draws about the Gas Town account — *"coaching in the prompt where a gate
belongs in code."* A lint is a discipline; a network deny is a gate. B also costs nothing new,
because core §6 already provisions the container. Do A as well if upstream will take it, but do
not rely on it.

---

## 4. What translates

### 4.1 `AdaptedClient` / `ProviderAdapter` — the cache seam

Section 3 above. The highest-value piece, and most of why the repo is worth reading.

### 4.2 `BaseTool` + `ToolRegistry` — layer 3 as a gate

`crates/opendev-tools-core/src/traits.rs:415` gives `name()`, `description()`, `parameters()`
returning JSON Schema, and `execute()`. `ToolRegistry` (`crates/opendev-tools-core/src/registry/mod.rs:27`)
is a `register()`-based map with no ambient population — you construct it and put in exactly what
you choose.

This is policy §1.6's requirement directly:

> The tool set is enumerated per role, and absence is a gate. A `verify` card constructed without
> a write tool cannot edit what it is reviewing.

Build the registry per role from config and the absence is real — not an instruction the card is
asked to honour. Rule 25 at the cheapest available price.

Two further benefits. `parameters()` yields tool schemas as a hashable artifact, and core §8.1.1
lists `tool_schemas(k)` as a `kind_hash` input — those bytes have to come from somewhere.
And `opendev-tools-lsp` / `opendev-tools-symbol` are real LSP and symbol-level tools: genuine work
not written.

### 4.3 The `react_loop` phase split

The loop is decomposed into `llm_call`, `tool_dispatch`, `response`, `completion`, `parallel` and
`safety` phases over a `loop_state`. This matters less for what it does than for what it permits:
phases can be **deleted** rather than surgically excised from a monolith. Given how much of §5
below must be removed, a loop you can subtract from is worth more here than a loop that is merely
good.

### 4.4 Multi-provider dispatch behind one internal format

Everything converges on OpenAI Chat Completions internally, then adapts outward. Policy §8.1.2
says *vary the model or the effort, not the seed*, and §7.3 E1 wants samples varied across models
against a human-authored control. Cross-provider sampling behind one payload shape is that
experiment's plumbing, already built.

---

## 5. What does not translate

| Component | Why not |
|---|---|
| `task_scheduler.rs`, `task_manager/`, `team_manager/`, `plan_index.rs`, `todo/` | Above the card boundary. The predicate is the scheduler (core §2 principle 2). These are the controller under a different name — core §3.4 deletes them by name, not by category. |
| `worktree/` | The workspace triple is provisioned host-side (core §6). Theirs knows nothing of leases or fencing. |
| `compaction.rs` | Compactor is deleted, core §3.4: *context is managed by splitting, not compressing*. Must be **disabled**, not merely unused — it is a live model call that fires on long context. |
| `--continue`, session persistence, `opendev-history` | §1.6: *does not persist between cards.* |
| `opendev-sandbox` | Linux-only microVM Python execution for context analysis, with recursive `lm_query()` sub-LLM calls. Not workspace isolation, and the recursive sub-call loop fails the §1.5 test outright. |
| Self-Critique workflow slot | Admissible only in §1.5's narrow *self-review before returning* sense — a cheap first filter whose verdict is never trusted. Not as a workflow slot. |
| `opendev-tui`, `opendev-web`, `opendev-channels`, `opendev-repl` | Interactive surfaces. There is no interactive surface here; there is SQL (core §9.1). |
| MCP dynamic tool discovery | A discovered tool changes `kind_hash` with no config edit, breaking the core §8.1.1 invariant that *a hash change with no version bump is a bug*. Pin or disable. |

**Note on `opendev-sandbox`:** it is named as though it were the isolation story and is not. Core
§6's container — pinned runtime, cgroup limits, network deny, a kill handle — remains entirely
ours to build. Nothing in OpenDev contributes to it.

---

## 6. Effect on §10 positioning

**No threat to the differentiator.** No database, no crash recovery, `--continue` resumes the most
recent session. That is precisely the *ledger maintained by discipline* position core §1 claim 1
is written against. Policy §12 says positioning changes if *"controller-based tools acquire
crash-safe records and parallelism."* OpenDev has the parallelism half and not the record half.

**It reinforces the parallelism correction.** §10 already records, corrected 2026-08-18, that
parallelism is table stakes rather than an advantage held. OpenDev is a third independent tool in
this class shipping concurrent sub-agents. Argue parallelism as a requirement met; never as an
advantage.

**It is not an E3 baseline.** §7.4 specifies a baseline as a specific shipped pipeline —
brainstorm → plan → subagent-driven development, with worktrees, TDD, task reviews, a bounded fix
loop and a final whole-branch review. OpenDev is a fleet of concurrent sub-agents with no
published plan-ledger discipline. It does not substitute for E3; it is a different comparison and
a weaker one.

---

## 7. Form of adoption — three options

What is needed from a card runtime is unusually small and unusually strict. That shapes the
choice more than the quality of the code does.

**A — vendor the crates.** Take `opendev-http` and `opendev-tools-*` largely whole, `react_loop`
with phases removed, discard the rest. Inherits the cache seam and the tool registry; costs a Rust
fork of a fast-moving upstream, and strictness is where forks rot.

**B — wrap the binary.** Run `opendev` as a subprocess per card with a pinned config. Cheapest,
but it forfeits the cache seam — the one thing actually wanted. Probably fatal to core §8.

**C — read it as a design source and build the runtime.** Take the `ProviderAdapter` shape,
`BaseTool`, the phase split. The runtime is small precisely because it does not do sessions,
scheduling, compaction, or a TUI.

**Leaning: C, with A as the fallback.** Not a decision — it turns on build cost and timeline,
which this assessment does not have. What it does establish is that B is disqualified on core §8
grounds, and that C is cheap because §5 removes most of what would otherwise have to be written.

Whichever is chosen, the container and network deny of core §6 and policy §6 are ours regardless,
and section 3.3 depends on them.

---

## 8. What would change this assessment

- **The two bypass paths turn out to be load-bearing** — if VLM or memory-selection cannot be
  routed through `AdaptedClient` without losing function, the seam is narrower than section 3.1
  claims and option A weakens.
- **`convert_request` turns out not to be the last mutation before the wire** — any header,
  parameter or body edit applied downstream in `HttpClient` would mean the hashed artifact is not
  the rendered one, and core §8.1.1 is not satisfied. Worth confirming by reading
  `client.rs:90-260` in full before an ADR.
- **Upstream restructures the provider layer** — the seam is one trait and one struct; it is not a
  stability commitment anyone has made to us. This is R60's argument (runtime upgrade is a run
  boundary) applied to a dependency we would not control.
- **The build cost of option C is measured and is larger than assumed** — then A becomes the
  recommendation and the fork-rot risk is accepted explicitly rather than by default.

---

## 9. Recommended next step

Before any ADR: read `crates/opendev-http/src/client.rs:90-260` and confirm that
`convert_request`'s output is the final mutation before serialization. That single fact is what
section 3.1 rests on, and it is the difference between an ADR-0004 candidate and a disqualified
one.
