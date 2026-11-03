# Jigs, Layers and Skills — sizing and placement

**v2.** Companion to `harness-core-v3.md`, `harness-policy-v3.md`, `odoo-adaptation.md`.
Status: **derived, not observed.** Nothing here has a RED pass behind it. Where a claim
rests on the v3 documents it is cited; where it is a recommendation it is marked as one.
Sections 2 and 3 depend on §5.1's cache-scope table being correct, which is unverified.

**Changes in v2**, after reading `fhidalgodev/odoo-development-skill` at source
(114 skill files, 4 agents, 1.44 MB ≈ 360k tokens):

- §2.1 corrected — cache scope amortises **price**, not **attention**. §3.2 and §3.5
  were in contradiction; §3.5 wins and generalises. P7 widened.
- §3.6 split — the 24 version-delta files are a different genre from the pattern files
  and are the one defensible import.
- §3.7 added — two hazards on import: `agents/` and `SKILL.md`'s workflow.
- Open questions 2 and 4 merged; they are one experiment.
- Naming pass, 2026-11-03: each layer gets one fixed name (§0), and open questions 5 and 6 added.
- ADR-0008, 2026-11-03: behavioural is not a kind or a jig (§1.3), and open question 5 closed.
- ADR-0010, 2026-11-03: §3.2 separates a chooser from a table of declared card fields.

---

## 0. What this decides

Three questions that turn out to be one question.

| Question | Answer |
|---|---|
| How many jigs will exist? | Single digits. Bounded by *kind*, not by domain. |
| Where does domain content live? | Layer 2, because layer 2 is the only cheap place. |
| How do I choose skills per kind? | You don't choose. Provenance assigns them. |

The single question underneath: **what is scoped per-kind and what is scoped per-card?**
Everything below falls out of that.

### Layer names

| Layer | Name | Layer | Name | Layer | Name |
|---|---|---|---|---|---|
| 0 | `system` | 3 | `tools` | 6 | `deps` |
| 1 | `house` | 4 | `orientation` | 7 | `retry` |
| 2 | `skills` | 5 | `task` | 8 | `checks` |

The numbers stay for now; they are ids, not the send order (open question 6). `task` follows core
§3.2: `task` in code, *card* in prose, so prose may still say "the card layer".

---

## PART 1 — How many jigs

### 1.1 The bound

Jig count is bounded by `kind`, and policy §1.1 enumerates eight. Three are conditional:

```
  execute       ── ships                    ┐
  verify        ── ships                    │
  re_verify     ── ships                    ├─ the five that ship flat (§3.1)
  integrate     ── ships                    │
  digest        ── ships                    ┘

  split         ── ships, but SIZE UNKNOWN  ← may emit only behavioural pairs
                                              if generate.py covers structural (R45, §5.7)
  spec_revision ── thin, may fold into a human-authored template
  preflight     ── DOES NOT EXIST until E1 shows conflicts the
                   mechanical checks miss (policy §11)
```

Realistic ship-one count: **five, six with `split`.** Ten is the ceiling worth defending.

### 1.2 The rule

> **A new jig is justified when the output schema differs. Not when the content differs.**

This is a recommendation, not something the v3 docs state. It is proposed because it is
mechanical — you can apply it without judgement, and judgement is what inflates counts.

### 1.3 The rule applied, including where it bites

**Two jigs, correctly:**

```
execute                                verify
  status: <enum>                         gaps: [...]
  decided: [...]                         unverifiable: [...]
  open_questions: [...]                  constraints_walk: [...]
  needs / conflict / concerns            minor: [...]

  └─ structurally unrelated shapes. Two jigs. ────────────────────────┘
```

**One jig, though it looks like two:**

```
execute, behavioural card              execute, structural card
  status: <enum>                         status: <enum>
  decided: [...]                         decided: [...]
  open_questions: [...]                  open_questions: [...]

  └─ SAME SCHEMA. One jig. ──────────────────────────────────────────┘

  What actually differs:
    · the test-file guard        → a check-ladder entry  (checks.yaml)
    · the semantic: line         → an empty layer-5 slot (per-card)
    · the ORM/view knowledge     → layer 2               (per-kind)

  None of those are the jig.
```

Behavioural and structural describe the card, not a kind or a jig (ADR-0008, rule 138).

