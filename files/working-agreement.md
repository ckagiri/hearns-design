# Working agreement

**How work is shaped, sized, reviewed and recorded in H3.**

Read this before writing a card, a contract or a jig. The design documents say what the substrate
guarantees. This says what a unit of work *is* — and the splitter, the execute jig and the review
gate all need that answer before any of them can be written.

Everything here is a property of a row on the board. Nothing here is a convention you have to
remember; where it matters, a gate enforces it.

---

## 1. The shape of the work

Three tiers. Each is a row in `cards`, distinguished by `tier`.

| Tier | Is | Accepted by | Produces |
|---|---|---|---|
| **Epic** | a module boundary: one oracle, one interface surface | the human rules on it at intake — then again when its stories are proposed | a branch merged over days |
| **Story** | a vertical slice that can be accepted or rejected whole | **the human** | one branch, three to six commits |
| **Card** | one acceptance criterion, or one technical step inside a slice | `verify` | one commit |

An epic's parent is null. A story's parent is an epic. A card's parent is a story.

**An epic owns one thing.** One package tree, one schema, one domain document, one service
interface, one set of published events. If it needs two domain documents, it is two epics. Platform
and build epics are the exception: no bounded context, no interfaces, and the build is the oracle.

**A story is a use case.** *Register a customer.* *Verify an email.* The epic is what those live
inside.

**An epic is a container, not a large use case.** A use case has an actor walking a path with
success and failure branches — that is a story. An epic is the boundary those belong to.

**Epics are constrained by `deps` and ordered by `rank`.** Both are roots; neither nests.

- **`deps`** is structural: this epic consumes an interface that one produces. Satisfied only by
  `done`, so an epic cannot start until its dependency has landed, and if one blocks, everything
  behind it sits visible and unclaimable. It must match `interfaces.consumes`, and the intake gate
  checks that.
- **`rank`** is judgement — value, risk, learning — over the epics that are unblocked. It is the
  human's, it has no mechanism, and it is expected to change. Re-ranking is an `UPDATE`; re-ordering
  `deps` would invalidate a decomposition.

Claim order is `priority DESC, rank ASC, id`.

**Not every epic splits.** A vertical slice through every layer — a walking skeleton, a spike, a
single configuration change — cannot be partitioned without its children colliding on the same
files. Its root is `kind: execute` and its tree is one node deep.

**There is no tier below `card`.** A card that cannot be done as one commit is a story that was
mis-typed. Say so — return `misclassified` — and it is replaced by a split. A card that cannot be
split without inventing facts is not too big; it is under-specified, and the outcome is
`needs_context`.

**A split may conclude there is nothing to split.** If no two parts of the work have separable
acceptance decisions, the split ends `atomic` and emits nothing. The original card is restored as
`execute` and cannot refuse the same way twice; a second `misclassified` on it is a `spec_conflict`,
because the system has now been told two contradictory things about one card and that is a human's
call.

Emitting nothing and saying why is a legitimate answer. Emitting one child that is a copy of the
parent is not — that is a level of nesting pretending to be a decomposition.

---

## 2. What makes something a story

> **Could a reviewer sensibly accept this and reject its neighbour?**

If yes, they are two stories. If the acceptance decision is the same for both, they are one.

This is the only sizing rule. It is not about hours, files, line counts **or acceptance-criterion
count**, because the story tier exists to be the unit a human reads and rules on — so the thing that
defines it is whether a ruling on it is separable.

**Many criteria can be one story.** Registration that validates an email, enforces password rules,
hashes the password, publishes an event and shapes its errors is six criteria and one ruling: you
would not accept it with the hashing missing. They are facets of one deliverable.

**One extra deliverable makes two stories.** A profile update that also introduces an audit trail is
two, because the audit trail could be rejected while the update is accepted. What separates them is
that the audit work touches a table nothing else in the story touches — which is what the emit gate
looks for.

Consequences worth stating:

- **A story is a vertical slice.** It touches whatever layers it needs to. A story that is "the
  database part" of something has no acceptance decision of its own.
- **Setup, configuration, scaffolding and documentation fold into the story whose deliverable needs
  them.** They are not separable rulings.
- **A story is never split into child stories.** Two nested things both claiming to be the
  acceptance unit is incoherent. Split it into independent sibling stories, or into cards within it.
- **Repeated small edits across many sites are one card**, whose contract enumerates every site.
  Not one card per site.
- **Two stories are one if their cards cannot be separated** — no shared files, no dependency
  between them, means two components and two stories. This is checked at emit.

---

## 3. Scope is declared, and it is a boundary

