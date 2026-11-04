# Pi — ideas worth borrowing

**Subject:** `github.com/earendil-works/pi`, MIT, TypeScript. Read at commit `1bc7076`, coding-agent
version 1.5.0, dated 2026-11-03. Written 2026-11-03.

**Basis.** The agent loop and argument validation were read in source. `pi-durable` and the evals
were read from their docs, and the provider tests by filename only. Nothing was run. The 2025 "will
not support" lists are out of date, so cite the repo rather than the posts.

---

## Worth borrowing

- **Separate what the model sees from what the ledger keeps.** A tool result has `content`, which
  reaches the model, and `details` and `durationMs`, which do not. See its
  `packages/agent/src/types.ts`. No provider code sends either field. Take the idea rather than the
  field: see ADR-0012.
- **Never run tool calls from a truncated response.** When the token limit cuts off a response, Pi
  fails every tool call in it, because truncated arguments can still pass the schema. See
  `failToolCallsFromTruncatedMessage` in `packages/agent/src/agent-loop.ts`. Its comment blames the
  streaming parser and ADR-0005 excludes streaming, so check what the SDK returns. Here it would end
  the attempt with its own `failure_class`.
- **An eval protocol that cannot report a false result.** See `packages/evals/README.md`. Take these
  for P3-5, because rule 121 deletes a skill on the result and a crashed arm must not read as "did
  not reproduce":
  - Runs and a protocol digest are fixed before execution.
  - A missing or errored arm blocks its pair and withholds the headline number.
  - Missing telemetry stays unavailable rather than zero.
  - Saturated controls, no lift and flakiness are flagged.
  - Material is removed symmetrically, including the prompt section that points to it.

  Do not take its default of one run per variant. Its own README says that cannot establish stability.
- **Provider tests as a checklist.** ADR-0005 accepted that provider quirks and their tests are now
  ours. `packages/ai/test` has 194 files, including `tool-call-without-result`,
  `openai-responses-empty-tool-result` and `context-overflow`. Only the names were read. The cases can
  be copied with no dependency, and can test the sketch's existing `CONTEXT_EXCEEDED` class.

## The replay cache

**Taken up in ADR-0012.** Reading Pi's split led there, though Pi does not solve this problem.

**Correction.** An earlier version of this note said no rule covers byte-stable tool output, and proposed
moving timing to a `details` field. `jig-sketch.py` and `PROTOTYPE_v3.md` (R-new-5) already require a
`normalize` step, which is the real mechanism. They are not core, policy or a rule, and the port notes
omit it, which is what the ADR fixes. It also rejects a `details` field, because `dispatch_tool` already
holds both versions and `tool_audit` can keep what is removed.

## Against the positioning

`pi-durable` commits turns and tool calls before showing them and resumes after a crash. It also bounds
crash loops, deduplicates submissions by `requestId` and exposes a task graph. That comes close to the
one differentiator left in policy §10, and core §13 says to acknowledge when that happens.

It is marked experimental and allows one process per store. A keyword search of its README and spec
found no cross-run equivalent of `project`, `intent_digest` or `config_hash`, which is not proof of
absence. What remains is narrower: step 7's question of whether the record answers questions other
tools cannot.

## Not borrowing

| Pi has | Why not |
|---|---|
| Argument coercion (`"42"` to a number) | Port notes §1.2 refuse silent rewriting. Pi's comment that models often send these is evidence for the port notes' §5 trigger. |
| Compaction, extensions, steering, mid-session model switching, subagents | Excluded by ADR-0005, core §3.4 and policy §1.6. |
| Code mode | Nested tool calls never enter the model's context, but it puts an interpreter inside the loop ADR-0005 keeps small. |
| Per-tool `replay` flags | Workspace destruction and `retry_safe` already cover this per card. |
| "Four tools is enough" | A 2025 claim that does not settle §1.6's tool-width question. The ablation does. |

## Verdict

Borrow the four ideas and adopt no package. Rule 63 sends findings to an existing document, so this note
is only the record of what was read.
