# Harness Core — v3

**Supersedes:** `harness-design-v2` §0–§5, §11, §12, §14, §15, and the substrate half of §16–§17.
**Companion:** `harness-policy-v3` — roles, decomposition, verification, tiering, experiments.
**Also live:** `odoo-adaptation`, `change-register` (rules, risks, numbering authority), ADR-0001,
`worked-run-odoo`, `superpowers-findings`, `superpowers-findings-2`, `store-and-lessons`.

**Why this document exists separately.** Five patch documents amended policy. **None amended the
substrate.** The board, the predicate, the claim protocol, fencing, the reaper and content-derived
ids were never contested, and all of them fired cleanly in the worked run. That asymmetry is the
finding, and this split is its consequence: what is settled stops being relitigated every time a
policy question moves.

**Rule of this document.** No new content. Everything here is traceable to v2 or to a patch
document. A new mechanism arriving during a rewrite is the elaboration failure recurring; it goes to
an ADR instead.

**Status of everything in here: settled.** Not because it is proven, but because nothing in five
documents of review argued against it. If something here changes, that is a significant event and
wants an ADR.

---

## 1. Purpose

**What this is.** A Postgres ledger of work cards, and stateless workers that claim them. The board
is the only place state lives. No component holds a plan.

**What the first build is for.** Learning the substrate, and accumulating a queryable record of what
was decided and why across many runs of one long-lived project. Production superiority over a
controller-based tool is a **secondary hypothesis**, tested at the step-7 checkpoint. A negative
result there is information about where the architecture pays, not a reason to stop.

**What it is not for.** Unattended operation. This is a **helper**. Human gates on the critical path
are acceptable and expected.

**The three claims that survive scrutiny**, stated narrowly:

1. **The record survives the controller dying**, because there is no controller. A comparable tool's
   ledger is a file maintained by discipline; here it is the only thing that exists.
2. **Work runs in parallel**, bounded by declared independence rather than by a controller's
   attention.
3. **Completed work is never re-dispatched.** Content-derived ids plus `ON CONFLICT DO NOTHING` make
   the most expensive observed failure of controller-based tools structurally impossible.

The compounding-fidelity argument is *not* on this list. It is unmeasured, and the crash-safety
argument is stronger because someone was demonstrably burned by its absence.

**What this is for**, as a property rather than a domain: workloads where a substantial fraction of
leaves admit an **objective, non-self-authored check**, and where the remainder is separable. Odoo
is an instance, not the definition.

**What it is not for.** Anything that fits in one context window. Use one window.

---

## 2. Principles

1. **The ledger is the only state.** Everything else is derived or disposable.
2. **The predicate is the scheduler.** Anything you would put in an orchestrator must be expressible
   as a dependency edge or a readiness rule.
3. **A deterministic sub-second transformation is a hook, not a card.** A card costs a row, a lease,
   two transactions and a scheduling decision. It must earn all four.
4. **Prefer the cheapest mechanism that can do the job.** The model gets what is left. Where a
   mechanical check and a model call cover the same ground, the mechanical check wins.
5. **Checks a card can fix are visible to it; checks that establish trust are hidden from it.**
6. **No party grades work done under its own instruction.**
7. **Degrade, do not hang.**
8. **Every mechanism costs whether or not it fires.** A mechanism that never fires in practice is a
   candidate for deletion, not a safety margin.

---

## 3. Vocabulary

### 3.1 Code names — authoritative in source

| Term | Meaning |
|---|---|
| `Task` | The unit of work. A row in `tasks`. |
| `Splitter` | Decomposes a task into children plus gates. |
| `Executor` | Executes a leaf task. |
| `Verifier` | Compares subtree outputs against the root intent. |
| `Integrator` | Merges repo changes from sibling tasks. |
| `Ledger` | The Postgres access layer: claim, commit, query. |
| `Jig` | Prompt template + tools + output schema + allowed outcomes, bound per kind. Names no check command (ADR-0008). |
| `Policy` | Failure class → outcome table. Config, not a process. |
| `Budget` | A claim-time query over spend (§5.3). May only say *no*. A function, not a process. |
| `Worker` | An OS process running the claim loop. **Synonymous with process.** |

`Judge` and `Relay` are **deleted** from v2's table. `Judge` moves to an ADR of record (never
adopted); `Relay` goes with notification, which is absent.

**Worker, role, process.** A *process* is an OS process. A *worker* is a process running the claim
loop — the same thing. A *role* is a config entry: which kinds and tiers to claim, which model and
effort, which jig, which hooks. A worker runs one role for its lifetime. Each kind has one jig, and
each kind and tier is claimed by one role (rule 136).

### 3.2 Whiteboard vocabulary — conversation only

Shop floor (the graph) · job card (task) · station (role) · traveler (`caused_by`) · inspection
(verify) · rework (retry) · scrap (quarantine) · tolerance (check strictness) · jig · WIP.

**`task` and `card` are the same thing.** `task` in anything code-adjacent; *card* only in prose.
Never `TaskCard`, never a `cards` table.

### 3.3 Banned terms

`Agent` as a role suffix · `Orchestrator` / `Coordinator` / `Manager` / `Controller` (if a class
wants one of these names, the design is wrong) · `Swarm` / `Hive` / `Colony` · `Pipeline`.

### 3.4 Roles deliberately absent

Recorded so nobody adds them in month four on the strength of a taxonomy.

**Router.** Routing is `WHERE kind = ANY($1) AND tier = ANY($2)`. No model call, inspectable in SQL.

**Guard (as a role).** Model-based content checking is the most bypassable rung of the constraint
spectrum. What is needed is the enforced version. Layers, not a role.

**Supervisor / coordinator.** No component holds a plan.

**Compactor.** Context is managed by splitting, not compressing.

**Critic (as a role).** Available as a check type in `checks.yaml` where no objective oracle exists. It
never displaces a test where a test is possible.

**Formatter.** See principle 3.

**Judge.** Selects between competing artifacts on a partly-subjective quality. Never adopted: it is
the role most likely to grow into a router, it was gated on an experimental outcome that never
happened, and it never fired in the worked run. Its equivalent here is a recorded human ruling.

---

## 4. Data model

### 4.1 Tasks

