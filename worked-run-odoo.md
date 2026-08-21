# A Worked Odoo Run

**Status:** extends §24 of `harness-design-v2` (which is eight lines and abstract). Not a new design
document (rule 63) — this is the same run, made concrete, to test whether the mechanisms actually
compose.
**Companions:** `odoo-adaptation`, `superpowers-findings-2`, ADR-0001.

**How to read it.** One run, in time order. Every artifact is shown as the system would actually
store it. §-references point at the mechanism being exercised. Failures are not collected into a
separate section — they happen where they happen, which is the point.

**What this is for.** A walkthrough is the cheapest test of a design that has never run. Three
things in v2 only look composable in prose, and writing the run out is how you find that: the
interaction of `retry_safe` with the container kill, what `integrate` actually checks, and whether
the verify gate has anything useful to say once introspection has already spoken.

---

## Part 0 — Before the harness

### 0.1 Two days earlier · `/superpowers:brainstorm`

The harness has no front end and should not grow one. It starts from a root intent and a schema,
and §19 says five minutes of writing beforehand removes a refusal, a drift gap and a round of
review. `brainstorm` is that five minutes done properly, and it is a shipped tool.

```
T-2d 09:10  /superpowers:brainstorm "prescription capture and controlled dispensing"
            → classifies: architectural (new subsystem, new interfaces others depend on)
            → 14 clarifying questions, one at a time
            → 3 approaches with trade-offs
            → sectioned design, approval per section
T-2d 11:40  → docs/specs/2026-08-13-pharmacy-dispensing-design.md, committed
```

Four of the fourteen questions are the ones that matter, and all four resolve things that would
otherwise have surfaced as a refusal or a spec conflict mid-run:

| Question | Answer | What it prevented |
|---|---|---|
| Does "readable only by pharmacists" mean the record, or the controlled lines within it? | The whole record. | The ambiguity behind §4.5's inverted rule — narrowed, though not eliminated |
| What is an audit entry? | Undecided at this point — flagged as open | Nothing. **See §0.3.** |
| Single branch, or multi? | Single. | An entire dimension of record rules |
| Dispensing against a lot with no expiry date? | Undecided — flagged as open | Nothing. **See §4.3.** |

Two of the four are recorded as open and carried into the design document unresolved. That is the
correct behaviour — `brainstorm`'s hard gate is approval, not resolution — but note where those two
reappear in this run: as a spec conflict at T+48:00 and a `needs_context` at T+26:44, costing two
human gates and roughly thirty minutes of blocked cards.

> **Amendment to §19.** A root intent's CONSTRAINTS lines are only as good as the design's open
> questions are closed. Add to the root-intent lint (Part 10, item 2): a CONSTRAINTS line whose
> supporting design section is marked open is a lint failure, not a card's problem to discover. Both
> of this run's human gates were foreseeable at T-2d.

### 0.2 The design document becomes the schema

`brainstorm` produces prose. The harness needs `spec/pharmacy.schema.yaml` (odoo-adaptation §5.1),
which is prose plus types. That translation is a human sitting down for an hour, and it is where the
DONE MEANS check becomes executable rather than aspirational.

It is worth doing by hand at least once. Writing the schema is what surfaces that `is_controlled`
needs `store: true`, that the ACL matrix has a hole for `unlink`, and that "audit entry" names
nothing — three of this run's four interruptions, all visible while typing YAML, none of them
visible in the prose design.

```
T-1d 14:00  spec/pharmacy.schema.yaml written from the design doc
T-1d 15:20  human review, committed
            → named in the root intent's OUT OF SCOPE as unmodifiable
```

### 0.3 The fork · `write-plan`, or let the harness split

This is the decision point, and both branches are legitimate.

**Path A — `write-plan`, harness ingests.** `/superpowers:write-plan` produces a plan whose task
blocks already carry Files (your `touch_set`), Interfaces consumes/produces (findings-2 §2.2) and a
Global Constraints header (your layer 4). A loader maps each task to an `execute` row and each
`Interfaces` block to edges, and the harness runs from there.

What this buys: **R1 — splitter quality, your top risk — is removed from the run entirely.** The
decomposition is human-reviewed before anything executes. If the harness then beats SDD on a plan
they both consumed, the win is attributable to the ledger and parallelism, which are the two
differentiators you can actually defend. It also gives you the false-rejection test from
odoo-adaptation §14.3 for free: run the emit-time gates against a plan that demonstrably worked, and
if they reject it, the gates are wrong.

**Path B — the harness splits.** What this run does, because the split jig is the thing under test
and Path A never exercises it.

```
T+3:00  splitter claims t-7c21
```

**Recommendation, stated once.** Run **A first, then B on the same schema**, and diff the two
decompositions. That comparison is E1 with a human-authored control, which E1 as written does not
have — §18.1 scores three model samples against each other and against your reading, with nothing
independent to anchor on. A `write-plan` plan is that anchor, and it costs one extra afternoon.

The rest of this document is Path B.

### 0.4 The root intent (§19)

```
INTENT
  Add prescription capture and controlled-substance dispensing to the pharmacy
  module. A pharmacy user records a prescription and dispenses against it; a
  prescription containing a controlled item is readable only by pharmacists.

DONE MEANS
  make check-static                                        # rung 0
  odoo-bin -d $DB -i pharmacy --stop-after-init            # rung 1
  odoo-bin -d $DB -i pharmacy --test-enable --test-tags /pharmacy  # rung 2
  python tools/introspect.py --spec spec/pharmacy.schema.yaml --db $DB  # rung 3, empty diff

OUT OF SCOPE
  Multi-branch and multi-company. Insurance claims. Supplier reordering.
  POS integration. Do not build for hypothetical future requirements.
  Do not modify spec/pharmacy.schema.yaml.

WHAT YOU SHOULD KNOW
  The module already installs and contains res.partner extensions for patients
  and prescribers (is_patient, is_prescriber). Odoo 18 series, Community.
  Lots are stock.lot. Product expiry uses use_expiration_date /
  expiration_date on the lot, from stock. No OCA addons in this module.

SHAPE
  Wide and shallow. Structural work (models, fields, views, menus, ACLs) fans
  out cheap. Behavioural work (record-rule domains, state guards, batch
  selection) is a test card then an implementation card. Expect ~11 leaves.

CONSTRAINTS                                       ← copied verbatim into layer 4
  - Dispensing must never select a lot whose expiration_date is in the past.
  - A prescription line quantity may not exceed the prescribed quantity.
  - Controlled-substance prescriptions are readable only by
    pharmacy.group_pharmacist. This is a regulatory requirement, not a
    preference.
  - Every state transition writes an audit entry. No transition is silent.
```

