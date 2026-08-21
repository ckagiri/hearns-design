---
paths:
  - "**/*.sql"
  - "migrations/**"
  - "queries/**"
---

# SQL, migrations and queries

## Migrations

- Forward-only. Numbered `NNN_name.sql`. **Never edit a migration that has been applied** —
  write a new one.
- `001_initial.sql` is consolidated and already includes `runs`, `project`,
  `summary_schema_version` and the `model_calls` table. Those three columns cannot be
  retrofitted; if a change would drop or rename them, stop and raise it.
- The runner takes `pg_advisory_lock` so two starting workers cannot migrate concurrently.

## Ledger SQL

- One statement per file, named for the operation.
- The claim query, the reaper and the predicate are transcribed from `docs/harness-core-v3.md`
  §5.1–5.4. If you change one, the design document changes with it — they are not allowed to
  drift.
- Indexes exist for reasons stated in core §4.1. Before adding one, check whether the query
  should instead be shaped to use `tasks_prefix_idx` (`text_pattern_ops`), which is what makes
  the subtree clause affordable.
- `id LIKE dep.id || '.%'` is a prefix scan on the hottest path. Any change here needs
  `EXPLAIN ANALYZE` at realistic graph size attached (R15).

## Queries

- `queries/lessons.sql` is an **acceptance test for schema fields**: a field nobody can write a
  query against is a field to remove. Add the query when you add the field.
- `queries/tree.sql` orders by `string_to_array(id, '.')`, not lexically — `t-x.10` must not
  sort before `t-x.2`.
- Human-facing output is a query rendered to static HTML by a script. The moment it acquires a
  backend, a login or a write path it has become the dashboard anti-milestone.

## Never

- No `SELECT *` feeding code that assumes column order.
- No `WHERE` or `JOIN` against the content store's `body` column. It is written and fetched by
  hash, never searched.
- No trigger that writes derived state. Nothing writes `ready`; it is a pure function of the
  graph so that nothing can lie about it.
- No `DELETE` from `tasks`, `runs`, `reviews`, `notes` or `tool_audit`. Growth is handled by
  partitioning, never by pruning (rule 94).
