-- Core §5.3, verbatim. Readiness and lease acquisition in one statement.
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
  INSERT INTO task_attempts (task_id, n, worker)
  SELECT id, attempts, $3 FROM claimed
)
SELECT * FROM claimed;
