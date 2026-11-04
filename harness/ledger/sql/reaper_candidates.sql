-- Core §5.4, verbatim. Teardown runs per candidate before reaper_flip.sql.
SELECT id, attempts FROM tasks
 WHERE state = 'failed'
    OR (state = 'leased' AND (lease_expires_at < now()
                              OR last_progress_at + stall_after < now()));