### 0.5 The schema is the anchor (odoo-adaptation §5.1)

`spec/pharmacy.schema.yaml` is committed, human-reviewed, and named in OUT OF SCOPE as unmodifiable.
Every structural contract will *cite* it rather than restate it (rule 89).

### 0.6 Run provisioning

```
T+0:00  image  pharmacy-runner:sha256:4b1e…       (Odoo 18.0 @ e91c2a, py3.12, wkhtmltopdf 0.12.6)
T+0:00  postgres container up, one for the run
T+0:04  createdb odoo_tmpl
T+0:04  odoo-bin -d odoo_tmpl -i base,stock,product,account,sale_management --stop-after-init
T+2:51  template ready.  hash tmpl-9f3c
T+2:51  config pinned (§14.2): image digest + odoo commit + tmpl-9f3c + model versions
```

Two minutes fifty-one seconds, once. Every card attempt after this gets a database in about a second
(odoo-adaptation §6.4). Without the template this run would spend roughly forty minutes installing
`base` and friends.

### 0.7 Workers

Six processes. Two `execute/cheap`, two `execute/strong`, one `split|verify/strong`, one
`integrate|digest/strong`. Nobody is assigned anything (§5.1). Poll only; notification is skipped
for run one per §20.

---

## Part 1 — T+3:00 · The split

A splitter worker claims `t-7c21` (kind `split`, tier `strong`). Layers 0–4 assemble; layer 4 is the
generated structure summary from `odoo_tmpl` plus the CONSTRAINTS block verbatim (odoo-adaptation
§9.1).

It emits eleven children, a preflight, and three gates, in one transaction (§7.5).

### 1.1 A structural child, as stored

```jsonc
{
  "id": "t-7c21.1",
  "kind": "execute", "tier": "cheap", "root_id": "t-7c21",
  "contract": "Create the models declared at spec/pharmacy.schema.yaml#models. Field names, types, comodels, required flags and selection values are authoritative there — do not restate them here or in code comments.",
  "check_spec": {"rungs": [0, 1, 3]},
  "touch_set": ["models/pharmacy_prescription.py",
                "models/pharmacy_dispense_line.py",
                "models/product_template.py"],
  "owns": {
    "xml_id_prefix": "pharmacy.model_",
    "models": ["pharmacy.prescription", "pharmacy.dispense.line"],
    "fields": {"product.template": ["pharmacy_is_controlled", "pharmacy_schedule"]}
  },
  "interfaces": {"consumes": [], "produces": [
      "pharmacy.prescription", "pharmacy.dispense.line",
      "product.template.pharmacy_is_controlled", "product.template.pharmacy_schedule"]},
  "open_questions": [
    "the schema does not say whether is_controlled on the prescription is stored; a rule domain will need it stored"
  ],
  "retry_safe": true,
  "contract_completeness": "complete"
}
```

Note the `open_questions` entry. The splitter noticed a real gap and did not resolve it. Whether
that pays off is §5.3 below — it is ADR-0001's whole bet.

### 1.2 A behavioural pair

```jsonc
{ "id": "t-7c21.6", "kind": "execute", "tier": "strong",
  "contract": "Write tests/test_controlled_substance_access.py asserting the semantic at spec/pharmacy.schema.yaml#rules.pharmacy.prescription[0]: a user in pharmacy.group_pharmacy_user and NOT in pharmacy.group_pharmacist cannot read a prescription containing a controlled item, and CAN read one that does not. Do not implement the rule.",
  "check_spec": {"rungs": [0,1,2], "expect": "FAIL"},        // ← RED, rule 83
  "touch_set": ["tests/test_controlled_substance_access.py"],
  "interfaces": {"consumes": ["pharmacy.prescription", "product.template.pharmacy_is_controlled",
                              "pharmacy.group_pharmacist", "pharmacy.group_pharmacy_user"]},
  "deps": ["t-7c21.1", "t-7c21.2"] }

{ "id": "t-7c21.7", "kind": "execute", "tier": "strong",
  "contract": "Implement the record rules at spec/pharmacy.schema.yaml#rules. The semantic is stated there; derive the domain. tests/test_controlled_substance_access.py must pass and is not yours to edit.",
  "check_spec": {"rungs": [0,1,2,3]},
  "touch_set": ["security/30_pharmacy_prescription_rules.xml"],
  "owns": {"xml_id_prefix": "pharmacy.rule_"},
  "deps": ["t-7c21.6"] }
```

`.7`'s `touch_set` does not contain the test file. Rule 82 is satisfied and, more usefully, the
commit-time namespace/touch-set hook (odoo-adaptation §3.2) makes it *unable* to edit the test even
if it decides the test is wrong. That is the property §8.3 says is otherwise unavailable: a check
written by another party, at another time, that the checked party cannot reach.

### 1.3 The emit-time gate runs (§7.4, odoo-adaptation §3.2)

No model call. Four checks over the eleven children:

```
touch-set intersections            : none
xml_id_prefix prefix-collisions    : none
model double-declaration           : none
(model, field) double-declaration  : none
consumes → produces resolution     : 23 symbols, 23 resolved, all with edges
placeholder scan                   : clean
```

