"""Verify harness/ledger/sql/*.sql and queries/*.sql against core, on a throwaway Postgres.
Start a throwaway database first, and remove it afterwards:
  docker run --rm -d --name hh-schema-test -e POSTGRES_HOST_AUTH_METHOD=trust postgres:16
  python3 -I tests/ledger/verify_files.py . hh-schema-test
  docker stop hh-schema-test
"""
import re
import subprocess
import sys
from pathlib import Path

repo, container = Path(sys.argv[1]), sys.argv[2]
core = (repo / "harness-core-v3.md").read_text()
migration = (repo / "001_initial.sql").read_text()
blocks = re.findall(r"```sql\n(.*?)```", core, re.S)
led = repo / "harness/ledger/sql"
results = []


def psql(sql, db="f", check=True, extra=()):
    p = subprocess.run(["docker", "exec", "-i", container, "psql", "-U", "postgres", "-d", db, "-At", "-q",
                        "-v", "ON_ERROR_STOP=1", *extra], input=sql, capture_output=True, text=True)
    if check and p.returncode:
        raise RuntimeError(p.stderr.strip() + "\n--- " + sql[:300])
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def report(name, ok, detail=""):
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"\n      {detail}" if detail else ""))


def fresh():
    for s in ("DROP DATABASE IF EXISTS f WITH (FORCE)", "CREATE DATABASE f"):
        subprocess.run(["docker", "exec", container, "psql", "-U", "postgres", "-q", "-c", s], check=True,
                       capture_output=True)
    psql(migration)


def body(name):
    """A ledger file without its leading comment lines."""
    lines = (led / f"{name}.sql").read_text().splitlines()
    while lines and lines[0].startswith("--"):
        lines.pop(0)
    return "\n".join(lines)


def norm(s):
    return " ".join(s.split())


def run(name, *args):
    q = body(name).strip().rstrip(";")
    for i in range(len(args), 0, -1):
        q = re.sub(rf"\${i}(?!\d)", lambda _: str(args[i - 1]), q)
    return psql(q + ";")[1]


def rows(sql):
    return psql(sql)[1]


# ── Transcribed files match core, whitespace aside (`/drift` check 3) ───────────────────────────────
claim_b = next(b for b in blocks if "WITH candidate AS" in b)
reaper_b = re.sub(r"--.*", "", next(b for b in blocks if "-- candidates: dead" in b))
parts = [s.strip() + ";" for s in reaper_b.split(";") if s.strip()]
for name, src in {"claim": claim_b, "reaper_candidates": parts[0], "reaper_flip": parts[1], "reaper_deadline": parts[2]}.items():
    report(f"{name}.sql matches core, whitespace aside", norm(body(name)) == norm(src))
hb = next(b for b in blocks if "last_heartbeat_at = now()" in b).replace("$ttl", "$4::interval")
report("heartbeat.sql matches core, $ttl aside", norm(body("heartbeat")) == norm(hb))
tree_core = next(b for b in blocks if "string_to_array(id, '.')" in b)
report("queries/tree.sql opens with core's query", norm(tree_core) in norm((repo / "queries/tree.sql").read_text()))
less_core = next(b for b in blocks if "-- which contract shapes" in b)
report("queries/lessons.sql opens with core's three", norm(less_core) in norm((repo / "queries/lessons.sql").read_text()))

# ── Everything parses and plans against the schema ──────────────────────────────────────────────────
fresh()
for f in sorted(led.glob("*.sql")):
    rc, _, err = psql(f"PREPARE p AS {body(f.stem).strip().rstrip(';')};", check=False)
    report(f"prepares: {f.name}", rc == 0, err)
report("one statement per ledger file", all(body(f.stem).strip().rstrip(";").count(";") == 0 for f in led.glob("*.sql")))
VARS = ("-v", "p='p'", "-v", "d='d'", "-v", "h='h'")
for f in sorted((repo / "queries").glob("*.sql")):
    rc, _, err = psql(f.read_text(), extra=VARS, check=False)
    report(f"runs on an empty board: queries/{f.name}", rc == 0, err)


