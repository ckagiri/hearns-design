# Odoo Adaptation

**Status:** adaptation of `harness-core-v3` + `harness-policy-v3`, not a new design document (rule 63).
Every section names what it amends, adds to, or constrains.
**Target:** a small-pharmacy Odoo module, first real application, ~12–18 months out.
**Companion documents:** `change-register` (rules and risks), `worked-run-odoo`, ADR-0001.

**§-references in this document use `harness-design-v2` numbering.** v2 has since been split into
core and policy; the legend below maps them. Inline rewriting was attempted and reverted — the
numbers are load-bearing in dozens of places and a legend is safer than eighty edits.

| v2 § | Now in |
|---|---|
| §1.1–1.3 purpose, principles | core §1–2 |
| §3.4 absent roles | core §3.4 |
| §4.1 task schema · §4.3 content · §4.5 notes | core §4.1 · §4.3 · §4.5 |
| §5.1 predicate · §5.4 reaper · §5.5 fencing · §5.6 heartbeats · §5.7 commit | core §5 |
| §6.2 roles · §6.4 tiering | policy §1.3 · §2 |
| §7.1–7.5 decomposition | policy §3 (§7.6 `judge` → ADR-0002) |
| §8.1 refusal · §8.3 drift and verify · §8.4 gate depth | policy §4.1 · §4.2 · §3.1 |
| §9.1–9.4 context layers | policy §5 |
| §11 repository work | core §6 (the workspace triple) |
| §12 human gate | core §7 |
| §13 enforcement | policy §6 (§13.3–13.7 deleted → ADR-0003) |
| §14.2 config pin | core §8.1, §8.1.1 |
| §15.2 metrics · §15.4 digest | core §9.2 · §9.3 |
| §16 failure modes | core §10 (substrate) · policy §9 (policy-level) |
| §17.1 three problems · §17.3 jig testing · §17.4–17.5 static | policy §7 · §1.4 · core §11 |
| §18.1–18.3 experiments | policy §7.2–7.4 |
| §19 root intents | policy §8 |
| §20.1 Gate A · §20.3 step 7 · §20.4 anti-milestones | core §11.1 · policy §10 · §11 |

---

## 0. Read this first

**The claim this document makes.** Odoo is not a convenient first application. It is the *right*
one, for a reason internal to the design: §8.3 says that if commission drift cannot be caught from
summaries, the honest response is to apply the architecture to domains where leaf checks carry
semantic weight. Odoo has such a check, and it is cheap. Module installation is a semantic gate —
a view referencing a field that does not exist fails the load, not a test — and the ORM registry is
introspectable, so a declared schema can be diffed against reality with no model call.

**The claim it does not make.** That property covers **structure**, not **behaviour**. Roughly half
a pharmacy module — dispensing rules, expiry and batch logic, controlled-substance access, the
prescription state machine — is behaviour, and introspection is blind to all of it. That half is
where the module's real risk lives, and it is where the harness has to earn its keep the hard way.
§8 of this document splits the work along that line and treats the two halves as economically
different.

**What is free and what is expensive.** Most of what follows is *convention* — file layout, naming,
a generated manifest — and costs nothing but discipline. A smaller part is machinery: the
introspection oracle, the workspace triple, the namespace checks. The conventions are worth adopting
even if the harness is never built, because they are what make an Odoo module splittable by anything,
including a human.

**Where to start.** §2 and §3. They unblock §7.4, which is otherwise unusable in Odoo, and they can
be validated on a throwaway module in an afternoon — long before Phase 1.

---

## 1. Why Odoo, stated as an argument rather than a preference

### 1.1 The three properties that matter

**Installation is a semantic check.** `odoo-bin -i <module> --stop-after-init` fails on: a view
field that is not on the model, an xpath that matches nothing, an ACL row naming a model that does
not exist, a group external id that was never defined, a `_inherit` on an absent model, a domain
referencing an unknown field, a broken `related` path. None of these are caught by "the code runs."
All of them are caught in one command, in seconds, with no test written.

This is the check §8.3 calls semantically weighty: passing means the thing is *right* in a
structural sense, not merely that it executes.

**The registry is introspectable.** After install, `ir_model`, `ir_model_fields`,
`ir_model_access`, `ir_ui_view`, `ir_rule`, `ir_act_window` and `ir_model_data` describe what the
module actually built, in SQL. A declared schema can be diffed against that. Spec-conformance
introspection against a declared schema is the exact example §8.3 gives.

**The unit of work has a natural boundary.** An Odoo module is a directory of files with a manifest,
and — with §2's conventions — most work decomposes along file lines that a reviewer could
independently accept or reject. That is the task right-sizing test from `writing-plans`, and Odoo
satisfies it more cleanly than most codebases.

### 1.2 The three properties that cut the other way

**Framework gravity.** Touching a model drags views, ACLs, the manifest and external ids along.
§7.4 anticipates exactly this. Without §2's conventions, touch-set disjointness rejects nearly every
split you would want, and the mechanism gets demoted to a warning — keeping the cost and losing the
protection.

**Slow checks.** A module install against a database is seconds to tens of seconds; a full test run
more. R28 (cheap-tier leaves take 2–3× the turns) compounds against check latency rather than only
against token price. §6 addresses this with a template database and §4 with a check ladder, but it
stays the dominant cost.

**Weak leaf checks on the behavioural half.** A compute method with a passing test written by the
same card is the weak case §8.3 names explicitly. Odoo's structural advantage does not extend there.

### 1.3 What this means for §1.1 of the design

**Amend §1.1 ("What this is for")** to name the property rather than the domain:

> Workloads where a substantial fraction of leaves admit an **objective, non-self-authored check** —
> schema conformance, load-time resolution, introspection against a declared contract — and where
> the remainder is separable and can be routed to a stronger tier with tests written first.

Odoo is an instance. Naming the property keeps the door open for the others (protobuf/IDL-driven
services, database migrations against a declared schema, infrastructure-as-code against a plan) and
keeps §1.1 from reading as a vertical.

---

## 2. Module conventions — unblocking §7.4

**Amends §7.4; adds to layer 1 (house preamble, §9.2).**

The problem in one line: default Odoo layout has three files that every card touches —
`__manifest__.py`, `security/ir.model.access.csv`, and often a single `views/<module>_views.xml`.
Touch-set disjointness is unusable against them.

Nothing in Odoo requires that layout. The manifest lists whatever data files you name.

### 2.1 One concern, one file, one owner

```
pharmacy/
  __manifest__.py            # GENERATED — no card writes this
  __init__.py                # GENERATED — globs models/, wizard/, controllers/
  models/
    __init__.py              # GENERATED
    pharmacy_prescription.py
    pharmacy_dispense_line.py
    product_template.py            # inherit-only files named for the model inherited
  security/
    10_groups.xml
    20_pharmacy_prescription_access.csv
    20_pharmacy_dispense_line_access.csv
    30_pharmacy_prescription_rules.xml
  views/
    40_pharmacy_prescription_views.xml
    45_pharmacy_prescription_menus.xml
  data/
    50_pharmacy_sequences.xml
  report/
  wizard/
  tests/
    test_prescription_state.py
    test_controlled_substance_access.py
```

**Rules that make this work:**