Split accepted. The splitter marks itself `done`, `outcome='expanded'`, and walks away (§7.1). Its
`result_summary` is about the decomposition, not the work.

**T+4:12.** Fifteen rows on the board. Nothing is scheduled.

---

## Part 2 — T+4:12 · Preflight

`t-7c21.P` is the only card whose deps are satisfied; the eleven children depend on it
(findings-2 §4.1). A strong worker claims it.

It emits a table, not a verdict:

| A | B | shares | A produces | B consumes | finding |
|---|---|---|---|---|---|
| .1 | .3 | — | `pharmacy.prescription` | model name in ACL rows | ok |
| .1 | .4 | — | field list | view fields | ok |
| .1 | .7 | — | `pharmacy_is_controlled` | rule domain | **`is_controlled` on the prescription is a compute; the schema does not declare `store`. An unstored compute cannot appear in `ir_rule.domain_force`.** |
| .2 | .3 | — | group xml ids | ACL group refs | ok |
| .6 | .7 | test file | — | — | ok — .7 does not own it |

One finding, and it is the same gap `.1`'s `open_questions` flagged, found independently by a
different party from a different direction. That is the uncorrelated-blind-spots argument
(ADR-0001) firing at split time rather than at verify time, which is cheaper.

Preflight cannot amend the schema (it is the anchor, §8.1), so it emits:

```
t-7c21.S   kind=spec_revision   state=awaiting_review
   "spec#models.pharmacy.prescription.fields.is_controlled needs store: true.
    An unstored compute cannot be used in ir_rule.domain_force (rule .7 requires it)
    or in a search view filter. Proposed: add store: true and depends: line_ids.product_id."
```

**T+4:40.** The human gate (§12) has one item. The eleven children are blocked behind preflight,
which is still `leased` — this is the serialisation cost odoo-adaptation §4.1 warned about, and here
it cost 28 minutes of a human's response time rather than 28 seconds of compute.

**T+21:00.** Human approves. Schema updated by the human, not by a card. Preflight commits `done`.
Eleven children become runnable at once.

> **What just got tested.** The preflight card earns its place here — the finding was real, and
> catching it now saved `.7` a full failed attempt plus a re-split. But it also cost a human gate on
> the critical path with everything blocked behind it. **E1's question about preflight
> (odoo-adaptation §14.1) should measure both.** If the finding rate is one per run and the block
> cost is twenty minutes, preflight is worth it only when a human is attentive — which contradicts
> the unattended-operation claim. Consider: preflight blocks only the children implicated in a
> finding, not all of them. That is a `deps` change, not a new mechanism.

---

## Part 3 — T+21:00 · The happy path, fully traced

Five cards go runnable and get claimed within seconds. Follow `t-7c21.1`.

### 3.1 Workspace provisioning (odoo-adaptation §6.1)

```
T+21:02  git worktree add .wt/t-7c21.1 -b card/t-7c21.1 <base-sha>
T+21:03  createdb -T odoo_tmpl card_t7c21_1_a1                    (1.1 s)
T+21:04  docker run -d --network run-net --read-only=false \
           -v $PWD/.wt/t-7c21.1:/mnt/addons/pharmacy \
           --memory 2g --cpus 2 pharmacy-runner:4b1e…              → cid 8ae3f1
T+21:06  lease written: worker w3, fence 41, container 8ae3f1, db card_t7c21_1_a1
```

The lease row carries the container id, because the reaper will need it (odoo-adaptation §6.3).

### 3.2 Context assembly (§9.2)

| Layer | Tokens | Content |
|---|---|---|
| 0 | 480 | executor role, four-status contract, refusal rules |
| 1 | 810 | house preamble — one-file-one-owner, generated manifest, no `sudo()`, ORM-not-SQL |
| 2 | 1,640 | the Odoo skill + its rationalization table |
| 3 | 390 | file edit, `odoo-bin` in-container, psql read-only on the clone. **No network.** |
| 4 | 1,120 | generated structure summary from `odoo_tmpl` + CONSTRAINTS verbatim |
| 5 | 310 | the contract, `owns`, `interfaces` |
| 6 | 0 | no dependencies |
| 7 | 0 | attempt 1 |
| 8 | 160 | rung definitions |
| | **4,910** | |

Under five thousand tokens for a card that will write three model files. That is §9.1's governing
principle doing its job — and note that layer 4's accuracy came from a SQL query, not a summary.

### 3.3 The work

The card reads `spec/pharmacy.schema.yaml`, writes three files, runs rungs in the container.

```
$ make check-static                                    # rung 0, in-container copy
  python compile        ok
  xml wellformed        ok  (0 files)
  csv shape             ok  (0 files)
  pylint-odoo           ok
  namespace prefixes    ok  (0 xml ids, 2 models, 2 inherited fields — all declared)
  placeholder scan      ok
  → 0.9s

$ odoo-bin -d card_t7c21_1_a1 -i pharmacy --stop-after-init   # rung 1
  … Modules loaded.
  → 22.4s

$ python tools/introspect.py --spec spec/pharmacy.schema.yaml --db card_t7c21_1_a1  # rung 3
  missing   : 0   (of the models in scope for this card)
  extra     : 0
  divergent : 0
  → 1.6s
```

### 3.4 The summary (§4.2)

```json
{
  "headline": "2 models + 2 inherited fields per spec#models",
  "counts": {"models": 2, "fields_new": 11, "fields_inherited": 2},
  "notable": ["is_controlled implemented as stored compute with depends=line_ids.product_id, per the approved spec revision"],
  "warnings": [],
  "decided": [{
    "what": "used ondelete='restrict' on patient_id and prescriber_id",
    "why": "the schema names restrict for patient_id and is silent for prescriber_id; a dangling prescriber on a dispensed prescription is an audit gap",
    "cost_if_wrong": "deleting a prescriber partner raises instead of nulling; visible immediately to whoever tries; one-line reversal"
  }],
  "artifacts": {"diff": "c-8b2f", "branch": "card/t-7c21.1"}
}
```

