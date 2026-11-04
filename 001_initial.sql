-- 001_initial.sql: the Phase 1 schema, consolidated.
--
-- RECONSTRUCTED 2026-11-04. The original (330 lines, per README) was never committed and could not be
-- found. This is rebuilt from the documents and is not a recovery of it. Applied to nothing yet, so it
-- may still be edited; once applied, forward-only (`.claude/rules/sql.md`).
--
-- Where each object comes from:
--   [core]     transcribed from harness-core-v3 §4. Core wins if the two ever differ.
--   [spec]     columns listed in a document, types chosen here.
--   [inferred] the documents name the table or its purpose. The columns are a reasonable guess.
--
-- Run in one transaction. The migration runner (P1-1) owns its own bookkeeping table and the advisory
-- lock, so neither is here.

-- ─── The board ───────────────────────────────────────────────────────────────────────────────────

-- [core §9.3] Compares digit runs as numbers, so the tree sorts t-x.2 before t-x.10. Needs ICU.
CREATE COLLATION tree_order (provider = icu, locale = 'und-u-kn');

-- [core §4.1]
CREATE TYPE task_state AS ENUM (
  'awaiting_review',  -- gated on a human
  'pending',          -- on the board, may or may not be runnable
  'leased',           -- claimed by a worker
  'done',
  'failed',           -- retryable; reaped back to pending
  'quarantined'       -- terminal; scrap pile
);

-- [core §4.1]
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

-- [core §4.1, ADR-0007] One row per delivery, written in the claim's transaction.
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

-- [inferred] Each reaper pass reads the open rows (core §5.4, rule 141).
CREATE INDEX task_attempts_open_idx ON task_attempts (task_id) WHERE ended_at IS NULL;

-- [core §4.2, ADR-0011]
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

-- ─── Model calls ─────────────────────────────────────────────────────────────────────────────────

-- [spec for the key: policy §1.5; the rest inferred] Per-call cost. Budget sums cost_usd (core §5.3).
-- served_from_cache: a hit writes a row at zero cost (ADR-0012).
CREATE TABLE model_calls (
  task_id           text NOT NULL,
  attempt           int  NOT NULL,
  seq               int  NOT NULL,
  model             text NOT NULL,
  effort            text,
  cache_key         text NOT NULL,
  served_from_cache boolean NOT NULL DEFAULT false,
  tokens_in         bigint NOT NULL DEFAULT 0,
  tokens_out        bigint NOT NULL DEFAULT 0,
  reasoning_tokens  bigint NOT NULL DEFAULT 0,
  cost_usd          numeric(12,6) NOT NULL DEFAULT 0,
  reasoning_ref     text,            -- policy §2.0.3: the trace lives in the content store
  created_at        timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (task_id, attempt, seq),
  FOREIGN KEY (task_id, attempt) REFERENCES task_attempts (task_id, n)
);

-- [inferred from core §8] The key is taken over the adapter's serialized bytes, which already hold the
-- model, effort, params and tool schemas (ADR-0005). root_id is what "TTL by run" (core §4.4) expires by.
CREATE TABLE model_cache (
  key        text PRIMARY KEY,
  response   jsonb NOT NULL,
  root_id    text NOT NULL REFERENCES runs(root_id),
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX model_cache_root_idx ON model_cache (root_id);

-- [ADR-0014] Provider failures, under the same key. Replay re-raises one unless model_cache has a response for that
-- key. A live run never reads this table, so it cannot serve a failure. A separate table keeps response NOT NULL.
CREATE TABLE model_failures (
  key           text PRIMARY KEY,
  failure_class text NOT NULL,
  root_id       text NOT NULL REFERENCES runs(root_id),
  created_at    timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX model_failures_root_idx ON model_failures (root_id);

-- ─── Content store ───────────────────────────────────────────────────────────────────────────────

-- [spec: core §4.3 names body, external and the hash; the table's name is a guess] Written and fetched by
-- hash, never searched. Refs elsewhere are plain hashes with no foreign key: content expires and rows do
-- not (core §4.4).
CREATE TABLE content (
  hash       text PRIMARY KEY,
  media_type text,                  -- core §4.3 truncates and expires by type, though put() takes only bytes
  body       bytea,
  external   text,
  expires_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT content_has_a_location CHECK (body IS NOT NULL OR external IS NOT NULL)
);

-- ─── The record of what happened ─────────────────────────────────────────────────────────────────

-- [inferred from ADR-0003, ADR-0012] What was attempted, including denials. A denied call never ran, so
-- it has no duration. raw_ref is set only when normalizing changed the bytes.
CREATE TABLE tool_audit (
  id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  task_id     text NOT NULL,
  attempt     int  NOT NULL,
  tool        text NOT NULL,
  decision    text NOT NULL CHECK (decision IN ('allowed', 'denied')),
  reason      text,
  args_digest text NOT NULL,
  duration_ms bigint,
  raw_ref     text,
  created_at  timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY (task_id, attempt) REFERENCES task_attempts (task_id, n)
);

-- [inferred from core §7] Every human action: what they had open, what they chose, why. The first five
-- verbs are core §7's. The rest are other actions the documents say a person takes: reset-from-a-point
-- (§8.2), clearing a halt (§5.3), raising a budget and abandoning a run (§10), and requeueing a card that
-- ran out of free retries (ADR-0011).
CREATE TABLE reviews (
  id         bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  task_id    text NOT NULL REFERENCES tasks(id),
  verb       text NOT NULL CHECK (verb IN ('approve', 'edit', 'split', 'kill', 'promote',
                                           'reset', 'requeue', 'clear_halt', 'raise_budget', 'abandon')),
  had_open   jsonb NOT NULL DEFAULT '[]',
  reason     text NOT NULL,
  detail     jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

-- [spec: core §4.5] Superseded, never edited. Promotion is a human verb, and a note carries the task it
-- came from. Ships as NullMemory, so nothing writes here yet.
CREATE TABLE notes (
  id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  project       text NOT NULL,
  scope         text NOT NULL CHECK (scope <> 'global'),
  task_id       text NOT NULL REFERENCES tasks(id),
  body          text NOT NULL,
  promoted_by   text NOT NULL,
  superseded_by bigint REFERENCES notes(id),
  created_at    timestamptz NOT NULL DEFAULT now()
);
