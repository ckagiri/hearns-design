# ADR-0015: What an attempt must record from the first run

**Status:** Proposed, held until implementation. Reviewed before the first plan item that builds what it decides, and
settled in full before any run, because rows a run never wrote cannot be recovered.
**Date:** 2026-11-06
**Would amend:** core §4.1, §4.3, §5.7, §7, §8.1.1, §11 (no §13 trigger applies); ADR-0005's proxy test;
`001_initial.sql`; `harness/ledger/sql/` `commit`, `commit_attempt`, `end_attempt`, `review_return`;
`queries/lessons.sql`; `jig-sketch.py`; `tests/ledger/`
**Would add:** rules 157–159; R66. ADR-0016's draft already uses rules 153–156 and R65.
**Guarded by:** the tests under each decision
**Informed by:** `borrow-notes.md` B1, B2, B3, B23-B27, B26, B31, B51, B54 and B56. The argument rests on
this design's own paths. The SQL ran on a throwaway Postgres 16.10 against copies of the statements. No worker
or model has run any of it.

## Context

Rows never written cannot be recovered, and these questions have no row.

- **Which rung failed?** `CheckResult` has no rung (`jig-sketch.py:695-697`), and `check_ref` is an output
  hash (`001_initial.sql:114`). `rung_results` was in `initial_plan.md:279` and `files/PILOT.md:90,226`, and
  was lost.
- **What was the model sent?** Core calls an old run "inspectable exactly as each step saw it"
  (`harness-core-v3.md:772`). `prompt_ref` is written before the turn loop (`jig-sketch.py:560`), and only
  `commit.sql` stores it.
- **Did a person loosen the check before this went green?** `review_return.sql` overwrites `contract` and
  `check_spec`, and no file under `harness/ledger/sql/` inserts into `reviews`, though core requires it
  (`harness-core-v3.md:758`).
- **What did a failed attempt return?** `fail.sql` never stores it, and `model_cache` has a TTL (core §4.4).
  The note's "`commit.sql` overwrites" is the smaller loss: it runs once per card, and a parked payload is in
  `refusal`.

## Decision

### 1. An attempt records each selected rung by name (rule 157)

**The id is `Rung.name`:** a required slug, `^[a-z][a-z0-9_]*$`, unique in `checks.yaml`, checked at startup.
The worked run has it (`worked-run-catalog.md:152`), and the sketch's `Rung` lost it
(`jig-sketch.py:230-240`). A name is never reused for a different check, and renumbering leaves it alone.

**`task_attempts.rung_results jsonb` maps name to result:** `{"static": "passed", "unit": "failed",
"integration": "not_reached"}`. `run_oracle` seeds `not_reached` from `rungs_for` and overwrites each rung it
reaches with `passed`, `failed` or `unavailable`. An absent key was not selected. `{}`: the oracle ran with no
rungs. NULL: no oracle reported. `failed` always means the rung rejected the card, so a held `expect: FAIL`
records `passed` and isn't counted as a catch (ADR-0016). The column decides nothing (rule 145).

**`check_spec` keeps selecting by `rung: int`, and rule 137 stands.** Layer 5 renders `check_spec`
(`jig-sketch.py:373`), so names there would put hidden rungs' names in the prompt (principle 5) and let a
rename move bytes. `render_rungs` doesn't gain the name. `check_ladder(k)` in `kind_hash` covers it
(`harness-core-v3.md:842`), since a rename changes what the record groups by. The cache key excludes
`kind_hash` (`jig-sketch.py:478`).

**Closing paths.** `commit_attempt.sql` and `end_attempt.sql` gain the column. A reaper flip after the
worker's close changes nothing, because `end_attempt.sql:4` matches only `ended_at IS NULL`. A dead worker,
drain and `rekind_split` write NULL. `reaper_deadline_close.sql` is unchanged. **The free-retry path drops
results today:** `land` raises `CHECK_UNAVAILABLE` (`jig-sketch.py:830`) and `worker`'s handler calls
`ledger.fail` with the class alone (`:880-887`), as it does after `pre_commit` (`:872`) and `SplitRejected`
(`:877`). `ledger.fail` is elided, so this is inferred. These handlers pass `rung_results` and nothing else:
passing `check` would write `check_ref` on an evidence class and move layer 7.