### 3.5 Commit, on the host (odoo-adaptation §6.2)

The card returns. The harness — not the card — runs the `pre_commit` hooks:

```
touch_set check     : 3 files modified, 3 declared           ok
namespace check     : ast + xml parse over the diff          ok
manifest regenerate : data list unchanged (no data files)    ok
decided/open_questions set difference (§8.3):
    open_questions : ["store on is_controlled"]
    decided        : ["ondelete on prescriber_id"]
    → open question NOT addressed in decided
```

**The set-difference detector fires.** It is a warning, not a rejection — the question was resolved
upstream by the spec revision, so the executor had nothing to decide. The hook cannot know that.

> **What just got tested, and it is not good news.** ADR-0001's detector produced a false positive
> on the *first structural card of the run*, for a structural reason: an `open_question` resolved by
> a spec revision stays in the child's stored contract and can never be matched by any `decided`.
>
> **Amendment required.** The set difference must exclude open questions closed by an intervening
> approved `spec_revision`. That is a join, not a judgement — `open_questions` entries need an
> optional `closed_by` field written when a spec revision that cites them is approved.
>
> Add to §15.2's mismatch metric: report *unresolved* mismatches, not raw ones, or the metric reads
> as alarming from run one. This is exactly the "high mismatch on cards that turn out fine" case
> ADR-0001 lists under **What would change our mind** — and it would have demoted the check from
> gate to warning on bad evidence.

Commit lands. `t-7c21.1` → `done`. Container killed, database dropped, worktree kept for
`integrate`.

**T+22:04.** 64 seconds of card time, 24.9 seconds of it check latency. Cost: one cheap model call,
~4.9k in, ~2.1k out.

### 3.6 The fan-out

`.2` (groups), `.3` (ACLs), `.4` and `.5` (views + menus) run in parallel across four workers. All
cheap. All rung 0/1, `.3` also rung 3.

```
t-7c21.2  groups          done  T+21:58  cheap  1 attempt   18.1s checks
t-7c21.3  ACL matrix      done  T+22:41  cheap  1 attempt   24.0s checks
t-7c21.4  prescription views  →  see Part 4 — this one does not go cleanly
t-7c21.5  dispense views  done  T+23:10  cheap  1 attempt   23.7s checks
```

Four structural cards, four parallel database clones, no contention, no collisions. §2's conventions
are the reason `.3`, `.4` and `.5` do not all want `ir.model.access.csv` and `pharmacy_views.xml`.

---

## Part 4 — The unhappy paths

### 4.1 `t-7c21.4` · The card that reached for a file it did not own

The views card writes list, form and search views for `pharmacy.prescription`, and decides the form
would be better with the controlled-substance flag visible on the product line — which means adding
a field to `product.template`'s form view.

It writes `views/40_product_template_views.xml`. Not in its `touch_set`.

**Rung 0, in-container, catches it before any database is touched:**

```
$ make check-static
  touch_set check : views/40_product_template_views.xml modified, not declared
  → FAIL (0.7s)
```

The card sees the failure — rung 0 is runnable in-container, so it is not hidden — reverts the file,
and returns `DONE_WITH_CONCERNS` (findings-2 §2.1):

```json
{
  "outcome": "done_with_concerns",
  "headline": "3 views for pharmacy.prescription per spec#views",
  "warnings": ["the product.template form does not surface pharmacy_is_controlled; a user cannot see which products are controlled while building a prescription. Outside my touch_set."],
  "decided": [...]
}
```

**Three things worth noticing.**

The concern is *correct and outside scope* — precisely the case §16.8 (quiet scope creep) exists to
prevent, and the card did the right thing. Without `done_with_concerns` in the enum this observation
would have arrived as either a silent omission or an out-of-scope edit. It arrives as a routed
signal instead, and the verify gate will read this summary first (odoo-adaptation §7).

The rung-0 check being *visible* to the card is what made self-correction possible. Contrast the
commit-time hooks, which are hidden. The distinction is deliberate and worth stating as a rule:
**checks the card can fix are visible; checks that establish trust are hidden.**

And it becomes a verify gap in Part 7, which is the system working as designed — an observation
became a card, one level up, rather than an edit.

### 4.2 `t-7c21.9` · The card that was not a card

`t-7c21.9` — *"implement prescription state transitions and their guards"* — is claimed by a strong
executor at T+24:02.

Its contract cites `spec#models.pharmacy.prescription.fields.state` and the CONSTRAINTS line about
audit entries. The executor reads it and finds: four states, transitions unspecified, guards
unspecified, "audit entry" undefined — no model, no format, no retention. The check is
`tests/test_prescription_state.py`, which `t-7c21.8` wrote and which asserts three transitions and
nothing about auditing.

It refuses (§8.1):

```json
{
  "outcome": "misclassified",
  "reason": "The contract names one deliverable but the work is three with different check surfaces: (a) the state field's transitions and guards, checked by .8's tests; (b) an audit model that does not exist in the schema and has no declared shape; (c) wiring every transition to write one. I cannot state a check for (b) because there is nothing to check against.",
  "emits": [{"kind": "split", "tier": "strong", "contract": "<same intent>",
             "notes": "audit entry is undefined in spec#models; likely spec_conflict"}]
}
```

**Cost: one strong model call, 31 seconds, no database.** Compare the alternative — an executor that
can only succeed or fail invents an `pharmacy.audit.log` model, which is then extra in rung 3's
introspection diff, and a human is arguing about a model nobody asked for at the verify gate.

The replacement `split` card is claimed at T+24:40. It reads the same contract and reaches the same
conclusion the refusal predicted, and emits `spec_conflict` rather than children:

```
t-7c21.9.S  kind=spec_revision  state=awaiting_review
   "CONSTRAINTS requires 'every state transition writes an audit entry', but spec#models
    declares no audit model. Options: (a) add pharmacy.audit.entry to the schema;
    (b) use mail.thread + message_post, which is the Odoo-native answer and adds a
    dependency on mail; (c) drop the requirement. (b) changes manifest.depends, which
    is root-intent-owned."
```

