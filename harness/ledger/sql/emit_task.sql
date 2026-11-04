-- Core §5.7's third statement, one row. A duplicate content-derived id no-ops. Rule 140's checks run first.
INSERT INTO tasks (id, root_id, project, parent_id, kind, tier, state, intent, title, contract,
                   contract_completeness, check_spec, touch_set, owns, interfaces, open_questions, deps,
                   retry_safe, deadline_at, priority, caused_by, config_version, config_hash, base_sha)
VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21,
        $22, $23, $24)
ON CONFLICT (id) DO NOTHING;