# ── The lifecycle, through these files ──────────────────────────────────────────────────────────────
def emit(id, root=None, deps="{}", kind="execute", state="pending", retry_safe="true"):
    root = root or id.split(".")[0]
    parent = "NULL" if "." not in id else f"'{id.rsplit('.', 1)[0]}'"
    return run("emit_task", f"'{id}'", f"'{root}'", "'p'", parent, f"'{kind}'", "'cheap'", f"'{state}'", "'{}'::jsonb",
               "'title'", "'contract'", "'complete'", "NULL", "'{}'::text[]", "NULL", "NULL", "'[]'::jsonb",
               f"'{deps}'::text[]", retry_safe, "NULL", "0", "NULL", "'v'", "'h'", "NULL")


def claim(worker="w1"):
    q = body("claim").strip().rstrip(";")
    for k, v in {"$1": "ARRAY['execute','split']", "$2": "ARRAY['cheap']", "$3": f"'{worker}'", "$4": "'60 seconds'", "$5": "'5 minutes'"}.items():
        q = q.replace(k, v)
    return psql(q.replace("SELECT * FROM claimed", "SELECT id||':'||attempts FROM claimed") + ";")[1]


def state(id):
    return rows(f"SELECT state||'/'||attempts||'/'||max_attempts||'/'||coalesce(failure_class,'-') FROM tasks WHERE id='{id}';")


def open_run(id, limit=12):
    rows(f"INSERT INTO runs (root_id,project,intent_digest,config_pin,max_free_retries) VALUES ('{id}','p','d','{{}}',{limit});")


FREE = "ARRAY['rate_limited','overloaded','timeout','provision_failed','released']"
EVIDENCE = "ARRAY['check_failed','context_exceeded','provider_refused','malformed_output','turn_limit']"


def end(id, n, cls, check="NULL", hidden="NULL", refusal="NULL"):
    run("end_attempt", f"'{id}'", n, f"'{cls}'", check, "NULL", hidden, refusal)


def fail(id, worker, n, cls, free="false", outcome="NULL", check="NULL"):
    run("fail", f"'{id}'", f"'{worker}'", n, f"'{cls}'", free, outcome, check)


def commit(id, worker, n, check, outcome="ok"):
    run("commit", f"'{id}'", f"'{worker}'", n, "NULL", "NULL", "NULL", f"'{outcome}'", check, 0, 0, 0, 0, "'m'", "'e'", 0, 0, "NULL", "NULL")


def park(id, worker, n, outcome, summary="NULL"):
    run("park", f"'{id}'", f"'{worker}'", n, f"'{outcome}'", summary, "NULL")


def expire(id):
    rows(f"UPDATE tasks SET lease_expires_at = now() - interval '1 minute' WHERE id='{id}';")


def ready(id):
    rows(f"UPDATE tasks SET not_before=NULL WHERE id='{id}';")

fresh()
emit("t-a"); open_run("t-a")
emit("t-a")
report("re-emitting the same id no-ops", rows("SELECT count(*) FROM tasks WHERE id='t-a';") == "1")
report("claim", claim() == "t-a:1")
run("heartbeat", "'t-a'", "'w1'", 1, "'60 seconds'")
report("heartbeat bumps the fenced lease", rows("SELECT last_heartbeat_at IS NOT NULL FROM tasks WHERE id='t-a';") == "t")
run("heartbeat", "'t-a'", "'w1'", 0, "'60 seconds'")

