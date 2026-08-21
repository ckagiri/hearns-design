# `h3 state` — the state file is generated, not maintained

**Status:** proposal. This is `digest` (policy §1.1) with a concrete output and a reason to build it
earlier than planned.

---

## 1. The move

A hand-maintained `current-state.md` — checkboxes for what is built, a sprint focus section, a
technical-debt table — is a genuinely good artifact and the standard practice around agent-driven
projects. It is also **a report about the board, maintained by discipline.** Files like this
routinely carry a freshness command in the header telling you to check `git log` for when it was
last updated, which is an admission that it can drift.

In H3 the board *is* the state. So:

```
h3 state > docs/context/current-state.md
```

Three queries, rendered as markdown, committed on every successful integrate. **It cannot be stale,
because nothing maintains it.**

This is the clearest demonstration of the primary claim available. Not a diagram of a ledger — the
same file, generated, with a git history showing it evolve week by week, every line traceable to a
row.

---

## 2. The three queries

`digest` is already specified as three queries. These are the three, named:

**Q1 — what is built.** Cards in `done`, grouped by epic and story, with the commit sha and the
acceptance ref. This is the checkbox list, except each checkbox is a merged commit rather than
someone's memory of one.

**Q2 — where the work is.** Epics in `deps` order with status; per epic, story counts by status.
This is the sprint-focus section, and it is the same query that answers *what is the harness doing
right now.*

**Q3 — what is stuck and on whom.** Cards pending behind a `blocked` or `failed` ancestor, stories
in `awaiting_review`, open questions, and gap cards emitted by `done_with_concerns` but never
scheduled. This is the one that does not exist in the
hand-maintained version, because nobody writes down what they are blocking.

Q3 is the query the prototype plan already keeps despite cutting `digest` — it is the same query,
and building the other two beside it is most of a day rather than most of a week.

---

## 3. Output shape

```markdown
# Current state — todo
Generated from the ledger at 2026-08-21T09:14:02Z. Do not edit.

## Built

### E00 walking skeleton — done
- [x] S00.1 add and list                        `a3f9c21`  AC1, AC2

### E01 item lifecycle — running (2 of 3 stories)
- [x] S01.1 toggle done                         `7b2e004`  AC1
- [x] S01.2 rename item                         `0f3a91c`  AC2, AC3
- [ ] S01.3 delete item                         awaiting review

## Next
| Epic | Rank | Status | Blocked on |
|---|---|---|---|
| E02 views and filtering | 20 | draft | — |
| E03 persistence hardening | 10 | draft | E02 |

## Waiting on you
| What | Since | Detail |
|---|---|---|
| Review S01.3 | 40m | 3 commits, 112 lines |
| Question, E01 | 2h | Should rename preserve completion state? |

## Cost
| Epic | Cards | Attempts | Rung 0 | Rung 1 | Rung 2 | Verify | Killed by you |
|---|---|---|---|---|---|---|---|
| E00 | 1 | 1 | 0 | 0 | 0 | 0 | 0 |
| E01 | 7 | 9 | 1 | 3 | 0 | 2 | 1 |

## Commit shape
| Type | This week |
|---|---|
| feat | 11 |
| test | 11 |
| fix | 2 |
| chore | 1 |
```

The commit table is countable because types are derived from cards rather than chosen. `style`
should always read zero — formatting is rung 0's job, so a non-zero means the ladder is being
bypassed. `revert` should always read zero — a story killed at review never merged, so a revert
means something reached `main` that the review gate should have caught.

The rung columns are failure counts, read straight off `attempts.rung_results`. They are the reason
that column is per-rung rather than one blob.

**Breaking changes get a line under *Waiting on you*** — a card changed a symbol another epic
consumes, detected at rung 0 and never self-declared. It is a fact, not a rejection, but it is the
one fact you want in front of you before accepting a story.

