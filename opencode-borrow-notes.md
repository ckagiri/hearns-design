# OpenCode — ideas worth borrowing

**Subject:** `github.com/anomalyco/opencode` (`sst/opencode` redirects there), MIT, TypeScript, at commit `93f30ca`,
dated 2026-11-04. Latest release at that date: v1.19.5. Written 2026-11-04. Paths are under its `packages/`. The
`packages/opencode` directory no longer holds code: the live agent loop is `core/src/session/runner/`, and the
provider layer is `ai/src/`.

**Basis.** Subagents read the source in two strands, and the main findings were checked against the source and this
repo. Items marked *(unchecked)* rest on one subagent's reading. Nothing was run. `shell/scan.ts`, the serialization in
`packages/ai`, most protocol files, the body of the compaction code and the server handlers were not read. "Not found"
means by keyword search, which is not proof of absence.

---

## Worth borrowing

**Replay and the kept proxy test**

- **The kept test may fail as designed.** `CachedModel` hashes `wire` plus the adapter identity, but `complete` calls
  `provider.post(body)`, so the SDK serializes what is sent (`jig-sketch.py`, `AnthropicAdapter` and `CachedModel`).
  ADR-0005's test compares the key with a hash of the body the proxy observed, and those differ on two counts. This
  is inferred from a sketch. Send `wire` verbatim, and compare over `observed body + identity`.
- **The key ignores headers.** OpenCode's recorder matches method, URL, headers and key-sorted JSON
  (`http-recorder/src/http/matching.ts:8-16`), and its adapter adds `anthropic-beta` as a header
  (`ai/src/protocols/anthropic-messages.ts:1535-1542`). Here the key covers the body only, so a setting sent only as a
  header would not move it. Whether any setting here does that was not checked. If one does, add it to the key
  through an allow-list.
- **Name what changed on a miss.** `requestDiff` reports differences by JSON path (`matching.ts:40-57`), and `ReplayMiss`
  carries only the key. A diff needs the recorded request, so this depends on the DeepSeek note's `request_ref`.
- **Refuse to store secrets.** A recording containing a key pattern or an environment secret value fails to write
  (`http-recorder/src/cassette/store.ts:132-135`, `http-recorder/src/redaction/secrets.ts`). No rule was found for what
  `model_cache` and `content.put` may store. It should cover any fixture the proxy test keeps.

**Failures and retries**

- **Honour `retry-after`.** OpenCode waits for the longer of its backoff and the provider's hint, capped at 15 minutes
  (`core/src/model-retry.ts:12-20,31-35`). `not_before` here ignores provider hints (core §5), and ADR-0011 records that a
  long rate limit can exhaust free retries. This is harness retry, so ADR-0005's loop exclusion still holds. ADR-0005
  also gives retries to the SDK, so settle how the two layers combine.
- **Three more stop-reason and status cases.** These extend the DeepSeek note's "read the stop reason", as test cases
  rather than code:
  - `model_context_window_exceeded` is a stop reason. OpenCode files it under `length`
    (`anthropic-messages.ts:1023`). Here it should be `CONTEXT_EXCEEDED`, not truncation.
  - `refusal` is a stop reason (`:1025`). With no parseable text, `_turn_loop` sends it to schema repair.
  - A 429 can mean quota (`ai/src/provider-error.ts:141-145,239-244`). Misread, `billing_exhausted` spends free retries
    instead of halting the run. Cerebras's `token_quota_exceeded` is the reverse trap, a throttle that reads as quota.

  ADR-0011's "status and typed errors" would not catch the first two, which arrive in 200 responses.

**The record**

- **Hash the exact tree checked.** OpenCode captures a dirty tree with a separate git dir and a temporary index, leaving
  HEAD and the real index alone (`core/src/snapshot.ts:95-97`, `core/src/git.ts:644-647,771-774`). This fits the Jig
  note's "Evidence record". `write-tree` was not found here. ADR-0014 also says staging is unspecified, so this may
  answer both. Run it through rule 150's runner. Don't copy its failure handling: a failed capture only logs a warning
  (`snapshot.ts:146`), and untracked files over 2MB are skipped (`:141`).

**Smaller**

- **A separate cap for timeouts.** `MAX_TIMEOUT_RETRIES = 3` (`core/src/model-retry.ts:40`), because a timed-out call has
  already spent minutes.
- **Edit-miss hints.** A failed edit returns "already applied" or the closest lines (`core/src/tool/plugin/edit.ts:199-241`)
  *(unchecked)*. Nothing measures whether this saves a turn.

## Rule 135 and `bash`

OpenCode's read-only `explore` agent is allowed `shell` (`core/src/plugin/agent.ts:80-84`), and its prompt says "Shell
commands MUST be read-only" (`:15`). That is rule 25's coaching where a gate belongs.

