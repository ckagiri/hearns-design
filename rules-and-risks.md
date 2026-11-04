# Rules and Risks

**Authority for rule and risk numbering.** Check here before assigning a number.
**Replaces** the live half of `change-register` (§3, §4, §6–§9). The migration half of that document
— what changed from v2 and why — is frozen as `migration-v2-to-v3.md` and is not edited again.

**This is not a change register.** Rules and risks were §22 and §23 of the design; they are *part of*
it, not a record of amendments to it. A file that collects pending changes grows until someone
proposes a new version to consolidate it — which is the loop v2 fell into, and the reason core and
policy are separately editable.

---

## 1. The forward process

Three landing places. There is no fourth.

| Change | Lands |
|---|---|
| A section is wrong, incomplete, or superseded | **Edit** `harness-core-v3`, `harness-policy-v3` or `odoo-adaptation` in place |
| A decision — especially a deletion | **A new ADR**, naming what it amends and what would reopen it |
| A new rule or risk | **Appended here**, numbered from this file |

A change touching four files is still not a register entry: the ADR names what it amends and the
edits go in the files. ADR-0003 does exactly this across policy §6, core §5.9 and the vocabulary.

**Rule 133 exists because "we need a document to hold these changes" is the sentence that starts
every one of these cycles.**

---

## 2. Numbering — three collisions resolved

Recorded because silent reassignment is worse than a visible one.

**Rules 64–67.** v2's rule list runs to **67**, not 63. Patch documents written afterwards assumed
it ended at 63 and reused 64–68. The patch-chain numbering is now used across six documents, so it
stands, and v2's originals are relocated:

| v2 rule | Disposition |
|---|---|
| 64 — `decided` paired with `open_questions`; set difference is the detector | → **ADR-0001**, which supersedes it as a decision of record with an amended frame |
| 65 — declarations verified against reality where cheaply possible | → absorbed into rules 81 and 85 (commit-time hooks, host-side) |
| 66 — any rate used as a quality indicator is reported with its false-positive rate | → **rule 131**, preserved; it is captured nowhere else |
| 67 — the diagnostic: remove any worker type, the system must degrade | → **rule 132**, preserved; core §2 principle 7 states the weaker form |

**Rules 91–96** were independently assigned three times. `worked-run` keeps 91;
`store-and-lessons` keeps 92–98; `odoo-adaptation`'s schema-authoring rules moved to 99–104.

**Risks R28–R30.** v2's register already used these. Same resolution — the patch chain stands,
v2's originals move to R54–R56.

---

## 3. Rules

Rules 1–63 are v2's, carried forward. Where core, policy or an ADR has changed one, it is marked
**→** rather than silently rewritten, because a superseded rule with a pointer is more useful than a
deleted one.

### Control stays decentralized

| # | Rule |
|---|---|
| 1 | Nothing assigns work. Availability is a query; workers claim for themselves. |
| 2 | The readiness predicate is the scheduler. No role overrides it. |
| 3 | Dependency satisfaction is subtree-aware: a dependency's descendants must be terminal too. |
| 4 | Terminal means *nothing runnable and nothing leased* — never *nothing pending*. |
| 5 | Workers never message each other. They append and exit. |
| 6 | No worker waits on another's response. No blocking asks. |
| 7 | A worker emits findings, not sequences. |
| 8 | Observation is never control. Observers and budget arbiters report or refuse, never direct. |

### The board holds the truth

| # | Rule |
|---|---|
| 9 | Postgres owns state. |
| 10 | *(notification payloads carry a task id and nothing else)* → **void**, ADR-0003: notification is absent |
| 11 | The system must work with notification disabled → **trivially satisfied**, ADR-0003 |
| 12 | Failure state lives on the board — never in a transport layer. |
| 13 | *(write then publish, via the outbox, in one transaction)* → **void**, ADR-0003: the outbox insert leaves the commit path |

### Cards stay small

| # | Rule |
|---|---|
| 14 | Intents are refs and parameters under a byte ceiling, enforced by CHECK and CI. |
| 15 | Big outputs go to the content store; cards hold references. |
| 16 | Every large artifact gets a small structured summary. |
| 17 | Context is managed by splitting, not compressing. |
| 18 | A summary records what the card **decided** that its contract did not specify — not only what it found. → extended by rule 67 |

### Decomposition is disciplined

| # | Rule |
|---|---|
| 19 | Split on four tests: stateable postcondition, sibling independence, safe retry or refusal, children accounting for exactly the parent. |
| 20 | If success can only be judged by opinion, split further. |
| 21 | Splitting is ordinary work: do it, mark `done` with `outcome='expanded'`, walk away. Never watch your children. |
| 22 | Every split emits its gates at split time, depending on all siblings. |
| 23 | Fan-out is harness-guaranteed, not model-volunteered. |
| 24 | Sibling independence is gated structurally on declared touch-sets, not on coaching alone. |
| 25 | Rich coaching in the prompt; crude gates in code. |
| 26 | A splitter summarises its decomposition, never its children's results. |

