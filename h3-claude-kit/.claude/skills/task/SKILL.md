---
name: task
description: Start a work item from the project breakdown with its design context and exit criteria loaded. Use when beginning a task with a phase ID like P1-3 or P0-8, or when the user says "let's do", "start on", or "next task".
argument-hint: [task ID, e.g. P1-5]
---

## Where things stand

!`git log --oneline -5`
!`git status --short`

## Task

Start work item: $ARGUMENTS

### Step 1 — establish the contract before writing anything

Read the row for this task in `docs/h3-project-breakdown.md`, then read **the design sections it
cites** — not the summary in CLAUDE.md. Then state back, in four lines:

- What this task delivers, in one sentence.
- Which design sections govern it (`core §x`, `policy §x`, rule numbers).
- Its exit criteria, quoted from the breakdown.
- What it explicitly does not include.

If any of those four is unclear, ask now. A model handed an ambiguous instruction does not stop
and ask — it resolves toward the modal answer, confidently. That failure mode is the one this
whole project is built around, so it is worth spending a question on.

### Step 2 — plan before editing

Use plan mode for anything touching the ledger, the reaper, the workspace triple, or the config
hash. Those four are where a wrong assumption is expensive and where the design is most specific.

The plan names: the files, the SQL, the tests, and — for a mechanism — **its detector**.

### Step 3 — test first where the behaviour has a stateable semantic

Write the test, confirm it **fails**, and only then implement. The implementing step must not be
able to edit the test. Use the `test-first` subagent for this if the boundary matters; it is
blocked from writing outside `tests/`.

This is the one mechanism in the worked run that caught the specimen five others passed. Treat it
as load-bearing rather than as ceremony.

### Step 4 — done means

A task is done when it has:

- a test that fails without the change,
- a **named detector** for the failure it prevents (rule 62) — or an explicit statement that none
  exists,
- for a mechanism: an answer to *has it fired?* (principle 8),
- `uv run ruff check`, `uv run mypy harness` and `uv run pytest` green.

### Standing cautions for this repo

- If the work seems to want a mechanism the design does not name, stop and say so. Do not add it
  and mention it afterwards. Version 1 of this design failed by elaboration; that is the failure
  mode with the highest base rate here.
- If the design document is wrong, say that too — that is a legitimate finding and it lands as an
  edit or an ADR, not as a workaround in code.
- Prefer the cheapest mechanism that can do the job. A hook beats a card; a SQL check beats a
  model call; a schema constraint beats a convention.
