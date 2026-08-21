# H3 pilot — ten days to something you can show

**Not the prototype.** The prototype is `PROTOTYPE_v3.md` and it is three weeks. This is what you
build first so those three weeks are spent on a design you have watched run.

**The deliverable is a demo, a week of commits, and a list of what broke.** Code quality bar: it
works on your machine, twice in a row.

**Rule for the week:** if you find yourself opening a design document to check something, write the
obvious thing and note the question in `NOTES.md`. That file is the real output.

**Two parts.** Days 1–6 build the machinery. Days 7–10 drive three epics through it and produce a
real state history and the first numbers. **Stop at day 6 if part 1 slips** — a working flat pilot
beats a broken deep one.

Six of the eight kinds ship: `split`, `execute`, `verify`, `re_verify`, `integrate`, and `digest` as
`h3 state`. `preflight` and `spec_revision` are out — §8 says what that costs.

---

## What the demo has to show

Seven moments, about ten minutes:

1. **`h3 plan`** — five epics as draft rows. The plan is on the board, not in a file.
2. **`h3 intent submit`** — a thin epic gets **refused** by a model-free gate. Fix it, resubmit.
3. **`h3 board`** — epic splits into stories, stories into cards, dependencies visible. Two children
   rejected by an emit gate before they ever land.
4. **Three workers.** Parallel pickup, each card claimed exactly once, unmet deps stay put.
5. **`kill -9` a worker mid-card.** Another picks it up, the workspace resets, the dead worker's
   half-written files are gone.
6. **`h3 reviews`** — a story, three commits, 112 lines. You read it and approve. The next story
   unblocks.
7. **`git log docs/context/current-state.md`** — a week of the project describing itself, generated,
   never hand-edited.

Moment 7 is the one that lands with a non-technical audience. Moment 5 is the one that lands with
engineers.

---

## What's in, what's out

**In, because it *is* the idea:**

- Postgres: `cards`, `attempts`, `reviews`, `questions`
- `SELECT ... FOR UPDATE SKIP LOCKED` — the whole concurrency story
- The dependency predicate, with `SATISFIES_DEP = {"done"}`
- Three tiers: epic (`parent = null`), story, card
- A git worktree per card, a branch per story
- N worker processes, no controller
- Lease + heartbeat + a reaper
- The intake gate — model-free, refuses
- `split` emitting in one transaction behind two model-free gates
- **The check ladder as config** — `checks.yaml`, rung 0 on the host, rungs 1–2 in the workspace
- **Test cards before implementation cards**, with the tool-set gate holding them apart
- `execute` and `verify`, one crude prompt each
- `integrate` — harness-side on the happy path, a card on the unhappy one
- The human gate at the story tier
- `h3 state`, generated and committed

**Out for the week:**

| Cut | Instead |
|---|---|
| Containers | Subprocess in a venv. It's your machine and it's a todo app |
| Per-attempt DB clone | The todo app writes to SQLite or a file. **Yes, this hides P1-9. Note it and move on** |
| Model cache, `config_hash`, `kind_hash` | Log the exact prompt string into `attempts` |
| Fencing done properly | `WHERE id = %s AND lease_holder = %s`. Roughly right, don't prove it |
| Jigs, skills, layers | A paragraph per kind in `prompts/*-v0.md`. Do not call them jigs |
| `preflight`, `spec_revision` | See §8 |
| Review policy beyond `default: story` | Hard-code it. `auto_accept_if` is a day 11 idea |
| Rung 3 | The todo app has no domain rung above integration. **Note that this is why verify has little to do here** |
| ADRs, register entries, `/drift`, hooks | `NOTES.md`, one bullet per surprise |
| Migrations runner | One `schema.sql` you re-run after `dropdb` |
| Tests, mostly | Five: exclusive claim under contention, kill-then-requeue, each emit gate rejecting a case built to trip it, the intake gate refusing a thin epic, and rung 0 catching a gutted test |

---

## Part 1 — the machinery, days 1–6

### Day 1 — the board exists

`schema.sql`:

