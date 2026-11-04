# Jig Harness — ideas worth borrowing

**Subject:** `github.com/jig-harness/jig`, Apache-2.0 with MIT-0 templates, TypeScript. Read at commit
`d9740470`, version 0.127.1, dated 2026-11-03. Written 2026-11-03.

**Not this repo's jigs.** The shared word is a coincidence: this is an outside project, and nothing
here refers to the jigs in `jigs-layers-skills-v2.md`.

**Basis.** Its docs and measurements of the repo. The `drive-pr` code was not reviewed and nothing
was run.

---

## Worth borrowing

- **Three gate outcomes.** A gate can pass, find violations, or report "could not check" (exit 0, 1
  and 2). A renamed folder or a failed command then can't silently turn a check green. See its
  `modules/M1-gates-enforcement-ladder/`.
- **Self-pruning exceptions.** An allowlist entry fails the gate once it no longer suppresses
  anything, so allowlists can't quietly grow stale.
- **An audit that changes nothing.** `/jig:audit` scores a repository with file-path evidence, and a
  person decides what to act on.
- **Drive state on the PR.** A review loop keeps its state in a ledger on the pull request, so
  another machine can resume it if the driver dies.
- **Low-risk setup.** The plugin loads no packages at run time, and the templates are MIT-0, so they
  can be copied with no notice.

## Worth borrowing from its glossary

Read from `GLOSSARY.md` at commit `986c1f70`, dated 2026-11-04. The glossary only defines terms, and the
modules behind them were not read. Gaps were checked against this repo's design docs and sketch by keyword
search, so "not found" is not proof of absence. Nothing here has been run.

**Likely gaps**

- **Skip tripwire.** A check fails if it ran zero tests. Rule 145 stops a `check_spec` that selects no
  rungs, but `run_oracle` in `jig-sketch.py` reads only `r.ok`, so a rung that runs no tests and reports ok
  returns `passed`, and the card reaches `done`.
- **Fresh-base probe.** Rerun a failing test on the base before blaming the change. No failure class for an
  already red base was found, so each card would be charged `check_failed`. This works only for tests
  that already exist on the base, since new ones are expected to fail there.
- **Cause fingerprint and flood breaker.** Give each failure a stable identity (check, scope, normalized
  signature), and stop repeat alerts after N failures from one cause. Only confirmed recovery resets it, not
  silence. This fits R63, and is more precise than ADR-0011's "failures span unrelated cards" breaker.
- **Evidence record.** Keep the command, exact tree, exit code and test counts for each check, and treat a
  later edit as voiding it. `task_attempts` has `check_ref` and `diff_ref`, but nothing records which tree
  was checked, or any counts. `tasks.result_sha` may cover part of this. When it is written was not traced.
- **"Avoid" lines.** Each glossary term names the rival words not to use. This repo has no glossary, yet
  ADR-0008 exists because the docs described one concept differently, and ADR-0002 and ADR-0003 removed
  `judge` and `Relay` from the vocabulary.

**Smaller**

- **Framed decision.** A shape for the `refusal` payload: the question, options with costs, a
  recommendation, and what was already done.
- **Tally versus constraint.** A test for which numbers in prose will drift.
- **Dead-man's switch.** An alarm if the reaper itself stops, once runs are unattended.

**Already covered here**

- Could not check: `unavailable`.
- Fencing: `attempts`.
- Wall: `halted_class`.
- Mutation check: R2 and the policy's oracle mutation tests.
- Reopen condition: roughly each ADR's "What would change our mind".

**Keep this repo's words.** The same words mean something else there: `rung` is a step of its enforcement
ladder, `tier` a model or deploy tier, `kind` a code-stats dimension, and `park` is reserved for human
decision classes. `card` is on its list of words to avoid, in favor of "issue".

## Verdict

Borrow the ideas, but don't run `drive-pr` or the dispatcher yet. Revisit once other teams use them
and its issues #399–#403 are closed.