# A free failure, through the reaper, charges nothing.
fail("t-a", "w1", 1, "provision_failed", "true")
end("t-a", 1, "provision_failed")
c = rows(body("reaper_candidates")).split("|")
run("reaper_flip", f"'{c[0]}'", c[1])
report("a free failure raises max_attempts and never lowers attempts", state("t-a") == "pending/1/4/provision_failed", state("t-a"))
report("free rows are countable", run("count_free_attempts", "'t-a'", FREE) == "1")
report("no evidence yet", run("last_evidence_attempt", "'t-a'", EVIDENCE) == "")

# A charged failure, then another free one: layer 7 must read the charged one.
rows("UPDATE tasks SET not_before=NULL WHERE id='t-a';"); claim()
fail("t-a", "w1", 2, "malformed_output")
end("t-a", 2, "malformed_output")
run("reaper_flip", "'t-a'", 2)
rows("UPDATE tasks SET not_before=NULL WHERE id='t-a';"); claim()
fail("t-a", "w1", 3, "rate_limited", "true")
end("t-a", 3, "rate_limited")
run("reaper_flip", "'t-a'", 3)
last = run("last_evidence_attempt", "'t-a'", EVIDENCE)
report("layer 7 reads the last evidence attempt, skipping a later free one", last.startswith("2|malformed_output"), last)
report("claim clears failure_class; the row keeps history", rows("SELECT count(*) FROM task_attempts WHERE task_id='t-a' AND failure_class IS NOT NULL;") == "3")

# A stale writer cannot fail or release a newer claim.
rows("UPDATE tasks SET not_before=NULL WHERE id='t-a';"); claim()
before = state("t-a")
fail("t-a", "w1", 1, "malformed_output")
run("release", "'t-a'", "'w1'", 1, "true")
report("stale fail and release change nothing", state("t-a") == before, state("t-a"))

# Drain.
run("release", "'t-a'", "'w1'", 4, "true")
end("t-a", 4, "released")
report("drain's release is free and backed off", state("t-a").startswith("pending/4/") and rows("SELECT not_before > now() FROM tasks WHERE id='t-a';") == "t", state("t-a"))
emit("t-r"); open_run("t-r")
rows("UPDATE tasks SET state='leased', lease_holder='w1', attempts=3, max_attempts=3 WHERE id='t-r';")
run("release", "'t-r'", "'w1'", 3, "false")
report("past the free limit, a card out of attempts quarantines rather than sits pending", state("t-r").startswith("quarantined"), state("t-r"))

# Halt: the first class stays, and clearing restores claims.
fresh()
emit("t-h"); open_run("t-h")
run("halt_run", "'t-h'", "'auth_rejected'")
run("halt_run", "'t-h'", "'billing_exhausted'")
report("the first halting class stays", rows("SELECT halted_class FROM runs WHERE root_id='t-h';") == "auth_rejected")
report("a halted run refuses claims", claim() == "")

# Deadline: reaper_deadline.sql leaves an open row unless its companion closes it.
rows("UPDATE runs SET halted_class=NULL WHERE root_id='t-h';")
claim()
report("the attempt is open", run("reaper_open_attempts") == "t-h|1")
rows("UPDATE tasks SET deadline_at = now() - interval '1 second' WHERE id='t-h';")
rows(body("reaper_deadline") + body("reaper_deadline_close"))
report("the deadline quarantines and closes the attempt",
       state("t-h").startswith("quarantined") and run("reaper_open_attempts") == "", state("t-h"))

# Stalled: transitive, and only through deps.
fresh()
for i, d in [("t-x", "{}"), ("t-y", "{t-x}"), ("t-z", "{t-y}"), ("t-w", "{}")]:
    emit(i, deps=d)
rows("UPDATE tasks SET state='quarantined' WHERE id='t-x';")
stalled = psql((repo / "queries/stalled.sql").read_text(), extra=VARS)[1].splitlines()
report("stalled.sql follows deps transitively and spares the unrelated",
       sorted(s.split("|")[0] for s in stalled) == ["t-y", "t-z"] and all("t-x" in s for s in stalled), str(stalled))