- **One ACL csv per model.** `ir.model.access.csv` is a filename convention, not a requirement —
  Odoo loads any csv named after a model (`ir.model.access.csv` loads into `ir.model.access`). Name
  them `<n>_<model>_access.csv`; each is still a csv whose rows load into `ir.model.access`.
- **One view file per model**, one menu file per top-level menu, one data file per concern.
- **Inherit-only python files are named for the model inherited**, not for the module. A card adding
  fields to `product.template` owns `models/product_template.py`, and no other card may open it.
- **Numeric prefixes carry load order.** The generated manifest globs in sorted order, so a card
  declares its position in the load sequence by naming its own file. No card edits a shared list to
  express ordering. Bands: `10` groups, `20` ACLs, `30` record rules, `40` views, `45` menus and
  actions, `50` data, `60` reports, `70` wizards.

### 2.2 The manifest and `__init__.py` are generated, never authored

A `pre_commit` hook (§6.6 — a deterministic sub-second transformation is a hook, not a card)
rewrites `__manifest__.py`'s `data` list from a sorted glob, and each `__init__.py` from a sorted
directory listing.

```python
# hooks/regenerate_manifest.py  (sketch)
DATA_GLOBS = ["security/*.xml", "security/*.csv", "data/*.xml",
              "views/*.xml", "report/*.xml", "wizard/*.xml"]
# sorted() within the union; numeric prefixes give deterministic order
```

Everything else in the manifest — `name`, `depends`, `version`, `license`, `application` — lives in
a `manifest.yaml` that is **root-intent-owned**, not card-owned. A card that needs a new dependency
does not edit it; it emits `spec_conflict` (§8.1), because adding a dependency changes what every
sibling can assume and is a decomposition-level fact.

**Consequence:** `__manifest__.py` and every `__init__.py` leave every card's `touch_set`. They
become build artifacts, and a card that modifies one has violated its declared set — caught
mechanically by the commit-time check §7.4 already specifies.

### 2.3 What this buys, stated precisely

Touch-set disjointness starts rejecting *real* collisions instead of structural ones. Two cards
adding two models to a pharmacy module now genuinely share nothing on disk. That is the
precondition for §7.3's harness-guaranteed fan-out to produce anything but conflicts.

### 2.4 What it costs

Non-idiomatic file layout. An Odoo developer opening this repo will expect `ir.model.access.csv`
and one views file. Document the reason in the module README, because the alternative — explaining
it in month four — is worse. Add to the CONSTRAINTS block (§9 below) so every card sees it.

---

## 3. `touch_set` extended from paths to namespaces

**Amends §7.4 and §4.1 (task schema).**

§7.4 says "paths or entities". Odoo is what forces the entity half to actually exist, because it has
three shared namespaces that no path-level check can see:

| Namespace | Collision looks like | Discovered at |
|---|---|---|
| XML external ids (`ir_model_data`) | two cards both define `pharmacy.group_pharmacist` | install, as a duplicate-id error, or worse, silently as an overwrite |
| Model names (`_name`) | two cards both declare `pharmacy.dispense.line` | registry build |
| Field names on an inherited model | two cards both add `expiry_alert_days` to `product.template` | install or, worse, at runtime with the wrong definition winning |

None of these are path collisions. All of them are exactly the sibling incoherence §7.2 test 2
exists to prevent.

### 3.1 Schema addition

Each child declares, alongside `touch_set`:

```jsonc
"owns": {
  "xml_id_prefix": "pharmacy.prescription_",     // every id this card creates starts here
  "models": ["pharmacy.prescription"],           // models it declares with _name
  "fields": {                                    // fields added to models it does not own
    "product.template": ["pharmacy_is_controlled", "pharmacy_schedule"]
  }
}
```

The `fields` block is the Odoo instantiation of `interfaces.produces` from findings-2 §2.2 — a
sibling that reads `product.template.pharmacy_is_controlled` declares it in `consumes`, and the
emit-time gate resolves the symbol against some sibling's `produces` plus a dependency edge.

### 3.2 Two checks, both model-free

**Emit-time (in the split gate, alongside touch-set intersection):**

- No two children's `xml_id_prefix` values are prefixes of one another.
- No model name is declared by two children.
- No `(model, field)` pair is declared by two children.
- Every `consumes` symbol resolves to some sibling's `produces`, with an edge.

**Commit-time (`pre_commit` hook, host-side, no database needed):**

- Parse every XML file in the diff; every `<record id="...">`, `<menuitem id="...">` and
  `<template id="...">` must start with the card's `xml_id_prefix`.
- Parse every python file in the diff with `ast`; every `_name = "..."` must be in `owns.models`,
  and every module-level field assignment on a class with `_inherit` must be in `owns.fields`.

The commit-time half reports fact, not prediction, so per §7.4's caution it cannot false-reject and
stays a gate even if the emit-time half is demoted to a warning.

### 3.3 Why the prefix and not a list

A card cannot enumerate its external ids in advance — it does not know how many views it will write.
A prefix is declarable before the work and checkable after it, which is the same shape as
`check_spec`. It also gives the digest a free query: every `ir_model_data` row is attributable to
the card that made it.

---

## 4. The check ladder

**Amends §7.2 (postcondition), §4.1 (`check_spec`), §17.**

`check_spec` in Odoo is not one command. It is a ladder, and the ladder ordering is the single
biggest lever on run cost, because each rung kills a class of failure at a fraction of the next
rung's price.

| Rung | Needs | Typical cost | Catches |
|---|---|---|---|
| **0 · Static** | nothing | < 1 s | python syntax, XML well-formedness, csv column shape, manifest parses, `pylint-odoo`, namespace violations (§3.2), touch-set violations (§7.4), placeholder scan (findings-2 §4.1) |
| **1 · Load** | database clone | 5–30 s | field/view mismatch, unresolvable xpath, missing group ids, bad `_inherit`, broken `related`, ACL naming an absent model, domain on unknown field |
| **2 · Test** | database clone | 10 s – minutes | behaviour the card's tests assert |
| **3 · Introspect** | database clone | 1–3 s after rung 1 | declared schema vs registry reality (§5) |

**Rules that follow:**

- **Rung 0 always runs, on the host, and the card cannot see or edit it.** It is the hidden oracle,
  so layer 8 does not render it (rule 137).
- **A card that fails rung 0 never gets a database.** Most bad cards die here, and this is what keeps
  R28 survivable.
- **`check_spec` declares which rungs apply**, and the splitter must justify omitting rung 2 —
  a structural card legitimately has no tests; a behavioural card claiming none is a refusal signal.
- **Rung 3 is the verify gate's input for structural work** (§10), not the executor's own check,
  because it compares against the root-intent schema rather than against the card's contract.

**Amend §17.4 (static invariants):** rung 0 is the Odoo instantiation of that section — milliseconds,
high value — and it should be runnable standalone as `make check-static` so it is usable by hand
during the year of preparation, before any harness exists.

---

## 5. The declarative spec and the introspection oracle

**Amends §19 (writing root intents) and §8.3 (drift control).**

### 5.1 The root intent carries a schema, not a description

§19's DONE MEANS is the highest-value heading and should be executable where possible. In Odoo it
can be a **file**:

