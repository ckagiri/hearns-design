-- ADR-0011. In the failing transaction. The first halting class stays until a person clears it.
UPDATE runs SET halted_class = $2 WHERE root_id = $1 AND halted_class IS NULL;
