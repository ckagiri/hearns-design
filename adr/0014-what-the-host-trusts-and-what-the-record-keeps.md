# ADR-0014: What the host may trust from a worktree, and what the record must keep

**Status:** Accepted by the owner on 4 November 2026, with the container mask not required: this is still design
and subject to change.
**Date:** 2026-11-04
**Amends:** core §4.1, §4.4, §5.3, §5.4, §6, §8, §8.1.1, §9.4, §11, §11.1; `odoo-adaptation` §6.2 and its rule 85
row; rules 85 and 141; ADR-0013's "the attempt row records what the card was", which this makes true;
`001_initial.sql`; `harness/ledger/sql/claim.sql`; `queries/lessons.sql`; `jig-sketch.py` `CachedModel`;
`tests/ledger/`; PLAN P1-9, P1-22; `PROTOTYPE_v3`'s worktree hook hazard
**Adds:** rules 150–152; R64
**Guarded by:** the tests under each decision below
**Informed by:** `deepseek-ai/deepseek-harness` at `8bd07339`, read 4 November 2026 and not run here. See
`borrow-notes.md` (the original DeepSeek note is in git history). Decision 1 rests on git probes run for this ADR: git 2.50.1 on macOS,
scratch repositories, marker files only, no container and no harness.

## Context

Reading DeepSeek Harness exposed three gaps in this design. None is a problem with that project, and each
is cheap to close now because nothing is built and the migration is unapplied.

**The host trusts a file the card can write.** Core §6 and `odoo-adaptation` §6.2 bind-mount the worktree,
then commit from the host. A worktree's `.git` is a file inside that mount, and it tells git which repository
to use. No document says it is masked or ignored, and none specifies how the host calls git. Rule 85 says
commit hooks are unreachable from inside the card. The probes show what a card can do by writing only inside
its worktree, if the host calls git in the usual way:

| Host call, on a worktree whose `.git` points at a repository the card made | Result |
|---|---|
| `git status` | **The card's `core.fsmonitor` program runs on the host** |
| `git commit` | **The card's `pre-commit` hook runs on the host.** The real branch gets nothing |
| `git -c core.hooksPath=/dev/null status` | The card's `core.fsmonitor` program still runs |
| `git diff --name-only HEAD`, with a tracked file changed | **Empty.** `pre_commit`'s `ws.diff_paths()` would see no change |
| `git worktree remove --force` | Refused, so teardown fails on every pass |

**Attempts do not record what the card was.** ADR-0013 says they do, but `task_attempts` has no such columns,
and `escalate_tier.sql` and `rekind_split.sql` overwrite `kind`, `tier` and `config_hash` on the task. So
`queries/lessons.sql` drops a rewritten card's `execute` refusals and books its earlier calls to its final
tier. The first of those is the question core §9.4 uses to justify the schema.

**Replay cannot reproduce a failed provider call.** `CachedModel` writes to the cache only on success, and
`model_cache.response` is `NOT NULL`. Replaying an attempt that ended `provider_refused` finds no entry for
that key and raises `ReplayMiss`, while core §8 says any difference "is a genuine difference in your code".
The code did not change. A run with a charged provider failure cannot be replayed at all.

## Decision

### 1. Host git treats the worktree as untrusted input (rule 150)

**Every host git call goes through one runner.** It takes the git directory from the harness's own record of
what it created, and never from the worktree's `.git`. The tested form:

```sh
env -i PATH=… GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1 \
  git --git-dir=<repo>/.git/worktrees/<name> --work-tree=<worktree> \
      -c core.hooksPath=/dev/null -c core.fsmonitor=false -c user.name=… -c user.email=… <command>
```

Against the same planted repository, plus a hook planted in the real repository, `status`, `add -A` and `commit`
ran none of the planted programs, and the commit landed on the real branch. `diff` reported the true paths.
Scrubbing host config also matters, because the card controls `.gitattributes`: with a filter defined in the
host's global config, a card naming it ran that filter on the host until the config was scrubbed.

Disabling git hooks loses no gate, because `pre_commit` is a harness function (`jig-sketch.py` `run_hooks`).

**Three more rules follow.**