### Cheap work stays honest

| # | Rule |
|---|---|
| 27 | A role's claim filter is `(kind, tier)`; both are columns written at emit time. |
| 28 | *(tier is chosen by propagation, not difficulty)* → **amended**, policy §2.1: for `execute`, tier and effort follow **contract completeness** |
| 29 | Refusal is a first-class outcome. |
| 30 | Leaf checks must be objective and hidden from the producer. → refined by rule 91 |
| 31 | Checks are welded to operations, never opt-in. |
| 32 | Bounces are counted; repeated refusal means the splitting is wrong. |
| 33 | Capability is restricted at the schema, not at runtime. |
| 34 | *(temperature is per-role config and a sampling control)* → **amended**, core §8.1.2: role-level only, largely unsettable under extended thinking, and **not** the determinism mechanism |

### Drift is caught structurally

| # | Rule |
|---|---|
| 35 | Verify compares outputs to the root intent, cold, withholding the derivation. → **contested**, policy §4.2: the axis is summary-versus-artifact, not cold-versus-informed |
| 36 | Verify asks what is missing, not whether it is good. |
| 37 | Gaps become ordinary cards. → amended by rule 64 |
| 38 | Gate frequency is config, not architecture. → **amended**, policy §3.1: ships `[leaf, root]`; the depth ladder is not built |

### Failure is expected

| # | Rule |
|---|---|
| 39 | Leases expire; that is the whole crash-recovery story. |
| 40 | Two clocks: a per-attempt lease and a total deadline. Heartbeats extend the first, never the second. |
| 41 | Every lease-guarded write carries a fencing token — `attempts`, as of claim time. |
| 42 | Workers are ephemeral in state; the restart counter lives on the card. |
| 43 | `SIGTERM` drains: stop claiming, finish or release, exit. |
| 44 | Quarantine, don't delete — with an owner, an alert and a triage path. Never automatic requeue. |
| 45 | Everything is idempotent; content-hashed ids make duplicate appends harmless. |
| 46 | A card whose side effects cannot be undone by destroying its workspace must not exist. → qualified by `retry_safe`, core §6 |

### Enforcement

| # | Rule |
|---|---|
| 47 | A model's tool call is a request, not an authorization. |
| 48–54 | *(five ordered checks, per-tool quota, side-effect class, in-card approval, fail-open policy)* → **void**, ADR-0003. Replaced by: container, network deny, read-only mounts, host-side commit hooks, `tool_audit`. Rule 51's substance survives — audit records refusals, which are the more informative half. |

### Determinism and memory

| # | Rule |
|---|---|
| 55 | Record responses keyed on the rendered prompt, model, effort, params and recalled note ids. |
| 56 | Config version is pinned at run start. Jig edits never apply to a run in flight. → enforced by rule 129 |
| 57 | Advisory memory may shape a prompt; it may never determine what runs. |
| 58 | Human-facing artifacts enter no card's context, no replay key, and no readiness decision — and what a reviewer was looking at is recorded. |

### Discipline

| # | Rule |
|---|---|
| 59 | If a step is deterministic and faster than a claim round trip, it is a hook, not a card. |
| 60 | A mechanism whose only justified user is deferred is itself deferred. → hardened by ADR-0003: deferred is not a state a design can hold |
| 61 | Every gate in the build order has a paper version. Run the paper version first. |
| 62 | Every documented failure mode names its symptom, why it hides, and its detector — or states that none exists. |
| 63 | No new design documents. Corrections are patched into an existing one, an ADR, or this file. **An addition must specify something being built now, or carry an explicit trigger.** |

### From the superpowers review

| # | Rule |
|---|---|
| 64 | Verify gaps sharing a `touch_set` and kind are emitted as one card, not one per finding. |
| 65 | A card never emits its own reviewer. Gates are pinned by the splitter. |
| 66 | Patterned work — the same small edit across many sites — is one child enumerating every site. |
| 67 | `decided` entries carry what, why, and what it costs if wrong. An entry with no `cost_if_wrong` is not a decision, it is a description. |
| 68 | The last delivery escalates one tier, by position, unless the flip before it was free (ADR-0013). At the tier ceiling, which is the highest tier a role claims for that kind (ADR-0008), escalation becomes a fresh-eyes framing in layer 7. |
| 69 | A verifier never widens its own scope. What it cannot verify it reports as `unverifiable`. |
| 70 | Retrieval cites the risk that justified it, and the citation lands in the summary. |
| 71 | A card's kind ratchets toward `split` and never away. A single-`execute`-child split is rejected. |
| 72 | Role config has no default tier. A missing tier is a validation error. |
| 73 | Every child declares `interfaces.consumes` and `produces`. An unresolved consumed symbol rejects the split. |
| 74 | A contract never refers to a sibling. The executor cannot read it. |
| 75 | A jig is written against observed failures, captured before the jig existed. |
| 76 | The digest's Rulings list is a query over `decided`, not a summarisation. |
| 77 | A deferred-findings list that no gate takes as input is deleted, not kept. |