Gap cards from `done_with_concerns` appear under *Waiting on you* as a count, never as a section.
They are ordinary backlog; a state file that starts curating them is writing a debt register.

**No prose, no interpretation, no technical-debt table.** Debt is a judgement and belongs in the
register or an ADR. A generated file that starts carrying opinions is a design document growing back
in a place rule 63 does not watch.

**The last table is the one that pays for the other three.** Attempts, failures by rung, verify
rejections and human kills per epic are the numbers that tell you whether the harness is working,
and they exist nowhere else without a query.

Two of its readings are immediate:

- **A rung that never fails is a deletion candidate.** A mechanism that has never fired is not
  evidence of anything, and this is the only place you would notice.
- **`rank` order matching topological order everywhere** means either the work is a genuine chain
  or the dependency graph is making product decisions nobody made.
- **Rung failures far outnumbering verify rejections** is the expected shape on a workload with a
  strong ladder. The inverse means either the ladder is thin or verify is inventing findings, and
  which one is a question you would not know to ask without the split.

---

## 3a. The module doc is half generated too

A per-module document — package structure, endpoints, service interface, dependents, implementation
status — is a good artifact. It is also **almost entirely derivable**, and every derivable fact that
is hand-maintained is a fact that will eventually be wrong. The characteristic drift: a status table
saying four stories are done while the interface listing below it still marks one of their methods
as planned.

The rule:

> **If a fact is derivable from the board or the code, it is generated. If it is a judgement, it is
> written.**

| Section | Source |
|---|---|
| Implementation status | the board — stories under this epic, with status |
| Package structure | `git ls-files` for the module, annotated from the board |
| Endpoints, service interface | parsed from the source |
| Depended on by | the import graph |
| Events published and consumed | parsed from the source |
| **Responsibility** | **written, one paragraph** |
| **Security considerations** | **written** |
| **Integration points with external systems** | **written** |

So `docs/context/modules/<module>.md` is a short hand-written header followed by a generated body,
emitted by the same harness operation that writes the state file. Navigation and orientation
documents — *what do I read to do X* — stay hand-written, because they are judgements about what
matters.

The check that keeps this honest: **a status marker nobody generated is a status marker nobody is
maintaining.** Anything with a ✅ in it should have been produced by a query.

---

## 4. Where it runs

Written on every successful integrate to `main`, as part of the same harness operation, in the same
commit or the one immediately after. Not a hook the workload can influence; not something a card can
write.

**A card must never be able to edit it.** If a card can write the state file, the file describes what
a model claimed rather than what the board holds, and the entire argument collapses. Add it to
`guard_invariants.py` alongside the ledger paths.

---

## 5. Why build it during the prototype

The prototype plan cuts `digest` as an anti-milestone — a dashboard before the queries are painful.
That reasoning is right about dashboards and wrong about this file, for three reasons:

1. **It is the demo.** A week of `git log docs/context/current-state.md` shows the project building
   itself. Nothing else in the system communicates the claim as fast.
2. **It is three queries, not a UI.** The anti-milestone guards against a rendering layer. This is
   `SELECT` plus f-strings.
3. **Q3 is already in the plan** and the other two are the same shape.

It lands on **day 7** of the pilot, at the head of part 2, because part 2 is where a week of history
accrues and a state file with one commit in it demonstrates nothing.

The thing it does not buy: any evidence the *harness* works. It is an observability artifact. Do not
let it substitute for Gate A, and do not build the tree renderer alongside it.

---

## 6. What would change this

- **Nobody reads it.** Then it is a demo artifact, not a working tool, and it should be honest about
  which — a demo artifact is still worth a day, but not a place to add sections.
- **It starts needing an argument to be readable** — if the raw three queries do not communicate
  without prose, either the board's vocabulary is wrong or the file is trying to be a report.
- **Somebody edits it by hand** — that is the mechanism failing, not a person misbehaving. Find what
  the file could not express and put it in a query.
