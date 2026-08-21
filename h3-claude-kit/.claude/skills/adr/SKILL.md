---
name: adr
description: Write an architecture decision record in this project's house format, especially for a deletion. Use when a decision needs to be recorded, when a section is being removed, or when the user says "ADR", "record this decision", or "we're deleting X".
disable-model-invocation: true
argument-hint: [short title of the decision]
---

## Existing ADRs

!`ls -1 docs/adr/ 2>/dev/null || echo "(no docs/adr directory yet)"`

## Task

Write an ADR for: $ARGUMENTS

**An ADR exists so a deletion keeps its argument.** Without one, a removed section is just a gap
that grows back. If this decision is not a deletion, it still needs the same shape — a decision
whose reasoning is not written down gets relitigated.

### Before writing

1. Read the sections being amended. Name them precisely (`core §x`, `policy §x`, or a v2 section
   number where `odoo-adaptation` uses those).
2. Check `docs/rules-and-risks.md` for rules or risks this decision voids, amends or creates.
   That file is the numbering authority and has already resolved three collisions.
3. Take the next number in sequence from the listing above.

### Format — follow the existing ADRs exactly

```
# ADR-NNNN: <one-line statement of what is decided, not what was discussed>

**Status:** Accepted (a deletion) | Accepted | Accepted, frame widened <date>
**Date:** YYYY-MM-DD
**Supersedes:** <document and section, or —>
**Guarded by:** <the detector, experiment, or reopening trigger that makes this checkable>

## Context
## Decision
## Alternatives considered
## Consequences        (Good / Accepted costs / Follow-on work required)
## What would change our mind
```

### The two sections that carry the weight

**Alternatives considered.** Each alternative gets its real argument, not a strawman, and an
explicit disposition: rejected, deferred as the fallback, or *adopted*. Where an alternative was
considered seriously and rejected, say what would have made it right.

**What would change our mind.** Each entry names an observation, not a feeling. "If X is measured
at Y, this decision is revisited." A trigger that cannot be observed is not a trigger. If a
deletion is being recorded, this section must name the incident that reopens it — and state that
it does not reopen on the grounds that it would be more complete.

### House rules for this document

- Deferred is not a state a design can hold. Write "absent, not deferred" and mean it.
- If the decision has no detector, say so plainly in Consequences under "Accepted costs" and
  mark it as a residual (rule 62).
- Record evidence separately from costs. What a worked run showed is evidence *about* the
  decision, not a cost *of* it.
- Do not soften. These documents are read a year later by someone deciding whether to reverse
  the decision, and hedging is what makes that person guess.

### After writing

- Edit the affected sections of `harness-core-v3.md` / `harness-policy-v3.md` /
  `odoo-adaptation.md` in place — the ADR names what it amends, and the edits go in the files.
- Add the one-line entry to the changelog at the end of `docs/rules-and-risks.md`.
- Add a row to the "Decisions of record" table in `README.md`.
- Mark superseded rules with **→** and a pointer rather than deleting them.