- **Reject gitlinks.** A repository nested in the worktree is staged as mode `160000`, so `diff_paths()` sees
  one path and none of its contents. A staged gitlink is a touch-set violation, even when the path is in the set.
- **Teardown removes by path, then runs `git worktree prune`.** It does not use `git worktree remove`. Tested on
  a tampered worktree: removal and prune cleared the registration and ran nothing. Core §6's check that the path
  is inside `workspace_root` still comes first. Rule 141's sweep uses the same route.
- **Mask `.git` read-only inside the container, as a second layer.** The runner protects the harness, not a person.
  Rule 149 keeps failed worktrees for review, and someone running `git status` in one could run the card's program.
  The mask covers the top-level pointer only, so a nested `.git` remains. Review shows kept work through the
  runner. The mask is **untested and required by nothing**: the probes used no container, and no other decision or
  test here depends on it.

**Core §11.1 (Gate A) gains:** plant a `.git` pointer with a hook, an fsmonitor and a filter, then assert that no
marker appears, the commit lands on the real branch, `diff_paths()` reports the true paths and teardown clears
the worktree. Plant a nested repository and assert rejection.

### 2. An attempt records what the card was (rule 151)

`task_attempts` gains `kind`, `tier` and `config_hash`, all `NOT NULL`, written by `claim.sql` from the row it just
claimed and never updated.

```sql
INSERT INTO task_attempts (task_id, n, worker, kind, tier, config_hash)
SELECT id, attempts, $3, kind, tier, config_hash FROM claimed
```

**Queries about what ran read the attempt.** In `lessons.sql` and its copies in core §8.1.1 and §9.4, that is: which
contract shapes produce refusals, the same slice across runs, cost and tokens, and reasoning tokens. `model_calls` already
has a foreign key to the attempt. Distributions by a card's final `kind` still read `tasks`.

**Core §11 gains:** escalate a card and rewrite another to `split`. Each earlier attempt keeps its values, and the
refusal query still counts the `execute` refusal.

### 3. Replay reproduces provider failures, and a recorded response wins (rule 152)

```sql
CREATE TABLE model_failures (
  key           text PRIMARY KEY,
  failure_class text NOT NULL,
  root_id       text NOT NULL REFERENCES runs(root_id),
  created_at    timestamptz NOT NULL DEFAULT now()
);
```

```python
if hit := cache.get(key):                          # a response always wins
    record_call(req, key, served_from_cache=True, cost=0)
    return hit
if self.mode == "replay":
    if failure := model_failures.get(key):
        record_call(req, key, served_from_cache=True, cost=0)
        raise HarnessFailure(failure)
    raise ReplayMiss(key)
try:
    resp = self.inner.complete(req)
except HarnessFailure as e:
    model_failures.put(key, e.failure_class)       # upsert. Live mode never reads this table
    raise
cache.put(key, resp)
return resp
```

**Every provider failure is recorded, and no class list or ordinal is needed.** Letting a response win gives each
case the right behaviour:

| Live run | Replay |
|---|---|
| Charged failure, and the retry's key moved | Re-raises, so the same attempts follow and the retry hits |
| Free failure, then the same key succeeded | Serves the response. The outage is not replayed |
| Failed until the card quarantined or the run halted | Re-raises until the same terminal state |

**`attempts` may be lower in replay,** in the second row. Core §8 asserts the terminal graph, which does not change.

**The class is enough to rebuild the next prompt,** because layer 7 renders `failure_class` and check output, not
the provider's text. If layer 7 ever renders that text, this table has to store it.

Retention matches `model_cache`: TTL by run.

**Core §8 changes:** "Record every response" gains "and every provider failure", and the replay row of its table
becomes "every call hits or re-raises; a miss raises".

**Core §11 gains:** a run with a `provider_refused` attempt replays to the same terminal graph with zero outbound
calls. A rate-limited key that then succeeded serves its response. A key that never succeeded reaches the same
terminal state. A live call ignores a recorded failure.

## Alternatives considered

**Only disable hooks,** as DeepSeek Harness's runner does with `core.hooksPath` and `core.fsmonitor`. It keeps the
planted programs of those two kinds out, but the host still follows the card's pointer: the commit goes to the
fake repository and a diff can read empty. That is not a flaw in its runner, whose threat is different. No
equivalent of this attack was found there, and its runner is the starting point here.