```
cards(id, project, parent, tier, kind, title, contract, acceptance,
      deps[], touch[], produces[], consumes jsonb, non_goals, priority, rank,
      status, lease_holder, lease_expires, attempts, branch)
attempts(card_id, n, kind, prompt, diff, rung_results jsonb, outcome, reason, started, ended)
reviews(story_id, opened, closed, verdict, reason)
questions(id, epic_id, asked_by_card, text, answer, answered_at)
```

`tier` is `epic | story | card`. It is not derived from depth — you want to query on it.

Claim in one statement, copied out of core §5.3 rather than written:

```sql
UPDATE cards SET status='running', lease_holder=%s, lease_expires=now()+interval '10 min'
WHERE id = (
  SELECT id FROM cards WHERE status='pending'
    AND NOT EXISTS (SELECT 1 FROM unnest(deps) d
                    WHERE (SELECT status FROM cards WHERE id=d) IS DISTINCT FROM 'done')
  ORDER BY priority DESC, rank ASC, id FOR UPDATE SKIP LOCKED LIMIT 1
) RETURNING *;
```

`rank` is yours and `deps` is structural — keeping them apart is what lets you re-order the roadmap
without editing the dependency graph. `priority` is two words now and a migration later. It is set at intake only — a card that can raise
its own priority is an escalation channel a model can use on itself.

`IS DISTINCT FROM 'done'` is ADR-0006 and it is free if you write it now: a dep that ended `blocked`
is terminal but satisfies nothing.

Worker loop with **fake** card bodies — `time.sleep(20); open(f,'w').write('hi')`. Hand-write one
epic, three stories, nine cards. Three workers. `h3 board` prints the tree.

**End of day 1: demo moments 3 and 4**, with no model, no git, no containers.

### Day 2 — crash recovery

Heartbeat thread bumps `lease_expires`. Reaper: lease expired → kill the process group, `git
worktree remove --force`, back to `pending`, `attempts += 1`.

`kill -9` a worker mid-card and watch it come back. **Write the two tests here** — contention and
requeue — because these are the two claims you will make out loud.

**End of day 2: demo moment 5.**

### Day 3 — hierarchical integrate and the review gate

Both go here, while cards are still fake and each writes one file. Doing it now means day 4's real
cards land on a merge path that already holds.

**Card → story branch, no model call.** After a card's checks pass: advisory lock on the story
branch, `git merge --no-ff`, re-run `pytest` on the merged tree, green → commit, card `done`. Red or
conflict → roll back and **emit an `integrate` card** whose contract carries the conflicting paths
and the failing output.

**Story → `main`, but only through you.** All cards merged and the story branch green opens a row in
`reviews`. `h3 reviews` shows it; `approve` merges to `main` and unblocks the next story; `kill`
requeues the story with your reason attached, exactly as a verify rejection does.

**Epic → `done`** when all its stories are accepted, which unblocks the next epic by `deps`.

This is where **`done` starts meaning "merged, green, and accepted"** rather than "the card's own
checks passed." Say that out loud in the demo.

**End of day 3: demo moment 6**, with fake cards. Real ones make it harder, not different.

### Day 4 — real cards, and the check ladder

Freeze `spec.md`: twelve todo behaviours, one hour, **then stop touching it.**

**Seed E01's board with `h3 seed`, and rule on every row yourself.**

There are two ways a board comes into existence, and both are permanent:

| Path | When | Built |
|---|---|---|
| `h3 seed <file>` | bootstrap, regression fixtures, a decomposition you already hold | day 4 |
| `h3 intent new` → `split` | the normal path | day 5 |

**Seed is not a bypass.** It writes the same rows and runs the same intake gate and the same emit
gates. A seed file that would be rejected coming out of a splitter is rejected coming out of a file.
That is what makes it usable as a test fixture later.

Draft E01's YAML with a strong model — spec, working agreement, and E00's merged code as context —
then check five things by hand. **The checking is the day's actual learning**, not the drafting:

1. every behaviour in `spec.md` appears in some card's contract
2. no card whose contract is not traceable to A1–A3
3. each story is separately acceptable — could you approve one and reject its neighbour?
4. each card is one commit
5. every `consumes` names a real symbol or a real path

You will reject two or three rows. What they were missing is what a card contract has to contain,
and finding that out on day 4 is worth more than the board itself.

