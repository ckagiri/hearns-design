# Worked run — drug catalog service

**Status:** Reference. Read, do not edit.
**Date:** 2026-08-18
**Project:** `catalog` — FastAPI + Postgres drug catalog, anchored on `spec/catalog.schema.yaml`,
exporting to the Odoo pharmacy module.
**Purpose:** one run traced end to end, happy and unhappy paths, with an audit of which mechanisms
actually fired. Sibling of `worked-run-odoo`; a second instance of the same document type, not a new
one.

> **Note on filing.** `guard_invariants.py` blocks new `docs/*.md`. That is correct behaviour — the
> hook cannot distinguish a new reference artifact from a new design document. Adding this file is a
> deliberate override, recorded here so the next person knows it was a decision.

---

## 1. The anchor

Fragment of `spec/catalog.schema.yaml`. Two independent drafts were produced at different effort
levels and diffed (R44/R48); the diff and its resolution are in `spec/DRAFT-DIFF.md`.

```yaml
# spec/catalog.schema.yaml   (fragment)
#
# CONSTRAINT ON DERIVATION — do not remove.
# The FastAPI service and the Odoo pharmacy module are BOTH derived from this file,
# independently. Neither is generated from the other. Divergence between them is a
# computed check on this anchor, and that check dies the moment one is derived from
# the other (R48: correlated samples masquerading as independent).

version: 3
entities:
  manufacturer:
    fields:
      id:            {type: uuid, pk: true}
      name:          {type: text, required: true, unique: true}
      country_code:  {type: text, required: true, pattern: '^[A-Z]{2}$'}

  drug:
    fields:
      id:                    {type: uuid, pk: true}
      registration_code:     {type: text, required: true, unique: true}
      inn:                   {type: text, required: true}      # generic name
      brand_name:            {type: text}
      form:                  {type: enum, values: [tablet, capsule, syrup, injection, cream]}
      strength_value:        {type: numeric, required: true}
      strength_unit:         {type: enum, values: [mg, g, ml, iu, mcg]}
      atc_code:              {type: text, pattern: '^[A-Z][0-9]{2}[A-Z]{2}[0-9]{2}$'}
      schedule:              {type: enum, values: [none, II, III, IV, V], required: true}
      prescription_required: {type: bool, required: true}
      status:                {type: enum, values: [active, withdrawn], required: true}
      manufacturer_id:       {type: uuid, fk: manufacturer.id, required: true}
    invariants:
      - id: INV-DRUG-01
        statement: |
          A drug whose schedule is a controlled schedule (II, III, IV, V) MUST have
          prescription_required = true.
        direction: |
          This is an implication, not an equivalence. The converse is FALSE:
          many prescription-only drugs are not controlled (most antibiotics).
        # ^ this three-line note exists because the first draft omitted it and the
        #   second draft's reviewer asked "is this iff?". See spec/DRAFT-DIFF.md.

  pack:
    fields:
      id:          {type: uuid, pk: true}
      drug_id:     {type: uuid, fk: drug.id, required: true, on_delete: cascade}
      pack_size:   {type: int, required: true}
      unit:        {type: enum, values: [tablet, capsule, ml, vial]}

export:
  endpoint: GET /catalog/export
  cursor: since        # ISO8601; returns records changed at or after this instant
```

---

## 2. Configuration

### `config/roles.yaml`

Every value explicit. A missing model, effort or tier is a startup error, never a fallback
(rules 72, 107). Tool sets are enumerated and narrow; absence is a gate (rule 135, policy §1.6).

```yaml
roles:
  split:
    kinds:   [split]
    tiers:   [strong]
    model:   opus
    effort:  high
    jig:     split
    tools:   [read, grep, glob]           # cannot write: a splitter that edits is an executor
    lease_ttl: 120s

  execute_cheap:
    kinds:   [execute]
    tiers:   [cheap]
    model:   haiku
    effort:  minimal
    temperature: 0
    jig:     execute
    tools:   [read, grep, glob, write, edit, bash]
    lease_ttl: 60s

  execute_strong:
    kinds:   [execute]
    tiers:   [strong]
    model:   opus
    effort:  high
    jig:     execute
    tools:   [read, grep, glob, write, edit, bash]
    lease_ttl: 60s

  verify:
    kinds:   [verify, re_verify]
    tiers:   [middle]
    model:   sonnet
    effort:  medium
    jig:     verify
    tools:   [read, grep, glob]           # RULE 135 AS A GATE.
                                          # A verifier with no write tool cannot fix
                                          # what it reviews. Not instructed — unable.
    lease_ttl: 90s

  integrate:
    kinds:   [integrate]
    tiers:   [middle]
    model:   sonnet
    effort:  medium
    jig:     integrate
    tools:   [read, grep, glob, edit, bash]
    lease_ttl: 90s

  digest:
    kinds:   [digest]
    tiers:   [cheap]
    model:   haiku
    effort:  minimal
    jig:     digest
    tools:   [read]                       # no bash, no write
    lease_ttl: 30s
```