**`post_tool_call` rungs stay out.** They are best-effort, repeat within an attempt and decide nothing. Their
text reaches the wire (decision 2), so nothing is unrecoverable.

**Layer 7 never reads the column.** `last_evidence_attempt.sql:3` keeps its select list, so hidden results
stay one bit, and rule 147's byte-identical retry holds.

`queries/lessons.sql` gains this. No threshold is ported.

```sql
select a.kind, a.config_hash, r.key as rung, count(*) filter (where r.value <> 'not_reached') as reached,
       count(*) filter (where r.value = 'failed') as caught
  from task_attempts a, jsonb_each_text(a.rung_results) r group by 1, 2, 3;
```

**Core §11 gains:** fail the second of three rungs and read all three values, with an unselected rung absent.
A free retry keeps results. A worker's close survives the reaper's. Attempts differing only in `rung_results`
render the same layer 7.

### 2. Each model call keeps the bytes it sent (rule 158)

`model_calls` gains `request_ref text NOT NULL`, set by `content.put(wire, "request")` right after the key
(`jig-sketch.py:478`). It reads `wire` and returns a hash, so the key and hit rows' cost don't move.

**One column answers it.** `_turn_loop` sends `req.blocks + as_blocks(messages)` (`:578`), so each wire holds
every earlier tool result as normalized, `post_tool_call` text, repair prompts and layer 7. Tool arguments are
in the next wire's assistant turn (inferred: `as_assistant` is undefined). `raw_ref` stays, because
normalizing removed what it holds. API keys are in headers, not the wire, if the adapter keeps them out of the
body.

**`tasks.prompt_ref` and `join_for_audit` go.** The first call's `request_ref` replaces them, on every
attempt. One ref per block isn't needed: `build` emits one content block per layer (`:450,453`; inferred,
`as_content_block` is elided).

**Every branch writes a row.** A live provider failure writes none today (`:493-495`), so `record_call` is
added there, at cost 0, and the budget sum doesn't move. A worker that dies mid-call leaves bytes and no row,
and its retry resends them.

**The one change to sent bytes.** `complete` posts `body` (`:460`), so the transport serializes it and the
stored `wire` may not be what was sent. Post `wire` verbatim: the key is unchanged, the JSON is the same, and
nothing recorded is invalidated. ADR-0005's proxy test becomes: `content.get(request_ref)` equals the observed
body, and the key equals `sha256(observed + identity)`. If the transport can't send raw bytes, the test
compares parsed JSON and rule 158 says "what the adapter built".

**Storage.** Dedupe helps only with whole identical wires: replay, hits, and free or crash retries add
nothing. Inside an attempt each wire is the last plus a turn, so the total is quadratic: at 20 turns (`:208`)
with invented sizes, 40 KB rising 4 KB a turn, 1.6 MB per attempt before compression. Core §4.3 gains `request
→ full`, because a truncated wire isn't the wire, and `put` needs the type `001_initial.sql:191` says it
lacks.

**Core §11 gains:** every ref resolves, including on a hit and a failed call. A tool result and a repair
prompt appear in a later stored wire. No stored wire contains a hidden rung's output
(`harness-core-v3.md:1084`).

### 3. A verb records what it overwrote, and a call what it returned (rule 159)

**`review_return.sql` writes its own `reviews` row,** as `claim.sql` writes its attempt, so it can't be
skipped. The `UPDATE`'s clauses are unchanged.

```sql
WITH before AS (SELECT id, contract, check_spec FROM tasks WHERE id=$1 AND state='awaiting_review' FOR UPDATE),
returned AS (UPDATE tasks SET …  WHERE id=$1 AND state='awaiting_review' RETURNING id)
INSERT INTO reviews (task_id, verb, had_open, reason, detail)
SELECT b.id, $8, $9, $10, jsonb_build_object('deadline_at', $7::timestamptz,
         'was', jsonb_build_object('contract', b.contract, 'check_spec', b.check_spec))
  FROM before b JOIN returned r ON r.id = b.id;
```