**`spec.md` is the oracle, not this tree.** Coverage and invention are scored against the frozen
spec directly. A model-generated tree scored against a model-generated tree measures agreement
between correlated samples, not correctness — so do not use E01's board as day 5's ground truth.

**The ladder is config, authored once, and no model touches it.**

```yaml
# harness/config/checks.yaml
ladder:
  - rung: 0
    name: static
    where: host                      # the card cannot see it, edit it, or run it
    timeout: 30s
    steps:
      - ruff check . && ruff format --check .
      - mypy src
      - python tools/placeholder_scan.py     # TODO / pass / NotImplementedError in tests/
      - python tools/commit_type_check.py    # derived type matches the card
      - python tools/api_diff.py             # produces[] symbols changed by this diff

  - rung: 1
    name: unit
    where: workspace
    timeout: 120s
    steps: ["pytest tests/unit -q"]

  - rung: 2
    name: integration
    where: workspace
    timeout: 300s
    steps: ["pytest tests/integration -q"]
```

**Rung 0 running on the host is the whole point of the day.** Rungs 1 and 2 execute inside the
workspace, so a card can see them, run them iteratively, and reach the files they execute. Rung 0
cannot be seen, run or tuned against from inside — which is what makes it the thing that polices the
other two rather than a cheaper version of them.

`placeholder_scan.py` is thirty lines and is the highest-value script in the pilot: it is what
catches a test gutted to `pass`, from a place nothing in the workspace can reach.

**Write results per rung**, not as one blob. `rung_results` in `attempts` is what makes *which rung
failed, how often* a query on day 10, and it costs nothing to record now.

**Wire the model call.** Crudest possible prompt: card contract, acceptance ref, spec fragment, "make
the ladder pass." Tools: read, write, edit, bash. Log the assembled prompt verbatim. Any rung
non-zero → `failed`, requeue up to 3.

**The tool-set gate, from the first card.** An implementation card is constructed **without write
access to `tests/`**. Not instructed — constructed. It cannot edit what it must satisfy, and absence
of a tool is the enforcement.

**Conventional commits from the first card**, because the trailer is the join between the two
records:

```
feat(item): reject blank text on rename

Refs: E01 / S01.2 / AC3
Card: 0f3a91c
```

**The type is computed from the card, never chosen.** Test card → `test`, gap card → `refactor`,
`touch ⊆ docs/**` → `docs`, otherwise `feat`. Twenty lines in `commit_type_check.py`, and it is what
makes day 10's type counts worth counting.

**`api_diff.py` is the breaking-change check** and it is thirty lines on a Python codebase: parse the
symbols the epic declares in `produces`, diff their signatures against `main`, and if any changed,
the harness appends `!` and a `BREAKING CHANGE` footer. **Nothing self-declares** — a model asked
whether it broke something will say no. Rung 0 runs it on the host, which is the only place it can be
trusted.

The todo app will produce roughly one real breaking change across four epics. That is enough to show
the mechanism firing, and one firing is the whole bar.

**Expect a bad day.** Half of it will be worktrees and paths.

### Day 5 — intake and split

**Morning: intake and the gate.** `h3 intent new` is a synchronous CLI session that **drafts what it
can read** — touch surface from the package tree, `consumes` from the previous epic's `produces` —
and **asks about what it cannot**: acceptance, non-goals, oracle. It writes a draft epic row; you
rule on every field before `h3 intent submit`, which is a human action and cannot be automated.

Same division as day 4's seed: a model drafts, you rule, and the ruling is where the learning is.
`h3 intent submit` runs the model-free checks and refuses. Write a deliberately thin epic first and
watch it bounce; that is demo moment 2 and it takes ten minutes to build.

Write E02 through E05 as drafts while you are there. That is `h3 plan` and demo moment 1.

**Midday: `split`, two levels — on E02, not E01.** E01 already has a board and is running; splitting
it again would only tell you whether the splitter agrees with a draft it could have written. Promote
E02 through intake and split that. Epic → stories, story → cards, one model call per level, emitting
in **one transaction** behind two gates that run before anything lands and use no model:

```python
def gate_touch_sets_disjoint(kids):          # false independence
    for a, b in combinations(kids, 2):
        if reachable(a, b) or reachable(b, a):
            continue                          # ordered, so they cannot collide
        if set(a.touch) & set(b.touch):
            raise SplitRejected("touch_collision", a.id, b.id)

def gate_edge_carries_data(kids):            # false dependence
    for k in kids:
        for d in k.deps:
            carried = k.consumes.get(d)       # an interface name OR a file path
            if not carried:
                raise SplitRejected("edge_carries_no_data", k.id, d)
```

Plus two gates on the story tier itself:

```python
def gate_story_is_one_slice(story, cards):
    if len(connected_components(cards)) > 1:   # shared touch, or a deps edge
        raise SplitRejected("story_is_n_stories", story.id)

def gate_story_reviewable(story):
    if len(expand(story.touch)) > 12:
        raise SplitRejected("story_too_wide", story.id)
```

**Do not gate on acceptance-criterion count.** A registration story with six criteria is one story;
a profile-update story that also builds an audit trail is two, and the difference is whether the
cards form one connected component, not how many criteria there are. Same reachability primitive as
the collision gate.

**Record the real diff size when each review row opens.** If stories routinely exceed a few hundred
lines despite passing, the width estimator is wrong — that is a day 10 number.

**Two amendments over the naive version, both found by writing E01's board out concretely.**
Toggle, rename and delete all edit `model.py`. As parallel siblings the collision gate rejects them;
chained by `deps` the edge gate rejects them, because the edge carries no interface. **The naive
pair jointly rejects the correct board.**

So: an edge carries **an interface or a file** — `consumes: {S01.1: "src/todo/model.py"}` means *we
edit the same file and you go first*, which is real data. And collision applies only between
siblings with **no dep path between them**, since siblings that cannot run concurrently cannot
collide.

This predicts something for day 6: **on a small app most story-level parallelism is false.** An
honest todo board is mostly sequential, and a splitter emitting a wide parallel tree is wrong in a
way the gate now catches.

Forty lines, both falsifiable, and together the cheapest thing in the design. Reject → the whole
emit rolls back and the split retries with the reason appended. **Show that in the demo**; a gate
that has never fired is not evidence of anything.

Score against day 4's hand-written tree: did every frozen behaviour land in some card, and did the
splitter invent cards with no basis in the spec. Both countable. Whether the tree *looks like* yours
is not, and a different-but-valid decomposition would score badly on shape while being fine.

**Afternoon: the split emits test cards.** Where a behaviour has a stateable semantic, the splitter
emits a **test card** and an **implementation card that depends on it**. The test card's exit
criterion is that the test *fails* — a test passing against an empty implementation never guarded
anything, so the harness checks for red before marking it done.

That pairing plus day 4's tool-set gate is what makes rungs 1 and 2 mean anything. Neither works
alone: without test-first the assertions are written to pass, and without the tool gate they get
edited until they do.

Where the behaviour has no stateable semantic — a rename, a config change — one card, and the
contract says so rather than manufacturing an assertion.

### Day 6 — verify, and the traps that make it measurable

**Morning: `verify`.** A second model call per card — here is the diff, here is the contract and the
acceptance ref, did it do what was asked. `pass`/`fail` plus a reason into `attempts`. Fail →
requeue with the reason attached.

**Afternoon: five to eight seeded traps, hand-written, with known signatures.**

This is what converts verify from unobservable to a number, and it is the single most skippable
half-day in the pilot — which is why it is written down. On a Python todo app the ladder catches
nearly everything, so verify has almost no residue and will rubber-stamp. **Without traps you would
learn that verify runs, not that verify works.**

The traps are the residue the ladder structurally cannot see:

- an implementation that satisfies the test but not the acceptance criterion
- a behaviour implemented for the happy path only, with the test covering only that path
- a card that solves the contract by changing what the contract measures
- correct code in the wrong module, so the touch set was honest and the design was not
- an off-by-one that both the test and the code share

Each has an expected signature. Record what verify caught, as a fraction. That is the number.

