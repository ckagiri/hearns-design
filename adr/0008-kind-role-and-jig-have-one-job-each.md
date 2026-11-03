# ADR-0008: Kind, role and jig have one job each

**Status:** Accepted
**Date:** 2026-11-03
**Amends:** policy §1.3, §1.4, §1.6, §2.0, §2.1, §5.1; core §3.1, §3.4, §8.1.1; `odoo-adaptation` §4, §7,
§8.1, §9, §10.1; `jigs-layers-skills-v2` §1.3, P2 and open question 5; `PROTOTYPE_v3`'s templating
note; `files/PILOT.md`'s ladder example; rules 68, 117, 126 and 135
**Adds:** rules 136–138
**Guarded by:** startup config validation; the emit-time role check; core §11's hash-stability tests

## Context

The documents described the same four concepts differently, and nothing had been run that would
expose it:

- A jig was "bound per kind" in policy and core, but the sketch gave a role one jig and a list of
  kinds. `worked-run-catalog` ran `verify` and `re_verify` through one role, although policy gives
  them different outputs and different effort.
- The tool set sat on the role in the catalog and rule 135, on the jig in the sketch, and was hashed
  per kind in core.
- Layers 0 and 3 were role-scoped in policy and kind-scoped in `jigs-layers-skills-v2`.
- `kind_hash(k)` included `model(k)` and `effort(k)`, which are not functions of a kind: `execute`
  runs on three models.
- Checks lived in the jig (`passive`, `check`), by kind (`check_definitions`), and on the card
  (`check_spec`). Layer 8 listed rung definitions while `odoo-adaptation` §4 said rung 0 is hidden.
- "Behavioural" appeared as a jig name (`execute_behavioural`), as a row in the effort table, and in
  `odoo-adaptation` §8.1 as something that should not share a kind with structural work. Policy §2.1
  has three contract shapes and behavioural is none of them.

The catalog also shows the cost. Its cards `.5` and `.7` are `execute` at `middle` tier and its
config has no role claiming that pair, so as written they would stay `pending` forever.

## Decision

**A kind says what type of work a card is. A role says who claims it and how hard they try: model,
effort, lease, parallelism. A jig says how the work is done: prompt, tools, output schema, allowed
outcomes. A skill says what domain facts to know.**

1. **Each kind has exactly one jig. Each kind and tier is claimed by exactly one role. Every kind in
   a role shares that role's jig.** Validated at startup. More capacity is more processes on the
   same role, never a second role (rule 136). The role table is policy §1.3.
2. **A card whose kind and tier no role claims is rejected at emit time.** Startup validation cannot
   see this, because tiers are chosen by the splitter at run time (rule 136). Retries cannot strand a
   card either: a kind's tier ceiling is the highest tier a role claims for it (rule 68).
3. **Tools live on the jig**, and rule 135 reads per kind. Whether a card may write is a property of
   the work, not of the model doing it. ADR-0004 and ADR-0005 say "per role"; they are records of
   their decisions and are not rewritten, so read them as per kind.
4. **Layers 0 and 3 are kind-scoped.** Both now come from the jig, which closes
   `jigs-layers-skills-v2` open question 5.
5. **`config_hash` is per kind and tier**, and a role may fill a jig slot, so the rendered template
   is hashed the same way (rule 126). A retry that raises the tier moves the hash with it. The raised
   effort on attempt 2 reaches the cache key, not this hash.
6. **Check definitions live only in `checks.yaml`.** A jig names no command, a card's `check_spec`
   picks the rungs, and layer 8 renders only rungs marked visible. The hash still covers hidden
   rungs, because they decide outcomes (rule 137).
7. **For `execute`, tier and effort follow contract shape alone.** `split` and `verify` still tier on
   how far a mistake propagates (policy §2.1). Whether a card needs a test is a separate question,
   answered by `check_spec`. A behavioural card is an ordinary `execute` card: its test
   card has `expect: FAIL` and its implementation card has `expect: PASS` (rule 138).
8. **Values.** `re_verify` gets its own role. `execute_middle` is added. `verify` has
   `verify_middle` for summaries and `verify_strong` for diffs until E2 arm D decides whether both
   survive. `integrate` is sonnet at minimal effort and `digest` is sonnet at middle tier, because a
   human acts on the digest. `preflight` has no role until E1 justifies it, and `spec_revision` has
   none while a human writes it.

## Alternatives considered

**One jig per output schema, with kinds free to share.** This was the first recommendation. It says
nothing about a role with one effort serving two kinds that need different effort, which is what the
catalog's `verify` role does.

**Key the jig off the card, as skills are: `JIGS[task.kind]`.** Lets one role serve kinds with
different jigs. It saves a few lines of config and costs the simple answer to *what does this worker
do*, and a role's single effort would still force the split in the case that matters.

**Tools on the role.** Matches rule 135's wording and allows a cheap executor with fewer tools than a
strong one. Nothing wants that yet, and it would make tool-set ablation depend on tier. Reopen below
if it appears.

**A `behavioural` kind, or a field on the card.** A kind doubles the jig count or splits cache
amortisation for no change in output schema, which fails P1. A field would restate what `check_spec`
already says, and a second source of truth drifts.

## Consequences

**Good.** Each question about a card has one place to look. Config validation catches the catalog's
stranded cards before a run, or at emit time during one. Hash comparisons mean what they claim.

**Costs.** Rule 135's wording changes after ADR-0004 and ADR-0005 cited it. There are nine roles
rather than six, though most differ only by tier.

**Left stale on purpose.** `worked-run-catalog` and `worked-run-odoo` are marked read-do-not-edit and
record a paper run. Their role config, tools, pin and layer tables predate this ADR. Where they
differ, policy §1.3 and §2.0 win. `opendev-assessment` and `opendev-port-notes` also keep "per role"
as written at the time.

**Open.** Odoo's structural verify reads a third input, rung 3's diff, and no role claims it yet. One
role per kind and tier means the input has to follow the tier, so it gets `verify_cheap` once
`odoo-adaptation` open question 2 confirms cheap is enough. If it does not, this is reopened: running
it at middle would need a second input for one role.

**Not measured.** Like everything in these documents, this is derived rather than observed. None of
it has run.

## What would change our mind

- **A kind needs different tools at different tiers** → tools return to the role. The hash is already
  per tier, so nothing else moves.
- **E2 arm D settles verify's input** → one `verify` role goes.
- **Contract shape fails to predict turn count** (policy §2.1) → tiering falls back to card shape, and
  point 7 is reopened with it.
- **A check cannot be expressed as a rung** → the single home for checks was too strong.