```yaml
# spec/pharmacy.schema.yaml  — the anchor. Cards never amend it (§8.1).
module: pharmacy
depends: [base, stock, product, account, sale_management]

models:
  pharmacy.prescription:
    description: "Prescription"
    rec_name: name
    order: "date desc, id desc"
    fields:
      name:            {type: char, required: true, copy: false, default: "New"}
      patient_id:      {type: many2one, comodel: res.partner, required: true, ondelete: restrict}
      prescriber_id:   {type: many2one, comodel: res.partner, required: true}
      date:            {type: date, required: true}
      state:           {type: selection, values: [draft, validated, dispensed, cancelled], default: draft}
      line_ids:        {type: one2many, comodel: pharmacy.dispense.line, inverse: prescription_id}
      is_controlled:   {type: boolean, compute: _compute_is_controlled, store: true}
    constraints:
      - {type: sql, name: name_uniq}

  product.template:
    inherit: true
    fields:
      pharmacy_is_controlled: {type: boolean}
      pharmacy_schedule:      {type: selection, values: [none, s2, s3, s4]}

groups:
  pharmacy.group_pharmacy_user:   {implied: [base.group_user]}
  pharmacy.group_pharmacist:      {implied: [pharmacy.group_pharmacy_user]}

access:
  pharmacy.prescription:
    pharmacy.group_pharmacy_user: {read: 1, write: 1, create: 1, unlink: 0}
    pharmacy.group_pharmacist:    {read: 1, write: 1, create: 1, unlink: 1}

rules:
  pharmacy.prescription:
    - {name: controlled_pharmacist_only, groups: [pharmacy.group_pharmacy_user],
       semantic: "a non-pharmacist may not read a prescription containing a controlled item",
       test: tests/test_controlled_substance_access.py::test_user_cannot_read_controlled}

views:
  pharmacy.prescription: [list, form, search]
```

### 5.2 The oracle

```
odoo-bin -d $CLONE -i pharmacy --stop-after-init          # rung 1
python tools/introspect.py --spec spec/pharmacy.schema.yaml --db $CLONE   # rung 3
```

`introspect.py` reads the registry and diffs. The joins it needs, named so this is buildable:

- **Models:** `ir_model` filtered to the module via `ir_model_data` where `model = 'ir.model'` and
  `module = 'pharmacy'`.
- **Fields:** `ir_model_fields` joined the same way (`model = 'ir.model.fields'`), giving `name`,
  `ttype`, `relation`, `required`, `store`, `selection`, `related`, `compute`.
- **ACLs:** `ir_model_access` joined to `ir_model` and `res_groups`.
- **Rules:** `ir_rule` with `domain_force`, joined to `rule_group_rel`.
- **Views:** `ir_ui_view` with `type`, `model`, `inherit_id`.

It emits three lists, matching findings-2 §2.3's three channels: **missing** (in spec, not in
registry), **extra** (in registry, not in spec), and **divergent** (present, wrong type/required/
comodel/selection values).

### 5.3 What this changes about drift

For the structural half of the module, **commission drift is mechanically detectable**. A card that
declared `patient_id` as `many2one` to `res.users` instead of `res.partner` produces a summary
indistinguishable from a correct one — and rung 3 catches it in a SQL comparison with no model call.

That is a stronger result than ADR-0001's pair, in a narrower domain, and it should be recorded as
such: **on structural cards, `decided`/`open_questions` is redundant with introspection.** Keep the
pair for behavioural cards, where nothing else covers the ground.

**Amend §8.3** with a paragraph naming this: the design's honest fallback (narrow to domains with
semantically weighty leaf checks) has a worked instance, and the instance shows the fallback is not
a retreat — it is a stronger position than the general mechanism, wherever it is available.

### 5.4 The limit, stated in pharmacy terms

Rung 3 sees that `controlled_pharmacist_only` exists, applies to the right groups, and is attached
to the right model. **It cannot see that its domain is wrong.**

```xml
<!-- structurally perfect, semantically inverted -->
<field name="domain_force">
  ['|', ('is_controlled','=',False), ('create_uid','=',user.id)]
</field>
```

That rule passes rung 0, rung 1 and rung 3. Its card's summary reads *"added record rule restricting
controlled substances to pharmacists; module loads; tests pass."* A non-pharmacist can read every
controlled prescription in the database.

**This is the commission-drift case, and it is the one that matters most in a pharmacy.** It is also
the perfect E2 specimen (§14.2). The answer is not a better verifier — it is that security semantics
get a **behavioural test card written before the rule card**, which is what the `semantic:` and
`test:` keys in §5.1's schema are for. See §8.3 below.

---

### 5.5 How the schema is created — the anchor has no detector beneath it

**Amends §19 and §15 of this document.** Everything downstream is checked *against* the schema.
Introspection will cheerfully confirm that the module matches a wrong anchor. **This is the only
artifact in the entire system with nothing below it to catch a mistake**, and it should be made
accordingly.

The translation from the `brainstorm` design document has three kinds of content, with different
economics:

| Kind | Example | Who | Why |
|---|---|---|---|
| **Derivable** | field types, comodels, view types, one2many inverses | model | prose determines it; errors are loud at rung 1 or 3 |
| **Decided** | `required`, `ondelete`, `store`, `index`, defaults, the whole ACL matrix | **human** | prose is silent; errors are **quiet** — no rung fires on the wrong `ondelete` |
| **Untranslatable** | "readable only by pharmacists" | **copied verbatim** | becomes `semantic:` + `test:`; paraphrasing it *is* the drift |

The rule that matters for the third row: **a `semantic:` block that compresses the design document
has already lost the thing it exists to preserve.** Copy the sentence.

### 5.6 The authoring pipeline

**1 · Draft A.** A model translates the derivable content, copies `semantic:` blocks verbatim, and
marks every decided field `TODO_DECIDE` rather than guessing. A guessed `ondelete` is
indistinguishable from a considered one, which is the whole problem.

**2 · Draft B, independent.** **A different model, or the same model at a different effort level** —
not the same config resampled. Sampling one model twice gives variance without independence: same
training, same priors, same modal answer, and therefore *correlated* blind spots, which is the one
property this step depends on not having. **Diff the two.** Every divergence marks a place the design
document was ambiguous.

This is ADR-0001's argument applied to the anchor, and it is the *only* detector available here,
because there is nothing below the schema to check it against. The blind spots of two independent
translations are uncorrelated for the same reason two cards' are: different times, different
context. It costs one extra call and converts silent ambiguity into a visible diff.

**3 · Human resolves** the diff and every `TODO_DECIDE`. This is the hour, and it is now spent on
decisions rather than on typing YAML.

**4 · `schema_lint` — mechanical, no model, runs on every edit forever:**

- every `constraints:` entry has an `expressed_by` naming a real rule or behaviour
- every `rules:` entry has both `semantic` and `test`
- every `behaviour:` entry has a `test`
- a computed field referenced in any rule domain or search view has `store: true`
- every model in `access:` exists in `models:`; every group referenced exists in `groups:`
- no `TODO_DECIDE` survives
- every model has a declared view type or is explicitly marked embedded
- every `related:` path resolves within the declared models plus `depends`

