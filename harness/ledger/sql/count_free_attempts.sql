-- ADR-0011: a card's free retries are counted from its rows, so no counter is added. $2 is FREE_RETRY.
SELECT count(*) FROM task_attempts WHERE task_id = $1 AND failure_class = ANY($2);
