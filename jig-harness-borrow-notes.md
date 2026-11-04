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

## Verdict

Borrow the ideas, but don't run `drive-pr` or the dispatcher yet. Revisit once other teams use them
and its issues #399–#403 are closed.