### `config/checks.yaml`

Rung 0 runs on the host, after the card returns. The card cannot see it, edit it, or run it.

```yaml
ladder:
  - rung: 0
    name: static
    where: host                 # hidden oracle — unreachable from the workspace
    timeout: 30s
    steps:
      - ruff check . && ruff format --check .
      - mypy src
      - python -c "import yaml,sys; yaml.safe_load(open('spec/catalog.schema.yaml'))"
      - python tools/spec_lint.py            # anchor internal consistency
      - python tools/placeholder_scan.py     # TODO / pass / NotImplementedError

  - rung: 1
    name: unit
    where: workspace
    timeout: 120s
    steps: ["pytest tests/unit -q"]

  - rung: 2
    name: integration
    where: workspace
    timeout: 300s
    steps:
      - alembic-free migrate against the attempt's DB clone
      - pytest tests/integration -q

  - rung: 3
    name: oracle
    where: workspace
    timeout: 300s
    steps:
      - python tools/introspect.py --spec spec/catalog.schema.yaml --db $CLONE_URL --routes
      # ^ diffs LIVE DB schema and LIVE route table against the anchor. No model call.
      - schemathesis run --checks all http://localhost:8000/openapi.json
      # ^ generates cases from the spec. The card did not write these and cannot edit them.
```

### Run start

```sql
INSERT INTO runs (id, project, config_pin, intent_digest, started_at)
VALUES ('r-2026-08-18-01', 'catalog', $1, $2, now());
```

```jsonc
// runs.config_pin — resolved, not symbolic (rule 134)
{
  "image_digest":    "sha256:6a1f…",
  "source_commit":   "9c4e2b1",
  "spec_sha":        "sha256:b71d…",       // the anchor is pinned like code
  "lockfile_sha":    "sha256:0e5a…",       // includes the card runtime (R60)
  "runtime":         {"pkg": "pydantic-ai", "version": "1.4.2"},
  "template_db_sha": "sha256:44c8…",
  "kind_hash": {
    "split":   "sha256:1a2b…",
    "execute": "sha256:3c4d…",
    "verify":  "sha256:5e6f…"
  },
  "resolved_model_params": {
    "opus":   {"model": "claude-opus-5", "thinking": {"type": "enabled", "budget_tokens": 16000}},
    "sonnet": {"model": "claude-sonnet-5", "thinking": {"type": "enabled", "budget_tokens": 4000}},
    "haiku":  {"model": "claude-haiku-4-5", "thinking": {"type": "disabled"}}
  }
  // ^ RULE 134: resolved provider parameters, never the label "high". A label whose
  //   meaning varies by vendor cannot support a comparability claim (R59).
}
```

---

## 3. The card graph

```
t-9f2a  split  ─────────────────────────────────────────── strong
   │
   ├── .1  execute   schema + migration 002_catalog.sql      cheap    ✓
   ├── .2  execute   manufacturer routes                     cheap    ⚠ spec_conflict → §5.1
   ├── .3  execute   drug routes                             cheap    ✓  → §4
   ├── .4  execute   pack routes                             cheap    ⚠ reaped → §5.3
   ├── .5  execute   INV-DRUG-01 tests (RED)                 middle   ✓  ← test card
   ├── .6  execute   INV-DRUG-01 implementation              cheap    ⚠ specimen → §5.2
   ├── .7  execute   export endpoint                          middle   ⚠ mismatch → §5.4
   ├── .8  verify    (siblings .1–.7 against root intent)     middle   ✓
   └── .9  integrate  rung 1 on the merged tree               middle   ✓
t-9f2a.digest                                                 cheap    ✓

22 cards total including retries, re_verify and one spec_revision.
```

**Readiness is a pure function of the graph.** Nothing writes `ready`; nothing can lie about it.

