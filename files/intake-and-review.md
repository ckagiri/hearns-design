# Intake and review — how work enters the board and how a human accepts it

**Status:** proposal. One new mechanism (the intake gate), one new vocabulary (epic / story / card),
one reframing of an existing table (`reviews`). Everything else is existing machinery pointed at a
new job.

**The shape it assumes:** the human is a product and engineering manager. The harness is a senior
engineer. Nobody hands a senior engineer a project; they hand them an epic, review the stories, and
read the commits.

---

## 1. The problem this closes

The design gates the splitter's **output** — touch-set collision, `edge_carries_nothing`, the kind
ratchet, the commit-time hook — and gates nothing on its **input**.

That asymmetry is expensive in a specific way. A thin root intent costs an entire subtree of cards,
each with a workspace, a container, a clone and a model call, and the failure surfaces as a *bad
decomposition*. So you blame the splitter, tune the split jig, and the jig accumulates rules tracing
to a problem it did not have — R51 arriving through a door nothing is watching.

The root is also the one card with **nothing beneath it to catch a mistake**. That is R44's shape,
generalized: every other card can be checked against its parent's contract, and the root has no
parent.

---

## 2. Three tiers, three review semantics

| Tier | Row | Emitted by | Reviewed by | Artifact |
|---|---|---|---|---|
| **Epic** | `parent = null`, `kind: split` | the human, at intake | intake gate, then you approve its stories | a milestone |
| **Story** | child of an epic, `kind: split` | `split` on the epic | **you — accept or kill** | one branch, one PR-sized diff |
| **Card** | child of a story, `kind: execute` | `split` on the story | `verify`, no human | one commit |

`project` is an attribute on every row, not a tier — it is what makes *everything ever decided about
this product* a `WHERE` clause. Core §12 already flags it as unretrofittable, so it exists.

**Epics are siblings, not a chain of parents.** Sequencing is `deps` between root cards, using the
ordinary predicate. `SATISFIES_DEP = {"done"}` then means an epic cannot start until the previous one
actually landed, and if one blocks, the rest sit visible and unclaimable behind it — which the stall
query surfaces. No new mechanism.

### What an epic is

**An epic is a unit with one oracle and one interface surface.** In practice that is a module
boundary: one package tree, one schema, one domain document, one service interface, one set of
published events. If it needs two domain documents, it is two epics.

That definition is not a description — it hands you the six intake fields directly:

| Intake field | Read from |
|---|---|
| `touch` | the module's package tree and its migration directory |
| `interfaces.produces` | the module's service interface and the events it publishes |
| `interfaces.consumes` | the modules and shared libraries it depends on |
| `oracle` | the domain document |
| `non_goals` | what depends on this module — the surfaces that must not change |

**An epic is a container, not a large use case.** A use case is a single closed actor-goal
interaction with a beginning, an end and failure paths — *register a customer*, *verify an email*.
That is a story. An epic has no actor walking through it start to finish; it is the boundary saying
these use cases belong to the same slice of the system.

### Ordering: `deps` constrains, `rank` decides

These are two different kinds of fact and the design previously conflated them.

**`deps` is structural and checkable.** E03 cannot start before E01 because it consumes `Customer`.
An epic's `deps` should resolve to exactly the modules its `interfaces.consumes` names — and where
they diverge, the intake gate says so. That extends `edge_carries_nothing` up to the epic tier,
where it currently does not reach.

**`rank` is a judgement and it is the human's.** Dependency gives a partial order — what is
*possible*. Everything unblocked at a given moment is a set, and choosing within that set is a call
about value, risk and learning: which epic tells you fastest whether the idea works, which removes
the biggest unknown, which a stakeholder needs first.

```yaml
E03:
  deps: [E01]          # structural. Gated. Changing it invalidates a decomposition.
  rank: 20             # judgement. Yours. Changing it is an UPDATE.
```

Claim becomes `ORDER BY priority DESC, rank ASC, id`.

**Why they must not be the same field.** Encoded as `deps`, a preference edge is indistinguishable
from a structural one six months later, is wrong the moment you change your mind, and carries no
signal that it was ever soft. Worse, re-ordering the roadmap becomes an edit to the dependency graph
— so the cheapest thing is to keep following it, and dependency order quietly makes the product
decisions. That produces technically clean, business-blind sequencing.