Note the fourth rule. **The preflight finding at T+4:40 of the worked run — `is_controlled` needing
`store: true` — is a lint rule, not a discovery.** It should have failed at T-1d, before a single
card existed. Every mechanical check moved earlier removes a human gate from the critical path.

**5 · Coverage back to the design document.** A model lists every requirement in the design doc and
names the schema key expressing it. Anything with no key is an omission or belongs in
`out_of_scope`. This is the omission direction, which is the direction models are reliably good at —
the same reason the verify gate works at all.

**6 · Stub install.** A generator emits a minimal module from the schema — models with typed fields,
ACL csvs, bare views — and `odoo-bin -i` runs on it. This proves the schema is **expressible in
Odoo** before eleven cards are dispatched against it. A `related:` path that does not resolve, a
`selection` declared on a `many2one`, a comodel outside `depends`: thirty seconds, not card three.

### 5.7 The uncomfortable consequence of step 6

**Amends §8.1.** Once a generator emits a stub from the schema, the question arrives on its own: how
much further does it go?

Further than is comfortable. Models with typed fields, per-model ACL csvs from the `access:` matrix,
list and form views from the field list, menus from `menus:`, sequences — that is cards `.1` through
`.5` of the worked run. A generator produces them deterministically, in a second, with zero drift
and no model calls.

**The schema being complete enough to check the structural half against is the same property as
being complete enough to generate it from.** That is not a coincidence; it is the definition.

So §8.1's split is sharper than "cheap cards versus strong cards":

| Half | Mechanism | Harness role |
|---|---|---|
| Structural | **code generation from the schema** | none — it is a hook (§3.4 of v2) |
| Behavioural | test card, then implementation card | the entire thing |

If this holds, the harness's real workload on this project is six or seven behavioural cards, not
eleven plus four gaps. That is a smaller run and a more honest one, because those are precisely the
cards where a model does something a script cannot.

**Do not resolve this by argument.** The generator is needed for step 6 regardless, so write it
during the waiting year (§15), point it at a real schema, and measure how much of a module it
produces. Let the number decide how many structural cards ever exist. It is the same discipline as
everywhere else here: the cheapest mechanism that can do the job takes it, and the model gets what
is left.

**The residual argument for structural cards**, stated fairly so it is not lost: a generator emits
what the schema says, and nothing else. Idiomatic view layout, sensible field ordering and grouping,
`groups=` attributes on individual fields, help text — none of that is in the schema and none of it
should be, because putting it there makes the schema a view definition language. Structural cards
may survive as *polish over generated scaffolding*, which is a different and much smaller job than
writing the files.

---

## 6. The workspace is three things

**Amends §11 (repository work), §5.4 (the reaper), §13 (enforcement), §14.2 (config pinning).**

### 6.1 Worktree, container, database

An Odoo card cannot run rung 1 without a database, cannot run it reproducibly without a pinned
runtime, and cannot be merged without a branch. These are three separate needs and the design
currently names only the first.

| Component | Provides | Lifetime |
|---|---|---|
| **git worktree** | source isolation; a branch for `integrate` | per card attempt (ADR-0011) |
| **container** | pinned Odoo/python/wkhtmltopdf, cgroup limits, network deny, **a kill handle** | per card attempt, ephemeral |
| **database clone** | rung 1–3 execution | per card attempt |

**Rename §11's unit.** A workspace is the triple, provisioned together and torn down together, not a
checkout.

### 6.2 Git on the host, execution in the container

A `git worktree`'s `.git` is a file pointing into the parent repo's `.git/worktrees/<name>`.
Bind-mounting the worktree alone breaks git inside the container; bind-mounting the repo root gives
the card read/write access to every sibling's worktree, which discards the isolation.

**Resolution:** the harness creates the worktree, starts the container with it bind-mounted at a
fixed path (`/mnt/addons/pharmacy`), the card edits and runs rungs 1–3 inside, and **the harness
commits from the host after the card returns.**

Two things fall out of this that are worth more than the convenience:

- Commit is already a harness operation in your design (§5.7), not a card operation. This makes it
  literally so.
- The `pre_commit` hooks — touch-set (§7.4), namespace (§3.2), manifest regeneration (§2.2) — run
  on the host, **where the card cannot reach them.** Same property that makes the check oracle
  hidden, now extended to the structural gates.

The worktree's `.git` is inside that mount, so the card can write it. Both properties hold only because host
git ignores it and goes through one runner (rule 150, core §6, ADR-0014).

### 6.3 The kill handle closes §16

§16 is the zombie writer: a card whose lease expired and whose fencing token is stale, still
running and still writing. Fencing protects the ledger — the stale commit is rejected. It does not
protect the filesystem, and a reaped card holding a worktree keeps editing files a retry is now also
editing.

**Amend §5.4 (the reaper) and §4.1 (lease record):**

- The container's name derives from the card id and attempt (core §6, ADR-0007), so the reaper can
  find it even if the worker died before recording anything.
- The reaper's order is **kill, then requeue.** Requeue-first gives you two live writers.
- After the kill, the attempt's worktree is removed. The retry gets its own, from the card's base
  commit (ADR-0011).

This is a stronger argument for containers in this architecture than sandboxing is, and it should be
recorded that way in §13.

### 6.4 One Postgres for the run; databases from a template

Do not run a Postgres per card. Run one for the run, build a template once, clone per attempt:

```bash
# once per run
createdb odoo_tmpl
odoo-bin -d odoo_tmpl -i base,stock,product,account,sale_management --stop-after-init
# per card attempt  (~1 s)
createdb -T odoo_tmpl card_t_a3f8_2_7_attempt1
```

`CREATE DATABASE ... TEMPLATE` requires no active connections to the template, so **no worker may
ever connect to `odoo_tmpl`.** Enforce it in the connection layer, not by convention.

Without this, ten parallel cards each install base+stock+account from scratch and the run serialises
on Postgres. This is the single mechanism that makes the parallelism differentiator pay in Odoo.

Each clone gets its own filestore directory; drop both on card completion.

### 6.5 Ephemeral per card, not per worker

A worker is long-lived and could hold one container, swapping worktrees inside it — fewer starts,
warmer caches. Take ephemeral anyway. Every attempt being cold is a property retries already rely
on, and a reused container accumulates pip installs, `__pycache__`, and a filestore, which makes
§16 (the deploy that manufactures the crash) reachable. With a prebuilt image, start is a second
or two — noise beside the model call.

### 6.6 What joins the config pin

**Amend §14.2.** Replay is not replay if the runtime moved. Pin, alongside the model version:

- container image digest
- Odoo source commit (or series + point release)
- template database hash (a digest of the dependency list plus the Odoo commit)
- OCA/third-party addon commits, if any
- `requirements.txt` lock

### 6.7 Consequence for §13

This strengthens findings-2 §3.3's recommendation to delete §13.3–13.7. Container plus network-deny
plus read-only mounts covers what those sections wanted, **enforced rather than declared**, with no
per-tool table to maintain. §13's principle survives; its elaboration does not.

### 6.8 Consequence for Gate A

**Amend §20.1.** Gate A ("does crash recovery work reliably under contention") now has to include:
kill a container mid-write, confirm the reaper requeues cleanly, confirm the worktree is removed,
confirm the stale container's writes are not present, confirm the orphaned database clone is
collected. That is harder to test than a poll-loop crash and it is the right place to spend the
difficulty.