Every card declares `touch` before it runs. What it actually edits is checked against that
declaration after it commits, on the host, where the card cannot reach.

So scope is not advice. It is the thing two gates key on:

- Siblings whose declared touch sets intersect are rejected at emit — they cannot safely run at once.
- A card whose commit touches paths outside its declaration is rejected as fact, after the event.

**Work outside the contract is an observation, not an edit.**

If you notice something that should change and it is not needed for the work you were given, return
`done_with_concerns` and describe it. It becomes a card. It costs a row and changes no diff.

If restructuring *is* needed to land the feature, it belongs in the story: declared in `touch`, named
in `acceptance`, done as part of the work. That is not scope creep — it is the scope.

Three reasons this line is where it is:

1. A card that edits outside its declaration either trips the commit-time gate or forces touch sets
   to be widened until the collision gate stops meaning anything.
2. `verify` answers *did it do what was asked*. That question has no answer against a diff containing
   work nobody asked for.
3. The human reads a story as one diff. A hundred lines of feature plus two hundred of tidying is
   two rulings wearing one row.

Cross-cutting cleanup that spans modules is its own epic, framed around the risk it removes, with the
same six intake fields as any other.

**Work with no acceptance decision in it is its own card.** Generated scaffolding, a mechanical
rename, a formatter pass — none of these carry a ruling, so they get a `chore` card of their own and
never dilute a diff that does carry one. A diff should contain one kind of thing.

---

## 4. Defects

**Found while the story is open → a card under that story.**

Not a new story, not a separate report. The story is simply not done. The card gives the fix a
contract, an attempt record, a verify pass and a commit — without which the fix is a decision that
never became a row.

**Found after the story landed → a story of its own.**

Its first card writes the failing test, and that card's exit criterion is that the test **fails**.
Only then does a fix card run, depending on it. A bug story therefore has a sharper oracle than a
feature story: there is something concrete beneath the work that catches a mistake.

**Urgent and in production → an epic with `priority: 1` and no `deps`.**

Cards are claimed in `priority DESC, id` order, so a priority epic is claimable immediately, ahead of
everything queued before it.

> **Priority is set at intake, by the human, and never by a card.** A card that can raise its own
> priority is an escalation channel.

**Repeating in the same area → an architectural epic.** You do not have to notice the pattern.
Repeated fix stories with overlapping touch sets is a query.

---

## 5. Done

Done means something different at each tier. Say which one you mean.

| Tier | Done means |
|---|---|
| **Card** | Checks pass, `verify` passed, merged into the story branch, **and the story branch is still green** |
| **Story** | Every card done, branch green, **the human accepted it**, merged to `main` |
| **Epic** | Every story accepted. The next epic unblocks |

A card whose own checks pass is not done. Nothing is done until it is merged and the merged tree is
green, because the question that matters is whether the system works, not whether a card's tests do.

A story the human kills is requeued with the reason attached, exactly as a verify rejection is. The
round counter applies. A story killed twice is a signal about the epic, not about the story.

---

## 6. Commits

One card, one commit, one type.

```
feat(item)!: rename returns the updated item

Refs: E01 / S01.2 / AC3
Card: 0f3a91c
BREAKING CHANGE: rename previously returned None
```

The trailers follow the git trailer convention: a token, a colon and a value.

**The trailer is load-bearing.** It is the join between the two records — the commit is the
artifact, the card id is the row, and `h3 why <card>` goes from one to the other. A commit without
it is a diff whose reasoning is unreachable.

**A commit that fits two types is two cards.** You do not have to notice this; a card produces one
commit and carries one type, so the question cannot arise.

### The type is derived, not chosen

Nothing writing a commit picks its type. The harness computes it from the card, and rung 0 rejects a
mismatch.

| Type | Derived from |
|---|---|
| `test` | the card is a test card (`exit: red`) |
| `fix` | the card's story sits under a defect epic |
| `docs` | `touch ⊆ docs/**` |
| `ci` | `touch ⊆ .github/**` |
| `build` | `touch` includes a build or dependency manifest |
| `chore` | a scaffolding card, or `touch` is configuration only |
| `refactor` | a gap card emitted by `done_with_concerns` |
| `perf` | the card's acceptance criterion states a numeric threshold |
| `feat` | default |

Scope is the module, which is the epic. Also derived.

Deriving rather than choosing is what makes the type trustworthy enough to count, and counting types
across a week is most of what the convention is for.

**`style` is an error.** Formatting is rung 0's job. A `style` commit means the formatter is not in
rung 0, or something is bypassing it — fix the ladder, do not accept the commit.

**`perf` requires a number.** A performance card's acceptance criterion states the threshold, which
means it has an oracle. Without one it is `refactor` with an optimistic message.