```sql
CREATE TYPE task_state AS ENUM (
  'awaiting_review',  -- gated on a human
  'pending',          -- on the board, may or may not be runnable
  'leased',           -- claimed by a worker
  'done',
  'failed',           -- retryable; reaped back to pending
  'quarantined'       -- terminal; scrap pile
);

CREATE TABLE tasks (
  id                text PRIMARY KEY,          -- 't-a3f8', 't-a3f8.2.7', 't-a3f8.V'
  root_id           text NOT NULL,
  project           text NOT NULL,             -- cross-run identity. NOT retrofittable.
  parent_id         text REFERENCES tasks(id),
  kind              text NOT NULL,
  tier              text NOT NULL,             -- NO DEFAULT. Absence is a config error.
  state             task_state NOT NULL DEFAULT 'pending',

  intent            jsonb NOT NULL,            -- refs + params. NOT a context blob.
  title             text NOT NULL,             -- one line, for a human reading the tree
  contract          text NOT NULL,
  contract_completeness text,                  -- declared at emit; sets tier and effort (policy §2.1)
  check_spec        jsonb,                     -- {rungs:[...], expect: PASS|FAIL}
  touch_set         text[] NOT NULL DEFAULT '{}',
  owns              jsonb,                     -- namespace ownership; domain-specific
  interfaces        jsonb,                     -- {consumes: [], produces: []}
  open_questions    jsonb NOT NULL DEFAULT '[]',  -- entries may carry closed_by
  deps              text[] NOT NULL DEFAULT '{}',
  retry_safe        boolean NOT NULL DEFAULT true,

  lease_holder      text,
  lease_expires_at  timestamptz,               -- per-ATTEMPT: is the worker alive?
  last_heartbeat_at timestamptz,
  last_progress_at  timestamptz,               -- per-ATTEMPT: has the loop advanced? (§5.4)
  stall_after       interval,                  -- from role config at claim; NULL disables
  deadline_at       timestamptz,               -- TOTAL wall-clock across all attempts
  attempts          int  NOT NULL DEFAULT 0,   -- also the FENCING TOKEN (§5.5)
  max_attempts      int  NOT NULL DEFAULT 3,
  not_before        timestamptz,
  priority          int  NOT NULL DEFAULT 0,

  model_used        text,
  effort_used       text,                      -- reasoning effort; part of the cache key
  reasoning_tokens  bigint NOT NULL DEFAULT 0,
  tokens_in         bigint NOT NULL DEFAULT 0,
  tokens_out        bigint NOT NULL DEFAULT 0,
  cost_usd          numeric(12,6) NOT NULL DEFAULT 0,
  check_latency_ms  bigint NOT NULL DEFAULT 0,
  rung1_invocations int  NOT NULL DEFAULT 0,   -- R36: per card from run one

  result_ref        text,
  result_summary    jsonb,
  result_size       bigint,
  summary_schema_version int NOT NULL DEFAULT 1,   -- NOT retrofittable
  outcome           text,
  failure_class     text,
  check_result      text                       -- the oracle's verdict (ADR-0013)
    CHECK (check_result IN ('passed', 'failed', 'unavailable', 'not_applicable')),

  base_sha          text,
  result_sha        text,

  caused_by         text,
  config_version    text NOT NULL,
  config_hash       text NOT NULL,
  prompt_ref        text,
  created_at        timestamptz NOT NULL DEFAULT now(),
  updated_at        timestamptz NOT NULL DEFAULT now(),

  CONSTRAINT intent_size CHECK (pg_column_size(intent) < 4096),
  CONSTRAINT done_means_checked CHECK (state <> 'done'
    OR COALESCE(check_result IN ('passed', 'not_applicable'), false))   -- rule 145
);

CREATE INDEX tasks_claim_idx    ON tasks (kind, tier, priority DESC, created_at)
  WHERE state = 'pending';
CREATE INDEX tasks_root_idx     ON tasks (root_id);
CREATE INDEX tasks_project_idx  ON tasks (project, created_at);
CREATE INDEX tasks_prefix_idx   ON tasks (id text_pattern_ops);
CREATE INDEX tasks_lease_idx    ON tasks (lease_expires_at) WHERE state = 'leased';
CREATE INDEX tasks_deadline_idx ON tasks (deadline_at)
  WHERE state IN ('pending','leased') AND deadline_at IS NOT NULL;
```

**Field notes.**

- **`id`** — `t-` plus an 8-char content hash over `(root_id, kind, normalized intent)`, dotted for
  hierarchy. Content-derived ids give idempotent appends (a duplicate hits the primary key and
  no-ops), merge-safety, and prefix-scan rollups. This is claim 3 of §1.
- **`root_id` on every task** makes drift detection possible at any depth. **`project`** makes
  cross-run questions possible at all. Retrofitting either is painful; retrofitting `project` is
  effectively impossible, since old rows cannot be attributed.
- **`title` is written for a human, not for an executor.** One line, under ~60 characters,
  imperative, readable months later with no other context. `contract` is prose for the card doing
  the work — multi-line, citing anchors and paths — and a tree of contracts is unreadable. The
  emitting card writes the title; the jig's output validator enforces the length. Without this
  column the card tree is not browsable, and that is most of what the record is for (§9.3).
- **`tier` has no default.** A missing tier silently inheriting the most expensive model is a known
  failure of controller-based tools. Absence is a config validation error.
- **`intent` size cap** enforced by CHECK, not convention. The single most effective guard against
  context accumulation.
- **Three clocks.** `lease_expires_at` answers *is this worker alive?* and is per-attempt.
  `last_progress_at` answers *has its loop gone silent?* and is per-attempt. `deadline_at` answers
  *has this taken too long overall?* and spans every attempt.
- **`attempts` is the fencing token.** Monotonic per lease. Not optional — see §5.5.
- **`failure_class` is the current attempt's.** Claim clears it; `task_attempts` keeps the history.
  So does `outcome`'s: a later commit overwrites the card's, so the lessons queries read attempts (ADR-0013).
- **`outcome` disambiguates `done`.** The predicate does not consult it; §5.2 handles that
  structurally. The value set is policy-owned.
- **`summary_schema_version`** is written by the jig's output validator, never by a model. A schema
  change bumps it and never rewrites history.
- **`caused_by`** is the traveler: the sheet stamped at every station.

**Attempts.** One row per delivery, written in the claim's transaction and closed in the transaction
that ends the attempt. Per-call cost stays in `model_calls`, keyed `(task_id, attempt, seq)`.
*(ADR-0007.)*

```sql
CREATE TABLE task_attempts (
  task_id       text NOT NULL REFERENCES tasks(id),
  n             int  NOT NULL,     -- tasks.attempts at claim; the fence
  worker        text NOT NULL,
  kind          text NOT NULL,     -- what the card was at claim. Never updated (rule 151)
  tier          text NOT NULL,
  config_hash   text NOT NULL,
  failure_class text,              -- NULL while open and on success; a parked attempt's outcome
  check_ref     text,              -- content hash; what retry layer 7 reads. Visible rungs only
  hidden_check_ref text,           -- content hash; hidden rungs. Never rendered (ADR-0013)
  refusal       jsonb,             -- the payload of a parked or misclassified attempt
  diff_ref      text,              -- content hash; NULL if the worker died first
  started_at    timestamptz NOT NULL DEFAULT now(),
  ended_at      timestamptz,
  PRIMARY KEY (task_id, n)
);
```

### 4.2 Runs

```sql
CREATE TABLE runs (
  root_id       text PRIMARY KEY REFERENCES tasks(id),
  project       text NOT NULL,
  intent_digest text NOT NULL,     -- sha256 of the root intent text
  spec_digest   text,              -- sha256 of the anchor, where one exists
  config_pin    jsonb NOT NULL,
  max_cost_usd  numeric(12,2),     -- Budget's limit (§5.3); outside the pin; NULL is no limit
  max_free_retries int NOT NULL,   -- per card (ADR-0011); outside the pin; no default
  halted_class  text,              -- set by a halting failure; refuses claims until cleared (§5.3)
  started_at    timestamptz NOT NULL DEFAULT now(),
  ended_at      timestamptz,
  outcome       text               -- 'complete' | 'abandoned' | 'gated'
);
CREATE INDEX runs_project_idx ON runs (project, started_at);
```

