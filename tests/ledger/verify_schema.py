"""Verify 001_initial.sql against core's own DDL and queries, on a throwaway Postgres.

Core's SQL is extracted from harness-core-v3.md at run time, so this tests the document as it stands.
Start a throwaway database first, and remove it afterwards:
  docker run --rm -d --name hh-schema-test -e POSTGRES_HOST_AUTH_METHOD=trust postgres:16
  python3 -I tests/ledger/verify_schema.py . hh-schema-test
  docker stop hh-schema-test
"""
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

repo, container = Path(sys.argv[1]), sys.argv[2]
core = (repo / "harness-core-v3.md").read_text()
migration = (repo / "001_initial.sql").read_text()
blocks = re.findall(r"```sql\n(.*?)```", core, re.S)
results = []


def psql(sql, db="t", check=True):
    p = subprocess.run(
        ["docker", "exec", "-i", container, "psql", "-U", "postgres", "-d", db, "-At", "-q",
         "-v", "ON_ERROR_STOP=1", "-1"],
        input=sql, capture_output=True, text=True)
    if check and p.returncode:
        raise RuntimeError(p.stderr.strip())
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def report(name, ok, detail=""):
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"\n      {detail}" if detail else ""))


def block_with(needle):
    return next(b for b in blocks if needle in b)


def fresh(db="t"):
    for stmt in (f"DROP DATABASE IF EXISTS {db} WITH (FORCE)", f"CREATE DATABASE {db}"):
        subprocess.run(["docker", "exec", container, "psql", "-U", "postgres", "-q", "-v", "ON_ERROR_STOP=1",
                        "-c", stmt], capture_output=True, text=True, check=True)


# ── 1. Core's DDL, loaded on its own, against the migration ─────────────────────────────────────────
COLS = """SELECT table_name||'.'||column_name||' '||data_type||' '||is_nullable||' '||coalesce(column_default,'')
          FROM information_schema.columns WHERE table_schema='public' ORDER BY 1"""
INDEXES = "SELECT indexdef FROM pg_indexes WHERE schemaname='public' ORDER BY 1"
fresh("c")
ddl = "\n".join(b for b in blocks if re.search(r"CREATE (TYPE|TABLE)", b))
psql(ddl, "c")
core_cols = set(psql(COLS, "c")[2 - 1].splitlines())
core_idx = set(psql(INDEXES, "c")[1].splitlines())

fresh()
rc, _, err = psql(migration, check=False)
report("migration loads in one transaction", rc == 0, err)
my_cols = set(psql(COLS)[1].splitlines())
my_idx = set(psql(INDEXES)[1].splitlines())
report("every core column present with the same type, nullability and default", core_cols <= my_cols,
       "; ".join(sorted(core_cols - my_cols)))
report("every core index present, identically", core_idx <= my_idx, "; ".join(sorted(core_idx - my_idx)))
core_tables = {c.split(".")[0] for c in core_cols}
extra = sorted(c.split(" ")[0] for c in my_cols - core_cols if c.split(".")[0] in core_tables)
report("the migration adds no column to core's tables", extra == [], ", ".join(extra))
CONS = "SELECT conrelid::regclass||' '||conname||' '||pg_get_constraintdef(oid) FROM pg_constraint WHERE connamespace='public'::regnamespace AND conrelid IN ('tasks'::regclass,'task_attempts'::regclass,'runs'::regclass) ORDER BY 1"
report("core's constraints are identical", psql(CONS, "c")[1] == psql(CONS)[1])

# ── 2. Every query in core prepares against the schema ──────────────────────────────────────────────
claim = block_with("WITH candidate AS")
reaper = block_with("-- candidates: dead, silent, or explicitly failed")
tree = block_with("string_to_array(id, '.')")
lessons = block_with("-- which contract shapes produce refusals")
heartbeat = block_with("last_heartbeat_at = now()").strip().rstrip(";")
fence = block_with("WHERE id=$1 AND lease_holder=$2 AND attempts=$3;   -- value")
commit = """UPDATE tasks SET state='done', result_ref=$4, result_summary=$5, outcome=$6, tokens_in=$7,
  tokens_out=$8, cost_usd=$9, model_used=$10, check_latency_ms=$11, updated_at=now()
  WHERE id=$1 AND lease_holder=$2 AND attempts=$3"""
commit_attempt = "UPDATE task_attempts SET ended_at=now(), check_ref=$3, diff_ref=$4 WHERE task_id=$1 AND n=$2"
reaper_stmts = [s.strip() for s in re.sub(r"--.*", "", reaper).split(";") if s.strip()]
lesson_stmts = [s.strip() for s in re.sub(r"--.*", "", lessons).split(";") if s.strip()]
queries = {"claim": claim, "heartbeat": heartbeat.replace("$ttl", "$4::interval"),
           "fenced commit": commit, "attempt close": commit_attempt,
           "tree": tree.replace(":p", "$1")}
