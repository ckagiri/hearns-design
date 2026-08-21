---
name: red
description: Capture an observed model failure into the RED corpus, verbatim, before any jig or skill is written against it. Use when a model got something wrong in a way worth remembering, or when the user says "capture this", "RED case", or is about to write a jig or a layer-2 skill.
argument-hint: [what the model got wrong]
---

## Corpus

!`ls -1 red/ 2>/dev/null | tail -10 || echo "(no red/ directory yet — create it)"`

## Task

Capture: $ARGUMENTS

**A jig with no RED pass behind it is untested, regardless of how many golden files it passes**
(policy §1.4). Golden files test the *shape* of the output; they do not test whether the jig
prevents the behaviour it was written to prevent. A jig shipped without a RED pass is worse than
absent, because it presents as coverage.

This skill does step 1 only. Do not write the fix in the same pass.

### What to record

Create `red/<kind>-<short-slug>.md`:

```markdown
# RED: <one line, what the model did>

**Card kind:** execute | verify | split | re_verify | integrate | digest
**Date:**
**Config:** model, effort, and what else was in context

## The scenario
<the exact input, minimally reduced. A scenario nobody can rerun is an anecdote.>

## What the model did
<VERBATIM. Paste it. Do not summarise, do not clean up, do not fix the typo.>

## How it justified itself
<VERBATIM. The rationalization is the more valuable half — it is what the eventual
rule has to negate by name.>

## Why this is wrong
<one paragraph, in your words>

## What would catch it
<a check, a hook, a schema constraint — or "nothing mechanical", stated plainly>
```

### The rules that govern this file

- **Verbatim means verbatim.** The value of the corpus is that it records what a model actually
  said, not what you remember it saying. Paraphrasing the rationalization loses the thing the
  rule has to negate.
- **The kind that failed is the kind that gets the skill** (rule 120). The label arrives with the
  observation; there is no design meeting later where you decide which bucket it lands in.
- **Every skill file ships paired with its RED case** (rule 120), because the pairing does three
  jobs: it assigns the kind, it supplies the ablation test, and it makes the skill removable.
  Without it the corpus grows by accretion and nothing records what any file was for.
- **A skill whose RED case no longer reproduces on ablation is deleted, not kept as margin**
  (rule 121).

### When you have twenty of these

Only then write the jig or the skill, and write the minimum that addresses the observed failures —
not the hypothetical ones. Then pressure-test with scenarios combining three or more pressures
that force a concrete choice with no option to defer. Each new rationalization that survives gets
an explicit negation in the rule, a row in the rationalization table, and a red-flag entry.

Roughly one jig ≈ twenty observed failures ≈ weeks of capture. That ratio is why the jig count is
bounded at six, not why it should be rushed.