**The contamination rule holds all week:** a manufactured failure becomes a gate in the ladder, never
a rule in a jig. A failure you constructed is one you already understood, and understood failures
belong in code.

**Then break the machinery deliberately.** Each should produce visible, distinct behaviour:

- an epic missing `non_goals` and `oracle` → intake gate refuses
- a test card whose test passes on first run → not done, no implementation card claims
- a test gutted to `pass` → rung 0 catches it from the host
- an implementation card that tries to edit `tests/` → no such tool
- two sibling cards with overlapping touch sets, hand-edited on **after** the emit gate ran
- a card that sleeps past its lease
- two cards editing the same function, forcing a conflict and an `integrate` card
- a split whose stories drop one of the twelve behaviours
- a story you `kill` twice
- a card that changes an interface another epic consumes → `!` appended without being asked
- a commit whose type does not match its card → rung 0 rejects it

If everything succeeds you have learned nothing.

Walkthrough once, out loud, to a wall or a person. Then `NOTES.md`.

**Day 6's board is the checkpoint.** Green and repeatable twice → go on. Not → demo what you have.

---

## Part 2 — a week of work, days 7–10

### Why bother

Part 1 proves the machinery exists. Part 2 answers the question you actually care about: **after a
week, is there a readable history of features, fixes and refactors that you believe?**

It also produces the first numbers. Policy §3.1 says the per-level fidelity rate is assumed and
unobserved anywhere in the design. Four rough days gives you a per-*tier* version — badly measured,
on a toy, n of about thirty. It is still the only one in existence.

### Day 7 — `h3 state`, and the outcomes that let work flow back

**Morning: `h3 state`.** Three queries and a markdown renderer: what is built (by epic and story,
with commit shas), what is next (epics in `deps` order), what is waiting on you (reviews, questions,
stalls). Plus the cost table — attempts, rung failures by rung, verify rejections, human kills, per
epic. Written on every integrate to `main`, committed, and **unwritable by any card.**

It is three queries and f-strings, not a UI. Do not build a tree renderer beside it.

**Afternoon: the outcome enum**, which is what makes the working agreement's routing real. Every
attempt ends in one of five:

| Outcome | What the harness does |
|---|---|
| `ok` | proceed to integrate |
| `done_with_concerns` | proceed, **and emit a gap card** carrying the observation |
| `misclassified` | replace this card with a `split` of the same intent, parent intact |
| `needs_context` | open a row in `questions`, card waits |
| `spec_conflict` | `blocked`, loud, with the conflicting clauses named |

Add one paragraph to `execute-v0.md` giving permission to refuse, and the criterion to refuse
against: *could a reviewer sensibly accept one half of this and reject the other?*

**`done_with_concerns` is the working agreement's scope rule made mechanical.** Work outside the
contract becomes a row, never a diff. A card that tidies opportunistically instead trips the
commit-time touch-set hook — so the two mechanisms are the same rule seen from either side.

`h3 questions` answers in a batch, and **answers attach to the epic, not the asking card**, so a
question answered once is never asked twice.

Two guards on `misclassified`:

- **No fourth tier.** Below `card` there is no name and no reviewer semantics, so a split at that
  level goes `blocked` with a reason. The bound comes from the vocabulary, not an integer.
- **The kind ratchet.** A split emitting one `execute` child carrying the parent's intent is
  misclassification laundered through a level. One row count and a similarity check.

**Demo footage:** remove the tier bound, give a card a hopelessly vague contract, watch it regress.
Then put it back.

### Day 8 — the remaining epics

Promote and run E03 and E04 through the full path: intake session, split, cards, review. Nothing new
gets built. This is the day that produces the commit history, and the day intake gets used the way it
is meant to be — **`consumes` read off the repository rather than invented**, because E01 and E02
have landed.

Watch specifically for whether you can write E04's `non_goals` more precisely than E02's. If you can,
intake is doing its job. That is the same signal as `needs_context` falling, seen earlier.

### Day 9 — a refactor and a fix

Deliberately: one epic that is a refactor with no behaviour change, and one that is a bug fix with a
regression test. These exercise what the feature path does not. A refactor's `acceptance` is
"nothing changes", which is a real test of whether verify has anything to say; a fix has a RED test
before it has a card.

