# ADR-0009: The split schema has a domain slot for `owns`

**Status:** Proposed, held until `tools/generate.py` is measured (`odoo-adaptation` §15 item 5). Until
then `odoo-adaptation` §3.1 and §8.5 stay as written, as a known exception to P1 and P2.
**Date:** 2026-11-03
**Would amend:** `odoo-adaptation` §3.1, §3.2, §8.5; `jigs-layers-skills-v2` P1 and P2 stay as written
**Guarded by:** P1 and P2; the second domain, when one exists

## Context

`jigs-layers-skills-v2` says a new jig is justified when the output schema differs (P1), and that
domain knowledge never lives in a jig (P2).

`odoo-adaptation` breaks both for `split`. §3.1 adds Odoo keys to each child's output
(`owns.xml_id_prefix`, `owns.models`, `owns.fields`), and §8.5 adds an "Odoo-specific decomposition"
section to the split jig's system prompt. By P1 that is a different schema and so a different jig. By
P2 the prose is misplaced. Read strictly, `split_odoo` already exists under the name `split`, and
kinds × domains is back.

Every other domain would hit the same point. Terraform has resources and modules, not external ids.

## Decision (proposed)

**The split jig's schema carries `owns` as a slot, and the domain supplies what goes in it.**

1. The jig declares `owns` and nothing about its keys.
2. The domain supplies a sub-schema for the slot, plus one overlap test per key: prefix for
   `xml_id_prefix`, set intersection for `models`, pair intersection for `fields`. The emit-time gate
   in §3.2 runs those tests. The commit-time extractors stay domain hooks, as they are now.
3. The sub-schema is substituted when the jig renders at pin time. The model still sees a strict
   schema, and because `output_schema(k)` hashes the rendered form, changing it moves `config_hash`.
4. §8.5's prose moves out of the jig by the placement test:

| Content | Goes to |
|---|---|
| Behavioural children are a test card then an implementation card | Layer 0: true in any domain |
| Contracts cite the anchor, never restate it (rule 89) | Layer 0: true in any domain |
| A child never edits a sibling's file | Layer 0: true in any domain |
| `spec/pharmacy.schema.yaml` is the authority | Layer 1: this repo |
| Never edit `__manifest__.py` or `__init__.py`; emit `spec_conflict` for a dependency | Layer 1: this repo |
| "Every child declares `owns.xml_id_prefix`…" | Nothing: the sub-schema now enforces it |

**Build only Odoo.** This is a dict of three overlap functions and one sub-schema, not a plugin
system. There is one domain, and an abstraction drawn from one instance is a guess.

## Alternatives considered

**A `split_odoo` jig.** Honest about what exists, and simple today. It costs a RED pass per domain
(`jigs-layers-skills-v2` §1.5), and it is §1.4's left-hand column, the only documented route to tens
of jigs.

**Leave it as is, and read P1 and P2 as guidance.** No work now. But those rules are useful because
they can be applied without judgement, and an exception on the first domain removes that.

**Free-form `owns` with no schema.** Loses output validation, and a model-authored key would then
reach a gate that does not know it.

**Keep the Odoo keys and treat them as generic.** Fails on contact with any domain that lacks external
ids.

## Consequences

**Good.** P1 and P2 hold. The jig's RED pass stays meaningful across domains, because the part under
test does not change.

**Costs.** Rendering gains a substitution step, and the emit gate gains one level of indirection,
for a benefit nobody collects until a second domain exists. That is the main argument for waiting.

**Open.** Whether `split` needs domain skills at all is `jigs-layers-skills-v2` open question 1. If
`generate.py` absorbs the structural half, much of `owns` may go with it, and this ADR shrinks or
disappears (R45). Run the generator experiment first if the order is a free choice.

## What would change our mind

- **`generate.py` covers the structural half** → `owns` may no longer earn its place. Re-derive this
  before building it.
- **A second domain's ownership cannot be expressed as keys with overlap tests** → the slot is the
  wrong shape, and `split` may genuinely be per domain.
- **The split jig still needs domain prose in layer 0 after this move** → P2 is wrong for `split`.
  Record that here rather than quietly keeping the prose.