```sql
-- the predicate, from core §5.1
SELECT t.* FROM tasks t
WHERE t.state = 'pending'
  AND NOT EXISTS (
    SELECT 1 FROM tasks dep
    WHERE dep.id = ANY(t.depends_on)
      AND (dep.state <> 'done'
           OR EXISTS (SELECT 1 FROM tasks kid
                      WHERE kid.id LIKE dep.id || '.%'      -- tasks_prefix_idx
                        AND kid.state <> 'done'))
  );
```

### Split output (abridged)

```jsonc
{
  "children": [
    {
      "id": "t-9f2a.5",
      "kind": "execute", "tier": "middle",
      "contract": "Write failing tests for INV-DRUG-01 from the anchor. Do NOT implement.",
      "touch_set": ["tests/unit/test_inv_drug_01.py"],
      "check": "pytest tests/unit/test_inv_drug_01.py — MUST FAIL (rule 82)",
      "depends_on": ["t-9f2a.1"],
      "open_questions": []
    },
    {
      "id": "t-9f2a.6",
      "kind": "execute", "tier": "cheap",
      "contract": "Implement INV-DRUG-01 validation on drug create/update.",
      "touch_set": ["src/catalog/validation.py"],
      // RULE 83: the test file is NOT in the touch set. The implementing card
      // cannot edit the check that judges it.
      "depends_on": ["t-9f2a.3", "t-9f2a.5"],
      "open_questions": []
    },
    {
      "id": "t-9f2a.7",
      "kind": "execute", "tier": "middle",
      "contract": "Implement GET /catalog/export with a `since` cursor.",
      "touch_set": ["src/catalog/routes/export.py"],
      "depends_on": ["t-9f2a.2", "t-9f2a.3", "t-9f2a.4"],
      "open_questions": [
        {
          "id": "oq-3",
          "text": "Cursor semantics when only a pack row changes: the anchor says
                   'records changed at or after', but does a pack edit make its parent
                   drug exportable? I did not specify this.",
          "closed_by": null
        }
      ]
    }
  ]
}
```

### Emit-time gates — mechanical, no model call

```python
def gate_split_output(children, parent) -> list[Rejection]:
    r = []
    # touch-set disjointness across siblings
    for a, b in combinations(children, 2):
        if overlap := set(a.touch_set) & set(b.touch_set):
            r.append(Rejection(a.id, b.id, f"touch_set overlap: {overlap}"))
    # rule 83: no implementing card may name a test file written by a sibling test card
    tests = {p for c in children if c.is_test_card for p in c.touch_set}
    for c in children:
        if not c.is_test_card and (bad := set(c.touch_set) & tests):
            r.append(Rejection(c.id, f"names a sibling's test file: {bad}"))
    # single-execute-child split is a no-op wrapper
    if len([c for c in children if c.kind == "execute"]) == 1:
        r.append(Rejection(parent.id, "split produced one execute child"))
    return r
```

All gates passed at T+0:04. Cost: 0.3s, no model call.

---

## 4. Happy path — `t-9f2a.3`, drug routes

### Claim

One statement. Never a `SELECT` then an `UPDATE` (core §5.3).

```sql
WITH candidate AS (
  SELECT id FROM tasks
  WHERE state = 'pending' AND kind = ANY($1) AND tier = ANY($2)
    AND <readiness predicate>
  ORDER BY created_at
  FOR UPDATE SKIP LOCKED
  LIMIT 1
)
UPDATE tasks t
   SET state = 'leased',
       lease_holder = $3,
       attempts = t.attempts + 1,
       lease_expires_at = now() + $4::interval
  FROM candidate c
 WHERE t.id = c.id
RETURNING t.*, t.attempts AS fence;
```

`$1`/`$2` are the role's kinds and tiers — **this is the router**, and it is SQL (core §3.4).

### Workspace triple

```python
ws = Workspace.provision(task, run)
#   git worktree add .wt/t-9f2a.3 <base_commit>      — host
#   docker run --network=none --cgroup … --mount ro  — container
#   createdb catalog_t9f2a3 -T catalog_template      — 180ms clone
```

### The card runtime (ADR-0004, policy §1.6)