# Rollup: subtree numbers from a prefix scan, and order.
fresh()
for i in ("t-s", "t-s.2", "t-s.10", "t-s.2.1"):
    emit(i, root="t-s", kind="split" if i == "t-s" else "execute")
rows("UPDATE tasks SET cost_usd=1 WHERE id='t-s.2'; UPDATE tasks SET cost_usd=2, outcome='refused', attempts=3 WHERE id='t-s.10';"
     "UPDATE tasks SET state='quarantined' WHERE id='t-s.2.1';")
out = psql((repo / "queries/tree.sql").read_text(), extra=VARS)[1].splitlines()
order = [r.split("|")[0] for r in out[:4]]
report("tree order is numeric-aware", order == ["t-s", "t-s.2", "t-s.2.1", "t-s.10"], str(order))
roll = out[4].split("|")
report("the rollup counts descendants, cost, attempts, refusals and quarantines",
       roll[1] == "3" and float(roll[2]) == 3 and roll[3] == "3" and roll[4] == "1" and roll[6] == "t", str(roll))

# ── ADR-0013: try to break each decision ────────────────────────────────────────────────────────────
print("-- ADR-0013")
Q = "SELECT state||'/'||coalesce(lease_holder,'-') FROM tasks WHERE id='{}';"

# Rule 145: the oracle decides.
fresh(); emit("t-1"); open_run("t-1"); claim()
expect = psql(f"UPDATE tasks SET state='done' WHERE id='t-1';", check=False)
report("a bare UPDATE to done is refused", expect[0] != 0 and "done_means_checked" in expect[2])
fail("t-1", "w1", 1, "check_failed", check="'failed'")
commit("t-1", "w1", 1, "'passed'")
report("a late commit cannot flip failed to done", state("t-1").startswith("failed"), state("t-1"))
fresh(); emit("t-2"); open_run("t-2"); claim()
out = subprocess.run(["docker", "exec", "-i", container, "psql", "-U", "postgres", "-d", "f", "-At", "-c",
                      "UPDATE tasks SET state='done', check_result='failed' WHERE id='t-2' AND lease_holder='w1' AND attempts=1 AND state='leased'"], capture_output=True, text=True)
report("commit with a failed check is refused by the database", "done_means_checked" in out.stderr, out.stderr)
commit("t-2", "w1", 1, "'passed'")
report("commit with a passed check lands", state("t-2").startswith("done"))
emit("t-3"); open_run("t-3"); claim()
commit("t-3", "w1", 1, "'not_applicable'", "expanded")
report("not_applicable can land for expanded", state("t-3").startswith("done"))

# Parking holds dependents, is not reaped, and the record survives a rerun.
fresh(); emit("t-p"); emit("t-c", deps="{t-p}"); open_run("t-p"); open_run("t-c"); claim()
park("t-p", "w1", 1, "needs_context", """'{"needs":["fact"]}'::jsonb""")
end("t-p", 1, "needs_context", refusal="""'{"needs":["fact"]}'::jsonb""")
report("parking clears the lease", psql(Q.format("t-p"))[1] == "awaiting_review/-", psql(Q.format("t-p"))[1])
report("a parked dep holds its dependent", claim() == "")
report("the reaper does not select a parked card", rows(body("reaper_candidates")) == "")

# The way back cannot strand a card, and the record survives it.
rows("UPDATE tasks SET attempts=3, max_attempts=3 WHERE id='t-p';")
rows("INSERT INTO task_attempts (task_id,n,worker,kind,tier,config_hash) VALUES ('t-p',3,'w','execute','cheap','h') ON CONFLICT DO NOTHING;")
rows("UPDATE task_attempts SET ended_at=now(), failure_class='needs_context' WHERE task_id='t-p' AND n=3;")
run("review_return", "'t-p'", "NULL", "NULL", "NULL", "NULL", "NULL", "now() + interval '1 hour'")
report("a returned card with no attempts left is claimable", claim() == "t-p:4", state("t-p"))
report("attempts is not lowered, and the next delivery is not the last", state("t-p").startswith("leased/4/6"), state("t-p"))
commit("t-p", "w1", 4, "'passed'")
lessons = psql((repo / "queries/lessons.sql").read_text(), extra=VARS)[1]
report("needs_context survives the rerun in core's lessons query", '["fact"]' in lessons and "needs_context" in lessons)

