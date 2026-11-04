# Harness — document index

**Last updated:** 18 August 2026.

A Postgres ledger of work cards and stateless workers that claim them. The board is the only place
state lives; no component holds a plan.

**Purpose of the first build:** learning the substrate, and a queryable record of what was decided
and why across many runs of one long-lived project. Production superiority over a controller-based
tool is a *secondary* hypothesis, tested at step 7. A negative result there does not end the
project.

**Shape:** a helper, not an unattended system. Human gates on the critical path are expected.

---

## Read in this order

**New to it — 40 minutes.**
`harness-core-v3` §1–2 → `worked-run-odoo` → `harness-policy-v3` §10.
Purpose, then one concrete run end to end, then the honest positioning against the alternative.

**Building the substrate.**
`harness-core-v3` → `001_initial.sql` → core §12's build order → Gate A (core §11.1).
Nothing above that line needs a model call to test.

**Working on Odoo.**
`odoo-adaptation` → `pharmacy.schema.yaml` → `worked-run-odoo`.

**Writing jigs.**
`harness-policy-v3` §1.4 → `jigs-layers-skills-v2` → the jig templates.

---

## Live — build from these

| File | Lines | What it holds |
|---|---|---|
| `harness-core-v3.md` | 852 | **The substrate.** Board, predicate, claim, lease, fencing, reaper, workspace, replay, observability. Settled — nothing in five review documents argued with it. |
| `harness-policy-v3.md` | 863 | Roles, decomposition, verification, tiering, effort, context, experiments, positioning, **the card runtime**. **Contested** — ⚖ marks a live axis with a deciding experiment. |
| `odoo-adaptation.md` | 1,113 | The domain instantiation: conventions, namespaces, check ladder, the schema anchor, workspace mechanics. |
| `jigs-layers-skills-v2.md` | 511 | How many jigs, what goes in which layer, how skill sets are chosen and pruned. |
| `change-register.md` | 365 | **Numbering authority.** Rules 1–130, risks R1–R53, the data-model diff, the sequenced action list. |
| `001_initial.sql` | 230 | The Phase 1 migration. **Reconstructed** 2026-11-04 from these documents after the 330-line original was lost; its header marks what is inferred. |
| `harness/ledger/sql/`, `queries/` | — | **Drafts.** Ledger statements transcribed from core §5 where core has them, and the query catalogue. |

**Core is settled; policy is not.** That asymmetry is why they are separate files. Every policy
section carries *what would change it*; core carries the same list once, in §13, because it is
expected to be short.

## Decisions of record

| File | Decides |
|---|---|
| `adr/0001-decided-paired-with-open-questions.md` | Commission drift is surfaced by a paired signal. **Frame widened**: diff-reading verify added as an alternative and a mind-changer; `closed_by` added after a false positive. |
| `adr/0002-judge-not-adopted.md` | `judge` is deleted, not deferred. Ties are recorded human rulings. |
| `adr/0003-enforcement-collapsed-notification-absent.md` | Enforcement is isolation plus host-side hooks. Notification is absent. Both with named reopening triggers. |
| `adr/0004-card-runtime-below-the-boundary.md` | A library runs the card's tool loop, below the card boundary and nothing above it. The cache is its model interface. Scoped by what it excludes. |
| `adr/0008-kind-role-and-jig-have-one-job-each.md` | Each kind has one jig, each kind and tier one role. Tools on the jig, checks in `checks.yaml`, hash per kind and tier. Behavioural is not a kind. |
| `adr/0009-split-schema-has-a-domain-slot-for-owns.md` | **Proposed, held** until `generate.py` is measured. Odoo's `owns` keys move out of the split jig into a domain slot. |
| `adr/0010-retrieval-triggers-are-card-properties.md` | Knowledge narrower than a kind reaches layer 6 from a hashed table, triggered by declared card fields. Built when a RED case asks for it. |
| `adr/0011-what-a-workspace-or-provider-failure-costs-a-card.md` | Provisioning failures are free up to a ceiling, a failure no retry can fix halts the run, and worktrees are per attempt. Amends ADR-0007. |
| `adr/0012-command-output-is-normalized-before-the-model-sees-it.md` | Anything a command produced is normalized before the model can see it. Replay re-executes tools. Narrows what the cache buys a retry. |
| `adr/0013-what-a-card-must-show-to-reach-done.md` | The oracle decides `done`, and the database enforces it. Core's six states stand, a misclassified card becomes a `split` on its own row, and only evidence about the work changes what a retry sees. |
| `adr/0014-what-the-host-trusts-and-what-the-record-keeps.md` | Host git ignores the worktree's `.git`, an attempt records what the card was, and replay reproduces provider failures. The container mask is untested, and nothing depends on it. |

