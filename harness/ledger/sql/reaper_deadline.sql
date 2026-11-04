-- Core §5.4, verbatim. Runs no teardown; the sweep collects what it leaves (rule 141).
UPDATE tasks
   SET state='quarantined', failure_class='deadline_exceeded',
       lease_holder=NULL, lease_expires_at=NULL, updated_at=now()
 WHERE state IN ('pending','leased')
   AND deadline_at IS NOT NULL AND deadline_at < now();
