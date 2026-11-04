-- Core §5.7's first statement, with its elided columns filled in from §4.1. Fenced.
UPDATE tasks SET state='done', result_ref=$4, result_summary=$5, result_size=$6, outcome=$7,
                 check_result=$8, tokens_in=$9, tokens_out=$10, reasoning_tokens=$11, cost_usd=$12,
                 model_used=$13, effort_used=$14, check_latency_ms=$15, rung1_invocations=$16, prompt_ref=$17, result_sha=$18,
                 updated_at=now()
 WHERE id=$1 AND lease_holder=$2 AND attempts=$3;
