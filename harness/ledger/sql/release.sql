-- Drain's early release, after the worker's own teardown (core §5.8). Free up to the limit, with backoff (ADR-0011). Past it,
-- $4 is false, so a card out of attempts quarantines rather than sitting pending. retry_safe=false goes to a person (rule 149).
UPDATE tasks
   SET max_attempts = max_attempts + CASE WHEN $4::boolean THEN 1 ELSE 0 END,
       state = (CASE WHEN NOT retry_safe THEN 'awaiting_review'
                     WHEN $4::boolean OR attempts < max_attempts THEN 'pending'
                     ELSE 'quarantined' END)::task_state,
       not_before = now() + LEAST(interval '10 seconds' * power(2, attempts - 1), interval '5 minutes'),
       lease_holder = NULL, lease_expires_at = NULL,
       failure_class = 'released', updated_at = now()
 WHERE id=$1 AND lease_holder=$2 AND attempts=$3 AND state='leased';