---

## 7. Tiering and the cost model, revisited

**Amends §6.4, findings-1 §1.1, R28.**

findings-1 §1.1 replaced propagation-tiering with contract-completeness for `execute` cards. Odoo
lets you go further, because contract completeness is *derivable from the spec* rather than declared
by the splitter.

| Card shape | Contract completeness | Tier | Rungs |
|---|---|---|---|
| Model definition fully specified in `spec.yaml` | complete — the fields, types and comodels are enumerated | cheap | 0,1,3 |
| Field additions to an inherited model, enumerated | complete | cheap | 0,1,3 |
| Standard views (list/form/search) for a specified model | complete — derivable from the field list | cheap | 0,1 |
| ACL matrix rows from the spec's `access:` block | complete | cheap | 0,1,3 |
| Menus, actions, sequences, demo data | complete | cheap | 0,1 |
| Record rule with a stated `semantic:` and a pre-written test | constraint — the domain must be derived | **strong** | 0,1,2,3 |
| Compute / constrains / onchange | prose | middle–strong | 0,1,2 |
| State machine transitions and their guards | constraint, not instruction | strong | 0,1,2 |
| Report layout (QWeb) | prose | middle | 0,1 |
| Portal/controller | prose | middle | 0,1,2 |
| Migration script | constraint | strong | 0,1,2 + snapshot |

**The declaration is checkable.** A card whose contract is claimed complete but whose text contains
"handle edge cases" fails the placeholder scan (findings-2 §4.1). A card claimed complete that then
takes eleven turns is a metric row (§15.2). Both are one-column checks.

**R28 in Odoo terms, amended:** the risk is not only turn count but **turns × rung latency**. A cheap
model that takes three attempts at a view file costs three database clones plus three installs. The
mitigations are the check ladder (rung 0 kills most failures for free) and the template database
(rung 1 costs a second of setup rather than minutes). Measure `turns`, `rung1_invocations` and
`wall_clock` per card from run one — three columns, not a project.

---

## 8. Decomposition: what an Odoo card looks like

**Amends §7.2, §7.3, and the split jig's system prompt.**

### 8.1 The two halves

Write this into the root intent's SHAPE heading (§19), because it is a prior worth stating:

> **Structural work** — models, fields, views, menus, ACLs, sequences, data — is specified by the
> schema, checked by rungs 1 and 3, and tiered cheap. It is wide and shallow and should fan out
> hard.
>
> **Behavioural work** — computes, constraints, record-rule domains, state transitions, dispensing
> and expiry logic — is specified by prose plus a test, checked by rung 2, tiered by its contract
> shape, usually middle or strong, and gets a test card before an implementation card.

The two halves have different cost models, different contract shapes, different rungs and different
drift exposure. Treating them as one tier is what makes the cost model wrong. They remain one kind,
`execute`: contract shape sets the tier and `check_spec` sets the rungs (ADR-0008).

**Amendment, per §5.7.** The structural half may not be cards at all. If a generator can emit it
from the schema deterministically, it is a hook, and the partition below shrinks to the behavioural
pairs plus polish. Write the generator (§15), measure what it covers, and let that decide. The
partition below is stated in full because it is what gets run if the generator covers little — and
because it is the version the worked run traces.

### 8.2 A worked partition

Root intent: *prescription capture and controlled-substance dispensing for a single-branch pharmacy.*

```
t-ph                                    split
├─ t-ph.1   models + fields (spec §models)          execute  cheap   [rules 66: one card, all fields]
├─ t-ph.2   security groups                          execute  cheap
├─ t-ph.3   ACL matrix (spec §access)                execute  cheap
├─ t-ph.4   views + menus for pharmacy.prescription  execute  cheap   deps: .1
├─ t-ph.5   views + menus for dispense lines         execute  cheap   deps: .1
├─ t-ph.6   TEST: controlled-substance access        execute  strong  deps: .1,.2   ← test first
├─ t-ph.7   record rules (spec §rules)               execute  strong  deps: .6
├─ t-ph.8   TEST: prescription state machine         execute  strong  deps: .1
├─ t-ph.9   state transitions + guards               execute  strong  deps: .8
├─ t-ph.10  TEST: expiry/batch selection             execute  strong  deps: .1
├─ t-ph.11  expiry/batch dispensing logic            execute  strong  deps: .10
├─ t-ph.P   preflight (findings-2 §4.1)              gate            children dep on it; only if E1 justifies it
├─ t-ph.V   verify (rung 3 + summaries)              gate            deps: all
└─ t-ph.D   digest                                    gate            deps: all
```

Note the shape: cheap structural cards fan out wide with no interdependence beyond the model card;
every behavioural card is preceded by its own test card. That ordering is what §20's
"test-cards-first" means in Odoo, and it is the only thing standing between you and §8.3's weak
case — a test written by the card whose work it checks.

### 8.3 Test-cards-first, made concrete

A test card's contract is the `semantic:` line from the schema plus the test path. Its `check_spec`
is: **the test exists, it runs, and it FAILS** — RED, asserted by the harness, exactly as
`test-driven-development` requires and as findings-2 §5.1 applies to jigs.

The implementation card then depends on it, and its `check_spec` is: the same test passes, and no
previously passing test now fails.

This gives you the property §8.3 says is otherwise unavailable: the check was written by a different
card, at a different time, with different context, and the implementing card cannot edit it (the
test file is not in its `touch_set`, and the commit-time check enforces that).

**New rule.** In Odoo, a behavioural card never owns its own test file. If a card's `touch_set`
contains both `models/*.py` and `tests/*.py`, the split is wrong.

### 8.4 Patterned work — rule 66 in Odoo

Adding one field to fourteen models, or one ACL row per model, or the same `noupdate` flag across
eight data files, is **one card enumerating every site** (rule 66). Odoo generates a lot of this
shape, and the acceptance test from `writing-plans` is the operational question: *could a reviewer
sensibly accept one and reject its neighbour?* For a field added uniformly, no. One card.

### 8.5 Split system prompt additions

```
## Odoo-specific decomposition

The schema at spec/pharmacy.schema.yaml is the authority. Every structural
child's contract is a citation into it, not a paraphrase of it. If a child's
contract restates a field list, you have created a second source of truth —
cite the path and the key instead.

Structural children (models, fields, views, menus, ACLs, data) fan out wide
and depend only on the model card that declares what they reference.

Behavioural children (compute, constrains, record-rule domains, state
transitions) are always a PAIR: a test card, then an implementation card
depending on it. Never one card. The test card owns the test file; the
implementation card must not name it in touch_set.

A child never edits __manifest__.py, any __init__.py, or a sibling's file.
Those are generated or owned elsewhere. A child needing a new module
dependency emits spec_conflict.

Every child declares owns.xml_id_prefix, owns.models, owns.fields, and
interfaces.consumes.
```

---

## 9. The layer stack, instantiated

**Amends §9.2.**