`intent_digest` is what makes the highest-value cross-run query possible: hold the intent fixed,
vary the model, and see which machinery was compensating for the models of its era.

### 4.3 Content store

Two methods: `put(bytes) -> ref`, `get(ref) -> bytes`. Content-addressed and immutable. **Never
queried** — no `WHERE` over it, no indexing its contents. Anything decision-relevant lives on the
task.

That boundary settles the storage question: the part queried forever is rows, and rows are tiny. The
part that is large is the part never read again.

| Backend | Use | Why |
|---|---|---|
| Postgres `body` | default, under 1 MB | transactional with the commit |
| Object storage | above the threshold, or after tiering | keeps the recovery path small |
| Filesystem | **dev and tests only** | not transactional; does not survive the host |

**Write-side truncation, by media type:**

```
check log, exit 0     → last 40 lines + timing            ~2 KB
check log, exit != 0  → first traceback + last 200 lines  ~20 KB
diff                  → full
review package        → full, TTL 90 days
```

Roughly a 100× reduction on the dominant item, losing nothing anyone reads. Do this before
considering object storage; it makes the backend question academic for years.

**Tiering** is a background job with no consistency question: copy `body` out, set `external`, null
`body`, verify by rehash. Nothing references content by anything but its hash.

### 4.4 Retention

| Class | Policy |
|---|---|
| `tasks`, `task_attempts`, `runs`, `reviews`, `notes`, `tool_audit` | **Never deleted.** |
| `model_cache`, `model_failures` | TTL by run |
| content — diffs, artifacts | long TTL, tiered |
| content — check and container logs | short TTL, truncated on write |

Stated as policy because the instinct when the database grows is to prune old runs, and old runs are
the asset.

### 4.5 Notes

Advisory memory. Ships as NullMemory. Scope is never global.

```sql
notes( id, project, scope, task_id, body, promoted_by, superseded_by, created_at )
```

**Nothing is promoted automatically.** Promotion is a human verb at the gate (§7), and the note
carries the task it came from so the derivation is always recoverable. A note is **superseded, never
edited** — a lesson that turned out wrong is itself a lesson.

Manual promotion is slow and correct; automatic promotion is how a lessons store fills with noise
and stops being read.

---

## 5. Readiness, claiming and leases

Unchanged from v2 except where marked. This section is the part of the design nothing has argued
with.

### 5.1 The predicate

```sql
ready(t) :=
      t.state = 'pending'
  AND t.attempts < t.max_attempts
  AND (t.not_before IS NULL OR t.not_before <= now())
  AND NOT EXISTS (                              -- (a) direct deps done
        SELECT 1 FROM tasks d
         WHERE d.id = ANY(t.deps) AND d.state <> 'done')
  AND NOT EXISTS (                              -- (b) their descendants terminal
        SELECT 1 FROM unnest(t.deps) AS dep(id)
          JOIN tasks x ON x.id LIKE dep.id || '.%'
         WHERE x.state NOT IN ('done', 'quarantined'))
```

**This predicate is the scheduler.** A pure function of the graph. Not stored — nothing writes
`ready`, so nothing can lie about it. No role may override it.

**A dep must name a real card, and the predicate cannot check that.** `NOT EXISTS` over an id with no
row finds nothing, so a missing dep reads as satisfied, against ADR-0006. A cycle stays `pending`
forever, and no predicate sees it. Both are rejected when cards are emitted, in the emit transaction:
a dep names a card on the board or one emitted with it, and the emitted cards form no cycle (rule 140).
An existing card cannot depend on one not yet emitted, so checking the emitted set is enough.

### 5.2 Why clause (b) exists

`done` on a split card means *I decomposed*, not *the work is finished*, and dependents cannot tell
the two apart from state alone. Without (b), a gate becomes runnable while the subtree it is meant
to check has not been claimed.

Clause (b) makes satisfaction subtree-aware via hierarchical ids. Arbitrary depth is free: no
recursion, no counters, no completion events. The splitter needs no change — it never learns who
depends on it.

**Different bars.** A direct dependency must be `done`. A quarantined *descendant* is acceptable —
the subtree is finished, part of it failed, and noticing that is the gate's job. "Degrade, do not
hang", in the predicate.

### 5.3 The claim query

Readiness and lease acquisition in **one transaction**. Split them and two workers both claim.

```sql
WITH candidate AS (
  SELECT t.id FROM tasks t
   WHERE t.kind = ANY($1) AND t.tier = ANY($2)
     AND t.state = 'pending'
     AND t.attempts < t.max_attempts
     AND (t.not_before IS NULL OR t.not_before <= now())
     AND NOT EXISTS (SELECT 1 FROM tasks d
                      WHERE d.id = ANY(t.deps) AND d.state <> 'done')
     AND NOT EXISTS (SELECT 1 FROM unnest(t.deps) AS dep(id)
                       JOIN tasks x ON x.id LIKE dep.id || '.%'
                      WHERE x.state NOT IN ('done','quarantined'))
     AND NOT COALESCE((SELECT sum(m.cost_usd) >= r.max_cost_usd      -- Budget
                         FROM runs r
                         JOIN tasks x ON x.root_id = r.root_id
                         JOIN model_calls m ON m.task_id = x.id
                        WHERE r.root_id = t.root_id
                        GROUP BY r.max_cost_usd), false)
     AND NOT EXISTS (SELECT 1 FROM runs h                            -- halted run
                      WHERE h.root_id = t.root_id AND h.halted_class IS NOT NULL)
   ORDER BY t.priority DESC, t.created_at
   LIMIT 1 FOR UPDATE OF t SKIP LOCKED
), claimed AS (
  UPDATE tasks
     SET state='leased', lease_holder=$3,
         lease_expires_at = now() + $4::interval,
         last_progress_at = now(), stall_after = $5::interval,
         failure_class = NULL,
         attempts = attempts + 1, updated_at = now()
    FROM candidate WHERE tasks.id = candidate.id
  RETURNING tasks.*
), opened AS (
  INSERT INTO task_attempts (task_id, n, worker, kind, tier, config_hash)
  SELECT id, attempts, $3, kind, tier, config_hash FROM claimed
)
SELECT * FROM claimed;
```

**One host for now** (rule 143). `SKIP LOCKED` would allow claiming across machines with no distributed
lock, but the kill and workspace teardown in §5.4 only work on the local host, and the reaper runs from
any worker. Running on several hosts needs the host in `lease_holder` and teardown refused elsewhere.

Lease deadlines come from the **store's** clock — clock skew between workers is real.

**Budget refuses in the claim, not in `ready(t)`,** which stays a pure function of the graph. Spend is
summed from `model_calls` against `runs.max_cost_usd`. It is a brake rather than a guarantee: concurrent
claims see the same sum, and cards already claimed keep spending. Raising the limit changes no pin,
because it changes nothing a card saw.