> **Detector:** if `rank` order and topological order never diverge, either the work genuinely is a
> chain, or the dependency graph is making the product calls. One query, and it belongs beside the
> cost table in `h3 state`.

**Platform and infrastructure epics are the exception**, and should be honest about it. They have no
bounded context, no `interfaces`, and their oracle is the build.

**Three tiers, not five.** Standard agile practice runs Initiative → Epic → Feature → Story → Task.
Initiative and Feature exist to coordinate across teams and sprints; H3 has one human and N workers,
so neither would carry reviewer semantics distinct from its parent — and a tier whose review
semantics match its parent's is nesting, not a tier. See `depth.md` §2.

> **Reopening trigger for a fourth tier:** an epic that cannot be reviewed by one person in one
> sitting. That is the same condition standard practice gives for introducing a Feature level, and
> if it fires it probably means a second human, which is a different design.

**Not every epic splits.** A walking skeleton is vertical by construction: one thin path through
every layer, so it cannot be partitioned without violating touch-set disjointness. Its root intent is
`kind: execute` and the tree is one node deep. This case is not currently written down anywhere, and
the kind ratchet implies it without stating it.

---

## 3. The plan lives on the board

The obvious home for a phase plan is `plan.md`. That is a plan held outside the board, which is the
one thing the design forbids.

**A plan is a sequence of epic rows in `draft`.** Draft rows are visible, cost nothing, are not
claimable, and build no workspace — the same trick as children of a blocked parent staying pending.
`h3 plan` lists them in `deps` order. You promote one at a time.

So a brainstorming session produces five or six draft epics, each a paragraph. Not a document. Rows.

---

## 4. The epic intent: six fields, each earned by a gate

**The human owns these. Owning is ruling on them, not typing them.**

Most of the six are *read*, not invented — off the module's package tree, its service interface, its
domain document, its dependents. A session can draft all six and should, because after the first
epic the honest source for `interfaces.consumes` is the repository rather than anyone's memory of
it. What makes them the human's is that **none of them lands without a ruling**, and the ruling is
where the thinking happens: rejecting a draft field is how you find out what the field has to
contain.

The argument for each is not that it is good practice — it is that a specific mechanism cannot fire
without it.

| Field | What breaks without it |
|---|---|
| `contract` | Layer 5 has nothing to render as root intent into every descendant |
| `acceptance` | The leaf criterion has nothing to partition along; the splitter invents the reviewer's decisions |
| `touch` | The emit-time disjointness gate and the commit-time hook both key on touch sets |
| `interfaces` | `edge_carries_nothing` needs a `produces` vocabulary to resolve `consumes` against |
| `oracle` | Check ladder rung 3 has no anchor. R44, locally |
| `non_goals` | Coverage scoring can catch omission but not invention — nothing said the extra card should not exist |

**`acceptance` is the one field to rule on hardest.** It is the least derivable — nothing in a
repository tells you what a reviewer would accept — and it is what the splitter partitions along.
A draft is a starting point; the corrections are the work.

**Deliberately under-decomposed:** three to five entries for an epic that will become eight or twelve
cards. Twelve entries means it has been hand-decomposed and the splitter has nothing left to do.

**Acceptance decisions, not tasks.** The single highest-leverage instruction to a human:
*describe what you would accept or reject, not what should be done.* Tasks force the splitter to
reverse-engineer the reviewer's decisions from the work. Decisions give it the partition.

Each entry should name what a reviewer judges **on** — "on state transitions alone", "on what is
shown, not on storage". That phrase is what keeps two acceptance decisions from being accepted or
rejected together, and it is what a splitter reads to keep their touch sets apart.

### Worked example — `E01`