| Layer | Odoo content | Cache scope |
|---|---|---|
| 0 SYSTEM | role, output contract, refusal rules, the four-status outcome (findings-2 §2.1) | kind |
| 1 PREAMBLE | §2's conventions; ORM house rules; the banned list below | house |
| 2 SKILLS | the Odoo skill (§9.2 below), TDD skill, the relevant rationalization tables | kind |
| 3 TOOLS | file edit, `odoo-bin` in-container, psql read-only on the clone; **no network** | kind |
| 4 ORIENTATION | **generated** (§9.1) + the root intent's CONSTRAINTS verbatim | run |
| 5 | the card's contract, its `owns` block, its `interfaces` | card |
| 6 | dependency summaries + retrieved artifacts (named-risk only, findings-2 §5) | card |
| 7 | previous attempt's check output, on retry | attempt |
| 8 | the definitions of the rungs the card may see | kind |

### 9.1 Layer 4 is a query, not prose

findings-1 §4 wants the root intent's CONSTRAINTS block verbatim in layer 4. Odoo lets you generate
the other half of that layer from the template database:

```sql
-- module structure summary, computed once per run against odoo_tmpl
select m.model, f.name, f.ttype, f.relation, f.required
from ir_model_fields f join ir_model m on m.id = f.model_id
where m.model in (:models_the_module_touches)
order by m.model, f.name;
```

More accurate than any prose summary, cacheable per run, and it costs a script. It is also what
lets a card working on `product.template` know what is already there without a discovery card.

### 9.2 The Odoo skill (layer 2) — written RED-first

Models have strong and consistently wrong priors in Odoo: reaching for `sudo()` to make an access
problem go away, raw SQL instead of the ORM, `@api.one`-era decorators, unstored computes used in
search domains, `write()` in a compute, `noupdate` misunderstood, `stock.lot` versus the older
`stock.production.lot` name, ACL rows conflated with record rules. That set is exactly what
findings-2 §5.1's method is for.

**Do this during the waiting year.** Run twenty real Odoo tasks with no skill, capture what goes
wrong and how the model justifies it **verbatim**, then write against those observed failures and
build the rationalization table from what you saw. The result is useful whether the harness exists
or not, and it is the largest single lever on leaf quality.

Seed entries the table will almost certainly need:

| Excuse | Reality |
|---|---|
| "`sudo()` here to get the test passing" | You have disabled the security model you were asked to build. Fix the rule or the ACL. |
| "The compute doesn't need `store=True`" | Then it cannot be searched, grouped, or used in a rule domain. Check the spec. |
| "Adding the field to the shared views file is simpler" | That file belongs to another card. Yours is named in `touch_set`. |
| "The manifest needs this dependency" | You do not edit the manifest. Emit `spec_conflict`. |
| "Raw SQL is faster here" | It bypasses ACLs, record rules and the cache. Not in this module. |

---

## 10. Verify in Odoo

**Amends §8.3, §7.5, findings-2 §1.4 and §2.3.**

### 10.1 Two verifiers, different inputs

**Structural verify** takes rung 3's introspection diff plus the root schema. It is nearly
deterministic — the model's job is triage and explanation, not detection, because the missing/extra/
divergent lists are computed. This is the cheapest possible gate and it should be tiered accordingly,
though no role claims it yet (policy §1.3); it gets `verify_cheap` once open question 2 confirms cheap
is enough.

**Behavioural verify** takes the card's `touch_set` diff (findings-2 §1.4) plus the root intent's
CONSTRAINTS block plus the `semantic:` lines for anything it touched. This is where the diff-reading
configuration earns its keep, and where E2's arm D is really being decided.

### 10.2 Three channels, in Odoo terms

Per findings-2 §2.3:

- **gaps** → cards. A missing field, an absent ACL row, a view type not built.
- **unverifiable** → notes. "The dispensing sequence's correctness depends on the batch-selection
  rule in t-ph.11, which is outside this diff." Resolved at the parent gate or the human gate;
  the verifier never widens scope to chase it.
- **minor** → deferred list, carried to the root gate.

### 10.3 What verify cannot see, listed so nobody expects it to

Record-rule domain semantics. Compute correctness beyond what tests assert. QWeb report output.
Performance (an N+1 in a stored compute over `line_ids`). Multi-company boundaries. Access logic
that emerges from ACL and rule interaction. Anything requiring data to exist.

**The pharmacy-specific version of that list is the risk register entry.** Every item on it is a
place where a passing check and a clean summary coexist with a wrong system, and in this domain the
wrongness is dispensing the wrong quantity, an expired batch, or a controlled substance visible to
the wrong user. That is why §8.3's test-first pairing is not optional here.

---

## 11. Retry safety and migrations

**Amends §7.2 test 3 and §4.1.**

### 11.1 Greenfield cards are mostly retry-safe, and this is worth saying

Because every attempt gets a fresh database clone and a fresh worktree, a failed Odoo card leaves
nothing behind. Test 3 passes trivially for the structural half and most of the behavioural half.
That is a genuine property of this domain and it makes retry cheap.

### 11.2 The exceptions, and the flag

Retry safety breaks in three places:

1. **Migration scripts.** Once the module has been installed with data, changing a field type or
   renaming a model requires a `migrations/<version>/pre-migrate.py`, and validating it requires a
   snapshot **with data**, not a clean clone. A partial run leaves a database a second attempt would
   corrupt.
2. **Anything touching a shared branch or a non-clone database.**
3. **External side effects** — a card calling a supplier API, sending mail, writing to a filestore
   outside the clone.

**Amend §4.1:** add `retry_safe: bool`, default true. A `retry_safe: false` card that fails goes to
`awaiting_review`, not back to `pending`. The splitter sets it false for migration cards; the
`pre_commit` hook sets it false if the diff touches `migrations/`.

### 11.3 Migration cards need a data snapshot, not a template clone

**Amend §6.4:** the workspace provisioner takes a `db_source` — `template` (clean) or
`snapshot:<name>` (a captured database with representative data). Migration cards request the
latter, and it is the only card class that does.

Build one representative snapshot during the waiting year — a few hundred products, lots with
expiry dates, a month of prescriptions. It is also what makes rung 2 meaningful for the expiry and
batch logic, which cannot be tested against an empty database.

---

## 12. Integration

**Amends §11 and §7.5.**

The `integrate` gate merges sibling branches. With §2's conventions, structural conflicts should be
near-zero by construction — different files, no shared list. The residual conflicts are:

- **Generated files.** `__manifest__.py` and `__init__.py` will conflict on every merge, because
  every card regenerated them. **Resolution: do not commit them.** Add both to `.gitignore` and
  regenerate at integrate time and at install time. If that proves awkward, commit them but resolve
  the conflict by regeneration rather than by merge — a two-line merge driver.
- **Load-order collisions.** Two cards both choosing `40_` prefixes is not a conflict but is
  non-deterministic across filesystems; sort must be explicit and stable, and the band table (§2.1)
  should leave gaps.
- **The real one: post-merge load.** Two cards that each installed cleanly in isolation can fail to
  install together — an xpath that matched before another card's view inherited the same node, a
  field name collision the emit-time check missed.

**So `integrate`'s check is rung 1 on the merged tree, not just a clean merge.** State that in the
gate's `check_spec`. It is the only place the module is ever seen whole before the root verify.

---

## 13. Failure modes — Odoo additions to §16