# Misclassified: rewrite in place, dependents held, no chain.
fresh(); emit("t-m"); emit("t-d", deps="{t-m}"); open_run("t-m"); open_run("t-d"); claim()
run("rekind_split", "'t-m'", "'w1'", 1, "'cheap'", "'h2'")
end("t-m", 1, "misclassified", refusal="""'{"reason":"three deliverables"}'::jsonb""")
report("a misclassified card becomes a split on its own row", rows("SELECT kind||'/'||state||'/'||config_hash FROM tasks WHERE id='t-m';") == "split/pending/h2")
report("its dependent is held, and it is claimed as a split", claim() == "t-m:2" and claim() == "", state("t-d"))
attempt_was = "SELECT kind||'/'||config_hash FROM task_attempts WHERE task_id='t-m' AND n={};"
report("a rewrite leaves the earlier attempt as it was, and the new one records the split", rows(attempt_was.format(1)).startswith("execute/") and rows(attempt_was.format(2)) == "split/h2", rows(attempt_was.format(1)))
rows("INSERT INTO model_calls (task_id,attempt,seq,model,cache_key,cost_usd) VALUES ('t-m',1,1,'m','k',0.5);")
lessons = psql((repo / "queries/lessons.sql").read_text(), extra=VARS)[1]
report("the lessons queries still count a rewritten card's refusal as execute", "|misclassified|1" in lessons, lessons[:200])
report("its earlier spend stays booked to what it was", "|execute|0.5" in lessons, lessons[:200])
run("rekind_split", "'t-m'", "'w1'", 2, "'cheap'", "'h3'")
report("a split cannot be rewritten again", rows("SELECT state||'/'||config_hash FROM tasks WHERE id='t-m';") == "leased/h2")
park("t-m", "w1", 2, "misclassified")
report("a misclassified split waits for a person", state("t-m").startswith("awaiting_review"))

# Rule 149: retry_safe.
fresh(); emit("t-s", retry_safe="false"); open_run("t-s"); claim()
fail("t-s", "w1", 1, "check_failed"); end("t-s", 1, "check_failed"); run("reaper_flip", "'t-s'", 1)
report("a failed retry_safe=false card goes to review", state("t-s").startswith("awaiting_review"), state("t-s"))
report("the sweep spares its workspace with no open attempt", run("reaper_open_attempts") == "t-s|1")
emit("t-t", retry_safe="false"); open_run("t-t"); claim()
expire("t-t"); run("reaper_flip", "'t-t'", 1)
report("so does one whose worker died", state("t-t").startswith("awaiting_review"), state("t-t"))
emit("t-u", retry_safe="false"); open_run("t-u"); claim()
fail("t-u", "w1", 1, "provision_failed", "true"); end("t-u", 1, "provision_failed"); run("reaper_flip", "'t-u'", 1)
report("provision_failed is exempt: no work ran", state("t-u").startswith("pending"), state("t-u"))
ready("t-u"); claim()
run("release", "'t-u'", "'w1'", 2, "true")
report("drain cannot bypass it", state("t-u").startswith("awaiting_review"), state("t-u"))