The `verify` jig already demonstrates the collapsed form: `verify_input` is a
Jinja slot with four config values, not four jigs. E2's arms are configs. Same principle,
applied to a different axis.

### 1.4 Why the bound holds: kind, not domain × kind

```
   IF domain content lives in the jig:            IF it lives in layer 2:

        execute_odoo                                   execute
        execute_terraform                              verify
        execute_django                                 re_verify
        verify_odoo                                    integrate
        verify_terraform                               digest
        verify_django                                  split
        ...                                            ─────────
        ─────────                                      6, flat
        kinds × domains, grows                         domain is a swappable
        with every domain                              skill set in config
```

The left column is how you get to tens. Nothing else does.

### 1.5 The real bound is the RED pass

Policy §1.4: a jig with no RED pass behind it is untested regardless of golden files.

```
  1 jig  ≈  20 observed failures  ≈  weeks of capture
```

You cannot afford a hundred jigs because you cannot afford a hundred RED passes. A jig
shipped without one is **worse than absent**, because it presents as coverage. Both jigs
drafted so far carry `0.1.0-GREEN-PENDING-RED` for this reason.

### 1.6 Failure mode to watch

If jigs begin multiplying to encode *which card gets which treatment*, a router has been
rebuilt in the config directory. Core §3.4 deleted that role deliberately. It does not
become acceptable by being YAML.

---

## PART 2 — Why the volume belongs in layer 2

### 2.1 Cache scope is the economics

§5.1's scope column reads as bookkeeping. It is the cost model.

```
 LAYER   NAME          CONTENT                    SCOPE        WRITTEN         READ
 ───────────────────────────────────────────────────────────────────────────────────────────
   0     system        role, contract, outcomes   per kind     once per pin    every card
   1     house         house preamble             per house    once per pin    every card
   2     skills        skills                     PER KIND     once per pin    every card
 ═══════════════════════════════════════════════════════════════════════════════════════════
   3     tools         tools                      per kind     once per pin    every card
   4     orientation   orientation                per run      once per run    every card
 ───────────────────────────────────────────────────────────────────────────────────────────
   5     task          the card                   PER CARD     every card      once
   6     deps          dependencies               PER CARD     every card      once
   7     retry         previous attempt           PER ATTEMPT  every attempt   once
   8     checks        checks                     per kind     once per pin    every card
```

Above the double line: **written once, amortised across every card of that kind, for the
life of the run.** Below it: **paid fresh, per card, per attempt.**

So the placement question is never "is this important?" It is:

> **Is this true of all cards of this kind, or only of this one?**

General knowledge sitting in layer 5 is paying per-card for a constant. It is also **R39** —
a contract restating domain facts becomes a second source of truth that drifts from the
schema. The cost argument and the correctness argument point the same way.

### 2.2 The placement test

```
                    Something you want the model to know
                                   │
                    ┌──────────────┴──────────────┐
                    │ Would it still be true if   │
                    │ the domain were Terraform?  │
                    └──────────────┬──────────────┘
                       yes ────────┴──────── no
                        │                     │
                   ┌────┴────┐    ┌───────────┴───────────┐
                   │ LAYER 0 │    │ True of every repo    │
                   │ system  │    │ doing this domain, or │
                   └─────────┘    │ only of THIS repo?    │
                                  └───────────┬───────────┘
                              every repo ─────┴───── this repo
                                    │                   │
                              ┌─────┴─────┐       ┌─────┴─────┐
                              │  LAYER 2  │       │  LAYER 1  │
                              │  skills   │       │  house    │
                              └───────────┘       └───────────┘

  Anything left over — true only of THIS CARD — is layer 5, and is the
  splitter's output, not authored content.
```

Worked:

| Content | Layer | Why |
|---|---|---|
| "Declare ambiguity, do not resolve it" | 0 | role-level, domain-free |
| The outcome enum | 0 | role-level |
| "You do not commit" | 0 | role-level |
| §2 file conventions, generated manifest | 1 | this repo |
| Banned patterns list | 1 | this repo |
| `store=True` and search domains | 2 | Odoo fact |
| 14→19 breaking changes | 2 | Odoo fact |
| "`sudo()` to pass a test" rationalization | 2 | Odoo fact |
| `touch_set` for this card | 5 | this card |
| The `semantic:` line governing this card | 5 | this card |