| # | Mode | Tell | Response |
|---|---|---|---|
| 16.15 | **The `sudo()` escape.** A card makes an access test pass by bypassing the security model it was asked to build. | `sudo(` appearing in a diff whose card owns security work | Rung 0 static check: `sudo(` in a security-owning card's diff is a hard fail. Elsewhere, a finding. |
| 16.16 | **The silent overwrite.** Two cards define the same external id; the later load wins and the first card's record vanishes without error. | `ir_model_data` row count below the sum of declared records | Namespace prefix check (§3.2) prevents it at commit; introspection catches survivors. |
| 16.17 | **The structurally perfect wrong rule.** A record rule with correct groups, model and syntax and an inverted domain. | Nothing. Rungs 0/1/3 all pass. | Test-first pairing (§8.3). This is the failure the whole test-card discipline exists for. |
| 16.18 | **The unstored compute in a domain.** Passes install, fails at runtime the first time someone filters. | `store` false in `ir_model_fields` for a field named in any `ir_rule.domain_force` or view `search` default | Rung 3 check — computable, add it to `introspect.py`. |
| 16.19 | **The demo-data dependency.** A test passes only because `--test-enable` loaded demo data the production database will not have. | Test passes on template clone, fails on the data snapshot | Run rung 2 with demo data off for at least the behavioural cards. |
| 16.20 | **The orphaned clone.** Card dies; its database and filestore survive; Postgres fills. | Clone count exceeding live leases | The reaper drops the clone as part of kill-then-requeue (§6.3). |
| 16.21 | **The manifest that drifted.** A card edited a generated file and the hook silently regenerated over it, losing an intended change. | Diff between committed and regenerated manifest | Hook fails loud rather than regenerating silently when the card's diff touched a generated path. |

---

## 14. The experiments, instantiated

**Amends §18.**

### 14.1 E1 on a real schema

Write `spec/pharmacy.schema.yaml` for a genuinely small slice — prescription, dispense line, two
groups, one record rule, one compute — and run the split jig against it three times.

Measure everything §18.1 asks for, plus:

| Measure | Tells you |
|---|---|
| Fraction of children whose `check_spec` names a rung and is runnable | crude-gate pass rate |
| Touch-set intersections after §2's conventions | whether §2 actually unblocked §7.4 |
| `owns` collisions (prefix, model, field) | whether §3 is needed and whether it false-rejects |
| `consumes` symbols resolving to a sibling's `produces` | R30 |
| Whether the splitter pairs every behavioural card with a test card | whether §8.3 survives contact |
| Whether structural children cite the schema path or paraphrase it | second-source-of-truth risk |
| `open_questions` populated | ADR-0001's second signal |

**Do the RED pass first** (findings-2 §5.1): run the same schema with no split jig at all, three
samples, and record what a strong model does unprompted. That is what the jig gets written against.

### 14.2 E2 with a real specimen — use the record rule

§5.4 hands you the perfect arm-A/B/D specimen, and it is worth using precisely because it is the
pharmacy's actual risk rather than a contrived one.

Six summaries. Five correct. The sixth:

> *"Added record rule `controlled_pharmacist_only` on `pharmacy.prescription` restricting
> controlled items to the pharmacist group. Module loads. 4/4 tests pass."*

The diff behind it has `'|'` where `'&'` belongs.

| Arm | Input to the verify jig | What it measures |
|---|---|---|
| A | six summaries, `decided` empty | can a cold summary reader see it — almost certainly no |
| B | six summaries, `decided` populated with the domain choice | whether the field rescues it |
| **D** | the sixth card's `touch_set` diff + the `semantic:` line | **what summary-reading costs** |
| C | a real executor given the `semantic:` line and no test | does `decided` arrive |
| Control | all-correct set through each of the above | false-positive rate per input type |

Arm D is the one that decides §1.4 of findings-2, and this specimen makes it concrete: the diff is
four lines and the semantic line states the intent in one sentence. If arm D does not catch it,
that is a very strong result — and if arm A catches it, be suspicious and check the control.

**Add a fifth arm, cheap and specific to this domain:** hand the verify jig nothing but the
introspection diff for a *structural* specimen (a `many2one` pointing at `res.users` instead of
`res.partner`). Detection should be ~100%, because the diff is computed. If it is not, the gate has
a triage problem rather than a detection problem, and that is worth knowing before you trust rung 3.

### 14.3 E3 with the real baseline

`/superpowers:brainstorm → write-plan → subagent-driven-development` on the same slice, in a
worktree, with the same schema as the spec.

Record: wall-clock, cost, per-task quality, and `your_intervention_count`. And record the hazard
from earlier — SDD never dispatches implementers in parallel, so a wall-clock win proves only that
you parallelised, which nobody disputes.

**The high-value by-product:** `write-plan`'s output has a Files block (your `touch_set`), an
Interfaces block (your `consumes`/`produces`) and a Global Constraints header (your layer 4). So you
can run your emit-time gates — touch-set intersection, symbol resolution, namespace collision,
placeholder scan — against a **human-reviewed decomposition that actually executed successfully.**
That is a far stronger false-rejection test than three model samples on a hypothetical intent, and
it costs one script.

If your gates reject a decomposition that demonstrably worked, the gates are wrong. Find that out in
month two.

---

## 15. What to do with the waiting year

Ordered by dependency, not by phase.

**Now, and useful regardless of whether the harness is built:**

1. §2's conventions, on a throwaway module. Confirm a module with per-model ACL files and a
   generated manifest installs, updates and uninstalls cleanly. One afternoon.
2. `spec/pharmacy.schema.yaml` for a small slice, and `tools/introspect.py`. Confirm it detects a
   deliberately wrong field type, a missing ACL row, and an unstored compute used in a domain. One
   or two days. **This is the highest-information cheap experiment available**, because it validates
   §8.3's fallback position empirically.
3. Rung 0 as `make check-static`, standalone. Half a day.
4. `schema_lint` (§5.6 step 4). Half a day, mechanical, and it moves the worked run's first human
   gate from T+4:40 to T-1d.
5. **`tools/generate.py` — the stub generator (§5.6 step 6).** Needed for the schema smoke test
   regardless. Then push it: point it at the full schema and measure what fraction of the structural
   half it emits correctly. **This is the experiment that decides how many structural cards exist**
   (§5.7), and it is two or three days of work that could remove five cards from every run forever.
6. The container image and the template-DB script. One day.
7. Begin the Odoo skill's RED corpus — every time you run an Odoo task with a model this year,
   capture what it got wrong verbatim. Costs nothing incremental and compounds.

**Then, on paper:**

8. E3 on the real slice with superpowers (§14.3), and run your gates against its plan.
9. E2 with the record-rule specimen (§14.2).
10. E1 with the RED pass (§14.1) — and note that E1's scope depends on item 5. If the generator
    covers the structural half, E1 is measuring a splitter that only ever emits behavioural pairs,
    which is a much narrower and easier job than §14.1 currently assumes.

**Only then:** the step-7 decision in §20.3, with the threshold written before the numbers exist.

**Meanwhile, build the pharmacy module with superpowers.** It ships either way, and every task it
executes is a data point about task shape, check latency and turn count that no paper experiment
gives you.

---

## 16. Additions to the rules and risks