```yaml
id: 0
project: todo
parent: null
kind: split
status: draft
deps: [E00]

contract: |
  Complete the item lifecycle: mark done, mark not-done, rename, delete.
  Extends the walking skeleton; does not redesign it.

acceptance:
  - A1: an item can be marked done and marked not-done again
        (judged on state transitions alone)
  - A2: an item's text can be changed, keeping its identity
  - A3: an item can be removed and does not come back

touch: [ "src/todo/**", "tests/**" ]

interfaces:
  consumes:
    - Item          # src/todo/model.py:Item      ← read from the repo
    - Store         # src/todo/store.py:Store     ← not invented
  produces:
    - mutate_item

oracle:
  - spec/todo-flat.md
  - pytest
  - "empty list, one item, all-completed, all-active"

non_goals:
  - No filters, no counts, no clear-completed. Later epics.
  - Do not change Item's shape or Store's interface. If you need to,
    that is a spec_conflict, not a refactor.
```

**`consumes` names real symbols read off the repository**, because E00 already landed. That is the
schema-anchor move one level up: after the first epic, the human stops inventing interface names and
starts reporting them. It is also why epic ordering matters more than it looks.

**The last non-goal is a boundary only writable because the skeleton exists** — and it is what stops
three parallel stories each quietly redesigning the store.

---

## 5. Intake is a session, not a card

A card is claimed by a worker, holds a lease, runs in a worktree, and heartbeats. A human is none of
those. Make intake a card and you have put a person inside the worker loop — a lease expiring while
they think, a reaper killing them for being slow.

So `h3 intent new` is a **synchronous session**, and it does two things at once:

- **Reads.** Package tree, service interfaces, published events, the import graph, the previous
  epic's `produces`. Everything derivable is drafted, not asked.
- **Asks.** Socratic, one field at a time, section by section — for the parts nothing can read:
  what would you accept, what is out of scope, what beneath this work catches a mistake.

Section-by-section validation matters beyond convenience. It turns one large approval into a series
of small ones, which is the leaf criterion applied to the conversation: if you can accept section
three and reject section four, those are probably two epics.

**`h3 intent submit` is a human action and cannot be automated.** That is the entire mechanism of
ownership — not who typed the fields, but that nothing reaches the board without a person having
ruled on each one.

**The transcript lands in the content store**, referenced from the epic row, recording what was
drafted and what you changed. Free provenance: a year later, *why was this scoped this way* is
answerable, and it is the only artifact in the system recording what the human was thinking rather
than what a model did.

> **Detector: fields changed per epic.** If a session's drafts go through untouched, you are
> rubber-stamping and intake is theatre. That number should not trend to zero, and if it does, the
> honest response is to delete the session rather than keep performing it.

### The intake gate

`h3 intent submit` runs model-free checks and **refuses**:

- all six fields present and non-empty
- no unresolved `[NEEDS CLARIFICATION: ...]` markers
- every `acceptance` entry is a decision, not a task — heuristically, it names a judgement
- `interfaces.consumes` symbols resolve against a previous epic's `produces`, or the epic is first
- `touch` is a real path glob that matches something, or the epic is first

Twenty lines, no model call. Fails → the epic stays `draft`, nothing lands, no workspace is built.

**Half an hour of human time against a subtree of model calls.** That is the whole argument.

---

## 6. The story is the review unit

A story is one branch, three to six commits, a diff you would actually read. Done means: every card
merged into the story branch, the branch green, and **one row in `reviews`** waiting for you. You
open it, read 60–200 lines, and `approve` or `kill`.

`kill` requeues the story with your reason attached, exactly as a verify rejection does — so the
round counter and the breaker apply to human rejections too, and a story you kill twice is a signal
about the epic rather than about the story.

### Commits are the artifact

Each card commits once, conventionally, carrying its refs:

```
feat(item): reject blank text on rename

Refs: E01 / S01.2 / AC3
Card: 0f3a91c
```

`git log --oneline` for a story is three lines and reads as a changelog. Across a week, `feat`,
`fix`, `refactor`, `test` and `chore` are countable — which is the thing a manager wants to see and
which no amount of ledger querying communicates as immediately.

The trailer is what joins the two records: the commit is the artifact, the card id is the row, and
`h3 why <card>` goes from one to the other.

### Breaking changes surface before you accept

`interfaces.produces` does a second job. A card whose diff changes a symbol that another epic's
`consumes` names is a breaking change, computed at rung 0 on the host, against the board. The
harness appends `!` and a `BREAKING CHANGE` footer; nothing is asked to self-declare, because a
model asked whether it broke something will say no — the same under-reporting as refusal.