```python
# The cache IS the model interface, not a wrapper around the library (core §8).
# A call path that bypassed it would have to bypass the Model ABC, which the
# runtime has no way to do.
class CachedModel(Model):
    def __init__(self, inner: Model, store: ModelCache, run_id: str):
        self.inner, self.store, self.run_id = inner, store, run_id

    async def request(self, messages, model_settings, model_request_parameters):
        key = sha256_of(
            serialize_wire_request(messages, model_settings, model_request_parameters)
            # ^ the BYTES ON THE WIRE — the library's assembled system prompt and its
            #   generated tool schemas included. Rule 127 one layer down: hash the
            #   rendered artifact, not the inputs that render it.
        )
        if hit := await self.store.get(key):
            return hit.response                      # replay: zero outbound calls
        resp = await self.inner.request(messages, model_settings, model_request_parameters)
        await self.store.put(key, resp, run_id=self.run_id)
        return resp


agent = Agent(
    model=CachedModel(AnthropicModel("claude-haiku-4-5"), cache, run.id),
    instructions=render_jig("execute", layers, task),   # layers 0–8, cached per scope
    output_type=ExecuteResult,                          # the jig's ONE output schema
    tools=tools_for_role("execute_cheap"),              # rule 135
)

async with agent.iter(task.contract) as run_:
    async for node in run_:
        record_model_call(node)     # → model_calls (task_id, attempt, seq)
        record_tool_use(node)       # → tool_audit, INCLUDING denials
```

**Bounds.** Lease TTL and `deadline_at` are host-side and unreachable from the card. There is no
step cap: a cap is a guess about how many steps a task needs, and the model already signals
completion by returning text instead of a tool call. Context exhaustion is **not** bounded — R61,
recorded with no detector.

### The loop, as it ran

```
T+0:31  read   spec/catalog.schema.yaml                     (4.1k tok)
T+0:33  read   src/catalog/routes/manufacturer.py           — pattern to follow
T+0:41  write  src/catalog/routes/drug.py                   (218 lines)
T+0:52  bash   pytest tests/unit -q          → 3 failed     ← failure as observation,
T+0:58  edit   src/catalog/routes/drug.py                     not exception (§1.5 schema repair)
T+1:04  bash   pytest tests/unit -q          → passed
T+1:06  return ExecuteResult
```

6 model calls, 41.2k in / 3.8k out, $0.014.

### Result summary

```jsonc
{
  "outcome": "done",
  "summary": "Added CRUD routes for drug at /drugs, with pagination and filtering by
              status and manufacturer_id. Pydantic models derived from the anchor.",
  "touch_set_actual": ["src/catalog/routes/drug.py", "src/catalog/models/drug.py"],
  "decided": [
    {"what": "Page size default 50, max 200 — the anchor does not specify.",
     "cost_if_wrong": "low; a query parameter change"}
  ],
  "summary_schema_version": 3
}
```

### Commit — a harness operation, not a card operation

The card returns. It does not commit. Hooks run **on the host**, after the container is gone.

```python
def pre_commit(task, ws) -> list[Violation]:
    v = []
    diff = ws.diff_paths()                         # what actually changed
    if extra := set(diff) - set(task.touch_set):
        v.append(Violation("touch_set", extra))    # ← highest-firing hook in both runs
    v += namespace_check(diff)                     # AST + XML parse over the diff
    v += set_difference_check(task)                # ADR-0001, see §5.4
    v += echo_check(task)                          # decided restating open_questions
    return v
```

`touch_set_actual` included `src/catalog/models/drug.py`, which was **not** in the declared set.
The hook fired. The model file is a legitimate dependency of the routes, so the human approved an
`edit` verb widening the contract, and the card committed at T+1:19. **Cost of the hook: 40ms.
Value: the contract now matches reality, so the next card's disjointness check is trustworthy.**

---

## 5. Unhappy paths

### 5.1 `t-9f2a.2` — refusal, and a false positive that ADR-0001 already fixed

The anchor requires `manufacturer.country_code` but the export contract's example payload showed a
`country_name`. The card **refused rather than resolving toward the modal answer**:

```jsonc
{
  "outcome": "spec_conflict",
  "summary": "The anchor defines country_code (ISO-2). The export example shows
              country_name. Both cannot be right. I have not chosen.",
  "decided": [],
  "cost_if_wrong": "high — the Odoo side derives from the same anchor, so a wrong
                    choice here diverges two implementations silently"
}
```

→ `awaiting_review` at T+0:47. Human used `edit`, approving a `spec_revision` that fixed the
example. The revision cited open question `oq-1`, so:

```sql
UPDATE tasks
   SET contract = jsonb_set(contract, '{open_questions,0,closed_by}', '"sr-4"')
 WHERE id = 't-9f2a.2';
```

**Without `closed_by` this would have produced a false positive on the very next card.** An open
question closed upstream can never be matched by any `decided` entry, because the executor had
nothing left to decide. That is ADR-0001's amendment 1, and this run is the second time it earned
itself.