**Mask `.git` alone.** It leaves nested repositories and is untested, and one missed mount reopens everything.

**Rewrite the pointer before each git call.** It works, but it adds a step every caller must remember and destroys
the evidence of tampering. Pinning needs no step.

**Run git in the container.** Core §6 already rejects this: it gives the card the sibling worktrees or the gates.

**Mount a plain copy with no pointer at all.** Attractive, but it costs a copy per attempt and changes rule 141,
and pinning already works. The nested-repository case would remain.

**Keep whole-task revisions per attempt,** as DeepSeek Harness's `team/task` journal does. The statements read
overwrite few fields that any query needs. `rekind_split.sql` also clears `check_spec`, and no lessons query reads
it. Three columns give the benefit.

**Nullable attempt columns.** They spare the test fixtures and allow the gap this closes.

**Store failures in `model_cache` with a nullable response.** One mistake in `cache.get` would then serve a failure
to a live call. A separate table has no such path: absent is easier to guarantee than configured-off (ADR-0005).

**Serve recorded failures in live runs too.** A free retry would replay its own outage.

**Key failures by ordinal,** to replay each failure in sequence. It reproduces outages nobody wants reproduced, and
only exists to order failures against a later success, which "a response wins" already settles.

**Declare such runs out of scope for replay.** Then §8's "any difference is genuine" needs a caveat, and runs with
failures are the ones most worth replaying.

**An explicit override per run,** as DeepSeek Harness's `deriveReplayScript` demands for a thrown call. It suits
curated fixtures, not replaying whatever the ledger recorded.

## Consequences

**Good.** Rule 85's claim becomes true of the host. The touch-set gate reads the real tree. ADR-0013's sentence
about attempts becomes true, and the lessons queries survive a rewrite. Replay covers runs with provider failures.

**Costs.**
- **All host git goes through one runner,** and a direct call would look fine until a card exploited it. A
  `tests/ledger/verify_files.py`-style scan for direct `git` calls should guard it once the code exists.
- **Harness-side git config is now explicit,** so anything relying on host config, such as credentials or LFS,
  must be passed deliberately. The workload's needs here were not traced.
- **`add -A` commits whatever the card left,** such as the planted directory in the probes, so the touch-set gate
  must catch it. How the harness stages is not specified anywhere yet.
- **Three `NOT NULL` columns break two fixtures:** `tests/ledger/verify_schema.py:170` and `verify_files.py:256`.
  That suite also fails on any column core's §4 lacks, and `claim.sql` is marked a verbatim copy of core §5.3, so
  core §4.1 and §5.3 must change in the same commit.
- **One more table and one write on each provider failure.**

**R64: a host gate reads a file the card wrote.** `namespace_check` parses the diff on the host, and
manifest regeneration runs there. Pinning git says nothing about a planted symlink or a hostile parser input.

**Not measured.** Decision 1's table comes from probes on one git version with no container and no harness, and the
runner does not exist yet. Decision 2's SQL is exercised in `tests/ledger/` on Postgres 16. Decision 3's table loads
there too, but `CachedModel` exists only in the sketch, so its replay tests are specified and not yet written.

## Left open

- **How host gates should read card-written files (R64).** Not traced. It needs its own look before P1-9 ends.
- **Which uid the container writes as.** Git's `safe.directory` check might refuse some of this on its own, depending
  on ownership. It was not tested and is not relied on.
- **What replay does with a person's actions.** If a person edited a card after a free failure, its old key stays
  failure-only and replay stops where they acted. How replay treats `reviews` was not traced.

## What would change our mind

- **Any config or file in the work tree reaches pinned git and runs something** → pinning isn't enough. Move to a
  plain mounted copy with no git metadata.
- **The mask cannot hold in the container runtime,** or review never touches kept worktrees → drop the mask.
- **No query separates attempt values from task values by step 7** → the columns are margin, and principle 8 applies.
- **No run by step 7 records a provider failure that matters to replay** → drop `model_failures` and document the
  exclusion instead.
