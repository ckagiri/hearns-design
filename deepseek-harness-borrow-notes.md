# DeepSeek Harness — ideas worth borrowing

**Subject:** `github.com/deepseek-ai/deepseek-harness`, MIT, TypeScript, at commit `8bd07339`, dated 2026-11-03.
Also `github.com/deepseek-ai/dsh-superagent-prototype` at `8c32a9dc`, dated 2026-10-31. Written 2026-11-04. This
replaces nothing in ADR-0005's August survey.

**Basis.** Subagents read the source in four strands, and the main findings were spot-checked against the source
and this repo. Items marked *(unchecked)* rest on one subagent's reading. Items marked *(docs)* come from that
project's READMEs, notes or postmortems rather than its code. No DSH code was run. `ptc-runtime`, `ssh` and the
superagent article were not read. "Not found" means by keyword search, which is not proof of absence.

---

## Taken up in ADR-0014

Three gaps in this design, fixed before anything is built:

- **Host git follows a pointer the card can write.** DSH's runner suggested the shape, and the probes in the ADR
  go further than it does.
- **Attempts don't record what the card was.** DSH's `team/task` appends a whole task per `revision`
  (`packages/team/agent-team/src/journal.ts:63`) *(unchecked)*. Three columns are enough here.
- **Replay can't reproduce a failed provider call.** DSH's `deriveReplayScript` refuses a thrown call and demands
  an override (`packages/test-support/llm-replay/src/index.ts:467-476`).

## Worth borrowing

**Failure handling in the loop**

- **Read the stop reason, and fail closed on an unknown one.** See `stopReason` in
  `packages/llm/llm-deepseek/src/translate.ts:90-97`. `_turn_loop` never reads one, so truncated text gets
  `schema_repair_prompt`, and `CachedModel` stores the truncated response. Add `Response.stop` and an
  `OUTPUT_TRUNCATED` class with no repair. The Pi note covers truncated tool calls only.
- **Record the tool call before it runs.** `packages/session/session-checkpoint-policy/src/index.ts:70-75` flushes before `tools/execute`, and repair
  separates `TOOL_NOT_STARTED` from `TOOL_OUTCOME_UNKNOWN` (`packages/core/session/src/repair.ts:15-18`). The sketch
  audits after `t.fn` returns, so a hung tool leaves no row. Insert at dispatch and update at finish. An `allowed`
  row with a NULL `duration_ms` then means the outcome is unknown, and no new column is needed.
- **Assert tool pairing before computing the key.** `packages/llm/llm-deepseek/src/serialize.ts:131-146` rejects
  duplicate ids, orphan results and unresolved calls. Without this, our own bug becomes `PROVIDER_REFUSED`, which
  is in `EVIDENCE`, so layer 7 tells the card about it. Raise `HARNESS_BUG` instead. ADR-0005 names ordering as
  ours to test.
- **Separate "did not start" from "failed".** `run_oracle` returns `unavailable` only for `SpawnFailure`, so a daemon
  restart mid-rung is `BrokenPipe`, charged as `failed`, against ADR-0011. DSH proves no start from an unconsumed
  request file (`packages/subprocess/subprocess-local/src/linux-scope.ts:261-282`) *(unchecked)*. A harness-owned shim could record the start, on a mount the
  card can't write.
- **`expect: FAIL` can pass on a crash.** DSH's first regression test passed when "a timeout killed Vite and
  satisfied a nonzero-exit assertion" (`docs/postmortem/0003-web-agent-gui-feedback-loop.md:36`). Inversion is elided
  in the sketch and `run_oracle` reads only `r.ok`, so this is inferred. Report `started`, `exit_code`, `timed_out`
  and `tests_ran` separately. The Jig note's tripwire covers only zero tests reporting ok.
- **Kill the process tree on a tool timeout.** Killing a `docker exec` client may leave the tool running in the
  container, beside the next call. This is inferred and not run. Lease and deadline bound the attempt, not one tool.
- **Probe the boundary at provisioning.** DSH applies the real profile in its probes
  (`packages/sandbox/sandbox-local/src/index.ts:70,87`) *(unchecked)*. Add a canary for outbound network and for a
  write to a read-only mount, since R22 checks only that a container exists.

**Replay and tests**