for i, s in enumerate(reaper_stmts):
    queries[f"reaper {i+1}"] = s
for i, s in enumerate(lesson_stmts):
    queries[f"lessons {i+1}"] = re.sub(r":[pd]\b", "$1", s)
for name, q in queries.items():
    rc, _, err = psql(f"PREPARE p AS {q.strip().rstrip(';')};", check=False)
    report(f"core query prepares: {name}", rc == 0, err)

# ── 3. Behaviour, driven through core's own claim and reaper ────────────────────────────────────────
def task(id, root=None, deps=(), **kw):
    root = root or id.split(".")[0]
    d = ",".join(f"'{x}'" for x in deps)
    cols = {"id": f"'{id}'", "root_id": f"'{root}'", "project": "'p'", "kind": "'execute'", "tier": "'cheap'",
            "intent": "'{}'", "title": "'x'", "contract": "'c'", "deps": f"ARRAY[{d}]::text[]",
            "config_version": "'v'", "config_hash": "'h'", **kw}
    return f"INSERT INTO tasks ({','.join(cols)}) VALUES ({','.join(cols.values())});\n"


def do_claim(worker="w1", db="t"):
    q = claim.strip().rstrip(";")
    for k, v in {"$1": "ARRAY['execute','split']", "$2": "ARRAY['cheap']", "$3": f"'{worker}'",
                 "$4": "'60 seconds'", "$5": "'5 minutes'"}.items():
        q = q.replace(k, v)
    q = q.replace("SELECT * FROM claimed", "SELECT id||':'||attempts FROM claimed")
    return psql(q + ";", db)[1]


def expect_error(name, sql, needle):
    rc, _, err = psql(sql, check=False)
    report(name, rc != 0 and needle in err, err if rc == 0 or needle not in err else "")


fresh()
psql(migration)
run = "INSERT INTO runs (root_id, project, intent_digest, config_pin, max_free_retries, max_cost_usd) VALUES ('{0}','p','d','{{}}',12,{1});\n"
psql(task("t-a") + run.format("t-a", "NULL"))

expect_error("tasks.tier has no default", "INSERT INTO tasks (id,root_id,project,kind,intent,title,contract,config_version,config_hash) VALUES ('t-z','t-z','p','k','{}','t','c','v','h');", "tier")
expect_error("runs.max_free_retries has no default", task("t-y") + "INSERT INTO runs (root_id,project,intent_digest,config_pin) VALUES ('t-y','p','d','{}');", "max_free_retries")
big = "{\"a\":\"" + "".join(f"{i:x}" for i in range(4000)) + "\"}"
expect_error("the intent size CHECK fires", task("t-big", intent=f"'{big}'"), "intent_size")
expect_error("a state outside core's six is refused (the sketch writes 'blocked')", "UPDATE tasks SET state='blocked' WHERE id='t-a';", "invalid input value for enum")
expect_error("done with no check is refused", "UPDATE tasks SET state='done' WHERE id='t-a';", "done_means_checked")
expect_error("done with a failed check is refused", "UPDATE tasks SET state='done', check_result='failed' WHERE id='t-a';", "done_means_checked")
expect_error("done with an unavailable check is refused", "UPDATE tasks SET state='done', check_result='unavailable' WHERE id='t-a';", "done_means_checked")
expect_error("a global note is refused", "INSERT INTO notes (project,scope,task_id,body,promoted_by) VALUES ('p','global','t-a','b','me');", "scope")
expect_error("an unknown review verb is refused", "INSERT INTO reviews (task_id,verb,reason) VALUES ('t-a','bless','r');", "verb")
expect_error("content must have a location", "INSERT INTO content (hash,media_type) VALUES ('h','text/plain');", "content_has_a_location")
expect_error("a model call needs an attempt row", "INSERT INTO model_calls (task_id,attempt,seq,model,cache_key) VALUES ('t-a',9,1,'m','k');", "foreign key")
expect_error("a tool audit row needs an attempt row", "INSERT INTO tool_audit (task_id,attempt,tool,decision,args_digest) VALUES ('t-a',9,'read','allowed','d');", "foreign key")