**A halted run refuses the same way.** *(ADR-0011.)* A failure no retry can fix (`auth_rejected`,
`billing_exhausted`, `model_unavailable`) sets `runs.halted_class` in the failing transaction. Cards in
flight finish, and nothing new is claimed until a person clears it or abandons the run.

**Config drift check, at claim time.** The worker recomputes its own `kind_hash` (§8.1.1) and
compares it to the run's pinned value. A mismatch **fails loud** and the worker refuses the card
rather than proceeding.

Without this the pin is a claim rather than a fact: someone edits a jig mid-run, the pin says one
thing, the worker loads another, and the run silently stops being one experiment — which is the
exact failure §8.1 exists to prevent, arriving through the back door. A few lines, and it closes the
hole permanently.

**`attempts` increments at claim time.** This counts *deliveries*, which is what bounds a
crash-looping card: a card whose handler kills its worker never records an explicit failure.

### 5.4 The reaper

```sql
-- candidates: dead, silent, or explicitly failed
SELECT id, attempts FROM tasks
 WHERE state = 'failed'
    OR (state = 'leased' AND (lease_expires_at < now()
                              OR last_progress_at + stall_after < now()));

-- per candidate, after its teardown has run
UPDATE tasks
   SET state = (CASE WHEN NOT retry_safe AND failure_class IS DISTINCT FROM 'provision_failed'
                          THEN 'awaiting_review'
                     WHEN attempts >= max_attempts THEN 'quarantined'
                     ELSE 'pending' END)::task_state,
       not_before = now() + LEAST(interval '10 seconds' * power(2, attempts - 1),
                                  interval '5 minutes'),
       lease_holder = NULL, lease_expires_at = NULL,
       failure_class = COALESCE(failure_class,
         CASE WHEN lease_expires_at < now() THEN 'lease_expired' ELSE 'stalled' END),
       updated_at = now()
 WHERE id = $1 AND attempts = $2 AND state IN ('leased','failed');

UPDATE tasks
   SET state='quarantined', failure_class='deadline_exceeded',
       lease_holder=NULL, lease_expires_at=NULL, updated_at=now()
 WHERE state IN ('pending','leased')
   AND deadline_at IS NOT NULL AND deadline_at < now();
```

Run from any worker on a timer; idempotent. **Lease expiry is the entire crash-recovery story** — an
explicit error and a dead process collapse to the same path. Each flip closes the open
`task_attempts` row in the same transaction, recording the same `failure_class`.

**The stall clause catches silence, not uselessness.** *(ADR-0007.)* The card loop stamps
`last_progress_at`, fenced, on each model response and each finished tool call; never from the
heartbeat task, which runs regardless. `stall_after` comes from role config, and config validation
requires it to exceed the longest tool and model-call timeouts, so a long check is not silence.

**Backoff is set on every requeue,** whatever the class. A retry costs a container, a clone and an
install, and an immediate one against an outage spends all of a card's attempts in seconds.

**Amended: the reaper kills before it requeues.** Order matters:

```
0. revoke the lease              (recheck expiry; none lost means a live worker keeps its card)
1. kill the container            (named from the card id and attempt, §6)
2. drop the workspace database
3. remove the attempt's worktree
4. flip the row to pending
```

Fencing guarantees a stale writer cannot *commit*. It does not guarantee it cannot *write*. Requeue
first and a live process keeps writing beside its own retry. This closes a failure v2 recorded but did not
resolve. §6 states what a failure at each step does. `$2` keeps a flip from landing on a newer claim,
and the state check keeps it from landing on a commit that won the race. Teardown cannot land on a newer
claim either, because every name it touches carries the attempt it selected (ADR-0011).

**Revoke first** (rule 148, ADR-0013). Clearing `lease_holder` makes a late commit's fence fail, so a worker that
wakes during teardown cannot commit `done` onto a branch already removed. A `failed` candidate needs no revoke,
because commit requires `state='leased'`. The row stays `leased`, so nothing claims it mid-teardown.

**A `retry_safe: false` card goes to `awaiting_review`, and its evidence stays** (rule 149). The container is
killed. The worktree and database are kept until a verb acts, and the sweep spares them. `provision_failed` is
exempt, because no work ran.

**Tier is written here.** When the next delivery is the last, and this flip was not free, `escalate_tier.sql` sets
`tier` and `config_hash` in the flip's transaction (rule 68).

**Orphans are swept by name** (rule 141). The candidates above miss a container left by a crash after
commit, since the row is `done`, and one left by the deadline flip, which runs no teardown. So each pass
also lists the host's `card_*` containers, databases and worktrees, **then** reads the open
`task_attempts` rows, and removes anything whose name no open row derives. The order matters: a row
opens in the claim, before anything is provisioned, so reading rows last can never sweep a live attempt.
Worktrees go by path, then `git worktree prune` (§6). The branch of a committed attempt stays, because
`integrate` needs it.

**Why there is no watchdog watching the watchdog.** *(Added 2026-08-18.)* A comparable tool answers
stall detection with a four-role escalation chain — a watcher that may not kill, an executioner it
files warrants to, a checker for stuck watchers, and a process whose sole job is keeping the checker
alive. The question that chain answers is real and this design must answer it too: **what happens
when the reaper itself fails?**

Three properties make one reaper sufficient here, and they are properties of the substrate rather
than of the reaper's implementation:

- **It is idempotent and unelected.** It is a few statements run from any worker on a timer, not a
  process with a lifecycle. There is no singleton to die. Every worker running it concurrently is
  the normal case, not a race.
- **It has little semantic judgement to get wrong.** It fires on timestamp comparisons evaluated by
  Postgres. The comparable's watcher must decide whether an agent is *semantically* stuck —
  inferring from stale timestamps whether meaningful work is happening — which is a judgement, so it
  needs a check on its judgement, which needs a check on that. The chain length is a consequence of
  the first component being fallible in a way a timestamp comparison is not. **The stall clause moves
  toward that line, and ADR-0007 records it as a cost:** silence can be wrong too. It stays on this
  side because it asserts only silence, a wrong call costs one attempt, and its check is a query
  (§10) rather than another watcher.
- **Failure is inert, not corrupting.** A reaper that never runs leaves cards leased past expiry:
  the board stalls, visibly, and `SELECT count(*) FROM tasks WHERE state='leased' AND
  lease_expires_at < now()` is the detector. It cannot requeue work that is still running, because
  it kills before it requeues, and it cannot admit a stale commit, because fencing rejects it. The
  failure mode is *nothing happens*, which is observable and safe.

**This reopens if a stall is observed that neither clause catches** — a worker heartbeating and
still making calls while doing no useful work. That is a real gap: both signals say the loop is
moving, not that it is getting anywhere. The turn limit and `deadline_at` bound it, and no detector
exists for it (rule 62). Recorded as R57.

### 5.5 Fencing — not optional

`WHERE id = $1 AND lease_holder = $2` is *holder* identity, not *lease* identity. A paused worker
whose lease expired can be reaped, see the card reclaimed by others, claim it again itself, and then
have its original paused execution wake and commit on top of a newer claim — with a matching
`lease_holder`.