An ADR exists so a deletion keeps its argument. Without one, a removed section is just a gap that
grows back.

## Reference — read, do not edit

| File | Use |
|---|---|
| `worked-run-odoo.md` | One run traced end to end, happy and unhappy paths, with a mechanism audit of what actually fired. The fastest way to understand the system. |
| `worked-run-catalog.md` | The same treatment for the catalog exercise project. Second instance of the type, not a new document type. Shows the INV-DRUG-01 specimen, a reap with a stale writer, and one residual that nothing caught. |
| `pharmacy.schema.yaml` | A worked anchor. Shows what the schema can and cannot express. |

## Archive — provenance

`harness-design-v2.md` (split into core and policy) · `superpowers-findings.md` and `-2.md`
(absorbed into the register) · `store-and-lessons.md` (absorbed into core §4) ·
`jigs-layers-skills-v1.md` (superseded by v2).

Keep them. When someone asks in a year why `judge` does not exist, the full argument is in
findings-2, not in the register's one-line summary.

---

## Conventions

**Numbering.** The register is authoritative for rules and risks; it has already resolved one
three-way collision. **Check it before assigning a number.**

**Cross-references.** `odoo-adaptation` uses v2 section numbers with a legend at its head. Core,
policy and the ADRs use `core §x` / `policy §x` explicitly.

**Rule 63 still applies.** Findings go into an existing document, an ADR, the register, or code.
Not into a new design document.

**⚖ means undecided.** A config axis with a named experiment beside it, not a choice already made.
Baking an unmeasured decision into prose is how v2's compounding-fidelity argument became
load-bearing without evidence.

---

## Where things stand

**Settled and unlikely to move:** the substrate. Content-derived ids, the readiness predicate,
fencing, kill-before-requeue, the workspace triple, the cache as the determinism mechanism.
**Added 17→18 August:** one reaper rather than a watchdog chain — core §5.4 now states why, and
records R57 as the residual it does not cover.

**Decided but unmeasured** — these are the ⚖ sections, and the experiments that close them are in
policy §7 and register §7:

- Verify's input: summaries versus the card's diff (E2 arm D).
- Depth: shipping flat until a per-level fidelity rate is measured.
- Layer 2 sizing: whether a pinned skill set narrows attention (R50).
- Effort: whether reasoning suppresses refusal (R47, E2 arm C′).
- Whether the structural half needs a model at all, or a generator absorbs it (R45).
- Tool-set width: whether a narrow per-kind set changes behaviour or only price (policy §1.6).

**Added 18 August:** policy §1.6 — the card runtime. §1.5 acknowledged the tool loop; nothing
specified it. Now owned, with the adoption in ADR-0004 and two residuals recorded (R60, R61).

**Known to have no proof:** R44 — the schema anchor is the only artifact with nothing beneath it to
catch a mistake. Two independent drafts and a diff is the only mitigation, and R48 says it works
only if the drafts vary by model or effort rather than by seed. **Test that first; it is an hour.**

**Weakened 18 August:** policy §10's differentiator list is down to one — the record. Parallelism was
removed after the current comparable turned out to have it. Step 7 now has no fallback claim, which
raises the stakes on the primary hypothesis rather than on the secondary one.

**Before Phase 1**, five validation items in register §7, none needing the harness to exist. They
decide whether the design is right, and four of the five produce artifacts you want regardless.
