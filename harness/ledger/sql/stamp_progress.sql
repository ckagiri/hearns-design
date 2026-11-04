-- Core §5.4. Stamped on each model response and each finished tool call, fenced. Never from the heartbeat.
UPDATE tasks SET last_progress_at = now()
 WHERE id=$1 AND lease_holder=$2 AND attempts=$3 AND state='leased';