It appears on the story's review row as a fact rather than a rejection. Deciding whether a break is
acceptable is a judgement about the product, which is why it goes to you and not to a gate.

Two readings, both in `h3 state`:

- **Frequent breaks that you always accept** — either `produces` is drawn too wide, or module
  boundaries are not holding.
- **A break in an epic that has downstream consumers already merged** — those epics need
  re-examining, and this is the only place that would be visible.

### Scaffolding is its own card

Work with **no acceptance decision in it** — generated module scaffolding, a mechanical rename,
applying a formatter — is a card of its own, so it never dilutes a diff that has decisions in it.
It commits as `chore`, and you skim it in ten seconds instead of reading two hundred lines of
boilerplate mixed into the diff where the real design choices are.

This is the same principle as §6a's scope rule: **a diff should contain one kind of thing.**

It matters most exactly where review is hardest — the first story in a new module carries the
module's scaffolding, so the story whose shape you most want to examine arrives when the diff is
most tiring. A generator card takes the boilerplate out of it.

### The review gate is pinned at split time

Policy §1.2 is explicit that a card never emits its own reviewer and gates are pinned by the
splitter. So the epic carries a review policy and the splitter pins a gate onto each story:

```yaml
review_policy:
  default: story                        # every story waits for me
  auto_accept_if:
    - touch ⊆ tests/**                  # test-only stories land without me
  always_gate:
    - touch ∩ src/todo/store.py         # anything near persistence, I look
```

**Derived from the card's touch set, not chosen by a model** — so core §3.4's deleted router stays
deleted. It is a property of the board, evaluated at emit time.

### On big stories

A large story is a **long** review, not a hard one, and the two should not be confused.

The reviewable unit is not the diff — it is the commits. A story arrives as three to six card pairs,
each an assertion followed by what satisfies it, 40 to 90 lines apiece. A 600-line story is twelve
small commits rather than one large one, so the largest thing held in mind at once is unchanged.
That is the actual review-load lever and it works regardless of story size.

So three causes of a big story need three different answers, and only one is a defect:

| Cause | Answer |
|---|---|
| It is genuinely two stories | `gate_story_is_one_slice`, or you kill it with that reason |
| It is one slice carrying a module's scaffolding | A scaffolding card, per above |
| It is one slice and simply large | **Nothing. Do not split it** |

**No hard line cap.** A cap forces genuine slices apart, and the failure mode of a too-small story —
cards nobody can accept independently — is worse and less visible than a long review.

---

## 5a. Two entry paths, one set of gates

A board comes into existence one of two ways, and both are permanent.

| Path | Used for |
|---|---|
| `h3 intent new` → intake gate → `split` | the normal path |
| `h3 seed <file>` | bootstrap, regression fixtures, a decomposition already held |

**Seed is not a bypass.** It writes the same rows and runs the same intake gate and the same emit
gates. A board that would be rejected coming out of a splitter is rejected coming out of a file —
which is what makes seed files usable as test fixtures against the gates themselves.

### The ratchet, stated precisely

The kind ratchet is not *a split must emit more than one child*. It is:

> **A split must not emit exactly one child that is a copy of its parent.**

That case is a level of nesting wearing a decomposition's clothes: the tree is deeper, nothing is
smaller, two model calls are spent, and the ledger records a split that succeeded. Row count plus a
similarity check against the parent's contract catches it.

A split that finds the work genuinely atomic takes the other exit — outcome `atomic`, emitting
nothing. See the working agreement. **The `atomic` rate is the negative result of the refusal
mechanism**, and it is worth watching in both directions: silence means executors never refuse
(R-new-7), and a high `atomic` rate means they refuse work they could have done.

### Two more emit gates: is this story one slice, and is it reviewable

**Acceptance-criterion count is not a size signal.** A registration story with six criteria — email
format, uniqueness, password rules, hashing, event published, error shape — is one story, because
failing any of them means rejecting the whole slice. Multiple criteria are one ruling when they are
facets of one deliverable.

What goes wrong is **separability**, not count, and separability is mechanical once the story has
split into cards:

```python
def gate_story_is_one_slice(story, cards):
    # nodes: cards. edges: shared touch paths, or a deps relation
    if len(connected_components(cards)) > 1:
        raise SplitRejected("story_is_n_stories", story.id)

def gate_story_reviewable(story):
    if len(expand(story.touch)) > 12:
        raise SplitRejected("story_too_wide", story.id)
```