> **What just got tested.** The refusal path works and it is cheap. But note the shape: a refusal
> produced a split, which produced a spec conflict. Two model calls and a human gate to discover
> something a careful reading of the root intent against the schema would have found at T+0. This is
> an argument for a **root-intent lint** — a rung-0-style check that every CONSTRAINTS line names
> something the schema can express. Cheap, mechanical, runs before the split. Add to §19.

**T+48:00.** Human picks (b). `manifest.yaml` gains `mail`. Because the template database was built
without `mail`, the template is rebuilt (`tmpl-a04d`) and the config pin updated (§14.2). Cards
already `done` are not re-run — their diffs are unaffected — but this is the first thing in the run
that could not be fixed by a card, and it cost three minutes of rebuild plus the human's time.

### 4.3 `t-7c21.11` · Attempt 1, the missing fact

The batch-selection card — *dispense must never select a lot whose `expiration_date` is past* — is
claimed at T+25:10. Its test card `.10` has already landed RED.

At T+26:44 it returns `NEEDS_CONTEXT`:

```json
{
  "outcome": "needs_context",
  "reason": "Lots reach expiration_date through stock.lot, but whether this database's products have use_expiration_date set — and therefore whether expiration_date is populated at all — is not in my context and I cannot query production. If it is unset, the correct behaviour is a different question (block dispensing? warn?) and the CONSTRAINTS line does not cover it.",
  "needs": ["whether pharmacy products set use_expiration_date", "behaviour when expiration_date is null"]
}
```

This is not a refusal and not a failure. The card is correctly sized and correctly typed; it is
missing two facts.

**Without `needs_context` in the enum, this arrives as `misclassified`** and triggers a re-split of
a card that did not need splitting — one wasted strong call, one wasted split, and a tree that is
one level deeper than it should be for no reason.

The harness routes it to `awaiting_review`. The human answers in one line, the answer is appended to
the root intent's WHAT YOU SHOULD KNOW, layer 4 is recomputed, and the card is re-dispatched at the
same tier.

> **The metric that falls out.** `needs_context` count per root intent is a direct measurement of
> §19's WHAT YOU SHOULD KNOW quality. Two on this run, both real. Add to §15.2. It is also the only
> outcome in the enum that is feedback on *the human* rather than on the system.

### 4.4 `t-7c21.11` · Attempt 2, the zombie

Re-dispatched at T+51:00. Lease 900 s. The card gets into a long loop — writing a compute, running
rung 2, reading the failure, rewriting — and at T+66:00 the lease expires without a heartbeat
(§5.6): the container is CPU-saturated and the heartbeat thread starved.

**T+66:03.** The reaper wakes. Under v2 as written it would flip the row to `pending` and a second
worker would claim it — while container `d19a70` is still running, still editing
`.wt/t-7c21.11/models/pharmacy_dispense_line.py`.

Under odoo-adaptation §6.3, in order:

```
T+66:03  docker kill d19a70                      → exit
T+66:04  dropdb card_t7c21_11_a2                 → gone
T+66:04  git -C .wt/t-7c21.11 reset --hard <base>; git clean -fdx
T+66:05  UPDATE tasks SET state='pending', attempts=2 WHERE id='t-7c21.11'
```

Fencing (§5.5) already guaranteed the stale writer could not commit. The kill guarantees it cannot
*write*, which fencing never did. §16.6 closes.

**Attempt 3 is the final attempt, so it escalates one tier** (rule 68, findings-1 §1.4). It is
already `strong`, so escalation is a no-op — worth recording, because rule 68 as written has nothing
to say about a card that starts at the ceiling. **Amendment:** at the ceiling, the escalation
becomes a fresh-eyes framing instead — the previous attempts' check output enters layer 7 with
*"two prior attempts; read their failures; you own this now"* (their rounds-4-5 framing). Attempt 3
passes at T+71:20.

### 4.5 `t-7c21.7` · The one that matters

This is the card odoo-adaptation §5.4 and R35 are about. Watch it carefully, because it is the only
place in the run where a wrong answer is indistinguishable from a right one by every structural
means available.

`.6` (the test card) landed at T+29:00, RED as required:

```python
# tests/test_controlled_substance_access.py
@tagged('post_install', '-at_install')
class TestControlledAccess(TransactionCase):
    def test_plain_user_cannot_read_controlled(self):
        rx = self._prescription(controlled=True)
        with self.assertRaises(AccessError):
            rx.with_user(self.plain_user).read(['name'])

    def test_plain_user_can_read_uncontrolled(self):
        rx = self._prescription(controlled=False)
        rx.with_user(self.plain_user).read(['name'])   # must not raise
```

`.7` is claimed at T+29:20. Its contract gives it the *semantic* — a non-pharmacist may not read a
prescription containing a controlled item — and requires it to derive the domain.

**Attempt 1** produces:

```xml
<record id="rule_controlled_pharmacist_only" model="ir.rule">
  <field name="model_id" ref="model_pharmacy_prescription"/>
  <field name="groups" eval="[(4, ref('pharmacy.group_pharmacy_user'))]"/>
  <field name="domain_force">['|', ('is_controlled','=',False), ('create_uid','=',user.id)]</field>
</record>
```

Trace it against every check the system has:

| Check | Result | Why |
|---|---|---|
| rung 0 static | **pass** | valid XML, prefix `pharmacy.rule_` declared, `touch_set` respected, no `sudo(` |
| rung 1 load | **pass** | model ref resolves, group ref resolves, domain fields exist |
| rung 3 introspect | **pass** | `ir_rule` row exists, right model, right group — the schema declares the rule's existence, not its domain |
| summary plausibility | **pass** | *"added record rule restricting controlled prescriptions to pharmacists; module loads"* |
| `decided`/`open_questions` | **pass** | nothing flagged either side; neither party registered an ambiguity |

