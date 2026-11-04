-- Closes attempts left open by reaper_deadline.sql, in its transaction. Core §5.4: each flip closes its row.
UPDATE task_attempts a SET ended_at=now(), failure_class='deadline_exceeded'
  FROM tasks t
 WHERE a.task_id = t.id AND a.ended_at IS NULL
   AND t.state = 'quarantined' AND t.failure_class = 'deadline_exceeded';
