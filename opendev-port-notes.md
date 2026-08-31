# OpenDev — what to port into `harness/runtime/`

**Subject:** `github.com/opendev-to/opendev`, MIT, Rust. Read at commit `d32c660`, workspace
version 0.1.9, dated 2026-08-08. Written 2026-08-30.

**Requires:** ADR-0005 — the card runtime is hand-written, behind a provider port.
**Supersedes the operative half of:** `opendev-assessment.md`, which was written against ADR-0004's
open adoption question and did not know ADR-0005 had closed it.

**Why this document exists.** ADR-0005 decided the loop is written here, in Python, and budgeted
2–4 days for it. It also named its own largest risk: *"reimplementing 60% of a framework badly over
six months, one defensible improvement at a time."* The exclusion list is the stated mitigation, and
ADR-0005 says it must be written before the code.

Reading a shipped loop is the cheap way to see which 60% is the trap. That is what this is. **It
proposes no dependency, no vendoring and no FFI** — three shapes to borrow, one anti-pattern to name,
and a list of refusals each carrying the section that does the refusing.

---

## 1. Three shapes worth porting

All three are small: a protocol, a dict, and a file layout. None moves the loop toward ADR-0005's
500-line reversal trigger.

### 1.1 `BaseTool` as a `typing.Protocol` → `harness/runtime/tools.py`

Source: `crates/opendev-tools-core/src/traits.rs:415`. The trait carries thirteen members. **Take
five:**

| Member | Why |
|---|---|
| `name` | dispatch key |
| `description` | shown to the model |
| `parameter_schema` → JSON Schema | see below — load-bearing |
| `execute(args, ctx)` | the work |
| `format_validation_error(errors)` | see below — the non-obvious keeper |

**A Protocol, not an ABC.** Structural typing suits a per-role table assembled from config; nothing
should have to inherit to be a tool.

**`parameter_schema` is the load-bearing member.** ADR-0005 requires the provider request to be
assembled here, and core §8.1.1 lists `tool_schemas(k)` as a `kind_hash` input. So the schema must be
a **local, deterministic, canonically-serializable artifact**. A library's generated schemas were
rejected for exactly this — the schema has to move when we move it, not when a dependency releases.
Core §8.1.1's canonicalisation rules apply to it directly: sort collections byte-wise, no absolute
paths, no timestamps.

**`format_validation_error` is the one to take that looks skippable.** A schema failure that returns
a tool-authored message rather than a generic one is repair material, and policy §1.5 permits exactly
this under *schema repair*: "malformed output, re-prompted with the validation error. Same template,
bounded to one or two retries, no new decision." Cheap, and it is the difference between burning an
attempt on a parse error and not.

**Refuse the other eight**, with reasons:

- `is_read_only`, `is_destructive`, `is_concurrent_safe` — these exist to drive OpenDev's
  parallel-tool-execution policy. Cards are the unit of parallelism here (core §5.3), not tool calls.
- `display_meta` — TUI.
- `skip_dedup` — belongs to a dedup cache this design does not take (§1.2).
- `category`, `is_search_or_read` — classification feeding OpenDev's UI and heuristics.
- `is_enabled` — a tool that can disable itself at runtime is a tool set that changes without a
  config edit, which breaks core §8.1.1's invariant that *a hash change with no version bump is a
  bug*. Absence is the gate (policy §1.6); it is not a runtime property.

### 1.2 Four of the registry's ten execute steps → `harness/runtime/registry.py`

Source: `crates/opendev-tools-core/src/registry/execution.rs:96-110`, whose docstring enumerates the
pipeline. **Take four, in order:** resolve → validate against schema → execute → attach duration.

**The registry is a frozen `dict[str, Tool]`, built once per card from role config.** This is what
makes rule 135 structural exactly as ADR-0005 states it — *"a `verify` card has no write tool because
the table has no `write` key. There is no code path to test."*

