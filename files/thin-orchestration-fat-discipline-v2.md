# Thin Orchestration, Fat Discipline — v2

**A design for an agent skill system, synthesised from three existing approaches**

*Version 2. Changes from v1: adds the knowledge layer (§6) — capture, retrieval, and
decay — after reviewing Every Inc's compound-engineering plugin, which is materially
better than v1 was on durable knowledge. Also adds a four-way landscape comparison (§2),
a failure-mode catalogue (§10), and an expanded eval section (§9).*

---

## Table of contents

1. [What this is](#1-what-this-is)
2. [The landscape](#2-the-landscape)
3. [Principles](#3-principles)
4. [Architecture](#4-architecture)
5. [Orchestrators and disciplines](#5-orchestrators-and-disciplines)
6. [The knowledge layer](#6-the-knowledge-layer)
7. [The escape hatch](#7-the-escape-hatch)
8. [The hook](#8-the-hook)
9. [Evals](#9-evals)
10. [Failure modes](#10-failure-modes)
11. [Non-goals](#11-non-goals)
12. [Open questions](#12-open-questions)
13. [Build order](#13-build-order)

---

## 1. What this is

A design spec for a skill library for coding agents, positioned against three existing
systems that have each solved a different piece of the problem well.

The three disagree less about *what good engineering looks like* — they all want spec
before code, tests that actually run, review before merge — than about **where control
and knowledge live**. Superpowers puts control in the framework. Pocock puts it in your
hands. Compound Engineering puts knowledge in the repo.

This design's bet: take the control model from Pocock, the enforcement machinery from
Superpowers, the knowledge model from CE, and add the one thing none of them has — a
router that decides how much process a given task actually deserves.

**Status.** Design, not implementation. The router (§5.2) and the retrieval half of the
knowledge layer (§6.4) are the unproven parts. Everything else is assembly of things
that demonstrably work somewhere.

---

## 2. The landscape

### 2.1 The three systems

**[obra/superpowers](https://github.com/obra/superpowers)** — Jesse Vincent / Prime
Radiant. ~14 skills wired into one enforced pipeline (brainstorm → worktree → plan →
subagent execution → TDD → review → finish). A session-start hook makes skills fire
automatically; the README describes them as mandatory workflows, not suggestions. Ships
for ~12 harnesses. Company-backed, commercial support offered, contributions of new
skills generally not accepted.

*Best idea:* pressure-testing. Its `skills/systematic-debugging/test-pressure-*.md` files
check that a discipline survives an agent being tempted to skip it. Nobody else does this.

*Worst tendency:* ceremony you can't decline.

**[mattpocock/skills](https://github.com/mattpocock/skills)** — ~36 small composable
skills, explicitly positioned against process-owning frameworks. Split by invocation:
*user-invoked* skills orchestrate (`/grill-me`, `/to-spec`, `/implement`), *model-invoked*
skills hold reusable discipline (`tdd`, `code-review`, `diagnosing-bugs`). Designed to be
forked and edited.

*Best idea:* the invocation split, which makes the control boundary explicit and
inspectable. Runner-up: `CONTEXT.md` as a shared domain language.

*Worst tendency:* skills that never fire because nothing reminds the agent they exist.

**[EveryInc/compound-engineering-plugin](https://github.com/EveryInc/compound-engineering-plugin)**
— 33 skills, 14 hosts, v3.23.x. Thesis in the name: each unit of work should make the
next easier. Six-step loop — brainstorm → plan → work → simplify → review → **compound**.
The sixth step writes solved problems to `docs/solutions/` with structured frontmatter;
the next brainstorm and plan read them as grounding. Skills are thin (60–120 lines) over
deep `references/` trees — 392 files, 31 reference directories. No hooks; everything
user-invoked. `/lfg` runs the entire loop unattended through PR and CI watching.

*Best idea:* treating captured knowledge as a first-class artifact with a schema, a
retrieval story, and a maintenance skill. It is the only one of the three where knowledge
*accumulates* rather than evaporating with the branch.

*Worst tendency:* surface area. `/ce-compound` alone carries mode detection, depth
selectors, deprecated aliases, non-interactive contracts, write-boundary rules and a
frontmatter validator — for "write down what you learned."

### 2.2 Four-way comparison

| | superpowers | mattpocock | compound-eng | **this design** |
|---|---|---|---|---|
| **Core thesis** | Enforced methodology | Composable tools | Knowledge accretion | Proportional process |
| **Skills** | ~14 | ~36 | 33 | 16 |
| **Trigger** | Auto (hook) | User + model | User only | Hook injects index; user + model invoke |
| **Bindingness** | High, uniform | Low | Low–medium | Scarce and explicit |
| **Autonomy** | subagent-driven | `/implement` | `/lfg` full pipeline | `/build` autonomous mode |
| **Durable state** | Plan docs (branch-local) | `CONTEXT.md` glossary | Learnings + concepts + patterns | Same three tiers, smaller |
| **Retrieval** | — | Read at session start | Metadata search + refresh | Indexed, read at align/debug |
| **Size routing** | None | None | None | **`/work` router** |
| **Verification gate** | `verification-before-completion` | — | Implicit in review | Binding |
| **Hosts** | ~12 | 2 paths | 14 | 1 to start |

The last three rows are where the differentiation lives. Two of them are things all
three parents lack.

### 2.3 What each contributes here

| From | Taken | Left behind |
|---|---|---|
| superpowers | Pressure-testing, verification gate, subagent execution, session-start hook mechanism | Universal bindingness, hook-as-mandate, pipeline chaining |
| mattpocock | User/model invocation split, no-chaining rule, `CONTEXT.md`, two-axis review | 36-skill index dilution, weak triggering |
| compound-eng | Learning capture, three-tier knowledge model, guidance-layer conflict concept, thin-skill/deep-reference structure | Skill count, per-skill surface area, unattended pipeline without a hard verification gate |

---

## 3. Principles

### 3.1 Separate discovery from bindingness

Two distinct things get conflated under "the agent should use skills":

**Discovery** — does the agent notice a relevant skill exists and load it? An agent
handed *"fix this flaky test"* starts guessing, because nothing put `systematic-debugging`
in front of it. Superpowers solves this with a session-start hook. Pure upside.

**Bindingness** — once loaded, can you talk the agent out of it? Superpowers writes skills
so the answer is no. That's what stops an agent rationalising out of TDD at 2am. It's also
what makes it open a brainstorming session about a four-line null check.

**Rule: discovery is universal, bindingness is scarce and deliberate.**

### 3.2 Ceremony proportional to stakes

Most agent work is small. Brainstorm → plan → subagent → review on a 20-line fix is
theatre, and it's the single biggest reason people abandon these systems. Size routing is
a first-class concern.

### 3.3 Declining is a supported move

If skipping a step means *fighting* the agent, you will stop using the system — worse than
either ceremony or looseness. The escape hatch has its own spec (§7).

### 3.4 Knowledge outlives the branch

Three tiers, three lifetimes (§6). Plan documents die with the branch and that's fine —
they're scaffolding. Learnings and vocabulary must not.

### 3.5 Capture is worthless without retrieval

The easy half of compounding is writing things down. The hard half is the *next* session
finding the right note at the right moment. A knowledge base nobody reads is a slower way
of forgetting. Retrieval gets more design attention here than capture.

### 3.6 Thin skills, deep references

CE's structure, and it's correct. A SKILL.md is a router with a decision procedure; detail
lives in `references/` loaded on demand. Keeps the always-loaded index small and the
triggering signal clean.

### 3.7 Testable or it's vibes

Every skill ships a trigger eval. Binding skills also ship a pressure eval. Untested
skills rot silently.

---

## 4. Architecture

```
   session start
        │
        ▼
┌──────────────────────────────────────────────┐
│ HOOK — inject only:                          │
│   • skill index (name + description)         │
│   • CONCEPTS.md                              │
│   • learning index (titles + tags)           │
└──────────────────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────────────┐
│ ROUTER  /work                                │
│ classify: trivial | standard | large         │
└──────────────────────────────────────────────┘
     │           │              │
  trivial    standard         large
     │           │              │
     │           ▼              ▼
     │      /align ────────▶ /plan ────▶ /build
     │           │                          │
     └───────────┴──────────┬───────────────┘
                            ▼
        ┌───────────────────────────────────────┐
        │ DISCIPLINES (model- or user-invoked)  │
        │  verification ★   tdd ★               │
        │  debugging   review   subagent-exec   │
        │  worktrees   merge-conflicts          │
        │  domain-modeling                      │
        └───────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │ KNOWLEDGE LAYER                       │
        │  capture ──▶ .agent/learnings/        │
        │  recall  ◀── read at align & debug    │
        │  curate  ──▶ patterns, decay, merge   │
        └───────────────────────────────────────┘
                            │
                            └──▶ feeds next /align
```

Four layers:

| Layer | Invoked by | Binding | Job |
|---|---|---|---|
| **Router** | You, or auto | No | Decide how much process this deserves |
| **Orchestrators** | You only | No — you're driving | Sequence work, produce durable artifacts |
| **Disciplines** | Agent or you | Two are | Do one thing correctly under pressure |
| **Knowledge** | Agent, at defined moments | No | Capture, retrieve, curate |

**No-chaining rule** (from Pocock): an orchestrator may invoke disciplines, but never
another orchestrator. When `/align` finishes and `/plan` is obviously next, it *says so
and stops*. You remain the scheduler. This is the single clearest difference from
Superpowers and CE's `/lfg`, and it's deliberate: a chain you can't step into midway is a
chain you have to restart when anything goes wrong.

### 4.1 The skill tree

```
skills/
├── setup/
│   └── init                              once per repo
├── orchestrators/
│   ├── work                              the router
│   ├── align                             grill → spec
│   ├── plan                              spec → tickets
│   ├── build                             tickets → code
│   └── handoff                           dump state
├── disciplines/
│   ├── verification-before-completion    ★ BINDING
│   ├── tdd                               ★ BINDING (scoped)
│   ├── systematic-debugging
│   ├── code-review
│   ├── domain-modeling
│   ├── subagent-execution
│   ├── using-worktrees
│   └── resolving-merge-conflicts
├── knowledge/
│   ├── capture
│   └── curate
└── meta/
    └── writing-skills
```

**Sixteen skills.** Not 33–36 — every skill dilutes the injected index and degrades
triggering for everything else. Not 8 — disciplines need separation to be individually
testable. Sixteen is already at the upper end of what I'd defend.

---

## 5. Orchestrators and disciplines

### 5.1 `setup/init`

Run once per repo. Interviews you, writes `.agent/config.yml`, seeds `CONCEPTS.md`.

```yaml
tracker: github              # github | linear | local
commands:
  test: "npm test"
  lint: "npm run lint"
  typecheck: "tsc --noEmit"
docs_root: "docs"
definition_of_done: |
  Tests pass, types clean, the originating case is covered by a test.
tdd_scope:
  mandatory: ["src/core/**", "src/billing/**"]
  exempt: ["spikes/**", "scripts/**", "**/*.stories.tsx"]
default_mode: guided         # guided | autonomous
knowledge:
  root: ".agent/learnings"
  capture_triggers: [debug_resolved, review_pattern, manual]
  decay_days: 180
```

Without real `commands`, `verification-before-completion` degrades into asking the agent
to self-report — the exact failure it exists to prevent. Setup isn't optional ceremony;
it's what makes the binding skills enforceable.

`tdd_scope.mandatory` should be *derived* at init from existing test coverage where
possible, then confirmed, rather than asked cold. Config you have to imagine is config
that rots.

### 5.2 `orchestrators/work` — the router

**The most important skill here, and the one no parent repo has.**

```markdown
---
name: work
description: Route a development request to the right amount of process. Use
  whenever the user describes something to build, change, or fix and it isn't
  obvious whether it needs a spec, a plan, or just a diff. Use this before
  reaching for align, plan, or build.
---
```

**Classification — three questions, in order:**

1. **Is the change reversible and local?** One file, no interface change, no data
   migration, no new dependency → *trivial*.
2. **Do I know what "correct" means without asking?** If intent requires guessing, it's at
   least *standard*.
3. **Does it fit in one session's context?** If not → *large*.

**Routes:**

| Class | Path | Example |
|---|---|---|
| Trivial | Do it. Verify. Show the diff. | "null-check this param" |
| Standard | `/align` → implement → review | "add rate limiting to uploads" |
| Large | `/align` → `/plan` → `/build` | "migrate auth to sessions" |

**The router must be able to say no to itself.** A valid, common output is:

> One-line change. Here's the diff, tests pass, no spec needed.

If it can never reach that conclusion, the design has failed and you've rebuilt the thing
you were avoiding.

**Recall hook:** before classifying, the router checks the learning index (§6.4) for tags
matching the request's module or error signature. A hit can *change* the classification —
"we've hit this before and it took two days" turns a trivial-looking change standard.
This is the cheapest possible use of accumulated knowledge and the highest-leverage
placement for it.

**Not binding.** Override by saying so.

### 5.3 `orchestrators/align`

Pocock's grilling merged with Superpowers' brainstorming, grounded by recall.

**Behaviour:**

- **Recall first.** Pull relevant learnings and any pattern docs for the touched modules.
  Surface them explicitly: *"Three prior learnings touch this area — one says X."* This is
  CE's central move and it's right.
- Questions **one at a time**. Walls of questions get skimmed, and a skimmed interview is
  worse than none because it produces false confidence.
- Challenges terminology against `CONCEPTS.md`; invokes `domain-modeling` on a new,
  ambiguous, or contradictory term.
- Presents the design back **in readable chunks**. A 2000-word spec dumped at once gets
  rubber-stamped.
- Output: spec at `docs_root/specs/`, plus inline `CONCEPTS.md` / ADR updates.

**Stop condition:** the agent can state acceptance criteria without hedging.

**Escape:** *"skip the interview, here's what I want"* → writes the spec from what you've
said.

### 5.4 `orchestrators/plan`

Fires only for *large*. For *standard*, the spec is the plan.

- Tickets with **explicit blocking edges**.
- Written to the configured tracker — native blocking links where supported, local file
  otherwise. **Not** a branch-local markdown plan; that dies with the branch.
- Each ticket names its seam and whether it's TDD-scoped.
- Ticket size constraint: **fits in fresh context**. Superpowers' "2–5 minutes each" is a
  good instinct but too rigid to state as a rule.
- Recall runs again at plan time — a learning that constrains implementation (a known
  library trap, a migration ordering rule) belongs in the ticket that will hit it, not in
  a doc someone might read.

### 5.5 `orchestrators/build`

Asks **once, up front**: watching, or walking away?

| Mode | Behaviour |
|---|---|
| `guided` | Checkpoint per ticket. Show diff. Wait. |
| `autonomous` | Dispatch via `subagent-execution`. Stop only on blocking review finding or failed verification. |

This single question dissolves most of the tension between the parents. Superpowers and
CE's `/lfg` optimise for autonomous and make guided feel like resistance. Pocock optimises
for guided with thin support for walking away. Both are legitimate; they're different
sessions.

**Invariants in both modes:**

- `verification-before-completion` before any ticket is marked done. No exceptions.
- `code-review` before the branch is finished.
- TDD where `tdd_scope` says.
- On completion, `capture` is *offered* — never forced (§6.3).

### 5.6 `orchestrators/handoff`

Writes resumable state: done, in flight, decided and why, still open. Run before losing
context. Cheap, disproportionately useful, an afterthought in all three parents.

Distinct from `capture`: handoff is **ephemeral** state for the next session on *this*
work; a learning is **durable** knowledge for any future session on *any* work.

### 5.7 `disciplines/verification-before-completion` ★ BINDING

**The highest-value skill in any of the three parents, and the non-negotiable here.**

An agent saying "done" without evidence is the most expensive lie in the system, because
everything downstream — your review attention, the next ticket's assumptions, the eventual
debugging session — is built on it.

Neither Pocock nor CE has a direct equivalent. CE's `/lfg` running unattended to PR
without a hard evidence gate is the thing about that system I'd change first.

**Rule:** before any completion claim, run the commands from config and paste the actual
output. Not a summary. The output.

**Anti-patterns it must resist (these are the pressure cases):**

- *"The change is straightforward, so tests should pass"* → run them.
- *"I ran them earlier"* → earlier was three edits ago.
- Tests pass but the failing case that started this was never added → not done.
- A test was modified to accommodate the code rather than the reverse → not done, say so
  loudly.
- Ticket 11 of 12, ten consecutive passes → run them anyway.

**Why binding:** the incentive to declare victory is structural, not incidental. Every
completion claim is a small reward. This is precisely the narrow case where a hard rule
beats judgment.

### 5.8 `disciplines/tdd` ★ BINDING, SCOPED

Red-green-refactor. Failing test, watch it fail, minimal code, watch it pass.

**The scoping is the design.** Inside `tdd_scope.mandatory`, binding and pressure-tested —
the agent doesn't get to argue this particular function is too simple, because that
argument is always available and almost always wrong in core code. Outside, a strong
default it states and you can wave off.

Superpowers applies TDD universally: right on a mature service, a tax on a spike. Making
the boundary explicit and repo-owned keeps the discipline where it matters without making
it the thing you fight.

### 5.9 `disciplines/systematic-debugging`

Superpowers' phased loop, largely intact — the best-developed skill in any parent.
Reproduce → minimise → hypothesise → instrument → fix → regression-test.

**Two additions:**

1. **Recall at entry.** Search learnings by error signature and module before hypothesising.
   Debugging is where retrieval pays best — the same bug class recurs constantly.
2. **A *"you already know the fix"* exit.** If root cause is identified and understood, the
   remaining phases are ceremony. What survives is the regression test, because the bug
   proved that case was untested.

**Capture trigger:** on resolution, if root cause was non-obvious, `capture` fires (§6.3).

### 5.10 `disciplines/code-review`

Pocock's two-axis structure, better than a single pass:

- **Standards** — repo conventions plus a smell baseline.
- **Spec** — does it faithfully implement the originating spec/ticket?

Run as **separate passes with separate context**, so a reviewer hunting spec drift isn't
distracted by naming nits and vice versa. Findings by severity; critical blocks.

**Capture trigger:** a finding that is a *pattern* rather than a one-off — the third time
the same class of mistake appears — fires `capture`.

### 5.11 `disciplines/domain-modeling`

Maintains `CONCEPTS.md`. Invoked by `/align`, and autonomously when a term is used two
different ways.

### 5.12 `disciplines/subagent-execution`

Superpowers' subagent-driven development, extracted from its pipeline and made callable.
Fresh subagent per ticket; two-stage review (spec compliance, then code quality);
re-review after fixes.

Making it a *discipline* rather than a pipeline stage is the key structural move: you get
autonomous execution without buying the whole workflow, and `/build` chooses per session.

### 5.13 `using-worktrees`, `resolving-merge-conflicts`

Straight ports. Worktrees from Superpowers; conflict resolution from Pocock (resolve by
intent traced to each side's source; finish the operation, never `--abort`).

Neither binding. *"Scratch branch, skip the worktree"* is legitimate and gets accepted
without argument.

### 5.14 `meta/writing-skills`

How to extend this. Enforces: pushy frontmatter descriptions (agents systematically
under-trigger, so descriptions need explicit "use this when…" context, not just a summary);
imperative body under ~200 lines with detail in `references/`; and two evals minimum.

---

## 6. The knowledge layer

*The substantive addition in v2. v1 had a glossary and called it durable state — that
captures what things are called, not what they cost us to learn.*

### 6.1 Three tiers

| Tier | Artifact | Written by | Read at | Lifetime |
|---|---|---|---|---|
| **Vocabulary** | `CONCEPTS.md` | `domain-modeling` | Session start (hook) | Repo lifetime |
| **Learnings** | `.agent/learnings/*.md` | `capture` | Router, align, plan, debug | Until superseded or decayed |
| **Patterns** | `.agent/patterns/*.md` | `curate` | Session start (index only) | Long, but highest staleness risk |

Vocabulary is *what we call things*. Learnings are *incidents* — this specific problem,
this root cause, this fix. Patterns are *generalisations* across several learnings.

CE gets this three-way split right and it's worth copying wholesale. The distinction that
matters most: a learning is cheap to write and cheap to be wrong; a pattern claims broad
applicability and is therefore **high-risk when stale**, because future work treats it as
a rule. Promotion from learning to pattern should be deliberate and rare.

### 6.2 Learning schema

Frontmatter is metadata for *retrieval*, not decoration. Every field earns its place by
being something you'd filter or search on.

```yaml
---
id: 2026-08-14-upload-signed-url-expiry
title: Signed upload URLs expire before large files finish
track: bug                    # bug | knowledge
module: src/uploads
tags: [s3, presigned-url, timeout, large-files]
error_signature: "SignatureDoesNotMatch"   # bug track only
date: 2026-08-14
last_verified: 2026-08-14
supersedes: null
guidance_refs: ["docs/uploads.md#signing"]
confidence: high              # high | medium | speculative
---
```

**Body sections:**

```markdown
## Problem
What broke, observably. One paragraph.

## Root cause
Why. The part that took the time.

## Fix
What was changed, with the diff shape.

## What didn't work
Dead ends. Often the most valuable section — it's what stops the next
agent re-walking them, and it's the part every system forgets to record.

## Prevention
What would have caught this earlier. Feeds pattern promotion.
```

**Two tracks** (CE's terminology, adopted):

- **Bug track** — diagnosed defects. Requires `error_signature` where one exists; that's
  the highest-precision retrieval key you'll ever get.
- **Knowledge track** — conventions, decisions, workflow patterns. Requires
  `guidance_refs` (§6.6).

### 6.3 Capture

**Three triggers, no more:**

| Trigger | Fires when | Why |
|---|---|---|
| `debug_resolved` | `systematic-debugging` resolves a non-obvious root cause | The expensive knowledge is precisely here |
| `review_pattern` | `code-review` finds a *recurring* class, not a one-off | Patterns are worth writing; typos aren't |
| `manual` | You say "capture this" | Judgment beats heuristics |

**Not a pipeline stage.** CE makes `/ce-compound` a sixth step in every loop; that's how
you get either capture fatigue or, more likely, a step everyone skips — and a skipped step
is worse than an absent one because it makes the loop look complete when it isn't.

**Rules:**

- **One learning per run.** Batching produces mush that retrieves badly.
- **Check for overlap before writing.** Search existing learnings by tag and module first:
  - *High overlap* (same problem, cause, fix) → **update the existing doc**, bump
    `last_verified`. Two docs on one problem inevitably drift.
  - *Moderate* (same area, different angle) → write new, flag for `curate`.
  - *Low/none* → write new.
- **Bounded.** Capture is a paragraph-level activity. If it's taking a subagent fleet,
  something has gone wrong.
- **Refuse when there's nothing.** A session that solved nothing non-obvious produces no
  learning, and says so.

**Deliberately smaller than CE's.** Their `ce-compound` carries mode detection, depth
selectors, deprecated aliases, non-interactive contracts, write boundaries and a
frontmatter validator. Some of that is real (write boundaries matter when subagents are
involved). Most is the accumulated cost of making one skill serve every caller.

### 6.4 Recall — the hard half

**This is where these systems succeed or fail, and it gets more design attention than
capture.** Writing notes is easy. Having the next session surface the right one at the
right moment is the actual engineering problem.

**Index, not corpus.** The hook injects only an index — id, title, tags, module,
`error_signature` — roughly 25 tokens per learning. At 200 learnings that's ~5k tokens,
which is affordable. Full bodies load on demand. This is what makes the whole thing scale;
injecting bodies does not scale past about 30 learnings.

**Four recall points, each with a different key:**

| Point | Key | Effect |
|---|---|---|
| `/work` router | module + error signature | May reclassify the task's size |
| `/align` | module + spec keywords | Surfaces constraints during design |
| `/plan` | per-ticket module | Constraints land in the ticket that hits them |
| `systematic-debugging` | **error signature first**, then module | Highest-precision hit of all four |

**Precision over recall.** Surfacing three learnings, one of which is decisive, is useful.
Surfacing fifteen is noise the agent will skim and you'll learn to ignore — and once
you've learned to ignore it, the whole layer is dead weight. Cap surfaced learnings at
five per recall point and rank by: exact `error_signature` match > module match > tag
overlap > recency.

**Surface explicitly.** *"Two learnings touch this: X says the retry budget is per-host,
not global."* Silent conditioning is unverifiable and unfalsifiable — you can't tell
whether recall helped or the agent would have got there anyway, which means you can never
tune it.

**Recall failure is silent and therefore the most dangerous failure in the system.**
Nothing surfaces, the agent proceeds normally, you re-learn a thing you already paid for
and never find out you had it written down. Hence §9's dedicated recall evals.

### 6.5 Curate

Runs on demand, or on a cadence. Four jobs:

1. **Merge duplicates.** Two learnings on one problem → one, with the fresher context.
2. **Promote patterns.** Three-plus learnings sharing a root-cause shape → a pattern doc.
   Deliberate, never automatic: promotion turns an incident report into a rule.
3. **Decay.** Learnings past `decay_days` untouched get flagged, not deleted. A stale
   learning surfaced as current is worse than a missing one, because it's *confidently*
   wrong. The agent verifies against current code and either bumps `last_verified` or
   marks superseded.
4. **Guidance conflict check** — §6.6.

### 6.6 The guidance-layer conflict

**CE's sharpest single idea, and one I hadn't considered.**

The *guidance layer* is what an agent loads at the moment it acts: a skill's instructions,
`CONCEPTS.md`, `CLAUDE.md`, a runbook. A learning that contradicts guidance isn't merely
stale — **it will lose in practice**, because guidance is read at the moment of acting and
the learning is read at the moment of planning, if at all.

So a learning that disagrees with guidance it names is a *higher-severity* problem than an
ordinary stale note. `curate` handles it:

- Compare each learning only against guidance it explicitly names in `guidance_refs`.
  Comparing against everything is expensive and produces false positives.
- Resolve by **which side current code actually follows**. Code is the tiebreak.
- **Report a wrong guidance file; do not edit it.** Guidance is human-owned. An agent that
  silently rewrites the instructions it operates under is a system you can't reason about.

That last rule is worth stating as a general invariant: *the knowledge layer writes to
`.agent/`, never to the guidance layer.* `domain-modeling`'s `CONCEPTS.md` edits are the
one deliberate exception, and they're always visible in the diff.

---

## 7. The escape hatch

A specified feature, not an absence of enforcement.

| Tier | Skills | Override |
|---|---|---|
| **Default** | worktrees, review, debugging phases, capture | Say so. Complies without argument. |
| **Announced** | tdd outside scope, align for standard work | States what it's skipping and why, proceeds. |
| **Binding** | verification, tdd inside `tdd_scope` | Explicit override with a reason; logged. |

**On binding overrides:** the agent complies — you own the repo — but appends to
`.agent/overrides.log`. Not guilt. Data. If you override verification weekly, either
`commands.test` is wrong or `tdd_scope` is wrong, and the log is how you find out.

**Anti-nag rule:** once declined in a session, not raised again for that class of work.
Re-litigating settled decisions is the behaviour that makes people uninstall.

---

## 8. The hook

One hook, session-start, injecting context and nothing else.

**Injects:**

1. Skill index — name + description, ~40 tokens each, ~640 total.
2. `CONCEPTS.md` if present.
3. Learning index — ~25 tokens each (§6.4).
4. Pattern index — titles only.

Budget: roughly 1.5–6k tokens depending on repo maturity. If it exceeds that, `curate` has
work to do and should say so.

**Does not inject:** workflow mandates, "check for skills before every task," or any
instruction about how to behave. The index is a menu, not an order.

**Quiet on small diffs.** An agent that proposes a process for `git status` has already
lost you.

Superpowers' hook is the right mechanism with the wrong payload. Discovery yes, mandate no.

---

## 9. Evals

### 9.1 Trigger evals — every skill

Does it fire when it should and stay quiet when it shouldn't? Both halves matter; a skill
that fires on everything is as broken as one that never fires.

Run each prompt multiple times — triggering is stochastic and a single run tells you
nothing. Note that agents only consult skills for tasks they can't trivially handle alone,
so a trigger eval built on one-step prompts fails regardless of description quality. Use
substantive prompts.

### 9.2 Pressure evals — binding skills only

Does the rule hold when the agent is tempted? The step people skip, and where the value is.
Superpowers' `test-pressure-*.md` files are the model.

For `verification-before-completion`:

- User says *"just ship it, I'm in a hurry."*
- Suite takes four minutes; change is one line.
- Ticket 11 of 12, ten consecutive passes.
- Test fails for an apparently unrelated reason. ← *the interesting one, because correct
  behaviour is genuinely ambiguous, which is exactly what a pressure test should surface.*

Pressure-testing non-binding skills is wasted effort — you're happy to override them.

### 9.3 Router evals — the novel bet

The router is unproven and load-bearing. It needs a labelled corpus of ~50 real requests
with agreed classifications, scored two ways:

| Error | Cost | Tolerance |
|---|---|---|
| Over-classify (trivial → standard) | Ceremony on trivia — the failure this design exists to prevent | Low |
| Under-classify (large → standard) | Thin process on real work | Medium |

Asymmetric on purpose. Under-classification is recoverable — you notice and escalate.
Over-classification is what makes people quit, silently.

### 9.4 Recall evals — the other unproven half

Hardest to build and the most necessary, because recall failure is invisible.

Construction: take historical bugs from the repo's own git history. Write learnings for
the *earlier* ones. Present the *later* ones and measure whether the relevant learning
surfaces.

Metrics:

- **Hit rate** — relevant learning in top 5, when one exists.
- **Noise rate** — learnings surfaced when none is relevant. Directly predicts whether
  people start ignoring the recall block.
- **Decisiveness** — did the surfaced learning change what the agent did? Cheapest proxy:
  compare with and without recall on the same prompt.

A knowledge layer with a 90% hit rate and a 60% noise rate is worse than none, because
you'll stop reading it and lose the 90% too.

---

## 10. Failure modes

Catalogued because each maps to a specific mitigation, and because a design that only
describes its happy path is marketing.

| # | Failure | Symptom | Mitigation |
|---|---|---|---|
| 1 | Ceremony on trivia | Brainstorm for a null check | Router (§5.2), asymmetric eval (§9.3) |
| 2 | Skills never fire | Library installed, nothing uses it | Hook index (§8), trigger evals |
| 3 | Silent recall failure | Re-learning a known lesson | Recall evals (§9.4), explicit surfacing |
| 4 | Knowledge-base noise | Five irrelevant learnings per prompt | Cap at 5, precision ranking |
| 5 | Stale pattern as rule | Confidently wrong guidance | Decay flagging, `last_verified` |
| 6 | Capture fatigue | Nobody runs it | Three triggers only, never a pipeline stage |
| 7 | Verification theatre | "Tests should pass" | Binding + pressure evals |
| 8 | Config rot | `tdd_scope` describes a year-ago repo | Derive at init, revisit in `curate` |
| 9 | Escape-hatch friction | User fights agent, uninstalls | Tiered override, anti-nag rule |
| 10 | Index dilution | Triggering degrades as skills are added | 16-skill cap, `writing-skills` gate |
| 11 | Guidance contradiction | Learning loses to instructions silently | §6.6 conflict check |
| 12 | Autonomous drift | Long run ends far from intent | Verification per ticket, review before finish |

---

## 11. Non-goals

**No universal methodology.** TDD on a mature service is right; on a spike it's a tax.
`tdd_scope` exists because the repo knows which is which and the framework doesn't.

**No orchestrator chaining, no `/lfg` equivalent.** `/align` doesn't call `/plan`. A chain
you can't step into halfway is one you restart when anything goes wrong. Autonomy lives in
`/build`'s mode flag, bounded by per-ticket verification.

**No branch-local plan documents as primary state.** Tickets go to a tracker.

**No thirty-three skills.** Each addition degrades triggering for all the others.

**No automatic pattern promotion.** Promotion turns an incident into a rule; rules are
high-risk when stale.

**No agent edits to the guidance layer.** Report, don't rewrite.

**No hidden telemetry.** Opt-in if ever.

**One harness to start.** Superpowers ships ~12 and CE ships 14, which is a real reason to
pick them and a real maintenance burden. Starting narrow costs portability later; that's
an accepted trade, not an oversight.

---

## 12. Open questions

Listed because pretending otherwise would be worse.

1. **Does the router work?** The load-bearing novelty, unproven. If classification is
   unreliable you get failure mode #1 or #12. Gets eval attention first.

2. **Does recall clear the noise bar?** Failure mode #4 kills the knowledge layer quietly.
   CE has shipped this and their demo shows an 18-day-later hit, which is evidence it can
   work — but one demo isn't a hit rate, and I don't know theirs.

3. **Is `tdd_scope` maintained or abandoned?** Config requiring upkeep rots. Deriving from
   coverage at init helps; revisiting it in `curate` might.

4. **Do binding skills survive long autonomous runs?** Superpowers claims hours unattended.
   Whether a rule holds at ticket 30 with a degraded context window is empirical.

5. **Two binding skills — right number?** Verification and scoped TDD is the current bet.
   Code review has a plausible claim. Start at two, add only under evidence.

6. **When does capture's overlap check get expensive?** At 500 learnings, "search existing
   before writing" may need real indexing rather than tag matching. Unclear where the knee
   is.

7. **Learnings in `.agent/` or `docs/`?** CE uses `docs/solutions/` — visible, reviewable,
   in the PR diff. `.agent/` keeps them out of the way. Visibility probably wins for teams;
   `.agent/` wins for solo. Should be a config choice, and I haven't specified it as one.

8. **Does the three-tier model hold for teams?** Everything here assumes one repo, one
   person's judgment. Learnings written by one engineer and surfaced to another have a
   trust dimension this design doesn't address at all.

---

## 13. Build order

Each stage independently useful — which matters, because you may stop partway and that
should still leave you better off.

| Stage | Ships | Rationale |
|---|---|---|
| **1** | `init`, `verification-before-completion`, `tdd`, `code-review` | Highest value per skill. Useful with zero orchestration. No hook, no router. |
| **2** | `work`, `align`, `domain-modeling`, hook (skill index only) | Get the router under eval early. Vocabulary starts compounding. |
| **3** | `capture`, `curate`, recall points, hook (learning index) | Knowledge layer only after stages 1–2 are trustworthy — capturing learnings from an untrustworthy process bakes in bad lessons. |
| **4** | `plan`, `build`, `subagent-execution` | Autonomy last. It's the highest-risk mode and needs everything above it working. |
| **5** | `handoff`, worktrees, merge-conflicts, debugging | Ports and conveniences. |

**Stage 1 is four skills and no infrastructure** — already a defensible system, and
notably less than any of the three parents asks you to adopt.

**Stage 3 before stage 4 is deliberate.** CE's `/lfg` runs the full loop unattended and
captures learnings from it. Capturing from an unverified autonomous run is how you get a
knowledge base full of confident mistakes — failure modes #5 and #12 compounding each
other, which is the one failure here that gets *worse* over time rather than just staying
bad.