`attempts` is already monotonic per lease, so it is a fencing token for free:

```sql
UPDATE tasks SET state='done', …
 WHERE id=$1 AND lease_holder=$2 AND attempts=$3;   -- value returned at claim time
```

The same guard belongs on **heartbeat** and **release**. Treat the token as a capability: do not log
it next to task identifiers.

### 5.6 Heartbeats

```sql
UPDATE tasks SET lease_expires_at = now() + $ttl, last_heartbeat_at = now()
 WHERE id=$1 AND lease_holder=$2 AND attempts=$3 AND state='leased';
```

Short base TTL (60 s) for fast crash detection; live workers bump it, dead ones stop. Run the
heartbeat from a **background task**, not inside the model call, so a hung connection stops the
heartbeat rather than masking the hang. **`deadline_at` is never extended.**

A saturated container can starve the heartbeat thread. That is a real reaping cause, not a bug —
and §5.4's kill-first ordering is what makes it safe.

### 5.7 Commit

```sql
BEGIN;
  UPDATE tasks SET state='done', result_ref=…, result_summary=…, outcome=…,
                   tokens_in=…, tokens_out=…, cost_usd=…, model_used=…,
                   check_latency_ms=…, check_result=…, updated_at=now()
   WHERE id=$1 AND lease_holder=$2 AND attempts=$3 AND state='leased';   -- fenced
  UPDATE task_attempts SET ended_at=now(), check_ref=…, diff_ref=…
   WHERE task_id=$1 AND n=$3;
  INSERT INTO tasks (…) VALUES … ON CONFLICT (id) DO NOTHING;   -- idempotent append
COMMIT;
```

Every path that ends an attempt closes its row in that path's transaction: commit, failure, parking, reap, and
drain's early release (as `released`).

**Commit only reaches `done`** (rule 145). `state='leased'` stops a late commit flipping `failed` to `done`, and
`done_means_checked` refuses a row whose oracle did not pass. Refusals go through `park.sql`, and a failed check
through `fail.sql`. `not_applicable` is allowed only for `expanded`, or a kind with an empty ladder.

**Commit is a harness operation, not a card operation.** The card returns; the harness runs the
`pre_commit` hooks and writes. This is what makes the structural gates unreachable from inside the
card — the same property that makes the check oracle hidden (principle 5).

The `outbox` insert is gone with notification.

### 5.8 Graceful drain

`SIGKILL` is the acceptance test; `SIGTERM` needs a path, or every rolling restart burns a card's
worth of tokens.

```
SIGTERM → stop claiming immediately
        → finish the in-flight card if it fits the grace period
        → otherwise release the lease early
        → exit
```

Grace period must exceed observed p99 drain time. An early release is free: a restart is not the
card's failure (ADR-0011).

### 5.9 Scheduling

Poll only. Notification, relay and outbox are **absent** — not deferred. A poll loop is one query on
a timer and it has never been the bottleneck in anything measured.

---

## 6. The workspace

**The workspace is a triple**, provisioned and destroyed together:

| Component | Provides | Lifetime |
|---|---|---|
| **git worktree** | source isolation; a branch for integration | per attempt |
| **container** | pinned runtime, cgroup limits, network deny, **a kill handle** | per attempt, ephemeral |
| **database or equivalent** | the card's check environment | per attempt |

**Git on the host, execution in the container.** A worktree's `.git` is a file pointing into the
parent repo; bind-mounting the worktree alone breaks git inside, and bind-mounting the repo root
gives the card write access to every sibling's worktree. So: the harness creates the worktree, the
container mounts it at a fixed path, the card edits and runs checks inside, and the harness commits
from the host.

**Host git treats the worktree as untrusted input** (rule 150, ADR-0014). The worktree's `.git` is a file
inside that mount, and it tells git which repository to use. A card that points it at a repository of its
own can run a program on the host through a plain `git status` or `git commit`, and can make a plain diff read
empty. So every host git call goes through one runner, which takes the git directory from the harness's own
record:

```sh
env -i PATH=… GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1 \
  git --git-dir=<repo>/.git/worktrees/<name> --work-tree=<worktree> \
      -c core.hooksPath=/dev/null -c core.fsmonitor=false -c user.name=… -c user.email=… <command>
```

- **A staged gitlink is a touch-set violation,** even when its path is in the set. A repository nested in the
  worktree stages as one path, which hides its contents from `diff_paths()`.
- **Teardown removes a worktree by path, then runs `git worktree prune`,** because `git worktree remove` refuses
  a tampered one, even with `--force`.
- **`.git` is masked read-only in the container,** as a second layer for people rather than the harness. Rule 149
  keeps failed worktrees, and running git in one could run the card's program. Review shows kept work through the
  runner. The mask covers only the top-level pointer and is untested, so nothing depends on it.

**Ephemeral per card, not per worker.** A reused container accumulates installed packages, caches
and state, which makes environment-dependent failures reachable. Every attempt being cold is a
property retries already rely on.

**Retry safety comes from workspace destruction**, not from checkpointing:

> **A card whose side effects cannot be undone by destroying its workspace must not exist.**

Where that cannot hold — migrations against real data, external side effects — the card carries
`retry_safe: false` and a failure routes to `awaiting_review` rather than back to `pending` (§5.4). It is set at
emission, and the `pre_commit` hook sets it when the diff touches migrations.

**Shared expensive setup is built once and cloned.** Whatever the check environment is, build a
template at run start and clone per attempt. Without this, parallel workers serialise on
environment construction and the parallelism claim does not survive contact.

**Names derive from the card, never from card output.** *(ADR-0007.)* The key is the card id with `.`
and `-` mapped to `_`. The worktree is `<workspace_root>/card_<key>_attempt<n>`, on a branch of that name,
and the container and database share it (ADR-0011). `integrate` merges the branch of the committed
attempt, which is `tasks.attempts`. Ids are a hex hash plus dotted segments, so the mapping cannot collide. A
name over 63 bytes fails provisioning, because Postgres truncates longer identifiers without an error.
Because names are derivable, the reaper can kill a container whose worker died before recording
anything.

**Teardown checks its target first.** Before removing a worktree or running `DROP DATABASE`: the
resolved worktree path must be strictly inside `workspace_root`, and the database name must match
`card_*`, which excludes the template. A failed check refuses the step and counts as a blocking
failure below.

**Every stage has a time limit and a stated failure:**

| Stage | Runs | On failure or timeout |
|---|---|---|
| Provision: worktree, container, clone | after claim, each attempt | Attempt ends as `provision_failed` and retries with backoff, free up to `runs.max_free_retries` (ADR-0011). Infrastructure, not `harness_bug`. |
| Kill the container | before any requeue | **Blocks requeue.** The row stays put; the next reaper pass retries. |
| Drop the attempt's database and filestore | before any requeue | Logged. Requeue proceeds: a retry never reuses the name, and §10 detects the orphan. |
| Remove the attempt's worktree and branch, by path and then prune | before any requeue | Logged. Requeue proceeds: a retry never reuses the names, and the §5.4 sweep collects the worktree. |