**Do not port the interior mutability.** OpenDev's registry is `RwLock<HashMap<..>>` specifically to
allow late registration — its own comment says *"enabling late registration (e.g. `SpawnSubagentTool`
after `Arc<ToolRegistry>` is created)"*. A registry that can grow after construction is a tool set
that is not pinned, and the whole value of §1.1's `parameter_schema` depends on the set being fixed
at pin time. Frozen is both simpler and the stronger claim.

**Two omitted steps deserve a recorded decision rather than silence:**

- **Dedup cache** (step 3 — identical calls in one turn return a cached result). Plausibly useful,
  but it changes what the model sees in a way that leaves no trace in the transcript. **Default:
  out**, per ADR-0005's exclusion list. If ever taken, it must be recorded in the attempt.
- **Result truncation before results enter context** (part of step 10's sanitizer). The *placement*
  is right and worth taking — truncate before the result reaches the model, not after. But use
  **core §4.3's policy**, which already specifies it by media type: check log exit 0 → last 40 lines
  plus timing; exit ≠ 0 → first traceback plus last 200 lines. Do not port OpenDev's sanitizer.

**Refuse the rest:**

- **Middleware pipeline** (steps 5, 8) — this is the extension point through which a framework
  arrives by accretion. It is the single most likely route to ADR-0005's six-month failure.
- **Fuzzy name matching and "did you mean?" suggestions** (step 1) — a card calling a tool it was
  not given should fail cleanly. Suggesting near-misses tells it what it is missing, which softens
  the gate.
- **Parameter normalization** (step 2 — camelCase → snake_case, path resolution). Silent argument
  rewriting between what the model emitted and what ran. The cache keys on what was sent; the
  ledger should record what was run.
- **Overflow-to-disk**, **per-tool timeout overrides** — the lease and `deadline_at` bound wall
  clock host-side (core §5.6, §5.4), and that is stronger than a per-tool cap.

### 1.3 Phase separation as file layout → `harness/runtime/`

Source: `crates/opendev-agents/src/react_loop/phases/`.

The idea worth taking is not any phase's contents — see §2 — but that the loop is **files you can
delete** rather than a monolith with branches.

ADR-0005's exclusion list is long: no streaming, no retry of any kind, no provider abstraction
beyond the port, no conversation state beyond the single card, no sub-agents, no memory, no
compaction. **A loop whose steps are separate modules turns each exclusion into a file that does not
exist, which is auditable. The same logic inline turns each into an absence nobody can check.**

Concretely, ADR-0005's four steps — assemble → dispatch → append result → terminate → validate — as
small modules with a `loop.py` sequencing them. The 500-line ceiling ADR-0005 sets as a reversal
trigger then has a per-file denominator instead of being one number nobody looks at.

---

## 2. The anti-pattern — the most useful thing in the repo

`crates/opendev-agents/src/react_loop/loop_state.rs:22`. `LoopState` is 124 lines and carries:

> `iteration` · `consecutive_no_tool_calls` · `consecutive_truncations` · `consecutive_llm_failures`
> · `doom_detector` · `subdir_tracker` · `startup_paths` · `skill_model_override` ·
> `auto_approved_patterns` · `plan_edit_review_mode` · `todo_nudge_count` ·
> `all_todos_complete_nudged` · `completion_nudge_sent` · `consecutive_reads` · `bg_tasks_spawned` ·
> `bg_wait_nudge_count` · `activated_tools` · `proactive_reminders` · `collector_runner` ·
> `compaction_flag`

This is what an honest, well-built interactive assistant's loop state looks like. **Almost none of it
is a card runtime.** Nudge counters, doom-loop detection, plan-edit review mode, semantic and session
memory collectors, background-task tracking, per-subdirectory instruction injection.

Every one of those fields is individually defensible. Together they are ADR-0005's stated scope-creep
risk, realized, in shipped code — which is a different evidentiary class from *argued*, and policy
§10 already makes that distinction for the Gas Town observations.

`tool_dispatch.rs` is the same lesson at **1339 lines**: permission enforcement, approval gates, plan
edit review, interrupt checks, nudge resets, deferred tool activation, background-request polling —
wrapped around what is at its core *call the tool, append the result*.

**Proposed use.** ADR-0005 says the exclusion list is the mitigation and must be written before the
code. Give it a concrete test, and cite these two files by name:

> When something wants to be added to the loop, ask whether it is the first field of a `LoopState`.

---

## 3. Not portable, confirmed by reading

| Component | Refused by |
|---|---|
| `opendev-sandbox` | Linux-only microVM **Python execution for context analysis** with recursive `lm_query()` sub-LLM calls. Not workspace isolation — the name invites the error. The recursive sub-call also fails policy §1.5's test outright. |
| `parallel.rs` | Parallel execution only when all calls are `spawn_subagent`. Cards are the unit of parallelism (core §5.3, `SKIP LOCKED`). |
| `compaction.rs` | Core §3.4 — Compactor deleted by name. *Context is managed by splitting, not compressing.* Must be **absent**, not configured off. |
| `--continue`, `opendev-history` | Policy §1.6 — *does not persist between cards.* |
| `task_scheduler`, `task_manager`, `team_manager`, `plan_index`, `todo/` | Above the card boundary. The predicate is the scheduler (core §2 principle 2); core §3.4 deletes the controller by name. |
| `worktree/` | The workspace triple is provisioned host-side (core §6); theirs knows nothing of leases or fencing. |
| MCP dynamic tool discovery | A discovered tool changes `kind_hash` with no config edit (core §8.1.1). |
| `opendev-tui`, `opendev-web`, `opendev-channels`, `opendev-repl` | Interactive surfaces. There is no interactive surface here; there is SQL (core §9.1). |
| `AdaptedClient` / `ProviderAdapter` | See §4 — the reason is not the shape. |

---

## 4. Why the provider layer is not on the port list

`opendev-assessment.md` §3 found that `AdaptedClient` exposes the exact wire payload as one
materialized value before transport, and treated that as the decisive result. **It is a visibility
result, and visibility was never the binding constraint.**

ADR-0005 considered running that test and rejected it:

> Rejected because a passing test would not address the `config_hash` coupling — the test asks
> whether the bytes are *visible*, not whether they are *stable across upgrades*, and the second is
> the problem.

A 0.1.9 Rust workspace inside `config_hash` is worse on that axis than pydantic-ai was, and the
coupling is what ADR-0005 closed by construction. The `ProviderAdapter` shape is also *not* what
ADR-0005 wants: it says **the port is neutral and typed, not shaped after a provider's wire format**,
and the cache key is hashed over the adapter's serialized output, below the port. OpenDev's canonical
form is one provider's wire format — the same structural objection ADR-0005 raised against LiteLLM.

**Related correction.** The assessment rejected wrapping the binary on the grounds that it forfeits
the cache seam. ADR-0005 gives the correct argument and explicitly warns against that one: an opaque
runtime *can* be observed, via a local OpenAI-compatible proxy inheriting the base URL. The real
objection is that **the cache needs the key before dispatch; a proxy only produces it after** —
replay degrades from a guarantee to a recording.

---

## 5. What would change this document

- **The loop passes ~500 lines, or a third provider becomes necessary.** ADR-0005's own reversal
  trigger. At that point breadth stops being a cost paid for nothing and a library is the right
  answer — but the library would be a Python one, and none of §1 changes.
- **A refusal in §1.2 turns out to be load-bearing.** Parameter normalization is the likeliest:
  if providers emit arguments that cannot be dispatched without rewriting, the choice is between
  normalizing (and recording it) or failing. Recorded now so the decision is visible if it arrives.
- **The exclusion-list test in §2 needs a third exception in a quarter.** ADR-0005 already names
  this as the signal that the framework is arriving by accretion, and that the honest response is to
  adopt one deliberately.
