-- Rule 148. Before teardown, for a leased candidate. A late commit's fence then fails. No row back means the worker
-- heartbeated since selection, so skip it. The row stays leased, and a reaper dying here leaves it selectable.
UPDATE tasks SET lease_holder = NULL, updated_at = now()
 WHERE id = $1 AND attempts = $2 AND state = 'leased'
   AND (lease_expires_at < now() OR last_progress_at + stall_after < now());