Continuing findings-2's numbering.

| # | Rule |
|---|---|
| 78 | `__manifest__.py` and every `__init__.py` are generated. No card writes them. A card needing a module dependency emits `spec_conflict`. |
| 79 | One concern, one file, one owner: one ACL csv per model, one view file per model, inherit-only python files named for the model inherited. |
| 80 | Load order is expressed by numeric filename prefix, never by editing a shared list. |
| 81 | Every child declares `owns.xml_id_prefix`, `owns.models` and `owns.fields`. Every external id, `_name` and inherited field it creates is checked against them at commit, on the host. |
| 82 | A behavioural card never owns its own test file. A `touch_set` containing both `models/*.py` and `tests/*.py` is a malformed split. |
| 83 | A test card's check is that the test runs and **fails**. Its implementation card depends on it. |
| 84 | The workspace is a worktree, a container and a database clone, provisioned and destroyed together. |
| 85 | Git happens on the host; execution happens in the container. Commit is a harness operation and the `pre_commit` hooks are unreachable from inside the card, through rule 150's runner (ADR-0014). |
| 86 | The reaper kills the container before requeuing, then removes the attempt's worktree and drops the clone (amended, ADR-0011). |
| 87 | No worker connects to the template database. |
| 88 | `integrate`'s check is rung 1 on the merged tree, not a clean merge. |
| 89 | A structural card's contract cites the schema path and key. It never restates the schema. |
| 90 | Image digest, Odoo commit, addon commits and template-DB hash join the config pin. |
| 99 | The schema is drafted twice, independently, and the diff is resolved by a human. Divergence marks ambiguity in the design document. |
| 100 | A drafter marks decided fields `TODO_DECIDE` rather than guessing. A guessed `ondelete` is indistinguishable from a considered one. |
| 101 | A `semantic:` block is copied from the design document, never compressed. Paraphrasing it is the drift. |
| 102 | `schema_lint` passes before any card is emitted. A mechanical check that could have run at authoring time never becomes a human gate mid-run. |
| 103 | The schema installs as a generated stub before any card is dispatched against it. |
| 104 | If a generator can emit an artifact deterministically from the schema, it is a hook and not a card. |

| # | Risk | Mitigation |
|---|---|---|
| R34 | **Framework gravity defeats touch-set disjointness.** Default Odoo layout has three files every card touches; the gate false-rejects everything and gets demoted. | §2's conventions. Validate on a throwaway module before Phase 1 — this is a precondition, not a Phase 3 concern. |
| R35 | **The structurally perfect wrong rule.** A record rule or domain passes every rung and is semantically inverted. In this domain that means controlled substances visible to the wrong user. | Test-first pairing (§8.3), `semantic:` and `test:` keys in the schema, and E2 arm D. There is no purely structural answer. |
| R36 | **Check latency dominates the cost model.** Turns × rung latency, not turns × token price. | Check ladder (§4); rung 0 kills most failures free; template clones make rung 1 ~1 s of setup. Measure `rung1_invocations` per card from run one. |
| R37 | **Postgres is the contention point, not the models.** Parallel cards serialise on database creation and module install. | One Postgres per run, template clone per attempt (§6.4). If this fails, the parallelism differentiator does not exist in Odoo. |
| R38 | **The generated-file convention is non-idiomatic and will be reverted by a future human.** | Document in the module README and in layer 1; make the regeneration hook fail loud when a card edited a generated path (§16.21). |
| R39 | **The schema becomes a second source of truth.** Cards paraphrase `spec.yaml` into contracts; the two drift; introspection then checks the module against a stale anchor. | Rule 89 — contracts cite, never restate. Add a check: a contract containing a field list that also appears in the schema is a finding. |
| R40 | **Migration cards break retry safety once real data exists.** | `retry_safe: false`, `awaiting_review` on failure, and a data snapshot as `db_source` (§11). |
| R44 | **The anchor is wrong and nothing can tell.** Every downstream check compares against the schema, so a mistranslated design document produces a module that passes every rung while being wrong. This is the only artifact with no detector beneath it. | Two independent drafts and a diff (§5.6 step 2); `TODO_DECIDE` rather than guessing; coverage check back to the design document; stub install. None of these is a proof — the residual is real and is the price of having an anchor at all. |
| R45 | **The structural half does not need a model.** If a generator emits it deterministically, five cards per run are ceremony, and the run's cost and complexity are being paid for nothing. | Write the generator during the waiting year (§15 item 5) and measure coverage. Rule 96. This is a risk to the *design's scope*, not to correctness — the honest response is a smaller harness, not a defence. |
| R46 | **The schema becomes a view definition language.** Pressure to make the generator emit better output pulls layout, field ordering, `groups=` and help text into the schema, at which point it stops being an anchor and starts being the module. | The schema declares what rung 3 can check and nothing else. Polish is a card's job over generated scaffolding (§5.7), or it does not happen. |

---

## 17. Open questions

Recorded rather than answered, because guessing them now would be the elaboration failure the whole
v2 rewrite was correcting.

1. **Does the splitter reliably pair test cards with implementation cards, or does it emit combined
   cards that look tidier?** Rule 82 is mechanically checkable, so the failure is detectable — but
   if it happens on most children, the split jig needs restructuring rather than a gate. E1 answers.
2. **Is rung 3's introspection diff enough for the structural verify gate to run at cheap tier**, or
   does triage need judgement? §10.1 assumes cheap; unverified.
3. **How much of the pharmacy module is structural?** §8.1 assumes roughly half. If it is 20%, the
   argument in §1 is much weaker and the harness is carrying a mostly-behavioural workload with no
   semantic leaf check. Count it on the first real slice. **And note §5.7 makes this cut both ways:
   a large structural fraction is now an argument for a generator, not for the harness.**
7. **What fraction of the structural half can `tools/generate.py` emit correctly?** The number
   decides how many structural cards exist (§5.7). Anything above roughly 70% and the structural
   cards are polish over scaffolding; above 90% and they are ceremony.
8. **Do two independent schema drafts actually diverge in useful places** (§5.6 step 2), or do two
   models given the same prose make the same mistake? If they converge on a wrong answer, the only
   detector the anchor has does not work, and R44 has no mitigation at all. Testable in an hour on
   the first slice, and worth doing before trusting the pipeline.
4. **Does per-model ACL splitting interact badly with anything** — module update, uninstall, the
   Odoo apps store, OCA tooling, `pylint-odoo`? §15's step 1 exists to find out.
5. **Snapshot maintenance cost.** A representative data snapshot has to track the schema as it
   evolves, or migration cards validate against a stale shape. This may want a card kind of its own.
6. **Multi-company and multi-branch.** Assumed out of scope for a single-branch pharmacy. If it
   arrives later it touches every record rule and every ACL, which is a re-split, not an amendment.

---

## 18. Attribution

The conventions in §2 are ordinary Odoo practice pushed to an unusual extreme for a specific
reason. The test-first pairing (§8.3), the check-ladder framing, the named-risk retrieval rule and
the RED-first skill method are adapted from `obra/superpowers` (MIT, Jesse Vincent and Prime
Radiant) via `superpowers-findings` and `superpowers-findings-2`. Everything Odoo-specific is ours,
and untested until §15 runs.