A blocked teardown is the inert failure §5.4 relies on: the card stalls visibly rather than running
next to a live writer or on a dirty worktree.

---

## 7. Human gate

State `awaiting_review`. Five verbs:

| Verb | Effect |
|---|---|
| `approve` | card proceeds |
| `edit` | contract or check amended, then proceeds |
| `split` | becomes a `split` on the same row, carrying the same intent (ADR-0013) |
| `kill` | quarantined |
| `promote` | an observation becomes a note (§4.5) |

**A verb that returns a card to `pending` cannot strand it.** `review_return.sql` sets `max_attempts` to at least
`attempts + 3`, never lowers `attempts`, and sets a new deadline, because time in review can otherwise expire the
card on return. The new deadline is recorded in `reviews`.

**The interface shows the emitting card's `cost_if_wrong` where one exists.** Approval before
consequence, not after. A gate presenting three options and no costs produces fast approvals, and
the cost then surfaces in the digest — after the work is done.

Every human action is a row in `reviews`: what they had open, what they chose, why.

---

## 8. Determinism and replay

1. Record every response in `model_cache`, keyed on the **rendered prompt** plus model, **reasoning
   effort**, sampling params, tool-schema hash and recalled note ids. Record every provider failure in
   `model_failures` under the same key (rule 152, ADR-0014).
2. Replay serves from cache and makes zero outbound calls. Tools and checks re-execute, and only the
   model is served from cache. A recorded failure re-raises unless a response exists for that key, which
   wins. A live run never reads `model_failures`. Any difference is a genuine difference in your code.
3. Interleaving may differ between runs; the **causal graph** will not. Assert on the terminal
   graph, not execution order.
4. Content refs are immutable, so an old run is inspectable exactly as each step saw it.

**Command output is normalized before the model can see it** (rule 144, ADR-0012). The key is the bytes
on the wire, so anything a command prints reaches the key of every later call in that attempt. This
covers tool results, `post_tool_call` rung output and layer 7's check output. A normalizer removes only
what differs between two correct runs: clock times, durations, PIDs, `card_<key>_attempt<n>` names and
ordering that carries no meaning. Normalize first, then truncate. What it removes stays in `tool_audit`.
In a live run a miss costs one model call. In replay it raises `ReplayMiss`, which detects a difference
and corrupts nothing.

**What the cache buys a retry.** *(ADR-0012.)*

| Case | First call's key | Expected |
|---|---|---|
| Replay | unchanged | every call hits or re-raises; a miss raises |
| Free retry (ADR-0011) | unchanged | calls hit up to where the failed attempt stopped |
| Charged retry after evidence: a failed check, malformed output, a turn limit | moved by effort or model, and layer 7 | none hit |
| Retry after a dead worker or a stall (ADR-0013) | unchanged, unless it is the last delivery | calls hit up to where the attempt stopped |
| Reset-from-a-point (§8.2) | unchanged upstream | upstream hits; the raised subtree does not |

A hit writes a `model_calls` row at zero cost, so these rates are a query. A free failure that later succeeded
is not replayed, so `attempts` may be lower in replay. The terminal graph does not change.

**How the guarantee is kept.** *(Added 2026-08-18. ADR-0004.)* The zero-outbound-calls promise in
point 2 is only as good as the layer that can make a call. Where the card runtime is a library that
assembles prompts and dispatches to providers, the cache is implemented **as that library's model
interface** — a cache-backed implementation wrapping the real one — rather than as a wrapper around
the library. Two consequences, both load-bearing:

- **Nothing can route around it.** A call path that bypassed the cache would have to bypass the
  model interface itself, which the runtime has no way to do. Replay's guarantee stays structural
  rather than depending on every call site remembering to check.
- **The key is the bytes on the wire.** The rendered prompt in point 1 means what the provider
  actually received, including the library's assembled system prompt and its generated tool schemas
  — not the inputs we handed the library. This is rule 127's principle applied one layer down: hash
  the rendered artifact, not the thing that renders it.

The second point is the part that must be verified rather than assumed. If the runtime cannot expose
the exact request, it cannot satisfy §8, and that is disqualifying regardless of what else it
offers.

### 8.1 The config pin

Pinned at run start; every card resolves against that version. A mid-flight edit applies to the next
run — otherwise Monday's and Wednesday's cards came from different systems and the run is not one
experiment.

The pin carries: config version and hash, model versions per tier, **reasoning effort per role**,
sampling params, container image digest, runtime commit, third-party dependency commits,
environment-template hash, dependency lock. **Replay is not replay if the runtime moved.**

### 8.1.1 How `config_hash` is computed

v2 carried `config_version` and `config_hash` as columns and never said how. The shape matters,
because the wrong one makes the cross-run queries useless.

**Not one hash.** A digest over the whole config directory is too coarse: change the `digest` jig's
wording and every `execute` card in the project becomes incomparable to every earlier one, though
nothing an executor saw changed. Since the hash answers *did this card see the same system as that
one*, it is **per kind and tier**, because `execute` alone runs on three models (ADR-0008). It is
computed as a tree:

```
runtime_hash = H( image_digest, source_commit, sorted(addon_commits),
                  template_db_hash, dependency_lock )

kind_hash(k, t) = H( runtime_hash,
                   house_preamble,          # layer 1, shared
                   jig_template(k, t),      # RENDERED, not the file; a role may fill a slot
                   output_schema(k),
                   check_ladder(k),         # layer 8, plus the rungs hidden from the card
                   tool_schemas(k),         # layer 3
                   normalizers(k),          # tools and checks, with their pattern tables (rule 144)
                   skills_rendered(k),      # layer 2
                   model(k, t), effort(k, t), temperature(k, t) )
```

`tasks.config_hash` is `kind_hash` for that card's kind and tier, so a retry that raises the tier moves
it. `effort(k, t)` is the base effort: the raised effort on attempt 2 (policy §2.2) reaches the cache
key, not this hash. `runs.config_pin` remains the **full** snapshot. Two artifacts, two jobs: the pin answers *what was the system*, the hash answers *was this
card's slice of it the same*. That split is what makes the payoff query work:

```sql
select t.project, t.root_id, a.task_id, a.n, a.failure_class
from task_attempts a join tasks t on t.id = a.task_id
where a.kind = 'execute' and a.config_hash = :h;
```

**Hash the rendered artifact, not the file.** Layers 0, 1, 2, 3 and 8 sit above the cache line and
do not depend on card content, so they render at pin time against a null card. Hash that output.
This makes the hash track **what the model saw** rather than what is on disk: reformatting YAML,
reordering keys or editing a comment that never renders leaves comparability intact, while a comment
that *does* render is part of the prompt and belongs in the hash. Hidden rungs are the one exception:
no prompt shows them, but they decide outcomes, so their definitions are hashed anyway.

Canonicalisation, all boring and all necessary:

- normalise line endings; strip trailing whitespace
- sort every collection byte-wise, never locale-aware
- no absolute paths, timestamps, file mtimes or git dirty flag
- content-hash skill files individually, then hash the **sorted list of hashes** — so reordering
  `skills.yaml` without changing membership is a no-op, and swapping one file's content is not