**Five mechanisms, five passes, and a non-pharmacist can read every controlled prescription created
by anyone, plus every uncontrolled one — the `|` should be `&` and the second clause should not be
there at all.**

Then rung 2 runs:

```
FAIL: test_plain_user_cannot_read_controlled
  AssertionError: AccessError not raised
2 tests, 1 failed
```

**The test card caught it. Nothing else did, and nothing else could have.**

> **This is the single most important thing in the run.** R35 says there is no purely structural
> answer to the structurally perfect wrong rule, and this trace is the proof: introspection, the
> load check, the static check, the summary and ADR-0001's pair all pass on a rule that inverts a
> regulatory constraint. The only mechanism that fires is a check written by a different card, at a
> different time, that this card cannot edit.
>
> Two consequences:
> - **Rule 82/83 is not a nice-to-have, it is the load-bearing mechanism for the behavioural half.**
>   Treat any split that fails it as a hard rejection, not a warning.
> - **E2 arm D should use this exact specimen** (odoo-adaptation §14.2). Feed the verify jig the
>   four-line diff plus the `semantic:` line and see whether it catches what the summary hides. If
>   arm D fails on a specimen this small and this well-framed, summary-reading verify is not merely
>   weaker than diff-reading — the whole gate is decoration on the behavioural half, and the design
>   should say so.

Attempt 2, with the failure in layer 7:

```xml
<field name="domain_force">[('is_controlled','=',False)]</field>
```

Both tests pass. `decided` now carries the thing that was invisible in attempt 1:

```json
"decided": [{
  "what": "the rule excludes controlled prescriptions from group_pharmacy_user entirely rather than granting an owner exception",
  "why": "the CONSTRAINTS line is unconditional — readable only by pharmacists — and an owner exception would let a non-pharmacist read a controlled prescription they created",
  "cost_if_wrong": "a pharmacy user cannot see a controlled prescription they entered themselves; visible on their first attempt; reversible by adding a clause"
}]
```

Note that `cost_if_wrong` is writable here, which findings-1 §3 says is the refusal signal in
reverse: the executor understood the choice this time. On attempt 1 it did not, and the empty
`decided` was accurate — it genuinely had not noticed it was choosing.

**That is ADR-0001's failure mode observed rather than argued.** Drift is resolving an ambiguity you
did not register as one; the field is empty exactly when it matters. The pair did not save it. The
test did.

### 4.6 `t-7c21.I` · Integrate, and the thing that only breaks when assembled

All eleven leaves terminal at T+72:40. `t-7c21.I` claims, merges eleven branches.

```
git merge: 11 branches, 0 conflicts
```

Zero conflicts — §2's conventions doing exactly what they were for. Under stock Odoo layout, `.1`
through `.5` and `.7` would all have touched `ir.model.access.csv` and `pharmacy_views.xml`.

Then the gate's real check runs — rung 1 on the merged tree (rule 88):

```
$ odoo-bin -d card_integrate_a1 -i pharmacy --stop-after-init
ParseError: Element '<xpath expr="//field[@name=\'product_id\']">' cannot be located
  in parent view, in views/40_pharmacy_dispense_line_views.xml
```

`.5` inherited a node that `.4`'s form view restructured. **Each card installed cleanly alone. The
module does not install assembled.**

Nothing before this point could have caught it — not the touch-set check (different files), not the
interface check (no symbol involved), not preflight (the xpath did not exist when preflight ran),
not either card's rung 1 (each saw only its own branch on a clean template).

`integrate` emits a gap card scoped to `.5`'s file, tier cheap, contract quoting the ParseError.
Resolved at T+79:15. Re-merge, re-rung-1, clean.

> **What just got tested.** Rule 88 is not bookkeeping — it is the only check in the system that
> ever sees the module whole before verify, and it caught something real on the first try. Also
> worth recording: `integrate` needs its own workspace triple, which §11 does not currently say.
> Merging is a git operation but *checking the merge* needs a container and a clone.

---

## Part 5 — T+79:30 · Verify

`t-7c21.V` becomes runnable when the last sibling goes terminal — clause (b), §5.1. Nobody schedules
it.

### 5.1 Structural verify: introspection has already spoken

Rung 3 against the merged tree:

```
missing   : 0
extra     : 1   →  ir_ui_view 'pharmacy.prescription_form_inherit_product' declares
                   type=form on product.template; not in spec#views
divergent : 0
```

The `extra` is `.4`'s reverted-then-reintroduced attempt at the product form — a fragment survived
the revert. A computed finding, no model call, no judgement. It becomes a gap card: delete it.

**The structural verifier's model call adds nothing here.** The diff is computed; the "gap" is one
row. This is odoo-adaptation §17's open question 2 answered on one data point: for structural work,
verify is a *query plus a formatter*, and paying strong tier for it is waste. Tier it cheap, or make
it a hook.

### 5.2 Behavioural verify: reading diffs, per findings-2 §1.4

Input: the `touch_set` diffs of `.7`, `.9`, `.11`; the CONSTRAINTS block; the `semantic:` lines.
Not summaries.

Three channels out (findings-2 §2.3):

**gaps (→ cards):**
1. The stray `product.template` view fragment (from 5.1).
2. `.4`'s reported concern — nothing surfaces `pharmacy_is_controlled` on the product form, so a
   user building a prescription cannot see which items are controlled. The verifier reads `.4`'s
   `done_with_concerns` summary first, per triage, and confirms it against the merged view set.
   **A concern raised by a card two hours earlier becomes a card here, having travelled through the
   summary rather than through an out-of-scope edit.**
3. `pharmacy.dispense.line` has no ACL row for `group_pharmacist` with `unlink` — the schema
   declares it; rung 3 says present; the *diff* shows the row was added with `perm_unlink=0` and the
   schema says 1. Rung 3 missed it because `introspect.py`'s ACL comparison only checked existence,
   not the four permission columns. **That is a bug in the oracle, found by the diff-reading gate.**

