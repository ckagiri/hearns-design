-- Rule 68: nothing else writes tier. In the flip's transaction, when the next delivery is the last and the flip was
-- not free. A free flip never escalates, so an outage cannot raise a tier twice.
UPDATE tasks SET tier = $3, config_hash = $4, updated_at = now()
 WHERE id = $1 AND attempts = $2 AND state = 'pending';