**It is not the cache key.** They look alike and fail differently. The cache key is the rendered
prompt plus model, effort, params, tool-schema hash and note ids — per-call and exact; too coarse
and you serve wrong answers. `config_hash` is per kind and tier and coarser by design; too coarse and you get
misleading comparisons, which is a silent quality problem rather than a correctness one. They
overlap heavily, neither derives from the other, and unifying them would drag per-card content into
the comparability hash.

**`config_version` versus `config_hash`.** Version is human-readable and human-assigned
(`2026-08-17.3`); hash is the guarantee. Version is for talking about a config, hash for querying
against one. That yields an invariant worth asserting in the static checks (§11):

> A version bump with an identical hash is a no-op and fine. **A hash change with no version bump is
> a bug** — someone edited config without recording it.

**The full comparability key is `(config_hash, intent_digest)`.** Layer 4's generated orientation is
covered indirectly by `runtime_hash`, but its CONSTRAINTS block comes from the root intent, which
lives in `runs.intent_digest`. Two cards with the same config and different intents did not see the
same layer 4. Cross-run queries carry both — the model-comparison query in §9.4 already holds
`intent_digest` fixed, which is this rule applied.

### 8.1.2 Temperature is not the determinism mechanism

Recorded because the instinct is to reach for `temperature: 0` and believe the problem is solved.

It is not. Batching, floating-point nondeterminism and provider routing make identical outputs
unguaranteed at any temperature. **The cache is the determinism mechanism** — replay serves from
`model_cache` and makes zero outbound calls, which is a real guarantee rather than a statistical
hope.

Two consequences:

- Temperature is a role-level config value, not a per-card knob. A per-card temperature is a surface
  nobody can reason about and everybody will fiddle with, and it pollutes exactly the cross-run
  comparison the record exists for. "Let us try a different temperature" is a request that needs a
  hypothesis attached.
- On models where extended thinking constrains sampling, temperature is **not settable at all** at
  medium or high effort. The only cards where it is live are the minimal-effort ones — complete
  contracts, integration, digest — which are precisely the cards that want it near zero. The config
  is therefore close to degenerate, and that is a good outcome: one fewer surface to tune.

**Where the design wants divergence, temperature is the wrong tool.** Sampling one model twice gives
variance without independence — same training, same priors, same modal answer, and therefore
*correlated* blind spots, which is the one property the two-independent-drafts argument depends on
not having. Vary the model or the effort, not the seed.

**Rule.** Wherever this design asks for independent samples, the config must state **what is varying
and why**. Varying the seed measures stability; varying the model measures agreement. They are
different experiments and the distinction has to be made explicit at the point of sampling.

### 8.2 Reset-from-a-point

A single `UPDATE`: mark a subtree `pending`, clear results, bump `tier`, set the new config version.
Upstream results are untouched and their cached responses still serve, so only the subtree
re-executes. Recorded in `reviews` like any human action.

---

## 9. Observability

### 9.1 Everything is a query

There is no dashboard to build first. State, cost, provenance and history are SQL.

### 9.2 Metrics that exist from run one

Columns, not projects: cost and tokens by tier and kind · attempts distribution · outcome
distribution · `needs_context` count per root intent · unresolved mismatch rate · turn count by tier
and contract completeness · `check_latency_ms` as a fraction of wall clock · reap count ·
**reasoning tokens by kind and effort, against attempts saved**.

**Check latency as a fraction of wall clock is the one to watch.** Where it dominates, adding
workers buys less than it appears to, because the bound is the environment rather than the model.

**Reasoning tokens against attempts saved is the second.** Effort buys tokens inside one call in
exchange for fewer trips through the check loop; whether that trade pays is a two-column question
and it decides §8.1's effort settings.

### 9.3 The three human-facing outputs are queries

**Rulings** — every `decided` entry in the subtree, in commit order, with its `cost_if_wrong`.
Exhaustive by construction. It cannot be lossy and cannot be skipped by a model that ran out of
attention, which is strictly stronger than the same discipline maintained by prompt.

**Unverifiable** — what no gate could establish, routed to whoever holds the context.

**Deferred minors** — carried to the final gate, which must take the list as input. A roll-up nobody
reads is a silent discard; if no gate consumes it, delete the channel.

**The tree** — the project's history, browsable, at any distance from the work.

Because nothing holds a plan, the card tree **is** the plan, retroactively — structural rather than
maintained, permanent rather than compacted, and spanning runs because `project` is on every row. A
controller-based tool's equivalent is a file kept by discipline and truncated when context runs out.

```sql
select id, title, kind, outcome, attempts, tier, caused_by
from tasks
where project = :p
order by string_to_array(id, '.') COLLATE tree_order;   -- NOT lexical: 't-x.2' sorts before 't-x.10'
```

| In the row | Behind a click | Deliberately absent |
|---|---|---|
| title, kind, outcome, attempts, tier, `caused_by` | contract, check spec, touch set, `decided`, diff ref, prompt ref, config pin | tokens, `check_latency_ms`, hashes, timestamps beyond a date |

Rolled onto `split` rows by prefix scan: descendant count, subtree cost, max attempts in the
subtree, refusal and `needs_context` counts, whether any descendant was quarantined.

**`caused_by` is what makes it readable.** It turns *what happened* into *why this card exists* — a
gap from a verify gate, a replacement from a refusal, a human ruling. Months later that is usually
the question being asked.

**Titles flatter; the shape does not.** A card that got a security rule exactly wrong and one that
got it right have indistinguishable titles. `outcome` and `attempts` beside the title are what carry
the truth: a subtree with refusals, a `needs_context` and a re-verify round marks where the thinking
was hard, which is the part worth remembering.

**This is a digest for the project rather than for a run**, and it obeys the same rule — a query
rendered, not a service with state. A script that runs SQL and writes static HTML satisfies it. The
moment it acquires a backend, a login or a write path it has become the dashboard anti-milestone.

### 9.4 The lessons queries

Committed as `queries/lessons.sql` and treated as an **acceptance test for schema fields**: a field
nobody can write a query against is a field to remove.

```sql
-- which contract shapes produce refusals
select t.contract_completeness, a.failure_class, count(*)
from task_attempts a join tasks t on t.id=a.task_id
where a.kind='execute' and t.project=:p and a.failure_class is not null group by 1,2;

-- what facts were missing, per root intent
select r.intent_digest, a.refusal->'needs'
from task_attempts a join tasks t on t.id=a.task_id join runs r on r.root_id=t.root_id
where a.failure_class='needs_context' and r.project=:p;

-- same intent, different model version
select r.config_pin->>'model_strong' as model,
       sum((select count(*) from task_attempts a
             where a.task_id=t.id and a.failure_class='misclassified')) as misclassified,
       avg(t.attempts)
from runs r join tasks t on t.root_id=r.root_id
where r.intent_digest=:d group by 1;
```

---

## 10. Substrate failure modes

Only those the substrate itself must handle. Policy-level modes live in `harness-policy-v3`.

