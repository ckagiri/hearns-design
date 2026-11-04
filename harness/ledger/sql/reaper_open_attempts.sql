-- Rule 141's sweep. List the host's card_* names FIRST, then run this. Anything no row names is removed.
SELECT task_id, n FROM task_attempts WHERE ended_at IS NULL;
