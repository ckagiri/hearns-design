# H3 — Humble Helper Harness

## Project breakdown v2 — building with Claude Code

**Date:** 18 August 2026
**Supersedes** v1 (17 August), which is deleted — two plans is the same failure as two design
documents. **This file lives at the repo root, not in `docs/`.** It is a plan, not a design
document; `docs/` holds the four surfaces rule 133 names and nothing else.
**Stack:** Python 3.12+, PostgreSQL 16+. **Build tool:** Claude Code, per `h3-claude-code-setup.md`.

Same tasks as v1, same gates, same order. What changes is **how long each takes, who does it, and
which ones get more dangerous when an agent writes them.**

---

## 1. The honest headline

**55–73 ideal days becomes 38–51. That is about 30% off, not 70%.**

The arithmetic matters more than the number. Claude Code compresses *volume of code* by roughly
2.5–3× on the tasks where volume is the work — scaffolding, the CLI, the test suite, `tools/`. It
compresses almost nothing on the four things that dominate this project's critical path:

| Dominates the path | Why an agent barely helps |
|---|---|
| **P0-1**, the two schema drafts | The work is *judging whether two drafts converged on the same wrong answer*. That judgement is the deliverable |
| **P1-9**, the workspace triple | Docker, git worktrees, database clones. Environment debugging is where agents flail longest and most confidently |
| **Gate A** | Writing kill tests is fast. Making them pass is systems debugging against a real container runtime |
| **P2-2/P2-3**, the jigs | A jig is twenty observed failures compressed into a rule. The observation is calendar time and cannot be delegated |

If code-writing was ~40% of Phase 1 and it gets 3× faster, Phase 1 drops ~27%. That is the shape of
the whole plan. **Plan for less time and more variance**, not for a different project.

---

## 2. Delegation classes

Every task below carries one. This is the most useful column in the document.

| Class | Meaning | How the session runs |
|---|---|---|
| **DRIVE** | You decide; Claude drafts and argues | Plan mode. You state the shape, Claude proposes, you rule. Never accept a first plan on these |
| **DELEGATE** | Contract is complete; Claude implements | `/task P1-x`, plan, accept, review the diff, `@design-conformance` |
| **PAIR** | Neither works alone | Claude explores and runs experiments; you hold the model of what is happening |
| **HUMAN** | Do not delegate | Claude may prepare inputs. The act itself is yours |

**The HUMAN list, in full, because it is short and it is the project:**

- P0-1's verdict — did the two drafts converge, and does that mean the anchor is safe?
- Every RED capture (P0-10, P2-1) — the value is verbatim observation of failure
- Every ADR decision — `/adr` writes it, you decide it
- Step 7's two thresholds, written before P3-1 runs
- Any judgement that a mechanism should exist

---

## 3. Phase 0 — validation

*Register §6 items 1–5. Four of five produce artifacts you want regardless.*

| ID | Task | v1 | **v2** | Class |
|---|---|---|---|---|
| **P0-0** | **The `.claude` kit: CLAUDE.md, rules, settings, hooks, pre-commit** | — | **0.5 d** | DRIVE |
| **P0-1** | **Two independent schema drafts, diffed** | 1 h | **1 h** | HUMAN |
| P0-2 | Odoo conventions on a throwaway module | 0.5 d | 0.5 d | PAIR |
| P0-3 | `pharmacy.schema.yaml` for one slice | 0.5 d | 0.3 d | DRIVE |
| P0-4 | `tools/introspect.py` — the rung 3 oracle | 1.5–2 d | **0.5–1 d** | DELEGATE |
| P0-5 | Mutation tests for the oracle | 0.5 d | **0.2 d** | DELEGATE |
| P0-6 | `tools/schema_lint.py` | 0.5 d | **0.2 d** | DELEGATE |
| P0-7 | `make check-static` (rung 0) | 0.5 d | **0.2 d** | DELEGATE |
| P0-8 | `tools/generate.py`, **then measure coverage** | 2–3 d | **1–1.5 d** | PAIR |
| P0-9 | Container image + template-DB script | 1 d | 1 d | PAIR |
| P0-10 | RED corpus — **now much richer, see §8** | ongoing | ongoing | HUMAN |