### 5.2 The specimen — `t-9f2a.6`, and five mechanisms that passed

The invariant is an **implication**:

```
schedule ∈ {II,III,IV,V}  ⇒  prescription_required = true
```

The card implemented the **converse**:

```python
# src/catalog/validation.py — AS WRITTEN BY THE CARD
def validate_inv_drug_01(drug: Drug) -> None:
    if drug.prescription_required and drug.schedule == Schedule.NONE:
        raise ValidationError("INV-DRUG-01: prescription drugs must be scheduled")
```

Two failures in one, and both are real:

| Case | Correct | As written |
|---|---|---|
| Controlled, `prescription_required=false` | **reject** — the case the rule exists for | accepted ✗ |
| Uncontrolled, `prescription_required=true` (most antibiotics) | accept | **rejected** ✗ |

**What passed it:**

| # | Mechanism | Result | Why it could not catch this |
|---|---|---|---|
| 1 | Rung 0 static | pass | Syntactically perfect, typed, no placeholder |
| 2 | The card's own unit tests | pass | It wrote fixtures for the two agreeing cases |
| 3 | Rung 3 introspection | pass | The field exists, the constraint exists, the route exists. Structure is right; direction is not structural |
| 4 | Schemathesis | pass | The spec encodes types and formats, not this invariant's direction |
| 5 | Verify reading the summary | pass | The summary said *"added prescription-requirement validation for controlled substances."* Accurate about intent |
| 6 | `decided` / `open_questions` | pass | `decided` was **empty, and correctly so** |

That sixth row is this design's own reasoning observed rather than argued: **drift is resolving an
ambiguity you did not register as one.** The card never noticed it was choosing a direction, so it
had nothing to report. An empty `decided` here is honest, not negligent.

**What caught it:** `t-9f2a.5`, the test card, written earlier by a different role at a different
tier, from the anchor — including the three-line `direction:` note that the second schema draft's
reviewer had asked for.

```python
# tests/unit/test_inv_drug_01.py — written by t-9f2a.5, NOT in t-9f2a.6's touch set
def test_controlled_without_prescription_is_rejected():
    with pytest.raises(ValidationError):
        validate_inv_drug_01(make_drug(schedule="II", prescription_required=False))

def test_prescription_only_but_unscheduled_is_allowed():
    validate_inv_drug_01(make_drug(schedule="none", prescription_required=True))
```

```
T+2:14  rung 1 → 2 failed
        FAILED test_controlled_without_prescription_is_rejected  — DID NOT RAISE
        FAILED test_prescription_only_but_unscheduled_is_allowed — ValidationError
```

Attempt 1 failed the check. Attempt 2 (same card, `attempts=2`, same cheap tier) read the failures,
inverted the implication, passed at T+2:31.

**The card could not have made this go away.** `tests/unit/test_inv_drug_01.py` was not in its touch
set, so the `pre_commit` touch-set hook would have rejected the commit had it tried. The check was
written by a different party, at a different time, with different context, and the party being
checked could not reach it.

### 5.3 `t-9f2a.4` — container OOM, reap, and a stale writer

```
T+1:52  lease acquired, attempts=1, fence=1, expires T+2:52
T+2:10  container OOM-killed mid-write; the worker process survives, unaware
T+2:52  lease expires
T+2:53  reaper fires from an unrelated worker
```

**Kill-first order.** Requeue-first would put two live processes in one worktree.

```sql
-- 1. kill the container   2. drop the clone   3. git reset --hard && git clean -fdx
-- ONLY THEN:
UPDATE tasks
   SET state = 'pending', lease_holder = NULL, lease_expires_at = NULL
 WHERE state = 'leased' AND lease_expires_at < now();
```

At T+2:56 the original worker finished its model call and tried to commit against fence 1:

```sql
UPDATE tasks SET state='done', result_summary=$1
 WHERE id='t-9f2a.4' AND lease_holder=$2 AND attempts=$3;   -- $3 = 1
-- UPDATE 0
```

`attempts` is now 2. **Zero rows. The stale write is rejected and the worker releases quietly.**
Fencing guarantees a stale writer cannot commit; kill-before-requeue guarantees it cannot write
either.

### 5.4 `t-9f2a.7` — the set difference fires, and one residual escapes

The splitter had flagged `oq-3`: does a pack-only change make its parent drug exportable? The
executor's `decided` was silent. The hook needs no model call:

```python
def set_difference_check(task) -> list[Violation]:
    open_ids = {q["id"] for q in task.contract["open_questions"]
                if q.get("closed_by") is None}          # ← ADR-0001 amendment 1
    addressed = {d.get("addresses") for d in task.result["decided"]}
    if unresolved := open_ids - addressed:
        return [Violation("unresolved_open_question", unresolved)]
    return []
```

→ `awaiting_review` at T+3:22. The human ruled that a pack change **does** bump the parent's
`updated_at`, recorded with `cost_if_wrong: high — the Odoo side silently misses updates`, and the
card re-ran with the ruling in its contract.

**The residual.** The same card also decided that `since` is inclusive at the boundary
(`updated_at >= since`), which will re-export one record per sync forever. Neither party registered
it: the splitter did not flag it, so the set difference had nothing to fire on, and `decided` was
silent because the executor never noticed a choice. Rung 3 passed — the endpoint exists and matches
the spec. Verify passed — the summary was accurate.

**Nothing caught it.** This is failure mode §16.3, the honest limit of §8.3: where both parties fail
to notice, no mechanism in this design fires. It was found four days later by the Odoo side
receiving duplicates. Recorded here because it is evidence about ADR-0001's residual, not a cost of
this run.

---

## 6. Mechanism audit

| Mechanism | Fired | Cost | Verdict |
|---|---|---|---|
| Readiness predicate | every claim | ~2ms | Load-bearing. Zero orchestration code |
| Claim `SKIP LOCKED` | 31× | ~3ms | No double-claim under 4 workers |
| **Touch-set `pre_commit` hook** | **4×** | **40ms** | **Highest-firing, cheapest in the design** |
| Fencing on `attempts` | 1× (§5.3) | 0 | Rejected a stale commit that would have corrupted a reaped card |
| Reaper, kill-first | 1× | 2.1s | Correct order mattered; requeue-first would have raced |
| **Test card the implementer cannot edit** | **1× (§5.2)** | **1 card, middle tier, $0.03** | **Caught the only semantic defect five other mechanisms passed** |
| Rung 0 static (host, hidden) | 22× | 4s avg | Cheap, catches sloppiness, semantically blind |
| Rung 3 introspection oracle | 9× | 11s avg | Caught 2 structural drifts. Blind to direction |
| Schemathesis | 9× | 22s avg | Caught 1 nullable mismatch. Free hidden oracle |
| Emit-time split gates | 1× | 0.3s | No rejections. Untested against a *bad* split — see below |
| `decided`/`open_questions` set difference | 1× (§5.4) | 15ms | Fired correctly. Also **did not** false-positive on §5.1, because of `closed_by` |
| Echo detection | 0× | — | Never fired. Watch it |
| Verify reading summaries | 3× | $0.08 | Caught 1 omission. Caught **zero** commission (§5.2) |
| `judge` | — | — | Absent. No point in 22 cards where two candidates existed (ADR-0002 holds) |
| Notification | — | — | Absent. Poll latency 4.8s total against 31min wall clock (ADR-0003 holds) |

**Checks were 38% of compute wall clock** — consistent with the Odoo run's 42%, and several orders
above poll interval. ADR-0003's reopening trigger for notification remains far away.

**Total:** 22 cards, 31 claims, 3 retries, 1 reap, 1 refusal, 1 spec revision, 2 human gates.
Wall clock 31 min. Model spend $0.41.

---

## 7. What this run says about open questions

**R45 — does a generator absorb the structural half?** `generate.py` produced models, migration and
CRUD skeletons for all three entities. Cards `.1` through `.4` were review-and-adjust, not
authorship. **Coverage was 91% here and will not be 91% on Odoo** — a catalog is unusually
generatable. Do not conclude anything about the split jig's scope from this number alone.

**E2 arm D — would diff-reading verify have caught §5.2?** The diff is eleven lines and contains the
inverted predicate in plain sight. Almost certainly yes, at a cost the leaf `touch_set` bounds. This
is the strongest single piece of evidence yet for demoting the `decided`/`open_questions` pair from
detector to splitter feedback. **It is one specimen. Do not decide on it.**

**Emit-time gates are untested.** They passed a good split and were never shown a bad one. P3-2 —
running them against a human-reviewed decomposition that actually executed — is still the honest
test, and this run did not perform it.

**Rule 135 has no evidence.** The verifier had no write tool and never attempted a write, so
`tool_audit` recorded no denial. The gate is justified structurally and the attention claim remains
unmeasured (policy §1.6, P3-5).