**The check runs over the cards a split proposes, not over the cards a story eventually contains.**
Cards created in response to failure — an `integrate` card after a merge conflict, a gap card from
`done_with_concerns`, a defect card found while the story is open — are not part of the slice test.
They are not part of the decomposition either; they are what happened to it afterwards. A check
running continuously would eventually fail every story and would be measuring incident history
rather than the split.

The consequence is worth accepting rather than engineering around: **a story that accumulates six
defect cards mid-flight really has become two stories, and no gate will say so.** That is yours to
catch at review, and killing it with that reason is the feedback loop that tightens the gate.

A story whose cards converge on one path is one component and passes. A story that bolts an audit
trail onto a profile update has cards touching a table nothing else touches, with no dep edge back —
separate component, rejected. It uses the same reachability primitive as the collision gate, so it
costs nothing new.

**One part of this is not mechanical and should not be faked.** Two cards can be connected and still
separately acceptable. No gate catches that, which is why the story tier has a human on it — and the
feedback loop is already a row: **a story killed with the reason "this is two stories" is the
signal.** If that reason recurs, the connectivity gate is too permissive, and it gets tightened
against observed cases rather than an invented threshold.

Record the real diff size when the review row opens. Stories routinely exceeding a few hundred lines
despite passing both gates means the width estimator is wrong — a fact about the gate, not about the
person writing stories.

### An amendment to the emit gates

Written out concretely, the naive pair rejects correct boards. Three sibling stories that each edit
the same module collide if parallel, and carry no interface if chained.

- **An edge carries an interface or a file.** `consumes: {S01.1: "src/todo/model.py"}` means *we edit
  the same file and you go first.* That is data, and `edge_carries_nothing` accepts it.
- **Collision applies only between siblings with no dep path between them.** Siblings that cannot
  run concurrently cannot collide.

Consequence worth expecting: **on a small codebase most story-level parallelism is false.** An
honest board is mostly sequential, and a splitter emitting a wide parallel tree is wrong in a way the
gate catches.

---

## 6a. Refactoring and defects

Both have a standard agile answer, and one of the two inverts here. Full argument in
`working-agreement.md`; the rules a splitter needs are these.

**Refactoring is in the contract or it is an observation. Never opportunistic.** The Boy Scout Rule
— leave the code cleaner than you found it — works for humans because the person doing the cleanup
bears the cost of it being reviewed. Here the model bears none of it and you bear all of it, and the
rule breaks three mechanisms at once: cards edit outside their declared touch sets, verify cannot
answer *did it do what was asked* against a diff containing unasked-for work, and your story-sized
diff stops being story-sized.

> Declared in `touch` and named in `acceptance`, or reported as `done_with_concerns` and emitted as
> a card. `done_with_concerns` exists for exactly this and the worked run shows it doing exactly
> this.

**An in-flight defect is a new card under the same story, never a new story.** Standard practice
says don't log a ticket for a bug found mid-development — the story simply is not done. The intent
transfers; the justification does not, because a fix with no card has no contract, no attempt
record, no verify pass and no commit trailer. That is §1.5's failure one tier up. Cards are cheap in
a way tickets are not, so the row costs nothing and the story stays open until it lands.

**A production defect is a story, and its `oracle` is the failing test, written first.** Bug stories
therefore have a *better* oracle than feature stories: R44's problem does not arise, because there
is something beneath the work to catch a mistake.

**Priority is set at intake and never by a card.** Claim orders by `priority DESC, id`, and a hotfix
epic carries no `deps` so it is immediately claimable. The guard matters more than the feature: a
card able to raise its own priority is an escalation channel a model can use on itself. Set it where
the review policy is pinned.

---

## 7. Questions are rows, and answers are rulings

When a card returns `needs_context`, the question becomes a row. `h3 questions` returns everything
currently blocked on you **across the whole project**, not per card and not per epic — so you answer
in one sitting rather than being interrupted twelve times.

**The answer attaches to the epic, not to the asking card.** Available to every descendant by
ancestry, so a question answered once is never asked twice, and *why is it done this way* is
answerable from the board a year later.