**Phase 0: 8–11 d → 5–7 d.**

**P0-0 is new and goes first.** Half a day that pays back across every session after it. Do not
start P0-4 without the hooks in place — `guard_invariants.py` and pre-commit are what stop the
invariants eroding while you are moving fast.

**P0-1 stays one hour and stays yours.** It is the highest-leverage hour in the project and the
work is a judgement call. You may have Claude *generate* the two drafts — varying model or effort,
never seed, per R48 — but reading the diff and deciding what convergence means is the task.

**P0-8's measurement is PAIR, not DELEGATE.** Claude writes the generator quickly. The number it
produces reshapes the split jig and E1, and a generator that looks like it covers 80% while
covering 80% of the *easy* 80% is exactly the kind of measurement an eager collaborator produces.
Sample the output yourself.

---

## 4. Phase 1 — the substrate

*Core §12's build order.*

| ID | Task | v1 | **v2** | Class |
|---|---|---|---|---|
| P1-0 | Repo scaffold: uv, ruff, mypy, pytest, CI | 1 d | **0.3 d** | DELEGATE |
| P1-1 | Migration runner + `001_initial.sql` | 0.5 d | **0.3 d** | DELEGATE |
| **P1-2** | `Lease` value object + claim (one statement) | 1 d | **0.7 d** | **DRIVE** |
| **P1-3** | Heartbeat, release, commit — all fenced | 1 d | **0.7 d** | **DRIVE** |
| P1-4 | Commit as a harness operation + hook dispatch | 1 d | 0.7 d | DELEGATE |
| **P1-5** | Reaper, kill-first order | 1.5 d | **1 d** | **DRIVE** |
| P1-6 | Worker loop + role config + validation | 1.5 d | **0.7 d** | DELEGATE |
| P1-7 | Graceful drain on SIGTERM | 0.5 d | 0.3 d | DELEGATE |
| P1-8 | Content store, write-side truncation | 1.5 d | **0.5 d** | DELEGATE |
| **P1-9** | **Workspace triple: worktree + container + clone** | 3 d | **2.5 d** | **PAIR** |
| P1-10 | `tool_audit`, including denials | 0.5 d | 0.2 d | DELEGATE |
| P1-11 | `model_cache` + full key | 1 d | 0.5 d | DELEGATE |
| **P1-12** | Config pin + `kind_hash` over rendered layers | 1.5 d | **1 d** | **DRIVE** |
| P1-13 | Claim-time drift check, refuse loud | 0.5 d | 0.3 d | DELEGATE |
| P1-14 | `queries/lessons.sql` | 0.5 d | 0.3 d | PAIR |
| P1-15 | `queries/tree.sql` + static renderer | 0.5 d | 0.2 d | DELEGATE |
| P1-16 | Human gate: `reviews` + five verbs | 1 d | 0.5 d | DELEGATE |
| P1-17 | `h3` CLI | 1 d | **0.3 d** | DELEGATE |
| P1-18 | Ledger backup + one tested restore | 0.5 d | 0.3 d | DELEGATE |
| P1-19 | Static invariants + hash-stability tests | 1 d | **0.3 d** | DELEGATE |
| P1-20 | Property tests on the predicate | 1 d | **0.4 d** | DELEGATE |
| P1-21 | Contention tests | 0.5 d | 0.3 d | DELEGATE |
| P1-22 | Replay tests | 0.5 d | 0.3 d | DELEGATE |
| P1-23 | `EXPLAIN ANALYZE` at realistic size (R15) | 0.5 d | 0.4 d | PAIR |
| **P1-24** | **`CachedModel` spike — the runtime's model interface, backed by `model_cache`** | — | **0.5 d** | **DRIVE** |
| **Gate A** | The kill-test suite, passing | 2 d + | **2 d +** | **PAIR** |

**Phase 1: 21–27 d → 13.5–17.5 d.**

### P1-24 is new and it gates ADR-0004