**`revert` is rare by construction.** A story killed at review never merged, so there is nothing to
revert. `revert` exists only for something that reached `main` and was wrong — which makes its
frequency a signal about the review gate rather than about the code.

### Breaking changes are detected, not declared

Every epic declares `interfaces.produces`. A card whose diff changes a symbol that another epic's
`consumes` names is a breaking change — that is a lookup against the board, not a judgement.

**Rung 0 computes it on the host and the harness appends the `!` and the footer.** Nothing is asked
to self-declare, because a model asked to self-declare will under-declare, for the same reason it
under-refuses.

A breaking change is not a rejection. It is a fact that appears on the story's review row, so you
see it before you accept, and it appears in `h3 state` so downstream epics can be re-examined.

A story's `git log --oneline` is three to six lines and reads as a changelog.

## 7. Tests

**Where a behaviour has a stateable semantic, the test is its own card**, and the implementation card
depends on it.

The test card's exit criterion is that the test **fails**. The implementation card is constructed
without write access to `tests/`, so it cannot edit what it must satisfy. That is a gate, not an
instruction — absence of a tool is the enforcement.

**The ladder is config, and no card can change it.** `checks.yaml` declares the rungs and is pinned
into the config hash. A card cannot add a rung, remove one, or alter what a rung runs.

**Rung 0 runs on the host and is the only rung a card cannot reach.** It cannot be seen, run, or
tuned against from inside a workspace. Rungs 1 and above run in the workspace, so a card can execute
them iteratively and reach the files they run — which means rung 0 is what polices the rungs above
it, not a cheaper version of them. Put the domain's real oracle there.

**A test card carries named assertions**, not prose — an example table where the behaviour is
data-shaped, a property where the claim is an invariant, a bare named id where neither fits. Rung 0
checks that one test exists per id, named for it, failing on its own assertion, with every table row
present as a case. Five assertion ids per card; more means the card is two. See `assertions.md`.

**Where the behaviour has no stateable semantic** — a rename, a config change, a doc update — one
card, **and no assertions**. Say so in the contract rather than manufacturing one.

A test that asserts nothing but is named as though it does is a defect, and it is caught statically.

---

## 8. Questions

A card that lacks facts returns `needs_context` and stops. It does not guess, and it does not resolve
toward the likeliest reading.

The question becomes a row. The human answers in a batch. **The answer attaches to the epic, not to
the asking card** — so every card under that epic has it, a question answered once is never asked
twice, and *why is it done this way* is answerable from the board a year later.

`needs_context` is not a failure. It is the only signal in the system that is feedback on the intent
rather than on the work, and its count per epic is watched.

---

## 9. What is not tracked

- **Estimates.** Attempts per accepted story is the number the board produces. Nothing else is
  recorded.
- **Ceremonies.** `h3 state` is generated from the board on every merge and is current by
  construction.
- **Work-in-progress limits.** The review gate is the limit, set by how fast the human reads.
- **Branch policy beyond card → story → `main`.** No release branches, no environments, until
  something is deployed and the reason is recorded.

---

## 10. What would change this

- **`done_with_concerns` is never returned while touch-set violations rise** — §3's boundary is being
  ignored rather than followed. The answer is a gate, not a stronger instruction.
- **Defect cards outnumber a story's original cards** — stories are being scoped optimistically, and
  the problem is at intake rather than in execution.
- **`rank` never diverges from dependency order** — the dependency graph is making product calls
  that should be yours.
- **Priority is used on more than the rare urgent epic** — it has become a scheduling knob, which is
  a planning failure wearing a mechanism's clothes.
- **Story diffs routinely run to several hundred lines** — the story tier is mis-scoped, and either
  §2's criterion is being applied loosely or a tier is missing.
- **Stories are killed with "this is two stories"** — the separability check is too permissive, and
  it gets tightened against those cases rather than against a threshold someone picked.
- **Test cards pass while the implementation is wrong** — the tool-set gate is not holding, or the
  test card's exit criterion is not being checked for actually failing.
- **Rung 0 never fails** — it is a deletion candidate, or the domain's oracle has drifted into a rung
  the workspace can reach.
- **`style` commits appear** — the formatter is not in rung 0, or something is bypassing the ladder.
- **`revert` commits appear more than rarely** — things are reaching `main` that the review gate
  should have caught. That is a signal about the gate, not about the code.
- **Breaking changes are frequent and always accepted** — either `interfaces.produces` is drawn too
  wide, or module boundaries are not holding.
- **`needs_context` never fires** — cards are guessing. That is more serious than any of the above,
  because it is invisible in every other metric.