**`reviews.detail` exists only in the reconstructed schema** (`001_initial.sql:228`, `[inferred]` at `:217`),
and nothing writes it. It gets two jobs: ADR-0013's new deadline, and what the verb overwrote. A copy on the
attempt wouldn't do: a gated child is emitted `awaiting_review` (`jig-sketch.py:741`), so a person can edit it
before any attempt exists. `queries/lessons.sql` gains:

```sql
select t.id, r.verb, r.reason, r.detail #> '{was,check_spec}' as was, t.check_spec as now
  from reviews r join tasks t on t.id = r.task_id
 where t.state = 'done' and t.project = :p
   and r.detail #> '{was,check_spec}' is distinct from coalesce(t.check_spec, 'null');
```

**`model_calls.response_ref text`,** NULL on a failed call, is written beside `request_ref`, without the
reasoning trace (policy §2.0.3). An attempt's return is its last row. `CachedModel` cannot be bypassed
(ADR-0005), so no handler can drop it as in decision 1.

**ADR-0014's argument stands, applied field by field.** It rejected whole-task revisions because "the
statements read overwrite few fields that any query needs", noting that no lessons query reads `check_spec`.
Now one does, so `check_spec` is kept, with `contract`, which the same verb overwrites. Nothing else on item
3's list earns a column: `input_digest` already exists as the first call's `cache_key`, `prompt_ref` is the
first `request_ref`, `result_ref` and `result_summary` are inside `response_ref`, and `rung_results`' keys
show what each attempt selected.

**Tests,** passed on Postgres 16.10: an edit before the first claim keeps the old `check_spec`. A card not in
review writes no row. An unknown verb rolls the update back.

### What moves for replay

Decisions 1 and 3 move no sent byte and no key: `render` reads none of the new columns, and an `edit` moves
layer 5 as it does today. Decision 2 moves the transport's serialization to the bytes the key already covers.
A hit row gains two refs, and its cost and flag are unchanged.

## Not decided here

Unknown cost (`cost_source`), database-enforced immutability, promotion rules, per-rung thresholds, any
scorecard query, any retention policy (including a wire's `expires_at`), item 1's test-first gate, the six
unfinished verbs.

## Open for the owner

- **Secrets (R66): recommend deferring, on a condition.** Tool output already reaches the store through
  `raw_ref` and the provider receives it, but now all of it stays. A refuse-to-store step would run before
  dispatch, so a match stops the call and needs a failure class and a route. What a tool can read depends on
  B36, which is unsettled. **No run where a tool can reach a real credential until this is
  decided.**
- **Integer selection: recommend keeping it.** After a renumbering an integer can select the wrong rung: in a
  reset across configs (core §8.2), or where a cached `split` response survives an inserted hidden rung (repos
  note, New 9). `rung_results` shows what ran but doesn't prevent it. Names would need hidden rungs filtered
  from layer 5, which moves bytes.

## Alternatives considered

**An absent key means unreached,** as B1 first had it: it can't separate unreached from unselected
without `check_spec` at the attempt and a lookup from integers to names. **`result_ref` on the attempt:**
every handler must pass it. **One ref per block:** it dedupes the growth, but what's stored is no longer what
was sent. **Only the last wire per attempt:** a crash loses it, and prefix extension is untested.

## Consequences

**Good.** Core's "inspectable" sentence becomes true, B31 and step 7's scorecard (B78) have
their inputs, and `prompt_ref` leaves twelve sketch lines.

**Costs.**
- **Quadratic bytes per attempt,** unmeasured, and one insert per call.
- **A dead worker's reached rungs are lost,** because results are written at close.
- **`NOT NULL` breaks five fixtures:** `tests/ledger/verify_schema.py:135,175,176,179` and
  `verify_files.py:273`. `verify_files.py:258` and its `end` and `commit` helpers change, and core §4.1 and
  §5.7 move in the same commit.
- **If `as_assistant` carries thinking blocks, wires keep traces for `ok` outcomes,** against policy §2.0.3.
  Not checked.

**R66: the record holds whatever tools printed,** with no expiry and no refusal yet.

## What would change our mind

- **Stored wires dominate the database by run ten** → keep each attempt's last wire, once a test shows each
  call extends the last.
- **No query by step 7 reads `not_reached` or `response_ref`** → drop them.
- **A renumbering selects a wrong rung in a real run** → move `check_spec` to names and filter hidden ones
  from layer 5.