| Mode | Tell | Response |
|---|---|---|
| Worker dies mid-card | lease expiry | reaper: kill, drop, remove, requeue |
| **Zombie writer** | stale worker resumes after reclaim | fencing rejects the commit; the container kill prevents the writes |
| Crash-looping card | `attempts` climbs with no explicit failure | `attempts` counts deliveries, so `max_attempts` bounds it |
| Infrastructure failure consuming an attempt | `failure_class` names it | narrow allow-list raises `max_attempts` by one; `attempts` is the fence and never falls. Backoff still applies. Past `runs.max_free_retries` the failure is charged (ADR-0011) |
| Oracle cannot start | `check_unavailable` climbing across unrelated cards | free retries with backoff, then `awaiting_review`. Nothing halts the run (R63) |
| Late commit during teardown | none: it cannot land | `reaper_revoke.sql` clears the holder, so the fence fails (rule 148) |
| Silent loop | `last_progress_at + stall_after < now()` | reaper: as worker death, recorded `stalled` |
| Stall clause killing live work | `stalled` attempts that succeed on retry with no config change | raise `stall_after`; ADR-0007 sets the threshold for deleting the clause |
| Blocked teardown | leased past expiry, or `failed`, and not clearing; kill errors in the reaper log | none automatic: a person looks. The next pass retries |
| Provisioning outage | `provision_failed` climbing across unrelated cards | free retries with backoff; quarantines past `runs.max_free_retries` with the class named |
| Failure no retry can fix | `runs.halted_class` set; pending cards, none claimed | a person fixes the credential or account and clears it, or abandons the run |
| Run over budget | pending cards, none claimed, spend at or above `runs.max_cost_usd` | a person raises the limit or abandons the run |
| Runaway runtime | `deadline_at` | quarantine; never extended by heartbeats |
| Deploy-induced churn | reap count spikes on release | graceful drain |
| Orphaned workspace | clone or container count exceeds live leases | the reaper's sweep by name (§5.4) |
| Clock skew | leases expiring early or late | all deadlines from the store's clock |

---

## 11. Testing the substrate

Three problems stay separate: **the harness worked**, **the jigs worked**, and **the output is
good**. This section is only the first.

- **Static invariants** — milliseconds, high value, run on every commit. Config validation (no
  missing tier, no missing effort), schema constraints, id derivation, predicate correctness against
  fixtures, and the `config_hash` invariant: **a hash change with no version bump fails the build**.
- **Hash stability tests** — reformat the config, reorder `skills.yaml` without changing membership,
  rewrite a non-rendering comment: `kind_hash` must not move. Change a rendering comment, swap one
  skill file's content, bump an effort, change a normalizer: it must move. These are the tests that make cross-run
  comparison mean anything, and they are cheap.
- **Property tests on the predicate** — generate graphs, assert no card is ready whose subtree is
  unfinished, and that emission rejects a missing dep or a cycle.
- **Contention tests** — N workers, one board, assert every card is claimed exactly once.
- **Kill tests** — `SIGKILL` a worker mid-card; `docker kill` a container mid-write. Assert clean
  requeue, worktree removal, workspace collection, and that the stale process's writes are absent.
  Assert that a slow second reaper leaves the next attempt's workspace intact, and that the sweep
  collects a container left after a crash past commit.
  Assert one closed `task_attempts` row per delivery, and `not_before` set on the requeued card.
- **Stall tests** — hang the card loop while the heartbeat keeps running; assert it is reaped as
  `stalled`. Run a tool for longer than the base TTL within its timeout; assert it is not.
- **Teardown tests** — make the kill fail, then the reset, then the drop. Assert the first two block
  requeue and the third does not. Point teardown outside `workspace_root`; assert it refuses.
- **Replay tests** — same run twice from cache; assert identical terminal graph. Cover `post_tool_call`
  output and a card that reaches attempt 2. A run with a `provider_refused` attempt replays to the same graph
  with zero outbound calls. A rate-limited key that then succeeded serves its response. A key that never
  succeeded reaches the same terminal state. A live call ignores a recorded failure (ADR-0014).
- **Attempt record tests** — escalate a card and rewrite another to `split`. Each earlier attempt keeps its
  `kind`, `tier` and `config_hash`, and the lessons queries still count them as what they were (ADR-0014).
- **Normalizer stability tests** — for each tool and check type, two runs with a different clock, PID and
  attempt number give identical bytes. Odoo's test uses a captured real log. A failing fixture's
  normalized output still contains its failure text and exit status.
- **Free-retry hit tests** — fail a card with a free class after turn *k*; the retry serves *k* calls
  from cache. Do the same after `SIGKILL`: the prompt is byte-identical unless it is the last delivery.
- **Oracle tests** — a failed or unavailable check never reaches `done`, including `done_with_concerns` and a
  direct `UPDATE`. A hidden rung's output never appears in the next attempt's rendered prompt.
- **Late-commit tests** — pause a worker past its lease, reap it, wake it: its commit changes nothing and its
  card's branch is gone. Heartbeat between selection and revoke: the card is not reaped.

### 11.1 Gate A

Before anything is built on top of the substrate:

> **Does crash recovery work reliably under contention?** Includes killing a container mid-write and
> confirming clean requeue, worktree removal and clone collection.

It includes a tampered worktree (rule 150). Plant a `.git` pointer with a hook, an fsmonitor and a filter, then
assert that no marker appears, the commit lands on the real branch, `diff_paths()` reports the true paths and
teardown clears the worktree. Plant a nested repository and assert rejection.

This is harder to test than a poll-loop crash, and it is the right place to spend the difficulty.

---

## 12. Build order for the substrate

1. Schema, including `runs`, `project` and `summary_schema_version`. **These three cannot be
   retrofitted.** Half a day beyond the rest. `task_attempts` goes in here too: rows a run never wrote
   cannot be recovered.
2. Ledger access layer: claim, heartbeat, commit, release — all fenced.
3. Reaper, in kill-first order, with the stall clause and backoff.
4. Worker loop and graceful drain.
5. Content store with the two-method interface, Postgres backend, write-side truncation.
6. Workspace provisioning: worktree, container, environment clone.
7. Model cache and the config pin.
8. `queries/lessons.sql`.
9. **Gate A.**

Nothing above this line needs a model call to test. That is deliberate: the substrate is the part
that is hard to build and well understood, so it goes first, and it can be proven correct without
spending a token.

---

## 13. What would change this document

Recorded because a settled document should say what unsettles it.

- **The predicate proves insufficient** — some scheduling need turns out not to be expressible as a
  dependency edge or readiness rule. That would be the first real argument for a coordinator, and it
  should be an ADR before it is a component.
- **Contention at claim time** — `SKIP LOCKED` on one table becomes the bottleneck. Unlikely at the
  scale contemplated; measurable if it happens.
- **Kill-first proves insufficient** — a card finds a way to write outside its workspace. That is a
  containment failure and it reopens enforcement.
- **Content-derived ids collide meaningfully** — two genuinely different cards hashing the same. The
  fix is a longer hash, not a sequence.
- **The three claims in §1 stop being true** of the alternatives — if controller-based tools acquire
  crash-safe records and real parallelism, the substrate's differentiators evaporate and the honest
  response is to say so.
