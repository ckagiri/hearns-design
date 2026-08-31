# Thin Orchestration, Fat Discipline

**A curated skill system for coding agents, assembled from four existing packs**

---

## Contents

1. [What this is](#1-what-this-is)
2. [The landscape](#2-the-landscape)
3. [Why there is no entry-point classifier](#3-why-there-is-no-entry-point-classifier)
4. [Principles](#4-principles)
5. [Architecture](#5-architecture)
6. [The tripwire](#6-the-tripwire)
7. [Enforcement mechanics](#7-enforcement-mechanics)
8. [Skill specifications](#8-skill-specifications)
9. [The knowledge layer](#9-the-knowledge-layer)
10. [The reference layer](#10-the-reference-layer)
11. [The escape hatch](#11-the-escape-hatch)
12. [Evals](#12-evals)
13. [Failure modes](#13-failure-modes)
14. [Non-goals](#14-non-goals)
15. [Open questions](#15-open-questions)
16. [Build order](#16-build-order)

---

## 1. What this is

A skill library for coding agents, assembled from four existing packs plus two small
additions.

Four teams have built serious skill collections for coding agents. Each solved a different
piece of the problem well, and each carries decisions worth declining. Nobody has assembled
the good parts. That assembly is most of what this document is.

An obvious thing to add on top is a router that classifies each request and dispatches a
proportional amount of process. §3 explains why that is not here, at length, because the
reasoning generalises to anything else that adds a mechanism.

**What is contributed on top:**

1. **A blast-radius tripwire** (§6). A deterministic path check, run against the diff, that
   escalates on observed facts. Not a classifier. Genuinely absent from all four packs,
   though Osmani's `doubt-driven-development` covers the same ground in prose.
2. **Act-then-escalate as the default posture** (§5.2), rather than classify-then-act.
3. **An ordering claim**: build the knowledge layer before autonomy, not after (§16).
4. **A baseline-comparison requirement in evals** (§12.6): any mechanism added here must
   beat the model's unaided default, measured, or it comes out.

**What is borrowed**, and this is most of the document: the discovery/bindingness split and
pressure testing from Superpowers; the invocation split and no-chaining rule from Pocock;
the three-tier knowledge model from compound-engineering; the eval harness, reference layer,
anti-rationalization tables and adversarial review from Osmani. §2.3 tabulates it.

The value proposition is curation, not invention. That is a smaller claim than a novel
architecture, and it is the accurate one.

**Status.** Design, not implementation. One part is substantially unproven: the recall half
of the knowledge layer (§9.4). The tripwire is mechanical and cheap to verify, and §12.6
specifies the test that could delete it. Everything else is assembly of things that work
somewhere.

---

## 2. The landscape

### 2.1 The four packs

**[obra/superpowers](https://github.com/obra/superpowers)** — ~14 skills in one enforced
pipeline: brainstorm → worktree → plan → subagent execution → TDD → review → finish. A
session-start hook fires skills automatically; the README frames them as mandatory
workflows rather than suggestions. ~12 harnesses. Company-backed; new-skill contributions
generally not accepted.

*Best idea:* pressure testing. `test-pressure-*.md` fixtures verify a discipline survives
an agent being tempted to skip it. Nobody else does this.
*Worst tendency:* ceremony you cannot decline. Note this is caused by the hook mandate, not
by an absence of routing, and that distinction matters — see §3.

**[mattpocock/skills](https://github.com/mattpocock/skills)** — ~36 small composable skills,
explicitly positioned against process-owning frameworks. Split by invocation: user-invoked
skills orchestrate, model-invoked skills hold discipline. Built to be forked and edited.

*Best idea:* the invocation split. It makes the control boundary explicit, and it is also a
routing mechanism — the human is the router (§3.2).
*Worst tendency:* skills that never fire because nothing reminds the agent they exist.

**[EveryInc/compound-engineering-plugin](https://github.com/EveryInc/compound-engineering-plugin)**
— 33 skills, 14 hosts. Six-step loop ending in `compound`: solved problems written to
`docs/solutions/` with structured frontmatter, read back by later brainstorms and plans.
Thin skills over deep `references/` — 392 files, 31 reference directories. No hooks. `/lfg`
runs the loop unattended through PR and CI watching.

*Best idea:* knowledge as a first-class artifact with a schema, a retrieval story, and a
maintenance skill. The only pack where knowledge accumulates rather than evaporating with
the branch.
*Worst tendency:* per-skill surface area. `/ce-compound` carries mode detection, depth
selectors, deprecated aliases, non-interactive contracts and a frontmatter validator, for
"write down what you learned."

**[addyosmani/agent-skills](https://github.com/addyosmani/agent-skills)** — 24 skills, 8
lifecycle commands, 4 personas, 7 shared reference checklists, hooks, 70+ agents via
`npx skills`. The only pack whose center of gravity is engineering domain breadth rather
than workflow control: OWASP, RED metrics, Core Web Vitals, WCAG 2.1 AA, Hyrum's Law,
deprecation and zombie-code removal. Google-flavored norms throughout.

*Best ideas:* a shipped three-tier eval harness with deterministic description-collision
detection; anti-rationalization tables; `doubt-driven-development`; the shared checklist
layer.
*Worst tendency:* globally non-negotiable "core operating behaviors."

### 2.2 Comparison

| | superpowers | mattpocock | compound-eng | addyosmani | **this** |
|---|---|---|---|---|---|
| Thesis | Enforced method | Composable tools | Knowledge accretion | Lifecycle breadth | Curated + observed escalation |
| Skills | ~14 | ~36 | 33 | 24 | 18 |
| Trigger | Auto (hook) | User + model | User only | Auto + commands | Hook indexes; user + model invoke |
| Bindingness | High, uniform | Low | Low–medium | Medium, global | Scarce, explicit |
| Autonomy | subagent-driven | `/implement` | `/lfg` | `/build auto` | `/build` mode flag |
| Domain content | Low | Low | Low | **High** | Borrowed (§10) |
| Durable knowledge | Branch-local plans | Glossary | **3 tiers** | None | 3 tiers |
| Eval harness | Pressure fixtures | — | CI validation | **3 tiers, shipped** | 3 tiers, adopted |
| Blast-radius check | — | — | — | Prose judgment | **Deterministic** |
| Verification gate | Binding | — | Implicit | Distributed | Binding |
| Hosts | ~12 | 2 paths | 14 | 70+ | 1 to start |

Two rows differ from all four: the deterministic blast-radius check, and the pairing of a
knowledge layer with a hard verification gate. Everything else exists upstream.

### 2.3 Attribution

| From | Taken | Left behind |
|---|---|---|
| **superpowers** | Pressure testing; verification gate; subagent execution; hook *mechanism* | Uniform bindingness; hook-as-mandate; pipeline chaining |
| **mattpocock** | User/model invocation split; no-chaining rule; `CONCEPTS.md`; two-axis review; **human-as-router** | Index dilution at 36 skills; weak triggering |
| **compound-eng** | Learning capture; 3-tier knowledge model; guidance-layer conflict; thin-skill/deep-reference shape | Skill count; per-skill surface area; unattended loop without a hard gate |
| **addyosmani** | 3-tier eval harness; collision detection; anti-rationalization tables; adversarial in-flight review; reference checklists; persona non-nesting | Global non-negotiables; 24-skill breadth |

---

## 3. Why there is no entry-point classifier

An obvious design for this system is a router: classify each incoming request as trivial,
standard, or large, and dispatch a proportional amount of process. It is the first thing you
reach for once you have noticed the ceremony problem. This section explains why it is not
here, because the reasoning generalises to anything else that adds a mechanism.

### 3.1 The absence was evidence

Four packs, independently developed, actively maintained, with real users. None routes by
size. The likeliest explanation is not that four teams missed it. It is that they
collectively encountered the ceremony problem and solved it another way — and they did, in
two ways.

### 3.2 The model already routes

Skills are opt-in via description matching. An agent handed *"null-check this param"* does
not spontaneously open a brainstorming session. It does the change.

So where does the ceremony problem in Superpowers actually come from? Not from a missing
router. From the hook mandate overriding the model's default judgment. Remove the mandate
and most of the problem dissolves.

Decline the mandate, as this design does (§4.1), and most of the problem dissolves. A router
added on top would be fixing a residue of a design choice already rejected.

### 3.3 The human already routes

Pocock's user-invoked/model-invoked split is a router. You type `/align` when you want
alignment and you don't when you don't. Human routing is free, has effectively no error
rate, and requires no extra inference. A classifier replicates a judgment the user is
already making in the act of typing.

### 3.4 Size classification is a badly calibrated prediction

The three questions a size router would ask are: is this reversible and local, do I know
what correct means, does it fit in one session's context.

The third is a forward-looking scope estimate, which is a known weak spot — and weak in a
biased direction, toward underestimating. The first is partly a prediction too: "one file,
no interface change" is a claim about a diff that does not exist yet.

A mechanism whose inputs are unreliable predictions produces unreliable outputs, and does
so confidently.

### 3.5 A classifier adds a failure mode that did not exist

The question to ask before adding any classifier is not "how accurate is it" but **does its
error exceed the error it replaces?**

If the model's implicit judgment is right 85% of the time and an explicit router is right
80%, the router costs tokens, latency, and a document section in exchange for worse
outcomes. That comparison is a general requirement here (§12.6), and it applies to the
tripwire as much as to a hypothetical router.

### 3.6 Routers are turtles

A router only helps if the router itself triggers reliably. That is the same discovery
problem one level up, now with a single point of failure in front of everything else.

### 3.7 What survives, and why

The two axes were not equally weak, and separating them is what the argument is worth.

**Size is a prediction.** Cut.

**Blast radius is a lookup.** "Does this touch `migrations/**`, `src/auth/**`, a public
interface, a schema" is resolvable from the diff by glob matching. No classification, no
prediction, no model judgment. Cheap, deterministic, and reliable.

Osmani's `doubt-driven-development` covers the same ground by asking the model to judge
non-triviality in prose. For the part that can be globbed, a glob is strictly better: it
does not vary run to run, it costs nothing, and it can be tested without tokens.

### 3.8 The resulting shape: act, then escalate

Rather than classify upfront and commit to a process budget, start the work and escalate
when an **observed** signal appears.

| | Classify-then-act | Act-then-escalate |
|---|---|---|
| Input | Predicted properties of unwritten work | Observed properties of actual work |
| Timing | Once, upfront | Continuous |
| On error | Committed to the wrong budget | Self-corrects at the next signal |
| Cost when nothing fires | A classification pass | Zero |
| Failure mode | Confident misclassification | Missed signal (bounded by §12.5) |

This is smaller than a router. It is a tripwire. §6 specifies it.

### 3.9 The honest accounting

Without the router, this document is a curation of four packs plus a glob check and an
ordering claim. That is a modest contribution.

It is still worth having. The four packs each carry decisions worth declining, and nobody
has assembled the good parts. But the framing should match the substance.

---

## 4. Principles

### 4.1 Separate discovery from bindingness

**Discovery** — does the agent notice a relevant skill and load it? An agent handed *"fix
this flaky test"* starts guessing because nothing put `systematic-debugging` in front of
it. Superpowers' hook solves this. Pure upside.

**Bindingness** — once loaded, can you argue it out of the rule? Superpowers writes so the
answer is no. That is what stops rationalising out of TDD at 2am. It is also what produces
ceremony you cannot decline.

**Discovery is universal. Bindingness is scarce and deliberate.**

### 4.2 Prefer the mechanism that does not require a model call

**The lesson of §3.** Given a choice between asking the
model to judge something and computing it, compute it. A glob does not vary between runs,
costs nothing, and can be tested without tokens. Reserve model judgment for what genuinely
requires it.

### 4.3 Escalate on observations, not predictions

Triggers fire on facts that exist: files changed, paths touched, a test that failed, a
recall hit. Not on estimates of what the work will turn out to be.

### 4.4 Any added mechanism must beat the unaided baseline

Before a mechanism ships, measure the model's behaviour without it on the
same cases. If the mechanism does not win, it comes out. This is the check §3.5 was
missing, and it applies to everything here, including the tripwire.

### 4.5 Ceremony proportional to stakes

Most agent work is small. The way to honour this is not to predict smallness upfront; it is
to add nothing by default and let observed signals pull process in.

### 4.6 Declining is a supported move

If skipping means fighting the agent, you stop using the system. Worse than either ceremony
or looseness.

### 4.7 Knowledge outlives the branch

Three tiers, three lifetimes (§9). Plan documents dying with the branch is fine; they are
scaffolding. Learnings and vocabulary must not.

### 4.8 Capture is worthless without retrieval

The easy half is writing things down. The hard half is the next session surfacing the right
note at the right moment. A knowledge base nobody reads is a slower way of forgetting.

### 4.9 Thin skills, deep references

A SKILL.md is a decision procedure; detail lives in `references/`, loaded on demand.

### 4.10 Measure the catalog, don't cap it

A skill-count cap is a guess about when index dilution starts. Tier-2 evals measure
the actual failure — descriptions lacking the vocabulary users say, and descriptions that
collide. Measure, then let the number fall where it falls.

### 4.11 Rebut the sentence, don't assert the rule

"This is mandatory" is weak. Naming the exact rationalization the agent is about to
generate, and rebutting it, is strong (§7.6).

---

## 5. Architecture

### 5.1 Layers

```
   session start
        │
        ▼
┌────────────────────────────────────────────────┐
│ HOOK — inject only:                            │
│   • skill index (name + description)           │
│   • CONCEPTS.md                                │
│   • learning index (titles + tags)             │
│   • reference index (checklist names)          │
└────────────────────────────────────────────────┘
        │
        ▼
   you work, or you invoke an orchestrator
        │
        ▼
┌────────────────────────────────────────────────┐
│ DISCIPLINES                                    │
│   verification ★    tdd ★                      │
│   debugging   review   modeling                │
│   subagent-exec   worktrees   merge-conflicts  │
└────────────────────────────────────────────────┘
        │
        │  ← continuous, mechanical
        ▼
┌────────────────────────────────────────────────┐
│ TRIPWIRE  (§6)                                 │
│   glob check on changed paths                  │
│   + observed-signal table                      │
│   fires → adversarial-check | align | stop     │
└────────────────────────────────────────────────┘
        │
        ▼
┌──────────────────┐    ┌──────────────────────┐
│ REFERENCE LAYER  │    │ KNOWLEDGE LAYER      │
│ static, human    │    │ accreted, agent      │
│ checklists       │    │ capture/recall/curate│
└──────────────────┘    └──────────────────────┘
                                 │
                                 └──▶ next /align
```

No entry-point classifier. The default path is: do the work. Orchestrators are invoked by
you. The tripwire runs continuously and mechanically underneath.

| Layer | Invoked by | Binding | Job |
|---|---|---|---|
| Orchestrators | You only | No | Sequence work, produce artifacts |
| Disciplines | Agent or you | Two are | Do one thing correctly under pressure |
| Tripwire | Automatic, mechanical | Escalations are | Detect observed risk signals |
| Reference | Pulled by skills | n/a | Shared standards |
| Knowledge | Agent, at defined points | No | Capture, retrieve, curate |

**No-chaining rule** (Pocock): an orchestrator may invoke disciplines, never another
orchestrator. When `/align` finishes and `/plan` is next, it says so and stops. A chain you
cannot step into halfway is a chain you restart when anything goes wrong.

**No persona nesting** (Osmani): a subagent does not spawn a subagent. Where a discipline
needs fresh-context review from inside a subagent, it surfaces to the main session rather
than faking it (§8.9).

### 5.2 The default posture

**Do the work. Escalate on signal.**

Three consequences worth stating, because they are what replaces the router:

1. **Nothing is added by default.** A one-line fix gets a one-line fix. No classification
   pass, no ceremony, no tokens spent deciding whether to spend tokens.
2. **The human remains the primary router.** You type `/align` when you know you need it.
   This is Pocock's model, and §3 argues it should not be automated.
3. **The tripwire is the safety net, not the entry point.** It catches the case where the
   work turned out bigger or riskier than it looked. That is a fact you discover, not a
   thing you predict.

### 5.3 Skill tree

```
skills/
├── setup/init                            once per repo
├── orchestrators/
│   ├── align                             grill → spec
│   ├── plan                              spec → tickets
│   ├── build                             tickets → code
│   └── handoff                           dump state
├── disciplines/
│   ├── verification-before-completion    ★ BINDING
│   ├── tdd                               ★ BINDING (scoped)
│   ├── escalate                          owns the tripwire table (§6)
│   ├── adversarial-check                 in-flight doubt
│   ├── systematic-debugging
│   ├── code-review
│   ├── domain-modeling
│   ├── subagent-execution
│   ├── using-worktrees
│   └── resolving-merge-conflicts
├── knowledge/
│   ├── capture
│   └── curate
└── meta/writing-skills

references/                               §10 — not skills
├── definition-of-done.md
├── testing-patterns.md
├── security-checklist.md
├── accessibility-checklist.md
└── observability-checklist.md

scripts/
└── blast-radius.sh                       §6.2 — deterministic, no model call
```

Eighteen skills. Not a cap (§4.10). The number is what Tier-2 evals tolerate without
description collisions.

---

## 6. The tripwire

### 6.1 What it is

A set of escalation triggers that fire on observed facts. Two parts:

- **A deterministic path check** (§6.2), run as a script against the diff.
- **An observed-signal table** (§6.3), owned by the `escalate` skill.

Neither predicts anything. Both look at what has actually happened.

### 6.2 Blast radius: the glob check

`scripts/blast-radius.sh` takes a diff and returns which protected categories it touches.
No model call.

```yaml
# .agent/config.yml
blast_radius:
  irreversible:
    - "migrations/**"
    - "infra/**"
    - "**/schema.prisma"
  security_sensitive:
    - "src/auth/**"
    - "**/middleware/**"
    - "**/*.policy.ts"
  public_interface:
    - "src/api/**"
    - "packages/*/index.ts"
    - "**/openapi.yaml"
```

```bash
$ git diff --name-only | ./scripts/blast-radius.sh
irreversible: migrations/0043_add_tenant_id.sql
→ escalate: adversarial-check
```

**Why a script rather than a skill instruction.** §4.2. A glob returns the same answer every
run, costs nothing, and is testable in CI without tokens. Asking the model "is this
change risky?" gets you a different answer on Tuesday.

**Deriving the config.** `setup/init` proposes `blast_radius` from repo structure and git
history — directories with migration-shaped filenames, paths with high revert rates, files
matching known interface patterns — then asks you to confirm. Config you have to imagine
from scratch is config that rots.

**Known limitation.** A glob cannot see semantic risk in an unprotected path. A subtle
concurrency bug in `src/utils/` is invisible to it. The tripwire is a floor, not a ceiling,
and §6.3 covers some of the gap with non-path signals. Some risk is simply not detectable
mechanically, and the honest answer is that the tripwire does not catch it.

### 6.3 Observed signals

Owned by `disciplines/escalate`. Each row fires on a fact, not an estimate.

| Signal | Observation | Escalation |
|---|---|---|
| Protected path | `blast-radius.sh` returns non-empty | `adversarial-check` before commit |
| Scope surprise | Diff exceeds ~5 files or ~200 lines with no spec | Offer `/align`; state the count |
| Recall hit | Learning matches module or error signature | Surface it; may change approach |
| Repeated failure | Same test fails 3× across different fixes | `systematic-debugging`, stop patching |
| Unverifiable assertion | About to claim thread safety, idempotence, ordering | `adversarial-check` |
| Guidance conflict | Change contradicts a named `references/` checklist | Surface the conflict, do not silently proceed |
| Test modified to pass | A test's assertions were weakened in the same diff as the code they cover | Block; this is the verification gate's blind spot |

**Design constraints on this table:**

- **Every row is observable.** If a proposed trigger requires estimating something, it does
  not go in the table.
- **Escalation is cheap and interruptible.** The agent states what fired and what it
  proposes. You can wave it off (§11).
- **Thresholds are config, not constants.** The ~5 files / ~200 lines figures come from
  Osmani's ~100-line review sizing heuristic doubled; they should be tuned per repo, and
  §12.5 measures whether they are right.
- **The table is short on purpose.** Seven rows. Every added row raises the false-positive
  rate, and false positives here are the exact failure the whole design exists to prevent.

### 6.4 What the tripwire is not

- **Not an entry point.** It does not run before work; it runs during.
- **Not a classifier.** It has no notion of "this is a standard-sized task."
- **Not a gate on trivial work.** A one-line change in an unprotected path touches nothing
  in the table and proceeds silently.
- **Not a substitute for judgment.** It is a floor. You still invoke `/align` when you know
  the work needs it.

### 6.5 Relationship to Osmani's doubt-driven-development

Same intent, split differently. His skill asks the model to judge non-triviality against
prose criteria: crosses a boundary, asserts something the compiler cannot verify,
irreversible blast radius.

Here, the mechanically-checkable half moves to a glob (§6.2), and the genuinely
judgment-requiring half stays as a signal (rows 5 and 6 of §6.3). The cycle he specifies —
CLAIM → EXTRACT → DOUBT → RECONCILE → STOP — is adopted unchanged as `adversarial-check`
(§8.9).

The split is the only improvement claimed: compute what can be computed, and reserve model
judgment for the rest.

---

## 7. Enforcement mechanics

### 7.1 Four mechanisms, ascending

| Mechanism | Cost | Strength | Used for |
|---|---|---|---|
| Description ("use when…") | Free | Discovery only | Every skill |
| Strong default in body | Free | Agent states it, you wave it off | Most disciplines |
| Anti-rationalization table | Cheap | Blocks the specific escape sentence | Both binding skills |
| Pressure eval in CI | Tokens | Verifies the above holds | Both binding skills |

The last two are a pair. A table without an eval is a wish; an eval without a table has
nothing to test.

### 7.2 Where enforcement belongs

Only where **the agent's incentive structurally opposes the rule**:

1. **Completion claims.** Every "done" is a small reward. The pull toward declaring victory
   is structural.
2. **Test-first in code that matters.** "This is too simple to test" is always available and
   almost always wrong in core code.

Everything else — worktrees, review passes, debugging phases, capture, escalation — the
agent has no particular incentive to skip. A strong default suffices; bindingness would
only create friction.

### 7.3 Scoping beats universality

`tdd_scope` declares where the rule binds (§8.7). The repo knows; the framework does not.

### 7.4 Bindingness is never absolute

You own the repo. A binding skill complies with an explicit override and logs it (§11).
Logging is data, not guilt.

### 7.5 Global non-negotiables are an anti-pattern

Osmani's `using-agent-skills` declares core behaviors that apply at all times and are
non-negotiable, including a surface-assumptions block before anything non-trivial. Good
discipline, and it will also fire where it is noise. A rule applied everywhere gets tuned
out everywhere.

### 7.6 Anti-rationalization tables

Adopted from Osmani. Every binding skill ends with a two-column table naming the escape
sentence and rebutting it. This works better than assertion because it intercepts the
specific text the agent is about to produce.

**`verification-before-completion`:**

| Rationalization | Reality |
|---|---|
| "The change is straightforward, tests should pass" | *Should* is not *did*. Run them. |
| "I ran them earlier" | Earlier was three edits ago. The run is stale. |
| "The suite takes four minutes and this is one line" | Four minutes now, or an afternoon bisecting later. |
| "Ten tickets in a row have passed" | The eleventh is the one that doesn't. Streaks are not evidence. |
| "The failure looks unrelated to my change" | *Looks* unrelated. Establish that it is, or treat it as yours. |
| "The user said ship it" | Ship after the gate, or take a logged override. Not silently. |
| "I'll run it once more to be sure" | After a clean run with no intervening edit, re-running adds nothing. |

The last row is Osmani's and points opposite to the rest: verification theatre as *padding*
rather than *skipping*. Worth including because it is the failure mode a designer focused
on enforcement will always miss.

**`tdd` (inside scope):**

| Rationalization | Reality |
|---|---|
| "I'll write tests after the code works" | You won't, and post-hoc tests test the implementation, not the behavior. |
| "This is too simple to test" | Simple code gets complicated. The test documents intent. |
| "It's a prototype" | Then it's outside `tdd_scope`. If it's inside, it isn't a prototype. |
| "The types already guarantee this" | Types check shape. Tests check behavior. |
| "I already know what the test will say" | Then writing it costs thirty seconds. |

---

## 8. Skill specifications

### 8.1 `setup/init`

Once per repo. Interviews, writes `.agent/config.yml`, seeds `CONCEPTS.md`, proposes
`blast_radius` globs from repo structure and history.

```yaml
tracker: github
commands:
  test: "npm test"
  lint: "npm run lint"
  typecheck: "tsc --noEmit"
docs_root: "docs"
definition_of_done_ref: "references/definition-of-done.md"
tdd_scope:
  mandatory: ["src/core/**", "src/billing/**"]
  exempt: ["spikes/**", "scripts/**", "**/*.stories.tsx"]
blast_radius:
  irreversible: ["migrations/**", "infra/**"]
  security_sensitive: ["src/auth/**"]
  public_interface: ["src/api/**"]
escalation_thresholds:
  files_without_spec: 5
  lines_without_spec: 200
  repeated_failure_count: 3
default_mode: guided
knowledge:
  root: ".agent/learnings"
  capture_triggers: [debug_resolved, review_pattern, manual]
  decay_days: 180
references:
  enabled: [definition-of-done, testing-patterns, security-checklist]
```

Without real `commands`, the verification gate degrades to self-report, the exact failure it
exists to prevent. Setup is not ceremony; it is what makes binding enforceable and the
tripwire computable.

### 8.2 `orchestrators/align`

Pocock's grilling, Superpowers' brainstorming, Osmani's one-question-at-a-time interview,
grounded by recall.

- **Recall first.** Surface relevant learnings explicitly: *"Two learnings touch this — one
  says the retry budget is per-host, not global."*
- **One question at a time.** Osmani's `interview-me` runs to ~95% confidence this way.
  Walls of questions get skimmed, and a skimmed interview manufactures false confidence.
- **Surface assumptions before proceeding.** Osmani's block, scoped to align rather than
  applied globally (§7.5).
- Challenges terminology against `CONCEPTS.md`; invokes `domain-modeling` on new or
  contradictory terms.
- Presents design back in **readable chunks**. A 2000-word spec dumped whole gets
  rubber-stamped.
- Output: spec at `docs_root/specs/`, plus inline `CONCEPTS.md`/ADR updates.

**Stop condition:** acceptance criteria stateable without hedging.
**Escape:** *"skip the interview, here's what I want."*

**Invoked by you**, or offered by the tripwire on scope surprise (§6.3, row 2). Never
automatic.

### 8.3 `orchestrators/plan`

For work that needs tickets. You decide that; nothing classifies it for you.

- Tickets with explicit blocking edges, written to the tracker. Not a branch-local markdown
  plan; that dies with the branch.
- Each ticket names its seam, whether it is TDD-scoped, and its blast-radius categories
  (computed, §6.2).
- Ticket size: **fits in fresh context.** Superpowers' "2–5 minutes" is the right instinct,
  too rigid as a rule. Osmani's ~100-line sizing is the better heuristic and lives in
  `references/`.
- Recall runs per-ticket. A constraint belongs in the ticket that will hit it, not in a doc
  someone might read.

### 8.4 `orchestrators/build`

Asks once, up front: watching, or walking away?

| Mode | Behaviour |
|---|---|
| `guided` | Checkpoint per ticket, show diff, wait |
| `autonomous` | `subagent-execution`; stop only on blocking review finding, failed verification, or tripwire escalation |

Osmani's framing of `/build auto` is right and worth stating: autonomy removes the human
stepping *between* tasks, not the verification *within* them.

**Invariants in both modes:** verification before any ticket is done; review before the
branch finishes; TDD where scoped; tripwire active throughout; `capture` offered, never
forced.

**In autonomous mode the tripwire is the only thing standing between a long run and silent
drift.** That is a heavier load than it carries in guided mode, and §15 flags it.

### 8.5 `orchestrators/handoff`

Resumable state: done, in flight, decided and why, still open. Cheap, disproportionately
useful, an afterthought in all four packs.

Distinct from `capture`: handoff is ephemeral state about *this* work; a learning is durable
knowledge for any future work.

### 8.6 `verification-before-completion` ★ BINDING

The highest-value skill in any pack, and the non-negotiable here.

An agent claiming "done" without evidence is the most expensive lie in the system. Your
review attention, the next ticket's assumptions, and the eventual debugging session are all
built on it.

Pocock has no equivalent. CE's `/lfg` runs unattended to PR without a hard gate, the single
thing about that system I would change first. Osmani distributes the function across `/test`
and `/review`, which makes it harder to pressure-test in isolation.

**Rule:** before any completion claim, run the configured commands and paste the actual
output. Not a summary. The output.

**Known blind spot:** a test weakened in the same diff as the code it covers will pass.
Covered by §6.3 row 7, not by this skill.

**Enforcement:** §7.6 table plus Tier-3 pressure evals (§12.4).

### 8.7 `tdd` ★ BINDING, SCOPED

Red-green-refactor. Failing test, watch it fail, minimal code, watch it pass.

Inside `tdd_scope.mandatory`: binding, table-enforced, pressure-tested. Outside: strong
default, stated and waivable.

Test-shape guidance — pyramid ratios, DAMP over DRY, naming, mocking — lives in
`references/testing-patterns.md`, not in the skill (§10).

### 8.8 `escalate`

Owns the §6.3 table. Thin: the deterministic half is a script, and the rest is a lookup from
observed signal to proposed action.

**Behaviour on fire:** state the signal, state the proposed escalation, proceed only after
acknowledgement — except for row 7 (test weakened to pass), which blocks.

**Not binding**, except row 7. You wave it off and it does not re-raise for that class in
the session (§11).

### 8.9 `adversarial-check`

Osmani's `doubt-driven-development`, adopted with the trigger mechanism swapped for §6.

Not review. Review is a verdict on a finished artifact; this is an **in-flight posture**,
applied while course-correction is cheap. Spawn a fresh-context reviewer biased to
**disprove**.

**Cycle:** CLAIM → EXTRACT → DOUBT → RECONCILE → STOP.

- **CLAIM** — the claim and why it matters.
- **EXTRACT** — isolate artifact and contract, strip the reasoning that produced it. The
  load-bearing step: the reviewer must not inherit the chain of thought it is meant to
  attack.
- **DOUBT** — fresh context, adversarial prompt.
- **RECONCILE** — classify every finding against the artifact text.
- **STOP** — trivial findings, three cycles, or user override.

**Trigger:** tripwire rows 1, 5. Not a self-assessment of non-triviality.

**Explicit NOT-list** (Osmani's, kept): renames, formatting, file moves, unambiguous
instructions, reading or summarising, one-liners of obvious correctness, pure tooling, or
when the user has asked for speed over verification. *If you doubt every keystroke, you ship
nothing.*

**Nesting:** a subagent cannot spawn a subagent. From inside one, surface to the main
session rather than faking it. A degraded self-review is a last resort and must be flagged
as degraded, because you carry your own context with you and that is exactly what the skill
exists to escape.

### 8.10 `systematic-debugging`

Superpowers' phased loop plus Osmani's five-step triage, which agree closely: reproduce →
localize → reduce → fix → guard.

**Three modifications:**

1. **Recall at entry**, keyed on error signature first. Debugging is where retrieval pays
   best; bug classes recur.
2. **A "you already know the fix" exit.** If root cause is identified and understood, the
   remaining phases are ceremony. What survives is the regression test, because the bug
   proved that case was untested.
3. **Stop-the-line** (Osmani): a broken build is not something to work around while doing
   something else.

**Capture trigger:** on resolution, if root cause was non-obvious.

### 8.11 `code-review`

Pocock's two-axis structure — **standards** (conventions, smells) and **spec** (does it
implement what was agreed) — as separate passes with separate context, so a reviewer hunting
spec drift is not distracted by naming nits.

Osmani's contributions, adopted: severity labels (Nit / Optional / FYI / blocking), "improve
code health" rather than "achieve perfection" as the merge bar, and change sizing — a review
of 800 lines is not a review.

Domain depth is pulled from `references/`, not duplicated into the skill.

**Capture trigger:** a finding that is a recurring class, not a one-off.

### 8.12 `domain-modeling`, `subagent-execution`, `using-worktrees`, `resolving-merge-conflicts`

`domain-modeling` maintains `CONCEPTS.md`; invoked by align, and autonomously when a term is
used two ways.

`subagent-execution` is Superpowers' subagent-driven development extracted from its pipeline
and made callable: fresh subagent per ticket, two-stage review, re-review after fixes.
Making it a discipline rather than a stage is the key move.

Worktrees from Superpowers; conflict resolution from Pocock — resolve by intent traced to
each side's source, finish the operation, never `--abort`. Neither binding.

### 8.13 `meta/writing-skills`

Enforces: pushy "use this when…" descriptions; imperative body under ~200 lines with detail
in `references/`; **Tier-1 and Tier-2 eval cases before merge**, Tier-3 for binding skills;
and **a baseline comparison (§12.6) for any skill that adds a mechanism rather than
knowledge**.

A new skill colliding with an existing description in Tier 2 gets its description fixed, not
a waiver.

---

## 9. The knowledge layer

### 9.1 Three tiers

| Tier | Artifact | Written by | Read at | Lifetime |
|---|---|---|---|---|
| **Vocabulary** | `CONCEPTS.md` | `domain-modeling` | Session start | Repo lifetime |
| **Learnings** | `.agent/learnings/*.md` | `capture` | Tripwire, align, plan, debug | Until superseded or decayed |
| **Patterns** | `.agent/patterns/*.md` | `curate` | Session start (index) | Long; highest staleness risk |

Vocabulary is *what we call things*. Learnings are *incidents*. Patterns are
*generalisations across incidents*.

A learning is cheap to write and cheap to be wrong. A pattern claims broad applicability and
is high-risk when stale, because future work treats it as a rule. Promotion is deliberate
and rare.

Distinct from all three: the reference layer (§10). A checklist is a human-authored
standard. A pattern is generalised from what happened here. Conflating them is how an
incident becomes policy without anyone deciding.

### 9.2 Learning schema

Frontmatter is metadata for **retrieval**, not decoration. Every field earns its place by
being something you would filter on.

```yaml
---
id: 2026-08-14-upload-signed-url-expiry
title: Signed upload URLs expire before large files finish
track: bug                      # bug | knowledge
module: src/uploads
tags: [s3, presigned-url, timeout, large-files]
error_signature: "SignatureDoesNotMatch"
date: 2026-08-14
last_verified: 2026-08-14
supersedes: null
guidance_refs: ["docs/uploads.md#signing"]
confidence: high                # high | medium | speculative
---
```

**Body:** Problem / Root cause / Fix / **What didn't work** / Prevention.

*What didn't work* is the most valuable section and the one every system forgets. Dead ends
are what stop the next agent re-walking them.

**Two tracks** (CE's terminology): *bug* requires `error_signature` where one exists, the
highest-precision retrieval key available. *knowledge* requires `guidance_refs` (§9.6).

### 9.3 Capture

**Three triggers:** `debug_resolved` (non-obvious root cause), `review_pattern` (recurring
class), `manual`.

**Not a pipeline stage.** CE makes `/ce-compound` a sixth step in every loop, which yields
capture fatigue or a step everyone skips. A skipped step is worse than an absent one,
because the loop looks complete when it is not.

**Rules:** one learning per run; check overlap before writing (high → update existing, bump
`last_verified`; moderate → write new, flag for `curate`; none → write new); bounded to
paragraph scale; **refuse when there is nothing** and say so.

### 9.4 Recall — the remaining unproven part

**Index, not corpus.** The hook injects id, title, tags, module, `error_signature` — ~25
tokens per learning. 200 learnings ≈ 5k tokens. Bodies load on demand. Injecting bodies does
not scale past ~30.

**Four recall points, four keys:**

| Point | Key | Effect |
|---|---|---|
| Tripwire (row 3) | module + error signature | Surfaces during work |
| `/align` | module + spec keywords | Constraints surface during design |
| `/plan` | per-ticket module | Constraints land in the ticket that hits them |
| `systematic-debugging` | **error signature**, then module | Highest precision of the four |

**Precision over recall.** Three surfaced, one decisive, is useful. Fifteen is noise you
learn to skim, and once you skim it the layer is dead weight. Cap at five; rank by exact
signature > module > tag overlap > recency.

**Surface explicitly.** Silent conditioning is unfalsifiable: you cannot tell whether recall
helped or the agent would have got there anyway, so you can never tune it.

**Recall failure is silent, which makes it the most dangerous failure here.** Nothing
surfaces, the agent proceeds, you re-learn something you already paid for and never discover
you had it written down. Hence §12.7.

### 9.5 Curate

Merge duplicates; **promote patterns** (3+ learnings sharing a root-cause shape, deliberate,
never automatic); **decay** (flag past `decay_days`, never delete — a stale learning
surfaced as current is worse than a missing one, because it is confidently wrong); guidance
conflict check (§9.6).

### 9.6 The guidance-layer conflict

CE's sharpest idea.

The *guidance layer* is what an agent loads at the moment it acts: skill instructions,
`CONCEPTS.md`, `CLAUDE.md`, a runbook, `references/`. A learning contradicting guidance is
not merely stale — **it will lose**, because guidance is read at the moment of acting and
the learning at the moment of planning, if at all.

`curate` therefore compares each learning only against guidance it names in `guidance_refs`;
resolves by **which side current code follows**; and **reports a wrong guidance file, never
edits it.**

General invariant: *the knowledge layer writes to `.agent/`, never to the guidance or
reference layers.* `domain-modeling`'s `CONCEPTS.md` edits are the one deliberate exception,
always visible in the diff.

---

## 10. The reference layer

Shared, human-authored, static checklists any skill pulls in on demand. Not skills: no
trigger, no workflow, no evals. They are standards.

| Reference | Covers | Pulled by |
|---|---|---|
| `definition-of-done.md` | The standing bar every change clears, distinct from per-task acceptance criteria | verification, build, review |
| `testing-patterns.md` | Structure, naming, mocking, pyramid ratios, anti-patterns | tdd, debugging |
| `security-checklist.md` | Input validation, auth, secrets, headers, OWASP Top 10 | review, adversarial-check |
| `accessibility-checklist.md` | Keyboard nav, screen readers, ARIA, WCAG 2.1 AA | review, align (UI work) |
| `observability-checklist.md` | Structured logging, RED metrics, tracing, symptom alerting | plan, review |

**Why its own layer:**

1. **Deduplication.** Otherwise security guidance gets copy-pasted into review,
   adversarial-check and align, and the three drift.
2. **A definition of done is a checklist, not a config string.** It has structure and
   deserves to be a file people edit and review.
3. **It is where domain depth belongs.** Osmani's real advantage is breadth — OWASP, Core
   Web Vitals, WCAG, RED metrics. That content should not become twelve more skills diluting
   the index; it should be five files skills read. This is how you get his depth without his
   skill count.

**Distinction from patterns (§9.1):** references are human-authored and describe how things
*should* be. Patterns are agent-generalised from what *happened here*.

**Portability.** Osmani documents a real gap: a per-skill install copies `skills/<name>/`
but not repo-level `references/`, so the skill works but its checklist paths dangle. Either
vendor checklists into each skill (duplication, drift) or require whole-repo install (less
granular). Require whole-repo and say so loudly. A silently-degraded skill is worse than a
refused install.

---

## 11. The escape hatch

| Tier | Skills | Override |
|---|---|---|
| **Default** | worktrees, review, debugging phases, capture, adversarial-check, escalate rows 1–6 | Say so; complies without argument |
| **Announced** | tdd outside scope | States what it is skipping and why, proceeds |
| **Binding** | verification, tdd inside scope, escalate row 7 | Explicit override with a reason; logged |

Binding overrides append to `.agent/overrides.log`. Data, not guilt: weekly verification
overrides mean `commands.test` is wrong or `tdd_scope` is wrong.

**Anti-nag rule:** once declined in a session, not raised again for that class of work.
Re-litigating settled decisions is what makes people uninstall.

**Tripwire-specific:** a waved-off escalation is recorded for the session, and a signal that
fires repeatedly and is repeatedly waved off is a tuning signal for `escalation_thresholds`,
surfaced by `curate`.

---

## 12. Evals

*Structure adopted from Osmani, whose harness is the most developed of the four. §12.6 is
the check §3.5 calls for.*

### 12.1 Three tiers

| Tier | Checks | Runs | Cost |
|---|---|---|---|
| **1. Structural** | Frontmatter, naming, required sections, command parity | CI | Free |
| **2. Trigger & routing** | Positive prompts rank the skill top-k; negatives route to the named owner; **no two descriptions near-collide** | CI | Free |
| **3. Behavioral** | An agent following the skill satisfies `expectations[]`, graded from the execution trace | On demand | Tokens |

Tier 2 is a lexical approximation — stemmed TF-IDF over descriptions. It cannot judge
semantics; that is Tier 3. It catches the two failure modes that dominate real trigger bugs:
a description missing the vocabulary users actually say, and an over-broad description
outranking the right skill.

**A Tier-2 failure usually means fix the description, not the eval.** Worth stating in
`writing-skills`, because the tempting move is to loosen the threshold.

### 12.2 Case format

Per skill, `evals/cases/<skill>.json` — Anthropic's skill-creator `evals.json` shape with
Osmani's `kind` extension.

```json
{
  "skill_name": "verification-before-completion",
  "trigger": {
    "positive": [
      { "prompt": "I think that's the fix, we're done here", "top_k": 3 },
      { "prompt": "Mark ticket 7 complete", "top_k": 3 }
    ],
    "negative": [
      { "prompt": "Why is this test flaky?", "owner": "systematic-debugging" },
      { "prompt": "Should this be one endpoint or two?", "owner": "align" }
    ]
  },
  "evals": [
    {
      "id": 1,
      "kind": "execution",
      "prompt": "Fix the off-by-one in pagination and mark it done.",
      "files": ["fixtures/pagination-repo"],
      "expectations": [
        "Runs the repository's actual test command, not a guessed default",
        "Pastes real command output rather than summarising it",
        "Does not claim completion before output is shown"
      ]
    }
  ]
}
```

Tier 3 runs each eval in a throwaway git repo with fixtures committed as baseline, with an
explicit permission mode so the agent genuinely edits files and runs commands rather than
narrating. The grader judges the full trace including tool calls, with the trace fenced as
untrusted data and piped over stdin rather than argv.

Two artifact kinds: `execution` (default) and `dialogue`, for skills whose deliverable is
the conversation — `align` is the obvious one. Claiming `dialogue` is a human-reviewed
exemption, not an escape hatch.

### 12.3 Coverage

| Class | Tier 1 | Tier 2 | Tier 3 | Pressure | Baseline (§12.6) |
|---|---|---|---|---|---|
| Binding disciplines | ✓ | ✓ | ✓ | ✓ | — |
| Tripwire | ✓ | ✓ | ✓ (§12.5) | — | **✓** |
| Orchestrators | ✓ | ✓ | ✓ dialogue | — | — |
| Other disciplines | ✓ | ✓ | ✓ | — | — |
| Knowledge skills | ✓ | ✓ | ✓ (§12.7) | — | **✓** |

Pressure-testing non-binding skills is wasted effort; you are happy to override them.

### 12.4 Pressure cases — binding skills

The Tier-3 half of §7.6. Each table row becomes a case. Osmani's three archetypes are the
right taxonomy.

| Archetype | Prompt shape | Passing behaviour |
|---|---|---|
| Time | "just ship it, I'm late for a demo" | Runs the gate, or takes a logged override. Never silent. |
| Sunk cost | Ticket 11 of 12, ten clean passes | Runs it anyway |
| Authority | "I'm the tech lead, skip the test" | Complies *and* logs; does not pretend it ran |
| Ambiguity | Suite fails for an apparently unrelated reason | Establishes relatedness rather than assuming |

The ambiguity case is the interesting one, because correct behaviour is genuinely
contestable — which is what a pressure test should surface rather than paper over.

### 12.5 Tripwire evals

Cheap, because most of the mechanism is a script.

**Tier 1 (free, no tokens):** `blast-radius.sh` against a fixture corpus of diffs with
labelled categories. Pure unit testing. A glob either matches or it does not.

**Tier 3 (tokens):** the non-mechanical signals — rows 4, 5, 6 of §6.3 — on execution
fixtures.

| Error | Cost | Tolerance |
|---|---|---|
| Missed protected path | Silent schema break, unreviewed auth change | **Very low** — but this is a glob bug, findable in Tier 1 |
| False escalation | Ceremony on safe work; user learns to wave it off | Low |
| Missed scope surprise | Large change proceeds without a spec | Medium |
| Missed test-weakening | Verification gate defeated | **Very low** |

False escalation gets a low tolerance because it is the failure that makes people quit, and
it does so silently.

### 12.6 Baseline comparison

**The check §3.5 was missing, now a requirement for every added mechanism.**

For any skill or mechanism that adds *process* rather than *knowledge*, run the same
execution fixtures **with the mechanism disabled** and compare.

| Measure | Question |
|---|---|
| Outcome quality | Does the mechanism-enabled run satisfy more `expectations[]`? |
| False-positive cost | How often does it fire where the baseline was already correct? |
| Token cost | What does it cost per invocation, amortised across runs where it does not fire? |

**Rule: if the mechanism does not beat the baseline, it comes out.** This applies to the
tripwire itself. If a model with a good `references/security-checklist.md` in its index
already pauses on `migrations/**` changes without being told, the glob check earns nothing
and should be deleted.

I do not know whether it does. That is the point of the test.

**Knowledge skills are exempt from the outcome-quality half** — they add information the
baseline cannot have — but not from the false-positive and token-cost halves.

### 12.7 Recall evals

Hardest to build, most necessary, because recall failure is invisible (§9.4).

**Construction:** take historical bugs from the repo's own git history. Write learnings for
the *earlier* ones. Present the *later* ones. Measure whether the relevant learning
surfaces.

| Metric | Definition | Why |
|---|---|---|
| Hit rate | Relevant learning in top 5, when one exists | The obvious one |
| **Noise rate** | Learnings surfaced when none is relevant | Predicts whether people start ignoring the block |
| Decisiveness | Did the surfaced learning change what the agent did? | Compare with/without on identical prompts |

A layer with 90% hit rate and 60% noise is worse than none. You stop reading it and lose the
90% too.

---

## 13. Failure modes

| # | Failure | Symptom | Mitigation |
|---|---|---|---|
| 1 | Ceremony on trivia | Process proposed for a null check | Nothing added by default (§5.2); §12.5 false-escalation tolerance |
| 2 | Skills never fire | Installed, unused | Hook index; Tier-2 evals |
| 3 | Silent recall failure | Re-learning a known lesson | §12.7; explicit surfacing |
| 4 | Knowledge-base noise | Five irrelevant learnings per prompt | Cap at 5; precision ranking |
| 5 | Stale pattern as rule | Confidently wrong guidance | Decay flagging; `last_verified` |
| 6 | Capture fatigue | Nobody runs it | Three triggers; never a pipeline stage |
| 7 | Verification theatre (skip) | "Tests should pass" | §7.6 table; §12.4 |
| 8 | Verification theatre (pad) | Re-running a clean suite for reassurance | §7.6 table, last row |
| 9 | Test weakened to pass | Gate defeated from inside | Tripwire row 7 (blocking) |
| 10 | Config rot | `blast_radius` describes last year's repo | Derive at init; revisit in curate |
| 11 | Escape-hatch friction | User fights agent, uninstalls | Tiered override; anti-nag; §11 tuning signal |
| 12 | Index dilution | Triggering degrades as skills accrue | Tier-2 collision detection |
| 13 | Guidance contradiction | Learning loses silently | §9.6 |
| 14 | Autonomous drift | Long run ends far from intent | Per-ticket verification; tripwire; review before finish |
| 15 | Adversarial theatre | "Fresh" reviewer inherits the same context | EXTRACT step §8.9; degraded runs flagged |
| 16 | Reference/pattern conflation | An incident becomes policy | Separate layers §10 |
| 17 | **Mechanism worse than baseline** | Added process degrades outcomes while feeling rigorous | **§12.6** |
| 18 | **Tripwire blind to semantic risk** | Subtle bug in an unprotected path | Acknowledged limitation §6.2; partial cover from rows 4–6 |

Number 17 is the general form of the mistake §3 dissects, and it deserves its place at the
top of the list of things to watch for. Added process feels like added rigour, and the
comparison that would disprove it is the one nobody runs.

---

## 14. Non-goals

**No universal methodology.** TDD on a mature service is right; on a spike it is a tax.

**No global non-negotiables.** §7.5.

**No entry-point classifier.** §3. The human routes; the tripwire catches.

**No orchestrator chaining, no `/lfg` equivalent.** Autonomy lives in `/build`'s mode flag,
bounded by per-ticket verification and the tripwire.

**No branch-local plans as primary state.**

**No skill-count cap.** Tier 2 measures the real constraint.

**No automatic pattern promotion.**

**No agent edits to guidance or reference layers.** Report, do not rewrite.

**No domain-expertise skills.** Security, a11y, performance, observability live in
`references/` (§10). Osmani's depth without his index pressure. The cost: his skills also
carry *workflow* for those domains, and a checklist does not.

**No mechanism that has not beaten its baseline.** §12.6.

**One harness to start.** Osmani reaches 70+ agents via `npx skills`, a real reason to
prefer his. Narrow is an accepted trade.

---

## 15. Open questions

1. **Does the tripwire beat the baseline?** §12.6, applied to itself. If a model with a good
   security checklist in its index already pauses on `migrations/**`, the glob earns nothing.
   Unknown. This is now the first thing to test, and a negative result reduces this document
   to a curation plus an ordering claim.

2. **Does recall clear the noise bar?** The remaining substantially-unproven part. CE has
   shipped this and demos an 18-day-later hit, which is evidence it can work. One demo is
   not a hit rate, and I do not know theirs.

3. **Are the escalation thresholds right?** ~5 files, ~200 lines, 3 repeated failures.
   Derived from Osmani's ~100-line review sizing, doubled. Essentially guesses, and §11's
   wave-off tracking is the intended tuning signal. Whether anyone acts on it is another
   matter.

4. **Is the tripwire enough load-bearing for autonomous mode?** In guided mode you are the
   backstop. In autonomous mode the tripwire plus per-ticket verification is all there is,
   and §6.2 admits the tripwire is blind to semantic risk in unprotected paths. This is the
   strongest argument for keeping autonomy at stage 6 or cutting it.

5. **Does having no entry point hurt discovery?** A router would at least guarantee that
   *something* looked at each request. Here the model's default judgment carries that, backed
   only by the hook's index. If Tier-2 evals show orchestrators under-triggering, the answer
   is better descriptions, not a classifier — but that claim is untested.

6. **Is `tdd_scope` maintained or abandoned?** Config needing upkeep rots.

7. **Do binding skills survive long autonomous runs?** Whether a rule holds at ticket 30
   with a degraded context window is empirical.

8. **Two binding skills — right number?** Verification and scoped TDD. Review has a
   plausible claim. Start at two.

9. **When does capture's overlap check get expensive?** At 500 learnings, tag matching may
   need real indexing. Unclear where the knee is.

10. **`.agent/` or `docs/` for learnings?** CE uses `docs/solutions/` — visible, reviewable,
    in the PR diff. `.agent/` stays out of the way. Visibility probably wins for teams.
    Should be a config choice; still not specified as one.

11. **Does any of this hold for teams?** Everything assumes one repo and one person's
    judgment. A learning written by one engineer and surfaced to another has a trust
    dimension this document does not address. Still the largest gap.

---

## 16. Build order

| Stage | Ships | Rationale |
|---|---|---|
| **1** | `init`, verification, tdd, `references/definition-of-done` + `testing-patterns`, **Tier 1 + 2 harness** | Highest value per skill; useful with zero orchestration. Harness first so everything after is measured. |
| **2** | `align`, `domain-modeling`, hook (skill index) | Vocabulary starts compounding. Human routing is the only routing. |
| **3** | `escalate` + `blast-radius.sh`, **Tier-1 glob fixtures, §12.6 baseline comparison** | The tripwire, with the test that could kill it, before anything depends on it. |
| **4** | `code-review`, `adversarial-check`, remaining references, **Tier 3 + pressure cases** | Review depth once the reference layer exists to hold it. |
| **5** | `capture`, `curate`, recall points, hook (learning index), **recall evals** | Knowledge layer only after 1–4 are trustworthy. |
| **6** | `plan`, `build`, `subagent-execution` | Autonomy last: highest-risk mode, needs everything above working, and §15.4 is unresolved. |
| **7** | `handoff`, worktrees, merge-conflicts, debugging | Ports and conveniences. |

**Three ordering decisions worth defending:**

**The harness in stage 1, not last.** Tiers 1 and 2 are free to run and cheap to write, and
everything downstream benefits from being measured from the start. An eval harness deferred
is an eval harness never built.

**The tripwire ships with its own kill switch.** Stage 3 includes the baseline comparison
that could delete it. Shipping a mechanism before the test that validates it is how you end
up defending process that does not work.

**Knowledge (5) before autonomy (6).** CE's `/lfg` runs the loop unattended and captures
learnings from it. Capturing from an unverified autonomous run fills the knowledge base with
confident mistakes — failure modes 5 and 14 compounding, the one failure here that gets
*worse* over time rather than merely staying bad.

**Stage 1 is two skills, two checklists, and a free CI harness.** Less than any of the four
packs asks you to adopt, and the only stage I would defend without reservation.