### 2.3 Correction to the drafted execute jig

The rationalization table was placed in layer 0. **That is wrong.** §5.1 places
rationalization tables in layer 2, beside the skills they belong to.

```
  LAYER 0 (keep)                        LAYER 2 (move)
  ─────────────────────                 ─────────────────────────────────
  "the intent is obviously X"           "sudo() here so the test passes"
  "I'll note it in the report"          "the compute doesn't need store=True"
                                        "raw SQL is faster here"
                                        "the manifest needs this dependency"
                                        "adding it to the shared views file"
```

The split is not cosmetic. The left column survives a domain change; the right column is
Odoo knowledge and travels with the Odoo skill. Leaving the right column in layer 0 is
precisely what forces `execute_odoo` to exist — §1.4's left-hand column.

### 2.4 Layer 2 is pinned, not progressively loaded

The marketplace skills assume an interactive agent that reads a version dispatcher, then
fetches the right file. **There is no such step here.**

```
  MARKETPLACE MODEL                     HARNESS MODEL
  ─────────────────                     ─────────────
  agent reads dispatcher                config pin names the skill set
        ↓                                       ↓
  agent decides which file              hash of that set enters config_hash
        ↓                                       ↓
  agent fetches it                      rendered into layer 2, cached
        ↓                                       ↓
  a MODEL CALL chose the content        a HUMAN chose it, at pin time

                                        ← this is what makes replay valid
```

Odoo version is already in the config pin (rule 90). Flatten the dispatchers: pick the
version once, take that version's content, drop the indirection.

---

## PART 3 — Choosing which skills apply

### 3.1 The matrix is six rows

The instinct is skill→*card* matching. Layer 2 is scoped per **kind**. There are five or
six kinds.

```yaml
skills:
  execute:    [odoo-orm, odoo-views, odoo-security, odoo-19-changes, house-conventions]
  verify:     [odoo-security, odoo-19-changes]
  split:      [odoo-module-anatomy]
  re_verify:  []
  integrate:  []
  digest:     []
```

That is the entire selection mechanism. Six lines, part of `config_hash`, nothing
computes it.

### 3.2 Why `execute` can hold a broad set — on the cost axis only ⚠

```
  PER-KIND (what you have)              PER-CARD (the temptation)
  ────────────────────────              ─────────────────────────
  write once ──┐                        write ─→ card 1
               ├─→ card 1               write ─→ card 2
               ├─→ card 2               write ─→ card 3
               ├─→ card 3               write ─→ ...
               └─→ ...
                                        cache defeated;
  large set = one write, cheap reads    also requires something to CHOOSE
```

A broad execute skill set is a one-time write. Narrowing it **per card** would cost more
*and* require a chooser — a model call or a heuristic over card content, which can drift
from it. That is core §3.4's deleted router returning. Knowledge narrower than a kind goes
to layer 6 instead, from a table triggered by declared card fields, which is neither
(ADR-0010).

**Confirmation that the temptation is real:** `odoo-development-skill` ships that chooser.
`agents/odoo-skill-finder.md` is an agent whose stated job is locating relevant patterns
without loading whole files into context. Someone hit this problem and productised the
answer this design declines to build. That is better evidence for the static per-kind list
than the reasoning alone.

#### ⚠ Correction to v1: this holds on price, not on effect

v1 concluded *the affordable design and the simple design coincide*. They coincide **on
the cost axis**. They may diverge on attention.

```
  CACHE AMORTISES                        CACHE DOES NOT AMORTISE
  ──────────────                         ───────────────────────
  dollars per token                      presence in the window
  written once per pin                   read by EVERY call
  ↓                                      ↓
  a 40k-token layer 2 is                 a 40k-token layer 2 is in
  paid for once                          the context of every card
```

§3.5 asserts that a skill in `verify[]` narrows what the verifier notices. **Nothing about
that mechanism is verify-specific.** Telling a model where to look reliably makes it look
there, and marginally less likely to look elsewhere. If the effect is real for a verifier
it is real for an executor.

So `execute`'s set is kept minimal too — for **attention** reasons, where `verify`'s is
kept minimal for the same reason v1 already gave. P7 is widened accordingly.