Half a day, before Gate A, and it answers one question: **can the runtime expose the exact request
bytes sent to the provider?** Core §8 keys the cache on the rendered prompt, which means what the
provider received — the library's assembled system prompt and its generated tool schemas included.
If it cannot, ADR-0004's adoption reverses and the executor loop gets written by hand, which is the
recorded fallback.

It sits in Phase 1 rather than Phase 2 because it tests a core §8 guarantee, and core's guarantees
are what Gate A exists to establish. DRIVE, not DELEGATE: the failure mode is a spike that appears
to work because it hashes what was handed to the library rather than what the library sent.

### The four DRIVE tasks, and why

**P1-2, P1-3, P1-5, P1-12 are where an agent's instincts are actively wrong for this design.**

- **Claim must be one statement.** A `SELECT` then an `UPDATE` is more readable, and it is the
  shape a model reaches for. It is also the bug. The SQL is transcribed in core §5.3 — hand it over
  as the contract and diff the result against it.
- **Fencing is unintuitive.** `WHERE id = $1 AND lease_holder = $2` looks complete. Core §5.5
  explains why it isn't. An agent that has not read that section will simplify it back.
- **Kill-before-requeue looks like an ordering preference.** It is the difference between one live
  process and two editing the same worktree.
- **`kind_hash` over rendered layers, not files** (rule 127). "Hash the config files" is the
  obvious implementation and it is wrong in a way that only shows up months later as
  non-comparable runs.

For each: paste the design section as the contract, use plan mode, and diff the output against the
transcription rather than reading it for plausibility. `/drift` check 3 exists for exactly this.

### P1-9 stays expensive

Containers, bind mounts, git worktrees on the host with execution inside, database clones. This is
where an agent produces confident code against an environment it cannot see, and where the loop of
*try, fail, adjust* is slow regardless of who is driving. It is still the largest overrun risk in
the project. Prototype the git-on-host / execute-in-container split before trusting the estimate.

### Gate A does not compress

Writing the kill tests is a morning. Making them pass is systems work against real containers and a
real Postgres. Budget the same as v1 and treat any saving as luck.

---

## 5. Phase 2 — jigs and gates

*Gated on Gate A. Policy §11's order.*

| ID | Task | v1 | **v2** | Class |
|---|---|---|---|---|
| P2-1 | RED capture format + harness | 1 d | 0.5 d | HUMAN |
| **P2-2** | `execute` jig — RED → GREEN → pressure-test | 3–4 d | **2.5–3 d** | **PAIR** |
| **P2-3** | `verify` jig — same method | 3–4 d | **2.5–3 d** | **PAIR** |
| P2-4 | `checks.yaml` — four rungs, standalone | 1.5 d | 0.7 d | DELEGATE |
| P2-5 | Promote `introspect.py` to rung 3 | 0.5 d | 0.2 d | DELEGATE |
| P2-6 | Host-side `pre_commit` hooks incl. set difference | 2 d | **0.8 d** | DELEGATE |
| P2-7 | Echo detection | 0.5 d | 0.2 d | DELEGATE |
| P2-8 | `split` jig — scope set by P0-8 | 2–4 d | **1.5–3 d** | PAIR |
| P2-9 | Emit-time split gates | 1.5 d | 0.7 d | DELEGATE |
| P2-10 | `integrate` — rung 1 on the merged tree | 1 d | 0.5 d | DELEGATE |
| P2-11 | `re_verify` + round counter and breaker | 1 d | 0.5 d | DELEGATE |
| P2-12 | `digest` — the three queries | 1 d | 0.4 d | DELEGATE |
| **P2-13** | **Executor runtime: tool loop, per-kind tool sets, schema validation** | — | **1–1.5 d** | DELEGATE |
| P2-14 | `skills.yaml` — hand-chosen, RED-paired | 0.5 d | 0.5 d | HUMAN |
| P2-15 | Flatten version-delta files, strip `agents/` | 0.5 d | 0.2 d | DELEGATE |

**Phase 2: 16–22 d → 12–16.5 d.**