# Rule 147: evidence.
fresh(); emit("t-e"); open_run("t-e"); claim()
expire("t-e"); run("reaper_revoke", "'t-e'", 1); run("reaper_flip", "'t-e'", 1); end("t-e", 1, "lease_expired"); ready("t-e"); claim()
rows("UPDATE tasks SET last_progress_at = now() - interval '1 hour' WHERE id='t-e';")
run("reaper_revoke", "'t-e'", 2); run("reaper_flip", "'t-e'", 2); end("t-e", 2, "stalled")
report("a dead worker and a stall are not evidence", run("last_evidence_attempt", "'t-e'", EVIDENCE) == "" and run("count_evidence_attempts", "'t-e'", EVIDENCE) == "0")
report("but both still count against the crash bound", state("t-e").startswith("pending/2/3"), state("t-e"))
run("escalate_tier", "'t-e'", 2, "'strong'", "'h9'")
report("the last delivery's tier is written, and the role that claims it sees it", rows("SELECT tier||'/'||config_hash FROM tasks WHERE id='t-e';") == "strong/h9")
report("escalation leaves earlier attempts as they were", "strong" not in rows("SELECT string_agg(tier||'/'||config_hash, ' ') FROM task_attempts WHERE task_id='t-e';"), rows("SELECT string_agg(tier||'/'||config_hash, ' ') FROM task_attempts WHERE task_id='t-e';"))
ready("t-e")
rows("UPDATE tasks SET tier='cheap' WHERE id='t-e';"); claim()
fail("t-e", "w1", 3, "check_failed", check="'failed'"); end("t-e", 3, "check_failed", hidden="'abc'"); run("reaper_flip", "'t-e'", 3)
last = run("last_evidence_attempt", "'t-e'", EVIDENCE)
report("a hidden failure is marked, and its output is not in check_ref", last.startswith("3|check_failed||t"), last)
report("the third charged delivery quarantines", state("t-e").startswith("quarantined/3/3"), state("t-e"))

# Rule 148: the late commit.
fresh(); emit("t-l"); open_run("t-l"); claim(); expire("t-l")
run("reaper_revoke", "'t-l'", 1)
report("revoke keeps the row leased, so nothing can claim it mid-teardown", psql(Q.format("t-l"))[1] == "leased/-" and claim() == "")
commit("t-l", "w1", 1, "'passed'")
report("a late commit after revoke changes nothing", psql(Q.format("t-l"))[1] == "leased/-", psql(Q.format("t-l"))[1])
report("a reaper dying here leaves it selectable", rows(body("reaper_candidates")).startswith("t-l|1"))
emit("t-v"); open_run("t-v"); claim()
run("reaper_revoke", "'t-v'", 1)
report("a live worker keeps its card", psql(Q.format("t-v"))[1] == "leased/w1", psql(Q.format("t-v"))[1])
commit("t-v", "w1", 1, "'passed'")
report("and its commit lands", state("t-v").startswith("done"))

# stalled.sql follows clause (b).
fresh()
for i, d in [("t-q", "{}"), ("t-q.1", "{}"), ("t-w", "{t-q}"), ("t-n", "{}"), ("t-n.1", "{}"), ("t-y", "{t-n}"), ("t-a", "{}"), ("t-a.1", "{t-z}"), ("t-z", "{}"), ("t-b", "{t-a}")]:
    emit(i, deps=d)
rows("UPDATE tasks SET state='done', check_result='passed' WHERE id IN ('t-q','t-n','t-a');"
     "UPDATE tasks SET state='awaiting_review' WHERE id='t-q.1';"
     "UPDATE tasks SET state='quarantined' WHERE id IN ('t-n.1','t-z');")
stalled = psql((repo / "queries/stalled.sql").read_text(), extra=VARS)[1].splitlines()
names = sorted({s.split("|")[0] for s in stalled})
report("a dependent held by a parked descendant is listed", "t-w" in names, str(names))
report("a dependent behind only a quarantined descendant is not", "t-y" not in names, str(names))
report("a pending descendant held by a quarantined dep passes the hold on", {"t-a.1", "t-b"} <= set(names), str(names))

print(f"\n{sum(results)}/{len(results)} passed")
sys.exit(0 if all(results) else 1)