- **Replay equality proves determinism, not correctness.** Eight DSH scenarios passed while replaying `UNKNOWN_TOOL`:
  the suite "proved deterministic replay of the regression" (`docs/postmortem/0002-js-expression-disabled-filesystem-tools.md:19`).
  Core §11 asserts only an identical terminal graph. Also assert the ordered `cache_key` per attempt, and no
  `out_of_scope` denials in a baseline run.
- **Commit rendered prompts as text.** Hash tests show that something moved, not what. DSH keeps 101
  `system-prompt.expected.md` and 94 `tool-schemas.expected.json` files. R21 cites golden-file prompt tests, and
  none were found in core, `PLAN.md` or `PROTOTYPE_v3.md`. The cost is real: one rewording was refused because it
  would re-render 83 of them *(docs)*. Deduplicate per kind and tier.
- **Test that each call extends the last.** `expectPrefixExtension` in
  `packages/core/agent-loop/tests/request-reconstruction.spec.ts:69-74` compares values, not bytes. No runtime detector
  of what broke a prefix was found. Add it to P1-22, and consider `request_ref` on `model_calls` so that a miss can
  name the first differing block.
- **Carry thinking through the port as an opaque envelope.** `packages/llm/llm-deepseek/src/replay.ts:29,48-64`
  *(unchecked)*. `as_assistant()` is undefined in the sketch. Whether the provider needs thinking blocks returned is
  unchecked API knowledge, so confirm that first, then test that replayed call 2 has the same bytes as live call 2.
- **Record provider cache tokens, keeping unknown distinct from zero.** `packages/llm/token-meter/src/turn-usage.ts:136-137`
  *(unchecked)*. `model_calls` has no cache columns, so `cache_control` is unmeasured. This detects R61, not bounds it.
- **Cap tool results deterministically.** Head, tail and an exact omitted count, with `read` exempt
  (`packages/spill/spill-policy/src/index.ts:113-119,136`) *(unchecked)*. No cap was found in `dispatch_tool`, though
  ADR-0012 says "normalize first, then truncate". Don't copy the spill path: it contains `randomBytes`
  (`packages/spill/spill-local/src/store.ts:110`), which would move the key on every run.

**Ablation**

- **Size runs from the base rate.** Rule 121 deletes a skill and names no sample size. DSH's probe ran 150 requests
  per arm per model, with history ending at the decision point: 0/150 vs 6/150 on flash, 0/150 vs 23/150 on pro
  (`.agents/notes/implemented/bug-fix/2026-10-21-subagent-end-turn-guidance.md`) *(docs)*. At those rates, three runs
  miss the effect 88% and 61% of the time. The RED pairing should name an observable event and a base rate, and N
  follows from those. A six-benchmark eval read neutral on another sentence, which stayed on production evidence
  (`2026-10-26-read-guidance-line-ranges.md`) *(docs, unchecked)*. This adds to the Pi note's protocol, which covers
  arm integrity only.

**Smaller**

- **Shadow-run automatic decisions.** Superagent's `observe` mode records `would_accept` and acts on nothing
  (`src/policy.ts:55-58`) *(unchecked)*. The reaper could log would-stall rows for early runs, to test ADR-0007's guard
  directly.
- **A "nothing needed" outcome.** Superagent's `dropped` (`prompts/work.md:45`) *(unchecked)*. Decide in policy §4.1
  whether the record should tell it from `ok`.
- **Name the sweep's three objects.** Directory, registration and branch fail separately. Rule 141 says "worktrees".
  DSH has no sweep *(docs, unchecked)*, so ours is ahead.
- **Counter-test restriction text in prompts.** Stating read-only caused five of twelve zero-tool-call turns in one
  DSH note (`.agents/notes/archived/feature/2026-07-06-sandbox.md:159`) *(docs, unchecked)*.

## ADR-0005's limits, measured

**No trigger fired.** ADR-0005 says "the loop passes roughly 500 lines" without defining the loop, so it should name
the files.

| DSH item, by `wc -l` | Lines |
|---|---|
| `packages/core/agent-loop/src` | 2,127 |
| `preStep`, `turn`, `step`, `prepareRequest`, `buildRequest` *(unchecked)* | 448 |
| All `src` TypeScript in packages and apps *(unchecked)* | 542,772 |