### Odoo conventions

| # | Rule |
|---|---|
| 78 | `__manifest__.py` and every `__init__.py` are generated. A card needing a dependency emits `spec_conflict`. |
| 79 | One concern, one file, one owner. |
| 80 | Load order is expressed by numeric filename prefix, never by editing a shared list. |
| 81 | Every child declares `owns.xml_id_prefix`, `models` and `fields`; checked at commit, on the host. |
| 82 | A behavioural card never owns its own test file. |
| 83 | A test card's check is that the test runs and **fails**. Its implementation card depends on it. |
| 84 | The workspace is a worktree, a container and a database clone, provisioned and destroyed together. |
| 85 | Git happens on the host; execution in the container. *(Commit hooks are unreachable from inside the card)* → **amended**, ADR-0014: the card can write the worktree's `.git`, so that holds only through rule 150's runner. |
| 86 | *(then resets the worktree)* → **amended**, ADR-0011: the reaper kills the container before requeuing, then removes the attempt's worktree and drops the clone. Only a failed kill blocks requeue. |
| 87 | No worker connects to the template database. |
| 88 | `integrate`'s check is rung 1 on the merged tree, not a clean merge. |
| 89 | A structural card's contract cites the schema path and key. It never restates the schema. |
| 90 | Image digest, source commit, addon commits and template-DB hash join the config pin. |
| 91 | Checks a card can fix are visible to it; checks that establish trust are hidden from it. |

### The record

| # | Rule |
|---|---|
| 92 | Every run carries `project`, `intent_digest`, `spec_digest` and the config pin. Every task carries `project` and `summary_schema_version`. |
| 93 | A summary schema change bumps the version and never rewrites history. |
| 94 | `tasks`, `task_attempts`, `runs`, `reviews`, `notes`, `tool_audit` are never deleted. Content is tiered and expired; rows are not. |
| 95 | Nothing is promoted to a note automatically. Promotion is a human verb at the gate. |
| 96 | A note is superseded, never edited. |
| 97 | Check logs are truncated on write. Success keeps the tail; failure keeps the first traceback and the tail. |
| 98 | The filesystem content backend is for development and tests only. |
| 105 | Every card carries a one-line `title` written for a human reading the tree months later. |
| 106 | The project tree is a query rendered, never a service. |

### The anchor

| # | Rule |
|---|---|
| 99 | The schema is drafted twice, independently, and the diff is resolved by a human. |
| 100 | A drafter marks decided fields `TODO_DECIDE` rather than guessing. |
| 101 | A `semantic:` block is copied from the design document, never compressed. |
| 102 | `schema_lint` passes before any card is emitted. |
| 103 | The schema installs as a generated stub before any card is dispatched against it. |
| 104 | If a generator can emit an artifact deterministically from the schema, it is a hook and not a card. |

### Models and calls

| # | Rule |
|---|---|
| 107 | Role config carries reasoning effort explicitly. A missing effort is a validation error. |
| 108 | Effort is part of the model-cache key and the config pin. |
| 109 | Temperature is role-level, never per-card, and is not the determinism mechanism. |
| 110 | Where the design asks for independent samples, the config states what is varying and why. |
| 111 | Full reasoning traces are kept only for non-`ok` outcomes. |
| 112 | Escalation raises effort before it raises tier. |
| 113 | A jig has one output schema and one check. |
| 114 | A jig is stateless across attempts. |
| 115 | Stages with different checks are two cards. A jig that grew a second stage is a candidate split. |

### Jigs, layers, skills

| # | Rule |
|---|---|
| 116 | A new jig is justified when the output schema differs, not when the content differs. |
| 117 | Domain knowledge never lives in a jig. Check-ladder rungs hold domain commands, but they live in `checks.yaml`, not the jig (rule 137). |
| 118 | Rationalization rows live in layer 2 with their skill, except rows that survive a domain change. |
| 119 | Skill sets are selected per kind, by hand, at config-pin time. Nothing computes them. |
| 120 | Every skill file ships paired with the RED case that motivated it. |
| 121 | A skill whose RED case no longer reproduces on ablation is deleted, not kept as margin. |
| 122 | Every kind's skill set is kept minimal. Cache amortises price, not attention. |
| 123 | Layer 2 is pinned and flattened at config time. Version dispatchers are resolved by a human. |
| 124 | Imported skill material is stripped of anything that spawns an agent. |
| 125 | Imported material is stripped of network dependence, version detection from generated files, and decomposition decisions. Version deltas may be imported; pattern documentation is RED-derived or not adopted. |

### Config identity

| # | Rule |
|---|---|
| 126 | *(`config_hash` is per-kind)* → **amended**, ADR-0008: `config_hash` is per kind and tier. `runs.config_pin` holds the full snapshot; the hash holds this card's slice. |
| 127 | The hash covers the **rendered** layers, not the files. |
| 128 | A version bump with an identical hash is fine. A hash change with no version bump fails the build. |
| 129 | A worker recomputes its `kind_hash` at claim time and refuses the card on mismatch. |
| 130 | Cross-run comparison keys on `(config_hash, intent_digest)`. |