**P2-13 was missing from v1 and from this plan's first draft.** Phase 1 builds the substrate and
Phase 2 builds jigs — which are prompt templates — but something has to *execute* a jig inside the
container. ADR-0004 decides what: a library below the card boundary, with per-kind tool sets
(rule 135) so a `verify` card constructed without a write tool cannot edit what it reviews. Sized
at 1–1.5 d on the assumption P1-24 passed; 3–4 d if it did not and the loop is hand-written.

**The jigs compress least, and the reason is worth stating.** A jig is twenty observed failures
compressed into a prompt that negates each rationalization by name. Claude drafts the prose fast
and pressure-tests scenarios usefully. It cannot supply the observations. **P0-10's corpus is the
gate on Phase 2's real duration**, and it accumulates in calendar time whatever tooling you use.

**Watch for the jig writing itself into competence.** Ask Claude to draft a jig and it will produce
something fluent that covers the failures it can imagine. That is the inherited-elaboration risk
(R51) arriving through a new door. Every rule in a jig traces to a RED case or it comes out.

**Layer 3 is now settled structurally and contested behaviourally.** Rule 135 makes per-kind tool
sets a gate, which needs no experiment — a card without a write tool cannot write. Whether a
*narrower* set also improves attention is R50's argument moved to tools, and it is unmeasured;
policy §1.6 scopes the ablation and P3-5 runs it.

---

## 6. Phase 3 — experiments

*E3 → E2 → E1. Unchanged in order and substance.*

| ID | Experiment | v1 | **v2** | Class |
|---|---|---|---|---|
| P3-1 | **E3 — the baseline (Gas Town)** | 3–4 d | 3–4 d | PAIR |
| P3-2 | Emit-time gates vs a human-reviewed decomposition | 0.5 d | 0.4 d | PAIR |
| P3-3 | **E2 — verify axis**, arms A/B/D/E/C/C′/control | 4–5 d | **3–4 d** | PAIR |
| P3-4 | E1 — splitter, RED pass + plan-written control | 3–4 d | **2.5–3 d** | PAIR |
| P3-5 | Per-set ablation on layer 2 (R50) **and on tool-set width** (policy §1.6) | 1 d | 1 d | DELEGATE |

**Phase 3: 9–13 d → 7–10 d.**

Setup and harness code compress. Reading results does not, and should not — an agent summarising
its own experiment's output is the wrong reviewer for exactly the reasons policy §4.2 gives about
verify. **Write step 7's two thresholds before P3-1 runs**, by hand, in policy §10.

---

## 7. Failure modes specific to building this design with an agent

These are new risks introduced by the build tool, not by the design. Each names its detector.

| Failure | Why it hides | Detector |
|---|---|---|
| **A default appears where rules 72/107 forbid one** | `tier or "cheap"` is idiomatic, defensible, and silently reintroduces the failure core §4.1 names as a known controller bug | Config validation test; `@design-conformance` |
| **Transcribed SQL gets paraphrased** | The rewrite is often clearer. Both sides then look right in isolation | `/drift` check 3, diffing core §5 against `harness/ledger/sql/` |
| **A mechanism arrives as an improvement** | It genuinely is one. Elaboration always arrives defensible — that is R43's whole point | `guard_invariants.py` on vocabulary; `@design-conformance` on the diff; `/drift` check 6 |
| **A new design document appears** | An agent that has just done good work wants to write it down | `guard_invariants.py` rule 4; pre-commit `check_no_new_docs.py` |
| **Wall-clock time enters the ledger** | `datetime.now()` is correct almost everywhere else in Python | `guard_invariants.py` rule 2, both hooks |
| **Tests written to pass rather than to assert** | Same context wrote both. This is rules 82–83 at the build level | `test-first` subagent, blocked from writing outside `tests/` |
| **The spike hashes the wrong thing** | Hashing what you handed the library looks identical to hashing what it sent, and passes | P1-24 run as DRIVE; assert against a captured provider request, not against the inputs |
| **Velocity outruns the register** | Rules and risks accrete from real findings; the code moves faster than the file | `/drift` checks 2 and 7, at every phase boundary |