The 448 includes streaming and cancellation, which ADR-0005 excludes, so about 500 is plausible for the driver alone.
Counting assembly and dispatch takes it far past that *(unchecked: about 4,856)*.

The plugin boundary has a measurable cost. DSH's ACP server crashed on the first real connection "despite 178 green
unit tests and 100% line coverage" (`docs/postmortem/0001-acp-default-export-drops-inject.md:13`). A dispatch table
cannot fail that way, which supports ADR-0005 and the early hand-run in `PROTOTYPE_v3`.

## Against the positioning

**`session-query` threatens policy §10's wording, not a narrower claim.**

- **In favour of the claim:** session filters are `id`, `cwd`, `created-at`, `parent` and `availability`, and event
  filters are `seq`, `time`, `type`, `surface` and `text` (`packages/session-query/session-query/src/types.ts:205-221`).
  There is no equivalent of `project`, `intent_digest`, `config_hash` or an oracle verdict. No aggregates were found
  by keyword search *(unchecked)*.
- **Against it:** "the record survives the controller dying" no longer separates us, since batches are fsynced and
  torn tails repaired *(docs, unchecked)*. It answers text recall we refuse: core §4.3 never queries content, so "have
  we hit this error before?" has no answer here. Whole events can be exported over OTLP for a warehouse to aggregate
  *(unchecked)*. And DSH has run, while this has not.

Narrow §10 to typed questions across runs, list them for step 7, and record this under core §13's clause.

**Trusted "done" elsewhere supports ADR-0013.** `update_goal`'s `complete` runs no evidence check
(`packages/goal/tool-goal/src/index.ts:294-295`), and the README admits "No independent evaluator" *(docs, unchecked)*.
Superagent checks nothing itself on completion *(unchecked)*. Add evaluator-backed certification as a re-check trigger
in core §13.

**Nothing has lease plus fencing across processes.** Team tasks stay owned after a dead worker, workflows have no
journaling or resume, and schedules can duplicate delivery on a crash *(docs, unchecked)*.

## A correction

**`PROTOTYPE_v3.md`'s hook wrapper note was misleading.** It said DSH "built a wrapper for exactly this". The wrapper is
`scripts/install-lefthook.mjs`, a `postinstall` step for contributors' own hooks that exits in CI and sets a per-worktree
`core.hooksPath`. It solves installs overwriting shared hooks, not cards behaving nondeterministically. DSH's runtime
does the opposite and disables hooks (`packages/experimental/worktree/src/index.ts:258-264`). P1-9 should read that,
along with the environment scrub in `worktree/src/process.ts:19-24,59`. ADR-0014 corrected the note.

## Not borrowing

| DSH has | Why not |
|---|---|
| Everything is a plugin | The cost above, and ADR-0005's exclusion list. |
| `llm-retry`, compaction, `ToolCallRecovery` | Excluded by ADR-0005. An attempt that fails simply ends. |
| `repeat-tool-reminder` | `opendev-port-notes` excludes doom-loop detection, and an `args_digest` query gives the signal. |
| `blockedAfterConsecutiveRounds` | It delays refusals, which we want early. |
| `flock` ownership, same-session retries | Single host only, and contradicts stateless workers and identical-prompt retries. |
| Event-sourcing the ledger | ADR-0014 gets the benefit with three columns. |
| Indexing content for search, model-facing `session_search` | Core §4.3 and ADR-0005's small tool surface. Name the refused question instead. |
| `isContextWindowExceededError`, stderr signatures | Text matching, which ADR-0011 rejected. |
| `toolInput`'s `{}` fallback | Silent rewriting, which port notes §1.2 refuses. |
| Per-file 100% coverage | Postmortem 0001 shows it missed a dead product. |
| bwrap, Seatbelt and ACL backends, `sandbox_permissions` | Weaker than the container, and cards have no in-loop approver (ADR-0003). |
| Model-chosen skill loading | Conflicts with policy §5.1's hand-chosen sets. |
| Its benchmarks | They measure time, heap and scaling only, not agent quality *(docs)*. |

## Verdict

Borrow the failure stories and test ideas, and adopt no package. The postmortems in `docs/postmortem/` were the most
useful thing read per line. Rule 63 sends findings to existing documents, so this note is only the record of what was
read: ADR-0014 holds the three decisions, and the rest stay here until someone takes them up.