**unverifiable (→ notes, nobody chases them):**
- *"Whether the batch-selection compute in `.11` respects the expiry constraint under concurrent
  dispensing cannot be determined from this diff — it depends on lot reservation semantics in
  `stock`, outside the module."*

**minor (→ deferred list for the root gate):**
- Two docstring gaps, one non-standard field ordering.

> **Three things this section establishes.** The `unverifiable` channel earned itself immediately —
> under v2's single-channel gate, that concurrency observation becomes a *card*, and some poor
> executor is asked to prove something about `stock`'s reservation semantics with a `touch_set` of
> one file. Gap 3 is the argument for arm D in miniature: a computed oracle with a coverage bug was
> caught by a model reading four lines of csv diff, which is exactly the complementarity the design
> hopes for and has never demonstrated. And the fact that gap 3 exists at all means **`introspect.py`
> needs its own tests** — the oracle is code, it can be wrong, and when it is wrong it is wrong
> silently and systematically. Add to §17.4's mutation testing: mutate the schema, assert the oracle
> notices.

Three gap cards run and land. `t-7c21.V2` (a `re_verify`, findings-2 §2.4) verdicts each: ADDRESSED,
ADDRESSED, ADDRESSED; no new breakage in the fix diff; one out-of-scope observation ledgered. Round
1 of 5. No loop.

---

## Part 6 — T+94:00 · Digest

Three queries (findings-2 §4.3), not a summarisation.

**Rulings** — every `decided` entry in the subtree, in commit order, with `cost_if_wrong`:

```
t-7c21.1   ondelete='restrict' on prescriber_id — schema silent, dangling prescriber is
           an audit gap — deletion raises instead of nulling; one-line reversal
t-7c21.7   controlled prescriptions excluded from group_pharmacy_user entirely, no owner
           exception — CONSTRAINTS is unconditional — a user cannot see a controlled
           prescription they entered; reversible by adding a clause
t-7c21.9.1 audit via mail.thread rather than a bespoke model — Odoo-native, human-approved
           — message_post is not a tamper-evident log; if regulators require one, this is
           a re-do, not a patch
t-7c21.11  null expiration_date treated as "do not dispense" rather than "warn" — human
           answered; CONSTRAINTS says never dispense past-expiry and null is not evidence
           of non-expiry — blocks dispensing of any lot with no expiry date set
…          (7 more)
```

**Deferred minors:** 3 rows. **Unverifiable:** 1 row, the concurrency question.

The third ruling is the one a human needs to see and would never have found in a diff. `mail.thread`
was approved as an audit mechanism at T+48:00 in a one-line answer, and the card that implemented it
recorded a consequence the approver did not consider. It sits in the digest with its cost attached.

> A ruling that dies with the workspace was a decision made in secret. Here it is a `SELECT`, so it
> cannot be lossy and cannot be skipped by a model that ran out of attention — which is strictly
> stronger than the discipline it was borrowed from.

---

## Part 7 — What the run cost

| | |
|---|---|
| Wall clock | 94 min (of which 49 min human gate latency across 3 gates) |
| Compute wall clock | 45 min |
| Cards | 11 leaves + 1 preflight + 3 gates + 4 gap cards + 1 re-verify + 2 refusal-emitted = 22 |
| Model calls | 27 (5 strong on gates/behavioural, 14 cheap, 8 strong on behavioural leaves and retries) |
| Attempts | 27 across 22 cards — 3 retries, 1 refusal, 1 needs_context, 1 reap |
| Database clones | 31 |
| Check latency | 19 min total, 42% of compute wall clock |
| Rung 0 rejections | 4 (three touch-set, one placeholder) — cost 3.1 s total |
| Peak parallelism | 5 |

**Rung 0 is the whole cost story.** Four failures caught in three seconds that would each have cost
a clone, an install and a model turn — call it four minutes and four calls. The check ladder is the
mechanism that makes R36 survivable, and it is also the cheapest thing in the design to build.

**Check latency at 42% of compute wall clock** is the number to watch. The template database keeps
it from being 80%. It also means adding workers past five buys less than it looks like it should —
the bound is Postgres and `-i`, not the model. **Add `rung1_invocations` and `check_latency_total`
to §15.2 from run one.**

---

## Part 8 — What nothing caught

Stated because a worked example that ends in success is not evidence.

**The `mail.thread` audit decision.** Approved in a one-line human answer under time pressure, at a
gate that presented three options and no consequences. `message_post` is not tamper-evident. If the
regulator requires an immutable log, this is a re-do of every transition. The digest records it —
*after* the work is done. **Nothing in the design puts `cost_if_wrong` in front of a human at the
moment of approval, only after.** §12.5's interface shows four verbs and the card's contract. It
should show the emitting card's `cost_if_wrong` too, when one exists. That is a one-field change and
it is the difference between an informed approval and a fast one.

**The concurrency question.** Correctly classified `unverifiable`, correctly not chased, correctly
surfaced. And still unanswered — a channel that routes a question to a human is not a channel that
answers it. Fine, provided nobody reads the digest as an assurance.

**The second-order effect of ruling four.** Treating a null `expiration_date` as "do not dispense"
is defensible and was approved. Its consequence — every product without expiry tracking enabled
becomes undispensable — is a data-migration problem for the pharmacy, not a code problem, and no
card owns it. It is in the digest as a cost, which is the most the system can do.

**Whether the module is any good.** Eleven cards, every rung green, introspection clean, tests pass.
Nobody has dispensed anything. §17.1's three problems stay separate: the harness worked, the jigs
worked, and whether the *module* works is a question for the pharmacist.

---

## Part 9 — Mechanism audit

Which mechanisms actually fired, since a design's cost is paid for all of them and its value comes
only from the ones that do something.