Also demo the queue jump: give the fix epic `priority: 1` and no `deps`, and watch it claim ahead of
work created before it. That is the hotfix path, and it is one `ORDER BY` clause.

By the end, `git log --oneline` should show `feat`, `fix`, `refactor`, `test` and `chore`, and
`current-state.md` should have four or five commits of its own.

**No `style` commits should exist.** If any do, the formatter is not in rung 0 — which is a finding
about the ladder, found the only way it can be.

### Day 10 — measure it, write it up

| Number | How |
|---|---|
| Per-tier fidelity | Fraction of cards passing verify first attempt, by tier |
| Ladder shape | Failures by rung. **If rung 0 never fails, it is a deletion candidate** |
| Verify detection | Fraction of day 6's traps caught, with the trap list attached |
| Review acceptance | Stories approved first time vs killed |
| Intent quality | `needs_context` per epic, E01 → E03. Should fall |
| Gate firing | Times each emit gate and the intake gate rejected |
| Splitter coverage | Behaviours landed, cards invented, against day 4's oracle |
| Cost | Attempts per accepted story, and rung latency as a share of it |
| Story size | Real diff lines per story against what `gate_story_reviewable` estimated |
| Commit shape | Type counts across the week. `style` should be zero; `revert` should be zero |
| Interface churn | Breaking changes detected, and whether you accepted each one |
| Refusal | `misclassified`, `needs_context`, `done_with_concerns` counts. **A zero in any is a finding** |

Every number caveated: n≈30, one workload, one crude prompt, no controls. Policy §3.1 says depth is
unjustified until a fidelity number exists. This is not a good version of it. It is the first one.

Final `NOTES.md`:

- what broke, verbatim
- every place you wrote the obvious thing instead of the designed thing, and whether the obvious
  thing turned out to be wrong
- which mechanisms **never fired** — deletion candidates, and finding one is a real result
- what you now think the three weeks should be spent on

---

## Three things to be honest about

**No containers and no per-attempt database clone** means the workspace is a worktree, not a triple.
That is the single largest piece of the real prototype and this pilot does not touch it. Say so in
one sentence before someone else does.

**The check ladder has no rung 3, so verify is being measured on its worst case.** A Python todo app
is where `pytest` catches most of what there is to catch, which leaves verify almost no residue —
day 6's traps are the only reason the number means anything, and even then they are manufactured. On
a domain with a thinner ladder, that residue is the whole game and this pilot says nothing about it.

**Three tiers on a twelve-behaviour toy is not depth on real work.** What part 2 shows is that the
mechanisms exist and fire. It does not show the tier structure pays on a workload where an epic is
three weeks rather than three hours.

**The review gate makes you the bottleneck, on purpose.** Three or four cards in flight, not twelve.
Anyone who asks about throughput gets the honest answer: this mode trades parallelism for a record,
and the record is the primary claim.

---

## The two kinds you don't have

| Kind | What its absence costs |
|---|---|
| `preflight` | Day 6's commit-time touch-set check is the mechanical half. §3.7 calls preflight ⚖ anyway, and adding an adversarial model call before you know the mechanical checks miss anything is the wrong order |
| `spec_revision` | Needs a schema anchor to revise. Not until pharmacy |

---

## What this buys the prototype

`PROTOTYPE_v3.md` gets rewritten after these two weeks, not before. Written from evidence instead of
argument:

- Whether epic/story/card are the right three tiers, or a fourth is wanted
- Whether the intake gate rejects anything real, and whether `needs_context` falls after it
- Whether a story-sized diff is actually reviewable, or stories come out too big
- What the crude prompt fails at — the RED corpus seed, which cannot be imagined
- Whether verify catches anything the ladder cannot, measured against traps rather than assumed
- Which rung actually fails, and whether rung 0 earns its place or never fires
- Whether test-first plus the tool gate holds, or implementations satisfy weak assertions anyway
- Whether integrate-as-a-card is right, or conflicts want a human
- Whether `current-state.md` is a tool or a demo artifact
- Whether P1-9 is really 2.5–3 days, now that you have felt the worktree half of it
- Which mechanisms never fired