### Standing

| # | Rule |
|---|---|
| 131 | *(ex-v2 66)* Any rate used as a quality indicator is reported alongside its false-positive rate. |
| 132 | *(ex-v2 67, the diagnostic)* **Remove any worker type: the system must degrade, never hang.** |
| 133 | Changes land in an existing document, an ADR, or this file. A document created to hold pending changes is the failure this file exists to prevent. |
| 134 | Where an external tool selects a model or effort on this project's behalf, the **resolved** flags are what enters the record — never the abstract label. A label whose meaning varies by vendor cannot support a comparability claim. |
| 135 | *(a role's tool set)* → **amended**, ADR-0008: a kind's tool set is enumerated in its jig and is the narrowest that lets the kind produce its contract. **Absence of a tool is a gate**, not an omission — a card without a write tool cannot write. |
| 136 | Each kind has exactly one jig. Each kind and tier is claimed by exactly one role, and every kind in a role shares that role's jig. Startup validation enforces this; a card whose kind and tier no role claims is rejected at emit time. |
| 137 | Check definitions live only in `checks.yaml`. A jig names no command, a card's `check_spec` picks the rungs, and layer 8 renders only rungs marked visible. |
| 138 | For `execute`, tier and effort follow contract shape alone. Whether a card needs a test is a separate question, answered by `check_spec`. Behavioural is not a kind, a jig or a contract shape. |
| 139 | The harness adds a file to layer 6 only from a hand-written table keyed by kind, on a trigger that is a declared field of the card: never the intent text, the contract's wording or a model call. The table and files enter `config_hash`, each row names a risk, and each file obeys P5 and P6. Built when a RED case asks for it. |
| 140 | A dep names a card on the board or one emitted with it, and emitted cards form no cycle. Both are checked at emit, because the readiness predicate reads a missing dep as satisfied and cannot see a cycle. |
| 141 | Each reaper pass lists the host's `card_*` containers, databases and worktrees, then reads open `task_attempts` rows, and removes anything no open row names. In that order, so a live attempt is never swept. Worktrees go by path, then `git worktree prune`, because `git worktree remove` refuses a tampered one (ADR-0014). The committed attempt's branch stays. |
| 142 | Provisioning failures and drain releases are free, up to `runs.max_free_retries`. A failure no retry can fix halts the run rather than spending attempts, and only an unambiguous provider signal counts. A card never sees a free failure, and escalation counts charged attempts only. |
| 143 | One host for now. Kill and workspace teardown are host-local and the reaper runs from any worker. Several hosts need the host in `lease_holder` and teardown refused elsewhere. |
| 144 | Anything a command produced is normalized before it can enter model-visible text: tool results, `post_tool_call` rung output and layer 7's check output. A normalizer removes only what differs between two correct runs, enters `kind_hash`, and what it removes stays in `tool_audit`. Promotes R-new-5, ADR-0012. |
| 145 | A card reaches `done` only with a check that passed, or `not_applicable` for `expanded` or a kind with an empty ladder. A failed check is `failed`; one that could not start is free, then `awaiting_review`. The database enforces it with `done_means_checked`. ADR-0013. |
| 146 | Core's six states stand. Refusals go to `awaiting_review`. A misclassified card becomes a `split` on its own row, and a misclassified `split` goes to `awaiting_review`. ADR-0013. |
| 147 | Layer 7 and the effort rung read evidence attempts only: those whose failure says something about the work. A dead worker, a stall, a free failure and a parked outcome leave the next prompt byte-identical. Hidden rungs' output is never rendered. ADR-0013. |
| 148 | The reaper revokes the lease before teardown, rechecking expiry, so a late commit's fence fails and a live worker keeps its card. ADR-0013. |
| 149 | A failed `retry_safe: false` card goes to `awaiting_review`, on any failure but `provision_failed`, with its worktree and database kept until a verb acts. ADR-0013. |
| 150 | Host git treats the worktree as untrusted input. Every host git call goes through one runner: the git directory from the harness's own record and never from the worktree's `.git`, the work tree pinned, hooks and fsmonitor off, host config scrubbed. A staged gitlink is a touch-set violation. ADR-0014. |
| 151 | A `task_attempts` row records the card's `kind`, `tier` and `config_hash` at claim, and they are never updated. A query about what ran reads the attempt. ADR-0014. |
| 152 | Every provider failure is recorded in `model_failures`. Replay re-raises it, a recorded response wins over it, and a live run never reads it. ADR-0014. |

---

## 4. Risks

### Live from v2

| # | Risk | Mitigation / detector |
|---|---|---|
| R1 | **Splitter quality is the whole system.** | E1; human gate at depth ≤1; refusal rate as leading indicator. **Unresolved in general.** Removed entirely from run one if the harness ingests a human-reviewed plan. |
| R2 | Thin coverage makes leaf checks vacuous | Mutation probe. For greenfield: structure-checked only at first. |
| R3 | Machinery may be temporary | Gate frequency as config |
| R4 | Narrow-deep trees stall under the human gate | Bias toward width; ships flat (policy §3.1), which largely removes it |
| R5 | Repo work is the one stateful thing | The workspace triple; prefer diffs |
| R6 | Cross-cutting insight is genuinely lost | Partially recovered at split and verify time. Accepted. |
| R7 | *(LISTEN/NOTIFY is fire-and-forget)* | **Void** — ADR-0003, poll only |
| R8 | No sandbox for generated code | Container; ADR-0003 |
| R9 | Advisory memory becomes load-bearing by accident | Ships as NullMemory; rule 57 |
| R10 | **The whole design may be overkill** | **E3 baseline.** Without it, permanently unresolvable. |
| R11 | Graph growth on very long runs | Archive terminal subtrees; keep summaries. Known cliff. Note rule 94 — rows are never deleted, so archival means partitioning, not pruning. |
| R12 | Reimplementing a workflow engine by accretion | Answered once, in policy §10 |
| R13 | Speculative branching is not expressible | Recorded, not planned. Its only user left with ADR-0002. |
| R14 | Persona pressure causes role inflation | Core §3.4; cost per card by kind |
| R15 | **Prefix-scan cost on the predicate.** Two correlated `NOT EXISTS`, one with `LIKE` plus a join, on the hottest path. | `EXPLAIN ANALYZE` baseline at Phase 1, not deferred to "measure at scale". If it bites, denormalise `open_descendants` — only with a test proving it cannot drift. |
| R16 | Chronicle-derived lessons reinforce drift | Deferred until *comparable run* is definable. `intent_digest` (rule 92) is what makes it definable. |
| R17 | Tier proliferation | Two columns plus effort. A fourth axis is a routing table. |
| R18 | Human-facing artifacts drift into the execution path | Rule 58; CI grep |
| R19 | Stale writer defeats the lease guard | Fencing (rule 41) plus kill-before-requeue (rule 86) |
| R20 | Deploys burn model spend via lease-expiry recovery | Graceful drain; drain duration measured |
| R21 | Instructions arrive via tool or skill descriptions | Golden-file prompt tests; tool-audit anomalies. Sharpened by rules 124–125. |
| R22 | Enforcement unavailable, behaviour undefined | Container absent = no claim |
| R23 | Quarantine accumulates unread | Surfaced in the digest and the tree |
| R24 | **Design elaboration outruns evidence** | Rule 63; E1–E3 before Phase 1; the step-7 checkpoint |
| R25 | **Verify catches omission, not commission** | ADR-0001; E2 including arm D |
| R26 | Tier starvation | Pool-starvation metric |
| R27 | The throwaway ledger survives | Delete it the day Phase 1 lands. Present at Phase 3 = stop condition. |

### From the reviews and the worked run

| # | Risk | Mitigation / detector |
|---|---|---|
| R28 | Cheap-tier leaves are not cheap — 2–3× the turns on prose contracts | Tier and effort on contract completeness. Measure turn count by tier from run one. |
| R29 | **Summary-reading verify may be structurally unable to see commission.** An information problem, not a warmth one. | Verify input is config. E2 arm D. The fallback is flipping one value. |
| R30 | Sibling interface incoherence — paths disjoint, symbols incompatible | `interfaces` plus emit-time resolution |
| R31 | The verify loop has no cap | `re_verify` with a round count and breaker |
| R32 | Depth is unjustified by measurement | Ship flat. Let depth arrive via refusal. |
| R33 | Jigs are tested for shape, not for effect | RED-first; a rationalization table per discipline-bearing jig |
| R34 | Framework gravity defeats touch-set disjointness | Odoo conventions, validated on a throwaway module **before Phase 1** |
| R35 | **The structurally perfect wrong rule.** | Test-first pairing (rules 82–83). **Confirmed**: five mechanisms passed it in the worked run; only the separately-written test caught it. |
| R36 | Check latency dominates the cost model — turns × rung latency | Check ladder; template clones; measure `rung1_invocations` |
| R37 | Postgres is the contention point, not the models | One Postgres per run, template clone per attempt |
| R38 | The generated-file convention will be reverted by a future human | README, layer 1, hook fails loud on a generated path |
| R39 | The schema becomes a second source of truth | Rule 89 |
| R40 | Migration cards break retry safety once real data exists | `retry_safe: false`; a data snapshot as `db_source` |
| R41 | The lessons store fills with noise | Manual promotion only; the query catalogue as acceptance test |
| R42 | Cross-run comparison is silently wrong across a schema change | `summary_schema_version`; queries branch explicitly |
| R43 | **"For learning" licenses unbounded elaboration** | Anti-milestones and rule 63, re-read at each phase boundary |
| R44 | **The anchor is wrong and nothing can tell.** The only artifact with no detector beneath it. | Two independent drafts and a diff; `TODO_DECIDE`; coverage check; stub install. **None is a proof.** |
| R45 | The structural half does not need a model | Write the generator, measure coverage. The response is a smaller harness, not a defence. |
| R46 | The schema becomes a view definition language | The schema declares what rung 3 can check and nothing else |
| R47 | **Reasoning suppresses refusal.** Every visible metric improves as the signals degrade. | E2 arm C′ at two effort levels |
| R48 | **Correlated samples masquerading as independent** | Rule 110. Vary the model or effort, never the seed. Sharpens R44, whose only mitigation this is. |
| R49 | **A jig becomes a controller.** Staged decisions never become rows. | Rules 113–115; the acceptance test in policy §1.5 |
| R50 | **A pinned skill set narrows attention.** Cache amortises price, not presence. | Per-set ablation against cards the set was not written for |
| R51 | Inherited elaboration — a large, well-made, non-RED-derived corpus is available to paste | Rules 120–121, 125. Import version deltas; derive the rest. |
| R52 | **Silent config drift mid-run** — the run quietly stops being one experiment | Claim-time `kind_hash` recomputation (rule 129); hash-stability tests |
| R53 | Comparability hash too coarse | Per-kind-and-tier `kind_hash` over rendered layers |

### Relocated from v2's register

| # | Risk | Mitigation / detector |
|---|---|---|
| R54 | *(ex-R28)* **`decided` is self-report from the party with the blind spot.** The cards most likely to have drifted are least likely to populate it. | ADR-0001's pair and set difference. **Observed in the worked run: on the specimen that mattered, `decided` was empty and accurately so.** Where both parties miss the ambiguity, no detector exists. |
| R55 | *(ex-R29)* **The verifier over-produces.** A high gap rate reads as thoroughness or as bad decomposition — both sound like working. | Clean-set control arm of E2; calibrate before trusting gap rate. Rule 131. |
| R56 | *(ex-R30)* **Elaboration re-enters through consolidation.** Rule 63 blocks new documents, not growth inside one. | Rule 63's second clause; rule 133; the anti-milestones. **This file is a live instance of the risk** — see §8. |

### Added 2026-08-18 — from review of external comparables

| # | Risk | Mitigation / detector |
|---|---|---|
| R57 | **A worker heartbeats while making no progress.** The lease never expires, so lease expiry never fires. Liveness is signalled; progress is not. | **Partial, ADR-0007.** A silent loop is caught by the reaper's stall clause, whose own detector is `stalled` attempts that succeed on retry. **A busy loop is still a residual per rule 62:** a loop that keeps making calls is never silent, and only the turn limit and the deadline bound it. Core §5.4 states why one reaper is otherwise sufficient; this is the case it does not cover, and the case the comparable's watchdog chain exists for. |
| R58 | **Parallelism is not a differentiator.** Policy §10 asserted it against a sequential controller; the current comparable runs work in parallel with an equivalent claim protocol. | §10 corrected 2026-08-18. One differentiator remains and it is the primary hypothesis, so step 7 has no fallback claim. |
| R59 | **Effort labels do not mean the same thing across vendors.** An abstract `high` renders to a different flag, and a different scale, per harness. | Rule 134: record the *resolved* flags in the pin, never the choice name. R48's independence requirement depends on this. |
| R60 | **The card runtime assembles the prompt, so its version is part of what a card saw.** A library upgrade changes the system it ran under with nothing in the design moving. | Runtime pinned in the lockfile and inside `config_hash`; an upgrade is a run boundary. ADR-0004, policy §1.6. |
| R61 | **Context exhaustion inside a card produces a confident summary.** The lease bounds time and the deadline bounds the attempt; neither bounds the window. A card that runs out of context and then reports success is indistinguishable from one that succeeded. | **None.** Recorded per rule 62 as a residual. This is ADR-0001's commission case arriving by a route the pair cannot see, and diff-reading verify (E2 arm D) is the only proposed mechanism that would catch it. |
| R62 | **A normalizer removes something the card needed.** A card chasing a slow query sees no timing, and nothing tells it that it is missing. | The over-stripping test in core §11; `raw_ref` for diagnosis. Timing a contract needs should be a check's result rather than a log line. ADR-0012. |
| R63 | **A broken oracle looks like bad luck.** Every card spends its free retries on `check_unavailable` and then waits for a person, with nothing halting the run. Safe, because nothing reaches `done`, but slow and costly to notice. | The query in `queries/lessons.sql`. ADR-0011's circuit breaker if it recurs. ADR-0013. |
| R64 | **A host gate reads a file the card wrote.** `namespace_check` parses the diff on the host, and manifest regeneration runs there. Pinning git says nothing about a planted symlink or a hostile parser input. | **None yet.** Needs its own look before P1-9 ends. ADR-0014. |

---

## 5. Artifacts to build

| Artifact | Purpose | Effort |
|---|---|---|
| `001_initial.sql` | the Phase 1 schema, consolidated. The original was lost; this is a reconstruction, see its header | **reconstructed** |
| `make check-static` (rung 0) | the cheapest useful check in the system | half a day |
| `tools/introspect.py` | rung 3 oracle. **Needs its own mutation tests.** | 1–2 days |
| `schema_lint` | moves human gates off the critical path | half a day |
| `tools/generate.py` | stub generator; then **measure how far it goes** (R45) | 2–3 days |
| container image + template-DB script | the workspace triple | 1 day |
| `hooks/regenerate_manifest.py` | generated manifest and `__init__.py` | hours |
| commit-time namespace check | AST + XML parse over the diff, host-side | hours |
| `queries/lessons.sql` | the query catalogue, as an acceptance test for schema fields | drafted |
| `queries/tree.sql` + static renderer | the project tree; a script, not a service. Query drafted, renderer not | hours |
| `skills.yaml` | per-kind skill sets, part of `config_hash` | minutes |
| flattened version deltas | two files from the pinned bracket, dispatchers removed | hours |
| the Odoo skill (layer 2) | RED corpus collected, then written against it | ongoing |
| jig templates | adapted from the four reviewed prompt files, attributed | days |

---

## 6. Sequenced actions

**Before Phase 1 — validate what the design rests on.** None needs the harness to exist.

1. Odoo file conventions on a throwaway module: per-model ACLs, generated manifest, install/update/uninstall clean. *One afternoon. Unblocks R34.*
2. Schema for a small slice + `introspect.py`; confirm it catches a wrong field type, a missing ACL row, an unstored compute in a domain. *1–2 days. Validates the whole Odoo argument.*
3. **Two independent schema drafts of one design document; diff them.** *One hour. Tests whether R44's only mitigation works at all — and R48 says it works only if the drafts vary by model or effort rather than seed.*
4. `schema_lint`. *Half a day.*
5. `tools/generate.py`, then measure its coverage of the structural half. *2–3 days. Decides R45 and reshapes E1.*

**Phase 1.**

6. `001_initial.sql`, then core §12's build order, then **Gate A**.
7. `EXPLAIN ANALYZE` on the claim query at realistic graph size (R15). Not deferred.

**Paper experiments, in this order.**

8. E3 with the shipped baseline — and run the emit-time gates against its plan as a false-rejection
   test. **Baseline candidate: Gas Town** — controller-based, parallel, atomic claim from a shared
   SQL store; the closest comparable found. Three prepared comparisons, from the account cited in
   policy §10: does its parallel path beat the worked run's wall clock; does its missing validation
   layer produce the omission/commission gap ADR-0001 predicts; does its unenforced handoff produce
   orphaned work items where kill-before-requeue would not.
9. E2 with the inverted-record-rule specimen, including arms D and C′.
10. E1 with the RED pass and the plan-written control.

**11. The checkpoint** — policy §10's two questions, with both thresholds written before the numbers
exist.

> **On the name.** This is what every other document calls **step 7**, from an earlier draft where it
> was the seventh action. The list has since grown to eleven and the name did not move. It is kept as
> a *name*, not an index — "step 7" and "item 7" are different things, and item 7 is the
> `EXPLAIN ANALYZE` action above. Do not renumber the references; they are load-bearing in
> `odoo-adaptation`'s legend and in README.

**Throughout:** build the pharmacy module with the baseline tool. It ships regardless, and every task is a data point no paper experiment produces.

---

## 7. Open questions

1. Does `split` need domain skills at all, or does the generator absorb the structural half and leave splitting domain-neutral?
2. **Does a pinned skill set narrow attention, and at what size?** One experiment: per-set ablation against cards the set was not written for. The load-bearing uncertainty in layer-2 sizing.
3. Is one shared `execute` jig sufficient across structural and behavioural cards?
4. Do the version-delta files change output on this pin? If not, nothing is imported at all.
5. Can structural verify run at cheap tier once introspection has spoken? The worked run suggests it is a query plus a formatter.
6. How much of the module is structural? A large fraction now argues for a **generator**, not for the harness.
7. What fraction can the generator emit correctly? Above ~70% the structural cards are polish; above 90% they are ceremony.
8. **Do two independent schema drafts diverge usefully, or make the same mistake?** If they converge on a wrong answer, R44 has no mitigation.
9. Does per-model ACL splitting break module update, uninstall, or OCA tooling?
10. Snapshot maintenance cost for migration cards.
11. Multi-company. Out of scope; arriving later is a re-split, not an amendment.
12. **`spec_revision` has no role, so no tier or `config_hash`,** yet both are `NOT NULL` and it is written with `state='awaiting_review'`. Does a human-written card get a nominal tier, or do the columns relax?
13. **What are the pin's keys?** Core §9.4 reads `config_pin->>'model_strong'`, the sketch reads `pin.kind_hash[(kind, tier)]`, and the catalog run's pin has neither shape.
14. **What shape are `open_questions` and `decided` entries?** Core's `closed_by` needs objects, the Odoo run stores strings, and the catalog run's set difference needs `q["id"]` and `d["addresses"]`.
15. **Where does `unverifiable` go?** Policy and the Odoo adaptation route it to notes, but core §4.5 allows only human promotion.

---

## 8. Standing cautions

**The mechanism audit is the honest scoreboard.** In the worked run, what fired hardest was cheap
and mechanical: the static rung, the commit-time touch-set hook, rung 1 on the merged tree, and a
test written by a card that could not edit it. Three of those four are hooks. The most elaborate
mechanism in the design was outperformed on both halves of the work. One imagined run proves
nothing — but it is the shape E2 exists to confirm or refute.

**Every mechanism costs whether or not it fires.** `judge` and intermediate-depth verify never fired
at all, and both are now deleted. Prefer the cheapest mechanism that can do the job.

**Two of the last six risks share a shape**: R47 and R50 both describe mechanisms where every visible
metric improves while the thing being measured degrades. That suggests the metric set is better at
catching cost than at catching quiet degradation, and it is worth asking of any new mechanism which
of the two it would be.

**This file is a live instance of R56.** It is 133 rules and 56 risks for a system that has not run.
Growth here is not free just because it arrives as a table row. At each phase boundary the useful
question is not *what should be added* but **which rules have never been consulted and which risks
have never been observed** — and rules 121 and 132 are the model for what to do about them.

---

## 9. Changelog

Append-only. One line per change. Date, ADR where one exists, what moved.

```
2026-11-04  ADR-0014  host git ignores the worktree's .git; attempts record what the card was; replay reproduces provider failures; rules 85, 141 amended; rules 150–152; R64
2026-11-04  ADR-0013  what reaches done and what a retry learns: oracle decides, six states stand, misclassified rewrites in place, evidence attempts, revoke before teardown; rule 68 amended; rules 145–149; R63
2026-11-04  ADR-0012  command output normalized before the model sees it; replay re-executes tools; core §8's retry claim narrowed; rule 144; R62; R-new-5 promoted
2026-11-04  —         001_initial.sql reconstructed from the documents, the original having been lost; harness/ledger/sql and queries drafted
2026-11-04  —         core §9.3 corrected: the tree query sorted t-x.10 before t-x.2; now COLLATE tree_order
2026-11-03  ADR-0011  free provisioning and drain, a ceiling on free retries, halting failures, per-attempt worktrees; rules 68, 86 amended; rule 142
2026-11-03  —         core §5.1 corrected: missing deps and cycles rejected at emit; rule 140
2026-11-03  —         core §5.4 corrected: reaper sweeps orphans by name; rule 141
2026-11-03  —         core §5.3 corrected: one host for now, multi-node claim withdrawn; rule 143
2026-11-03  ADR-0010  retrieval triggers are declared card fields, from a hashed table; rule 139; built when a RED case asks
2026-11-03  ADR-0008  kind, role and jig have one job each; tools on the jig; hash per kind and tier; checks in checks.yaml; rules 68, 117, 126, 135 amended; rules 136–138
2026-11-03  ADR-0007  task_attempts; reaper stall clause, backoff, collects failed; workspace failure table; Budget as a claim query; rule 94; R57 now partial
2026-08-18  ADR-0004  card runtime adopted below the card boundary; core §8 cache is its model interface
2026-08-18  —         policy §1.6 added — the loop §1.5 acknowledged but nobody specified
2026-08-18  —         rule 135; R60, R61 — tool sets as gates, runtime in the pin, context exhaustion
2026-08-18  —         policy §10 corrected: parallelism is not a differentiator; R58
2026-08-18  —         core §5.4: why one reaper and no watchdog chain; R57 recorded with no detector
2026-08-18  ADR-0003  amended: external evidence for structural enforcement over instructed handoff
2026-08-18  —         rule 134; R59 — resolved flags, not effort labels, enter the pin
2026-08-18  —         §6 renumbered to eleven items; "step 7" retained as a name, not an index
2026-08-17  —         rules-and-risks split from change-register; migration half frozen
2026-08-17  —         collisions resolved: rules 64–67, 91–96; risks R28–R30 → R54–R56
2026-08-17  —         rules 131–133 added (ex-v2 66/67 preserved; forward process)
2026-08-17  —         001_initial.sql: model_calls fork closed in favour of the table
2026-08-17  ADR-0003  enforcement collapsed to isolation; notification absent; rules 10,13,48–54 void
2026-08-17  ADR-0002  judge not adopted; best-of-N and per-card temperature go with it
2026-08-17  ADR-0001  frame widened: diff-reading alternative; closed_by; arm D as mind-changer
2026-08-17  —         config_hash specified (core §8.1.1); claim-time drift check; rules 126–130
2026-08-17  —         reasoning effort as a third axis; rules 107–112; risks R47–R48
2026-08-17  —         multi-prompt jigs bounded; rules 113–115; risk R49
2026-08-17  —         layer 2 attention correction; rules 116–125; risks R50–R51
2026-08-17  —         title column and the project tree; rules 105–106
2026-08-17  —         harness-design-v2 split into core-v3 and policy-v3
```