**The last one is the one to watch.** v1's plan assumed the design would stay ahead of the code
because writing code was slow. It no longer is. Run `/drift` at every phase boundary, not
occasionally.

---

## 8. What you get for free, and what it costs

**Every Claude Code session on this project is a RED observation.** P0-10 was "ongoing, 0
incremental" in v1. It is now the richest source you have: a frontier model doing Odoo and Postgres
work, unprompted, with its rationalizations visible in the transcript. Capture the failures with
`/red` as they happen — you are running the data collection for Phase 2 while doing Phase 0 and 1.

**It is also E3 evidence.** Building H3 with a single-agent harness is direct experience of the
baseline you will measure against. Not a controlled experiment, and it must not be reported as one.
But when you write step 7's thresholds, you will have months of felt sense for what the alternative
does well — which is exactly the input §10's positioning section needs and currently lacks.

**The cost is a conflict of interest, stated once.** You are evaluating whether a ledger-based
harness beats an agent harness, while using an agent harness daily and becoming fluent in it.
Fluency will make the baseline look better than it is to someone who is not fluent. Note that in
§10 rather than correcting for it — it is not correctable, only declarable.

---

## 9. Critical path

```
P0-0 (0.5 d) ──► the kit; everything downstream is faster and safer
P0-1 (1 h) ────► HUMAN; can invalidate Phase 0's shape
P0-8 (1–1.5 d) ► sets P2-8 and E1 scope
      │
P1-0 → P1-1 → P1-2 → P1-3 → P1-9 → P1-5 → GATE A ──► P2-1 → P2-2/P2-3 → GATE 2 ──► P3-1 → P3-3 → P3-4 → STEP 7
                      ▲       ▲       ▲       ▲                  ▲
                   DRIVE    PAIR    DRIVE    PAIR              PAIR
                                            └── does not compress ──┘
```

**Every node on the critical path is DRIVE or PAIR.** That is the plan in one line: the agent
accelerates the branches, not the spine.

**Parallel worktrees** — P1-8, P1-11, P1-14, P1-15 are independent of the claim–lease–reaper spine
and can run in a second session. Apply your own four tests first: disjoint touch sets, no
cross-references, safe retry, and the two together accounting for the parent. If those fail, do
them in sequence. The temptation to parallelise because the tool permits it is the temptation your
design spends several sections resisting.

**Totals: P0 5–7 · P1 13.5–17.5 · P2 12–16.5 · P3 7–10 ≈ 40–53 ideal days.**

The rise from v2's first draft is P1-24 and P2-13 — the runtime work that was missing rather than
optimistic. A plan getting longer because a gap was found is the plan working.

---

## 10. Session discipline

**One task, one session.** Your tasks have written exit criteria, which makes the boundary obvious.
Start fresh rather than compacting — a compacted session has lost the design sections it read.

**Per session:** `/task P1-x` → plan mode → implement → `uv run pytest` → `@design-conformance` on
the diff → commit. The commit is your real undo; `/rewind` does not cover Bash-command changes or
subagent edits, and this project runs `docker` and `dropdb`.

**Model and effort.** Opus at high effort for the four DRIVE tasks, the jigs, and anything touching
`config_hash` — `ultrathink` on the predicate and the fencing argument specifically. Sonnet for
DELEGATE. The built-in `Explore` agent for "where is X handled."

**Per phase boundary**, run the standing review from `rules-and-risks` §8 — which rules have never
been consulted, which risks never observed — plus `/drift`, plus one question v1 did not need:
*which of this phase's mechanisms exist because the design called for them, and which because they
were easy to add?*

---

## 11. What has not changed

Every gate, every anti-milestone, every exit criterion, and the definition of done: a test, a named
detector for the failure it prevents, and — for a mechanism — an answer to *has it fired?*

**Gate A still blocks Phase 2.** Faster code makes it more tempting to start jig work while the
substrate is unproven, and more expensive when substrate bugs and jig bugs arrive mixed.

**P0-1 is still the first hour.** If two independent schema drafts converge on the same wrong
answer, R44 has no mitigation and the oracle is confirming a module against a mistake. Nothing
about the build tool changes that, and it is much better learned in week one.
