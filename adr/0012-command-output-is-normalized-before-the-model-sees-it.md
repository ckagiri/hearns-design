# ADR-0012: Command output is normalized before the model sees it

**Status:** Accepted
**Date:** 2026-11-04
**Amends:** core §8, §8.1.1, §11; policy §1.6; `opendev-port-notes` §1.1, §1.2; `jig-sketch.py`
`dispatch_tool` and the check path; PLAN P1-11, P1-22, P2-13
**Adds:** rule 144, which promotes R-new-5 as `PROTOTYPE_v3` asks; R62
**Guarded by:** the normalizer stability tests below; `ReplayMiss`; P1-22
**Informed by:** `earendil-works/pi` at `1bc7076`, read 3 November 2026 and not run here:
`AgentToolResult` keeps `details` and `durationMs` out of provider requests. Odoo `odoo/netsvc.py` at
branch 19.0, read 4 November 2026: `init_logger`'s default format.

## Context

The cache key is the bytes on the wire (core §8), so anything a command prints reaches the key of every
later call in that attempt. R-new-5 names the failure: replay dies at the second model call and looks
like a cache miss caused by the model. `jig-sketch.py` answers it with a required `normalize` on
`ToolImpl`. Its footer also says, *"This is not in core or policy and it belongs in one of them."* It
is still in neither. Five problems follow.

**The hand-written runtime's own plan leaves it out.** `opendev-port-notes` §1.1 takes five tool
members and §1.2 four execution steps, and `normalize` is in neither. Its "attach duration" step and its
use of core §4.3's "last 40 lines + timing" would put changing values into what the model reads.

**Two paths in the sketch skip it.** `dispatch_tool` normalizes the tool's output, then appends each
`post_tool_call` rung's output unnormalized. Layer 7 renders a stored check log, and a replayed check
produces a new one.