**The test is already in this document.** §3.4's ablation is per-skill. Run it **per-set**
as well, against cards the set was not written for:

```
  card the set WAS written for     ablate set → failure returns?   (does it help)
  card the set was NOT written for ablate set → detection rises?   (does it harm)
```

Same experiment, different control. It answers open questions 2 and 4 together, and it is
the only thing standing between a pinned skill corpus and unmeasured elaboration —
principle 8 applied to content, not just mechanisms.

### 3.3 Provenance assigns the kind — you never face a blank matrix

A skill exists because a card failed (§9.2). The kind that failed is the kind that gets it.

```
   20 real Odoo tasks, no skills
              │
              ▼
   ┌──────────────────────┐
   │  capture failures    │  verbatim, with the card kind that produced them
   │  (the RED corpus)    │
   └──────────┬───────────┘
              │
   ┌──────────┴───────────┐
   ▼                      ▼
 failed in            failed in
 an execute           a verify
 card                 card
   │                      │
   ▼                      ▼
 skill lands          skill lands
 in execute[]         in verify[]

   e.g. sudo() to        e.g. ratifying a
   pass a test           stated rationale
```

The label arrives with the observation. There is no design meeting.

### 3.4 Each skill ships with its RED case

```
  ┌──────────────┐
  │ observed     │
  │ failure      │──────┐
  └──────────────┘      │  paired, permanently
  ┌──────────────┐      │
  │ skill file   │──────┘
  └──────┬───────┘
         │
         ▼
  ┌──────────────────────────────────────────┐
  │ ABLATION: remove skill, rerun the case    │
  ├──────────────────────────────────────────┤
  │ failure returns   →  skill earns its keep │
  │ failure does not  →  DELETE (principle 8) │
  └──────────────────────────────────────────┘
```

The pairing does three jobs: it assigns the kind, it supplies the ablation test, and it
satisfies principle 8. Without it the corpus grows by accretion and nothing is ever
removable, because nothing records what any file was for.

### 3.5 Caveat: `verify`'s list stays thin

For an executor, layer 2 is **reference**. For a verifier it is an **attention lens**.

```
  executor + skill                  verifier + skill
  ────────────────                  ────────────────
  knows more                        looks HERE
  ↑ ceiling raised                  ↓ and, silently, less THERE
```

A skill telling `verify` to watch for `sudo()` makes it reliably find `sudo()` and makes
everything else marginally less likely to surface. `constraints_walk` exists partly to
hold attention open against this. Let CONSTRAINTS do the steering; keep verify's skill
set deliberately short.

*Unverified.* The narrowing effect is asserted, not measured. An E2 side-measurement
could test it: run arm D with and without `odoo-security` in `verify[]` against a
non-security specimen, and compare detection.

**v2:** this caveat is not a `verify` caveat. See §3.2's correction — it applies to every
kind, and the per-set ablation is the measurement for all of them.

### 3.6 Your skills will not look like the 114

```
  MARKETPLACE GENRE                     RED-DERIVED GENRE
  ─────────────────                     ─────────────────
  "here is how to write a view"         "models write X here.
  pattern documentation                  X is wrong because Y.
  complete, tutorial-shaped              write Z instead."
  long                                  correction, short, specific
  may change no output                  changes a known output, provably
```

The 114 files are a map of which failures a real Odoo shop hit often enough to write down.
Worth reading for that signal. Not worth pasting — inherited elaboration is still
elaboration, and principle 8 applies to content you did not write.

#### The exception: the 24 version-delta files

`odoo-*-14-15.md` through `odoo-*-18-19.md` are a **different genre** from the pattern
files, and v1 did not separate them.

```
  PATTERN FILE                          DELTA FILE
  ────────────                          ──────────
  "here is how to write a view"         "X changed to Y between 18 and 19"
  tutorial-shaped, complete             correction-shaped, bounded
  asserts a preference                  asserts a fact
  may change no output                  changes output when the model's
                                        prior skews to an older version
```

The delta files arrive at the RED-derived shape by a different route: they are corrections,
they are short, and what they correct is not a matter of taste. They also answer a failure
you can predict without observing it — **a model whose training skews toward an older Odoo
writing older patterns into a newer module** — which is partly caught by `pylint-odoo` and
partly not.