This design avoids that. `worked-run-catalog.md:121` gives `verify` `[read, grep, glob]`, with no `bash`. That file is
marked read-do-not-edit, ADR-0008 left it stale on purpose, and rule 135 now puts tool sets in the jig. No current
listing was found, so carry this one over when `verify`'s jig is written. It names `glob`, where the sketch's six tools
name `ls`.

## ADR-0005's argument, against this tool

**No trigger fired, and the decision stands.** Its reasoning against CLI harnesses is broader than it should be, though:

| ADR-0005's argument | Against OpenCode |
|---|---|
| Compaction is "logic we do not control" | It can be turned off, overflow included (`core/src/session/compaction.ts:295-296`) |
| A proxy only produces the key after dispatch | The `http.request` hook sees the request first, but `handler(sent)` always runs, so a proxy must serve hits (`core/src/session/model-request.ts:356-373`). Computing the key this way is inferred |
| Provider traffic can be observed | A configured `baseURL` replaces the endpoint (`core/src/config/plugin/provider.ts:75-82`) |

What still holds:

- **Prompt assembly moves with its releases (R60).** `core/src/session/runner/prompt/system.txt` ships with it, unless
  `agent.system` replaces it. Date and environment instructions are built in (`core/src/instructions/builtins.ts:25-45`).
  A plugin could probably strip them *(inferred)*.
- **Retries are on by default,** against `attempts`. The only off-switch found is a plugin hook
  (`core/src/session/runner/retry.ts:45-50`). "Absent is easier to guarantee than configured-off."
- **Tools are hidden only by a whole-tool deny** (`core/src/tool.ts:379-382`). Otherwise they are denied at call time,
  and a plugin hook sees the decision (`core/src/permission.ts:190`).

**Applied to ADR-0005.** After "A proxy buys observation. It cannot buy determinism.":

> *(Narrowed 2026-11-04.)* This describes an opaque runtime, and not every CLI harness is one. OpenCode at `93f30ca` can
> turn automatic compaction off, and a plugin hook sees each request before it is sent, so a key could probably be
> computed before dispatch, with a proxy serving the hits. That was read and not run. Rejecting such a harness rests
> on the other arguments here: its releases move the prompt (R60), its retries are on by default against `attempts`,
> and its tool sets are permission rules rather than an absent table key.

## Against the positioning

Recorded in policy §10. OpenCode's record survives process death, and a boot sweep resumes unfinished sessions, stopping
after 10 by default (`core/src/session/execution/restart.ts:34,81-92`). It has a write-ahead claim
(`core/src/session/execution.ts:73-80`) *(unchecked)*.

What remains different:

- **It resumes a controller,** injecting "Continue from where you left off" (`restart.ts:16-17`). There is no controller
  here.
- **It has no worker fence.** "The sweep assumes every orphaned claim's owner is dead," which it gets from a single
  managed server (`restart.ts:56-60`). No fence between embedded hosts was found *(unchecked)*.
- **No equivalent of `intent_digest` or `config_hash` was found.**

It has also run, while this has not.

## Not borrowing

| OpenCode has | Why not |
|---|---|
| Doom-loop detection | Excluded by the port notes. In OpenCode it is also dead: only a v1 config validator and a TUI label remain in code (`core/src/v1/config/permission.ts:27`), while its docs still describe it (`web/src/content/docs/permissions.mdx:168`) |
| Running complete tool calls from a truncated stream (`core/src/session/runner/step.ts:119-131`) | The Pi note's rule is stricter, and with no streaming it costs nothing |
| Output-limit continuation, compaction, in-loop retry, session resume, subagents | ADR-0005's exclusion list |
| Argument coercion and tool aliases (`core/src/plugin/tool-input-repair.ts`) *(unchecked)* | Port notes §1.2 |
| Overflow output saved to a generated path in the marker (`core/src/tool-output.ts:88-92`) | The path would move the key. The DeepSeek note rejects the same shape |
| About 40 overflow regexes as runtime logic (`ai/src/provider-error.ts:16-58`) | ADR-0011 rejects text matching. Use them as test cases if a second provider arrives |
| Treating unknown failures as retryable (`ai/src/schema/errors.ts:216`) | ADR-0011: ambiguous stays `provider_refused` |
| In-process recorder as the kept test | ADR-0005: "a recording proxy, not a transport hook" |
| Permission rulesets, asks, `external_directory` | Rules 48–54 are void, and cards have no in-loop approver (ADR-0003) |

## Verdict

Borrow the ideas and adopt no package. The most useful result was finding a likely flaw in this repo's own proxy test.
Rule 63 sends findings to existing documents, so this note is only the record of what was read: policy §10 holds the
positioning, and the rest stay here until someone takes them up.