**ADR-0011 made a volatile name visible.** Its database and worktree names carry the attempt number.
Its promise that a free retry's prompt "stays byte-identical" holds only until a tool output names one.
Odoo's default format is `%(asctime)s %(pid)s %(levelname)s %(dbname)s %(name)s: %(message)s
%(perf_info)s`, so its log lines carry a timestamp, a PID and the database name. Nothing specifies what
`strip_timings_and_paths` does with them.

**The hash does not see normalizers.** `kind_hash` covers `tool_schemas(k)`. A changed normalizer changes
what cards read, and no named input moves. Core does not say whether `source_commit` covers harness code.

**Core overstates what the cache buys.** §8 says a retried card "re-runs and every model call it
previously made hits the cache". On a charged retry none do: attempt 2 raises effort, which is in the key
(rule 108), and attempt 3 changes the model. Layer 7 changes both. A dead worker is a charged failure, so
its retry misses too. Only replay and free retries can hit.

## Decision

1. **Rule 144: anything a command produced is normalized before it can enter model-visible text.** This
   covers tool results, `post_tool_call` rung output and layer 7's check output. A check type declares a
   required normalizer, as a tool does. Normalize first, then truncate.
2. **A normalizer removes only what differs between two correct runs:** clock times, durations, PIDs,
   `card_<key>_attempt<n>` names, and ordering that carries no meaning. Exit status, failure text and
   anything else a card can act on stay. Domain patterns, such as Odoo's log prefix, sit in a table that
   enters the hash.
3. **Replay re-executes tools and checks. Only the model is served from cache.** Core §8 says this
   explicitly, as the sketch already assumes. In a live run a miss costs one model call. In replay it
   raises `ReplayMiss`, which is a detection and corrupts nothing.
4. **What normalization removes stays in the record.** `dispatch_tool` writes `duration_ms` to
   `tool_audit`, and a `raw_ref` when raw and normalized bytes differ, truncated under rule 97. The port
   notes' "attach duration" means this row and never the message.
5. **Normalizers enter `kind_hash`,** each by a version identity, as the adapter's identity does. So do
   the domain pattern tables.
6. **Core §8's claim narrows to what the design delivers:**

   | Case | First call's key | Expected |
   |---|---|---|
   | Replay | unchanged | every call hits; a miss raises |
   | Free retry (ADR-0011) | unchanged | calls hit up to where the failed attempt stopped |
   | Charged retry, including a dead worker | moved by effort or model, and layer 7 | none hit |
   | Reset-from-a-point (§8.2) | unchanged upstream | upstream hits; the raised subtree does not |

   "Checkpointing is mostly solved by accident" is deleted. It is true of free retries alone.
7. **Hits are counted.** A hit writes a `model_calls` row with zero cost and `served_from_cache`, because
   the sketch records only on a put, and §9.1 says the answer should be a query.

**Core §11 gains:**

- **Normalizer stability.** For each tool and check type, two runs with a different clock, PID and
  attempt number give identical bytes. Odoo's test uses a captured real log.
- **Over-stripping.** A failing fixture's normalized output still contains its failure text and exit status.
- **Free-retry hits.** Fail a card with a free class after turn *k*. The retry serves *k* calls from cache.
- **Hash stability.** Changing a normalizer or pattern table moves `kind_hash`.

P1-22's replay tests also cover `post_tool_call` output and a card that reaches attempt 2.

## Alternatives considered

**Leave it in the sketch.** The implementer of P2-13 follows the port notes, which omit it, and the sketch
itself says it belongs elsewhere.

**Send raw bytes and hash a normalized copy.** The model keeps its timings and replay keeps its hits. But
two different prompts then share a key, which breaks "the key is the bytes on the wire", and a response
could be served for a prompt that never produced it.

**Remove the noise at its source,** through test-runner flags or a custom log format. Useful where it is
cheap, and it reduces what a normalizer must do. It cannot be the rule, because it is per tool and cannot
reach every command `bash` may run.

**Freeze the clock in the container.** PIDs and attempt names remain, and timeouts may stop working.

**Record tool outputs and serve them in replay.** Replay would always pass, and would stop being able to
show a difference in the code. That difference is what core §8 says replay is for.

**A `details` field on the tool result, as Pi has.** Pi needs it to carry UI data out of the tool. Here
`dispatch_tool` already holds raw and normalized bytes, so the audit row does the job with no new type.
Pi's idea is kept: the model's view and the record's view are separate.

**Drop what normalization removes.** The cheapest option, and it may prove right. Without `raw_ref`, a
normalizer that strips too much cannot be diagnosed after the fact. See below.

## Consequences

**Good.** R-new-5 becomes a rule with tests. ADR-0011's byte-identical promise holds past the first tool
call. Core stops claiming a benefit charged retries cannot get. Reading a replay miss gets easier, because
known noise can no longer cause one.

**Costs.**
- **A normalizer can hide what a card needed (R62).** A card chasing a slow query sees no timing. If a
  contract needs timing, it should be a check's result rather than a log line.
- **A pattern table is domain code to maintain.** A new log format reaches the model as noise, and the
  symptom is a miss rather than a wrong answer.
- **One content-store write per changed tool output,** plus `tool_audit` and `model_calls` columns, which
  are in the reconstructed `001_initial.sql`.

**Not measured.** None of this has run. The failure is reasoned from the documents and the Odoo format
string, and no replay has been seen to miss. The first stability test is the first evidence.

## Left open

**Should a dead worker's retry raise effort?** A crash says nothing about effort, yet attempt 2 pays the
raised rate and loses every cached call, which is R20's cost by another route. Making `lease_expired` free
would weaken the crash-loop bound. A third shape keeps it charged and lets escalation count only attempts
with a failed check. That is a change to policy §2.2 and rule 68, so it is not decided here.

## What would change our mind

- **Ten real runs with no replay miss caused by a tool or check that lacked a pattern** → the tables are
  margin, and principle 8 applies to them.
- **`raw_ref` is never read to diagnose anything by step 7** → drop it and keep `duration_ms`.
- **Free retries are rare, and their served-call count is small** → stability matters only for replay, so
  normalize less and accept that replay is a test tool with a known list of exclusions.
- **A card is seen failing because a normalizer removed what it needed** → R62 is real. Narrow the
  normalizer first, and reopen this ADR only if the needed value cannot be stable.