**This is the one place where importing beats deriving**, because the delta is a property
of Odoo rather than a pattern someone likes. Take the deltas for the two versions that
bracket your pin, flatten them per §2.4, and leave the other 90 files as reading.

### 3.7 Two hazards on import

Neither is in v1, and both bite at copy time rather than later.

**`agents/` violates rule 65.** Four subagent definitions ship with the repo, including
`odoo-code-reviewer`. Any content lifted from that directory carries instructions to spawn
reviewers, and **a card never emits its own reviewer** — gates are pinned by the splitter.
Strip the directory on import; do not mine it for prose.

**`SKILL.md`'s workflow is antagonistic in four specific ways.** It is written for an
interactive agent with a browser, not for a card:

| Its instruction | Why it cannot come across |
|---|---|
| Detect the version by reading `__manifest__.py` | The manifest is generated (rule 78); the version is in the config pin (rule 90) |
| Exhaustive OCA/GitHub search before developing anything | Layer 3 denies network — and adding a dependency is `spec_conflict`, not an executor's call |
| Communicate in Spanish | Output-schema violation |
| "Don't reinvent the wheel" as an executor workflow | A real concern, but a **splitter-time** decision — it belongs in the split jig or in the schema's `depends`, never in an executor's preamble |

The fourth is worth keeping rather than merely deleting: dependency reuse is a genuine
question, and relocating it to the splitter is the correct answer rather than a workaround.

---

## 4. Rules proposed

| # | Rule |
|---|---|
| P1 | A new jig is justified when the output schema differs, not when the content differs. |
| P2 | Domain knowledge never lives in a jig. If a jig needs a domain name in its filename, the content is misplaced. Check-ladder rungs hold domain commands, but they live in `checks.yaml`, not the jig (rule 137). |
| P3 | Rationalization table rows live in layer 2 with their skill, except rows that survive a domain change. |
| P4 | Skill sets are selected per kind, by hand, at config-pin time. Nothing computes them. |
| P5 | Every skill file ships paired with the RED case that motivated it. |
| P6 | A skill whose RED case no longer reproduces on ablation is deleted, not kept as margin. |
| P7 | **Every kind's skill set is kept minimal.** Cache amortises price, not attention: a pinned skill set is read by every call of that kind. For `verify` specifically, CONSTRAINTS is the lens and the set stays shortest. |
| P8 | Imported skill material is stripped of anything that spawns an agent. A card never emits its own reviewer. |
| P9 | Imported material is stripped of anything requiring network, version detection from generated files, or a decomposition decision. Those belong to the config pin or the splitter. |
| P10 | Version-delta content may be imported. Pattern documentation is derived from a RED pass or not adopted. |

## 5. Open questions

1. Does `split` need domain skills at all, or does `generate.py` absorb the structural
   half and leave splitting domain-neutral? (Blocks the `split:` row above. R45, §5.7.)

2. **[merged, was 2 and 4] Does a pinned skill set narrow attention, and at what size?**
   v1 filed these separately — one as a `verify` caveat, one as a corpus-size curiosity.
   §3.2's correction shows they are the same question about every kind, and they have one
   experiment: per-set ablation against cards the set was not written for. **This is now
   the load-bearing uncertainty in Part 2**, because §2.1's cost argument does not
   survive a positive result.

3. Is one shared `execute` jig genuinely sufficient across structural and behavioural
   cards, or does the test-file guard turn out to need more than a check-ladder entry?

4. **[new] Do the version-delta files change output on this pin?** The predicted failure —
   older patterns written into a newer module — is assumed, not observed. It is the
   cheapest thing in this document to test: run five real cards with and without the
   `18-19` delta in `execute[]` and count version-inappropriate constructs. If the delta
   changes nothing, §3.6's exception closes and nothing is imported at all.

5. **[closed, ADR-0008] What is the cache scope of layers 0 and 3?** Per kind: both come from the
   jig, and each kind has one jig. Policy §5.1 now agrees with §2.1 here.

6. **[new] Where does layer 8 belong?** `jig-sketch.py` sends it before layer 4, so it sits in the
   cached prefix; the docs list it last. Checks read last may get more attention, which is
   measurable. Do not renumber until that is measured.