That matters beyond convenience: without it, the human's contribution is the one thing in the system
that leaves no trace, which would be a strange hole in a design whose primary claim is the record.

---

## 8. What a week looks like

- **Once per epic**, roughly weekly: intake session, promote from draft, approve the stories before
  any workspace is built.
- **A few times a day**: `h3 reviews` — one story each, PR-sized, approve or kill.
- **Whenever**: `h3 questions` — batched, answers become rulings on the epic.
- **Any time**: `docs/context/current-state.md`, current by construction. See `state-command.md`.

On a five-epic project you are involved seven or eight times per epic. That is a helper. It is not
an unattended system, and the README already declines to claim otherwise.

### The one scheduled gate, and why it is that one

Everything except **approve the stories** is demand-driven. That one is scheduled because
`needs_context` requires a card to *notice* it lacks facts — the same self-report R47 says is
unreliable, for the same reason. **The cards that most need you are the least likely to ask.**

Five to eight rows, minutes to read, before any workspace is built. A wrong split is the one error
with nothing beneath it to catch it, and the cheapest human minute in the system.

---

## 9. What this costs

**Parallelism drops.** Epic by epic with a review gate between stories, you have three or four cards
in flight, not twelve. Policy §10's differentiator list already lost parallelism when the current
comparable turned out to have it; this mode weakens it further. The honest framing: **H3-as-helper is
not a parallelism story.**

**But the record story gets stronger.** A project run this way is thirty cards across five epics over
weeks, in one ledger, with the questions asked and the rulings given attached, and a generated state
file with a git history. That is exactly the README's *queryable record of what was decided and why
across many runs of one long-lived project* — the primary hypothesis, not the secondary one.

> **The mode humans actually want to work in is the mode where the secondary hypothesis looks worst
> and the primary one looks best.**

That is not a problem. It is the finding, and it belongs in §10's positioning section, which
currently lacks exactly this input.

---

## 10. Register entries to file

- **R-new-9 — nothing gates the splitter's input.** A thin epic costs a subtree and presents as a
  bad decomposition, so the split jig gets tuned for a problem it does not have. Mitigation: §5's
  intake gate. Detector: `needs_context` count per epic.
- **R-new-10 — the human's contribution may leave no trace.** Answers consumed into one card's
  context are invisible to the ledger, which is §1.5's failure one tier up. Mitigation: rulings
  attach to the epic. Detector: any answer path that does not write a row.
- **R-new-12 — opportunistic refactoring would disable three mechanisms at once.** Touch sets stop
  meaning anything, verify's question becomes unanswerable, and review diffs inflate. Mitigation:
  §6a's rule. Detector: commit-time touch-set hook firing on cards that otherwise passed.
- **R-new-13 — a card that can set its own priority is a self-escalation channel.** Mitigation:
  priority is intake-only. Watch for: any proposal to let a card request expedite.
- **R-new-11 — review-gate policy is a router in disguise if a model evaluates it.** Mitigation: the
  policy is evaluated against touch sets at emit time, never by a model. Watch for: any proposal to
  let a card request or waive its own review.
- **Amendment to policy §10** — add §9's trade as an input to positioning. The helper mode
  strengthens the primary claim and weakens the secondary one, and step 7's thresholds should be
  written knowing that.

---

## 11. What would change this

- **The intake gate rejects almost nothing** — either the drafts are already good, in which case the
  gate is theatre and should be deleted, or the checks are too weak.
- **The human changes nothing the session drafted** — ownership has become rubber-stamping. Delete
  the session rather than keep performing it.
- **`needs_context` does not fall after intake is introduced** — the session is not earning its half
  hour, and the six fields are the wrong six.
- **Stories are routinely killed twice** — the epic tier is where the problem is, and the intake gate
  needs a coverage check it does not currently have.
- **The story-sized diff turns out not to be reviewable** — if stories routinely produce 800-line
  diffs, the story tier is mis-scoped and the review boundary belongs somewhere else.
- **`rank` never diverges from topological order** — see the detector above. Either a chain, or
  nobody is exercising judgement.
- **Auto-accept swallows most stories** — the review policy is being used to escape review, and the
  gate's value should be measured before that is allowed to widen.