| Mechanism | § | Fired? | Verdict |
|---|---|---|---|
| Readiness clause (b) | 5.1 | yes | verify waited correctly for `.9`'s refusal-spawned subtree |
| Fencing | 5.5 | yes | stale writer's commit rejected |
| Container kill before requeue | oa 6.3 | yes | **closed §16.6; fencing alone was insufficient** |
| Touch-set emit-time gate | 7.4 | no collisions | untested — §2's conventions may have made it unnecessary rather than satisfied |
| Touch-set commit-time hook | 7.4 | yes ×3 | cheapest useful check in the system |
| Namespace prefix check | oa 3.2 | no violations | untested this run |
| `interfaces` resolution | f2 2.2 | yes, at emit | 23/23 resolved; no failure to observe |
| Preflight | f2 4.1 | yes, 1 finding | real finding, but blocked 11 cards behind a human gate |
| Refusal → split | 8.1 | yes | 31 s to avoid inventing a model |
| `needs_context` | f2 2.1 | yes | would have been a wasted re-split under v2's enum |
| `done_with_concerns` | f2 2.1 | yes | routed an out-of-scope observation into a gap card |
| `decided`/`open_questions` set difference | ADR-0001 | **false positive** | needs `closed_by`; metric must report unresolved only |
| `decided` on the case it exists for | ADR-0001 | **empty when it mattered** | attempt 1 of `.7` — the predicted failure, observed |
| Test-card-first | oa 8.3 | **yes — sole catch** | the only mechanism that caught the inverted rule |
| Rung 0 | oa 4 | yes ×4 | 3.1 s to avoid ~4 min and 4 calls |
| Rung 3 introspection | oa 5.2 | yes, 1 extra + **1 coverage bug** | oracle needs its own tests |
| Rung 1 on merged tree | rule 88 | yes | caught what nothing else could see |
| Verify: gaps | 8.3 | yes ×3 | one of them a bug in the oracle |
| Verify: unverifiable | f2 2.3 | yes ×1 | prevented an unanswerable card |
| Verify: minors | f2 2.3 | yes ×3 | deferred, read at root gate |
| `re_verify` | f2 2.4 | yes, 1 round | no loop; the cap never engaged |
| Tier escalation on final attempt | rule 68 | **no-op** | card was already at ceiling; needs the fresh-eyes fallback |
| Digest as query | f2 4.3 | yes | surfaced the audit consequence |
| Judge | 7.6 | never | supports deleting it (f2 3.2) |
| Verify at intermediate depth | 8.4 | never — tree was flat except `.9` | supports shipping flat (f2 3.1) |

**Reading the column.** The mechanisms that fired hardest are the cheap mechanical ones — rung 0,
the commit-time touch-set hook, rung 1 on the merged tree — plus the one social mechanism,
test-card-first. The most elaborate mechanism in the design, ADR-0001's pair, produced one false
positive and one silence-when-it-mattered, which is a 0-for-2 on a single run and exactly the result
its own **What would change our mind** section anticipated.

Two rows never fired at all, and both are things findings-2 already argued for cutting.

---

## Part 10 — Amendments this exercise produced

Each names its target. None is a new design.

1. **§8.3 / ADR-0001** — `open_questions` entries take an optional `closed_by`, written when an
   approved `spec_revision` cites them. §15.2's mismatch metric reports unresolved mismatches only.
2. **§19** — add a root-intent lint: every CONSTRAINTS line must name something the schema can
   express. Mechanical, runs before the split. Would have caught the audit gap at T+0 instead of
   T+48.
3. **findings-2 §4.1 (preflight)** — preflight blocks only the children implicated in a finding, not
   all children. A `deps` change.
4. **Rule 68** — at the tier ceiling, escalation becomes a fresh-eyes framing in layer 7 rather than
   a no-op.
5. **§11** — `integrate` needs a workspace triple. Merging is git; checking the merge is a container
   and a clone.
6. **§12.5** — the human-gate interface shows the emitting card's `cost_if_wrong` when one exists.
   Approval before consequence, not after.
7. **§17.4** — `introspect.py` gets mutation tests: mutate the schema, assert the oracle notices.
   The oracle is code and this run found a coverage bug in it.
8. **§15.2** — add `rung1_invocations`, `check_latency_total`, `needs_context_count`,
   `unresolved_mismatch_rate`.
9. **New rule 91** — checks a card can fix are visible to it; checks that establish trust are hidden
   from it. Rung 0 in-container, commit hooks host-side.
10. **odoo-adaptation §10.1** — structural verify is a query plus a formatter. Tier it cheap or make
    it a hook.
11. **§19 / the root-intent lint** — a CONSTRAINTS line whose supporting design section is still
    marked open is a lint failure. Both of this run's human gates were foreseeable at T-2d, in the
    `brainstorm` output (§0.1).
12. **§18.1 (E1)** — run `write-plan` on the same schema and diff its decomposition against the
    splitter's. E1 currently scores three model samples against each other with no independent
    anchor; a human-reviewed plan that executed successfully is that anchor (§0.3).

---

## Part 11 — The honest summary

The run succeeded, and the mechanism audit says most of the credit belongs to four cheap things:
rung 0, the commit-time touch-set hook, rung 1 on the merged tree, and a test written by a card that
could not edit it. None of those four is architecturally interesting. Three of them are hooks.

The interesting mechanism — the summary-reading verify gate with a commission detector — was
outperformed by a computed diff on the structural half and by a pre-written test on the behavioural
half, and its own detector misfired once and stayed silent once.

That is one run, on paper, and it proves nothing. But it is the shape of result E2 exists to
confirm or refute, and the specimen in §4.5 is small enough to run for real in an afternoon. If arm
D catches the inverted rule and arm A does not, the design's centre of gravity moves from the pair
to the diff — and the pair becomes what findings-1 §3 said `open_questions` already was
independently useful for: feedback on splitter quality.

The parts of the design that carried this run — the board, the predicate, content-derived ids,
crash recovery with a kill handle, and the fact that nothing anywhere held a plan — never appear in
the narrative, because working infrastructure is invisible. Ninety-four minutes, one reaped
container, zero re-dispatched completed work. That is the differentiator, and it is the one nobody
disputes.
