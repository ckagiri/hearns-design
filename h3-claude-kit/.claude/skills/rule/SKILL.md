---
name: rule
description: Add a rule or a risk to the register, or look up what number a rule already has. Use whenever a new constraint, convention, failure mode or risk needs recording, or when the user says "add a rule", "what rule covers", "new risk", or cites a rule number.
argument-hint: [rule | risk] [what it says]
---

## Current highest numbers

!`grep -oE '^\| ([0-9]{1,3}) \|' docs/rules-and-risks.md | grep -oE '[0-9]+' | sort -n | tail -3 | tr '\n' ' '`
!`grep -oE '^\| R([0-9]{1,3}) \|' docs/rules-and-risks.md | grep -oE '[0-9]+' | sort -n | tail -3 | tr '\n' ' '`

## Task

$ARGUMENTS

**`docs/rules-and-risks.md` is the numbering authority. Check it before assigning a number.**
It has already resolved three collisions (rules 64–67, rules 91–96, risks R28–R30), and silent
reassignment is worse than a visible one.

### Before adding anything

1. **Search the register for an existing rule that covers this.** Most "new" rules are a
   restatement. If one exists, cite its number instead of adding.
2. Ask whether this belongs here at all. Three landing places, and there is no fourth
   (rule 133): edit a design document, write an ADR, or append here. If the thing being recorded
   is a decision — particularly a deletion — it is an ADR, and `/adr` is the skill for it.
3. Rule 63's second clause: **an addition must specify something being built now, or carry an
   explicit trigger.** A rule that does neither is elaboration arriving as a table row.

### Format

A **rule** is one line, imperative, in the section it belongs to. It states what is done, not why.
If it needs a paragraph to be understood, the paragraph belongs in a design document and the rule
cites it.

A **risk** carries three columns: the risk, stated as the thing that goes wrong; and its
mitigation *or detector*. Rule 62 applies — name the symptom, why it hides, and the detector, or
state explicitly that none exists. A risk with no detector and no acknowledgement that it lacks
one is not finished.

Bold the risks where every visible metric improves while the thing being measured degrades. Two
of the register's last six risks share that shape (R47, R50), and it is the metric set's known
blind spot.

### After adding

Append one line to the changelog at the end of the file: date, ADR where one exists, what moved.

### The standing question

This file is a live instance of R56 — 133 rules and 56 risks for a system that has not run.
Growth is not free just because it arrives as a table row. If you are adding at a phase boundary,
the more useful question is **which rules have never been consulted and which risks have never
been observed**. Rules 121 and 132 are the model for what to do about those.