psql("INSERT INTO reviews (task_id,verb,reason) VALUES ('t-a','requeue','out of free retries');")
report("claim leases the card and counts a delivery", do_claim() == "t-a:1")
report("claim opens one task_attempts row", psql("SELECT count(*) FROM task_attempts WHERE task_id='t-a' AND n=1 AND ended_at IS NULL;")[1] == "1")
stale = psql("WITH u AS (UPDATE tasks SET state='done' WHERE id='t-a' AND lease_holder='w1' AND attempts=0 RETURNING 1) SELECT count(*) FROM u;")[1]
report("a stale fence commits nothing", stale == "0")
report("a claimed card cannot be claimed twice", do_claim("w2") == "")

# The reaper, core's statements, attempt by attempt, ending in quarantine.
flip = reaper_stmts[1].replace("$1", "'t-a'")
states = []
for n in (1, 2, 3):
    psql("UPDATE tasks SET lease_expires_at = now() - interval '1 minute' WHERE id='t-a';")
    picked = psql(reaper_stmts[0] + ";")[1]
    psql(flip.replace("$2", picked.split("|")[1]) + ";")
    states.append(psql("SELECT state||'/'||failure_class||'/'||(not_before IS NOT NULL) FROM tasks WHERE id='t-a';")[1])
    if n < 3:
        psql("UPDATE tasks SET not_before=NULL WHERE id='t-a';")
        do_claim()
report("the reaper requeues with backoff, then quarantines at max_attempts",
       states == ["pending/lease_expired/true", "pending/lease_expired/true", "quarantined/lease_expired/true"], str(states))

# Clause (a), clause (b), and core's "different bars".
psql(task("t-p") + task("t-p.1", root="t-p", parent_id="'t-p'") + task("t-q", deps=["t-p"]) + run.format("t-p", "NULL") + run.format("t-q", "NULL"))
psql("UPDATE tasks SET state='leased' WHERE id IN ('t-p','t-p.1');")
report("clause (a): a dep that is not done blocks", do_claim() == "")
psql("UPDATE tasks SET state='done', check_result='passed' WHERE id='t-p';")
report("clause (b): a dep's unfinished descendant blocks", do_claim() == "")
psql("UPDATE tasks SET state='quarantined' WHERE id='t-p.1';")
report("a quarantined descendant is acceptable", do_claim() == "t-q:1")

# Budget and halt refuse in the claim.
psql(task("t-b") + run.format("t-b", "1.00") + task("t-b.1", root="t-b", state="'leased'", attempts="1"))
psql("INSERT INTO task_attempts (task_id,n,worker) VALUES ('t-b.1',1,'w');")
psql("UPDATE tasks SET state='leased', attempts=1 WHERE id='t-b.1';")
psql("INSERT INTO model_calls (task_id,attempt,seq,model,cache_key,cost_usd) VALUES ('t-b.1',1,1,'m','k1',0.50);")
psql("INSERT INTO model_calls (task_id,attempt,seq,model,cache_key,cost_usd,served_from_cache) VALUES ('t-b.1',1,2,'m','k2',0,true);")
report("spend under the limit still claims, and a cache hit adds nothing", do_claim() == "t-b:1")
psql("UPDATE tasks SET state='pending', lease_holder=NULL WHERE id='t-b';")
psql("INSERT INTO model_calls (task_id,attempt,seq,model,cache_key,cost_usd) VALUES ('t-b.1',1,3,'m','k3',0.50);")
report("Budget refuses at the limit", do_claim() == "")
psql(task("t-h") + run.format("t-h", "NULL") + "UPDATE runs SET halted_class='auth_rejected' WHERE root_id='t-h';")
report("a halted run refuses claims", do_claim() == "")
psql("UPDATE runs SET halted_class=NULL WHERE root_id='t-h';")
report("clearing the halt claims again", do_claim() == "t-h:1")

# Tree order is not lexical.
psql(task("t-o") + task("t-o.2", root="t-o", parent_id="'t-o'") + task("t-o.10", root="t-o", parent_id="'t-o'"))
tree_sql = tree.split("--")[0].strip().rstrip(";").replace(":p", "'p'")
order = " ".join(r.split("|")[0] for r in psql(tree_sql + ";")[1].splitlines() if r.startswith("t-o"))
report("t-o.2 sorts before t-o.10 under core's tree query", order == "t-o t-o.2 t-o.10", order)

# Contention, through the real claim, in separate connections.
fresh()
psql(migration)
psql("".join(task(f"t-c{i}") + run.format(f"t-c{i}", "NULL") for i in range(40)))
with ThreadPoolExecutor(8) as pool:
    got = list(pool.map(lambda i: do_claim(f"w{i}"), range(60)))
ids = [g for g in got if g]
report("60 racing claims on 40 cards: each claimed exactly once", len(ids) == 40 and len(set(ids)) == 40, f"{len(ids)} claims, {len(set(ids))} unique")

print(f"\n{sum(results)}/{len(results)} passed")
sys.exit(0 if all(results) else 1)
