# ADR-0010: Retrieval triggers are properties of the card

**Status:** Accepted. The shape is decided; it is built only when a RED case asks for it.
**Date:** 2026-11-03
**Amends:** `jigs-layers-skills-v2` §3.2; policy §5.2; `retrieval.yaml` joins `skills.yaml` when first needed
**Adds:** rule 139
**Guarded by:** core §3.4 (no router); P5 and P6; per-set ablation (P3-5)

## Context

A real Odoo module spans Python, XML, JS, security files and migrations. Layer 2 is all-or-nothing per
kind, so an OWL correction placed there is read by every `execute` card, including those that never
touch JS. The cost is R50, not tokens. The corpus also cannot go there at any scale: the 114-file
marketplace skill is about 360k tokens, over 70 times the 4,910-token prompt in `worked-run-odoo`.

So knowledge narrower than a kind needs another route, and the documents disagree about it:

- `jigs-layers-skills-v2` §3.2 says narrowing per card requires "a model call or a heuristic that
  drifts from card content", and calls that the deleted router returning.
- `PROTOTYPE_v3` §9 allows retrieval triggered by a card property, "derived from the board, not chosen
  by a model", and the sketch's §Skills makes it the first lever.
- Policy §5.2 describes named-risk retrieval, but only as something a card cites.

Only one example has ever been described, a Postgres-fixture skill. Nothing specifies the mechanism.

## Decision

**The harness adds a file to layer 6 only from a table in config, on a trigger that is a property of
the card's row.**

```yaml
# harness/config/retrieval.yaml — written by hand at pin time
execute:
  - when: {touch_set: "static/src/**/*.js"}
    load: knowledge/owl-corrections.md
    risk: owl-lifecycle
  - when: {touch_set: "security/**"}
    load: knowledge/acl-vs-record-rules.md
    risk: access-confusion
  - when: {touch_set: "migrations/**"}
    load: knowledge/migration-corrections.md
    risk: data-loss
```

1. **Triggers read declared fields only:** `touch_set`, and `owns` if ADR-0009 lands. Never the intent
   text, never the contract's wording, never a model call.
2. **It is keyed by kind**, so a `verify` card does not inherit `execute`'s table. `verify`'s stays
   the shortest (P7).
3. **The table and each file's hash enter `config_hash`.** Same pin, same row, same prompt, so replay
   holds.
4. **Every row names its risk**, and each firing is recorded with it. That answers *which cards
   retrieved what and why* as a query, and meets §5.2's rule that retrieval cites a risk.
5. **Each file obeys the skill rules:** paired with a RED case (P5), deleted if ablation stops
   justifying it (P6).
6. **A check comes first.** Knowledge that can be a rung or a generator becomes one. `sudo(` is a rung
   0 check, not a paragraph.

**Why this is not the router.** Core §3.4 deleted the router as a role and kept routing as a lookup: no
model call, inspectable in SQL. This table has the same shape, applied to what a card reads rather than
who claims it, and it adds no model's choice. §3.2's objection is drift between the
heuristic and what the card does, and a touch set cannot drift that way: it is enforced at commit, so
a card that strays outside it fails. §3.2 now names model calls and content heuristics
specifically.

Model-requested retrieval (`deps`' "retrieve only with a named risk") is a separate path and does not
change.

## Alternatives considered

**A broad `execute` set.** Simplest, but it runs into R50 and cannot hold the corpus.

**More kinds: `execute_py`, `execute_xml`, `execute_js`.** Static and hashable, and listed as lever 2
in the sketch. Halving a kind's population halves its cache amortisation, and framework gravity means
real cards cross these lines. Keep it for when bifurcation proves structural.

**A model that chooses, like `odoo-skill-finder`.** Rejected in §3.2 and still rejected: it breaks
replay, and it is the router by any reading.

**Do nothing until it hurts.** Reasonable for the twelve-card prototype, where `skills.yaml` starts
empty. It should not be built before a RED case asks for it. This ADR fixes the shape so the first one
has somewhere to go.

## Consequences

**Good.** The library can grow while each card reads a little. `verify` and unrelated cards pay
nothing. Policy §5.2's detector, retrieval with no named risk, gets something to detect.

**Costs.** Layer 6 is per card and uncached, so a file fired on many cards is paid many times; if a row
fires on nearly every card it belongs in layer 2. It is one more config file in the hash.

**The real weakness.** The touch set is written by the splitter, so a model still influences the
trigger indirectly. It is fixed on the row before claim, so it is recorded and replayable, but a
splitter that names the wrong files gets the wrong knowledge. Framework gravity makes this likely in
Odoo, where a Python card can depend on view semantics it never touches.

## What would change our mind

- **Ablation shows retrieved files change no output** → delete the table, and the corpus with it.
- **Cards fail for want of knowledge whose trigger did not fire** → touch sets are too coarse. Fix the
  trigger field, or promote the file to layer 2. That failure is its RED case.
- **Most rows fire on most cards** → the table is a slow layer 2, and kinds may need splitting.
- **Someone adds a trigger that is not a declared field** → that is the router. Reject it, or supersede
  this ADR openly.
