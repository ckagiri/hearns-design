-- approve, edit, split and requeue (core §7). NULL leaves a field alone. attempts is never lowered, and enough deliveries
-- remain that the next is not the last. Record the action and the new deadline in reviews, and tear down any kept workspace.
UPDATE tasks
   SET state='pending', kind=COALESCE($2, kind), tier=COALESCE($3, tier), config_hash=COALESCE($4, config_hash),
       contract=COALESCE($5, contract), check_spec=COALESCE($6, check_spec), deadline_at=$7,
       max_attempts=GREATEST(max_attempts, attempts + 3), not_before=NULL, outcome=NULL, check_result=NULL,
       failure_class=NULL, updated_at=now()
 WHERE id=$1 AND state='awaiting_review';
