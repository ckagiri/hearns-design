# Assertions — what a card's acceptance looks like

**Status:** proposal. One new field on cards (`assertions`), three new rung-0 checks, one cap. No new
tier, no new kind, no new table.

**Scope:** the card tier only. Epic `acceptance` is unchanged and stays prose — §6 says why.

---

## 1. The problem

A test card's contract is currently prose, and its exit criterion is `exit: red` — the test must
fail before the implementation card runs.

**Red is a weak check.** A test can fail for the wrong reason: an import error, a missing fixture, a
collection error, an assertion about something nobody asked for. Red proves the test runs and does
not pass. It does not prove it tests the right thing.

Two further gaps follow from the same root:

- **The model chooses its own values, and it will choose easy ones.** Prose saying *rejects blank
  text* leaves the author to decide what blank means, and you get `""` and nothing else.
- **`verify` has nothing concrete to check against.** *Did it do what was asked* against a paragraph
  is a judgement. Against four named rows it is a question with an answer.

---

## 2. The unit is a named assertion

Every assertion has an `id`. That id is the only thing every mechanism consumes, and it is what
flows epic → card → test name → commit trailer.

Three shapes, chosen by what the behaviour is. Not three styles — three different kinds of claim.

### Example table — when the behaviour is data-shaped

```yaml
- id: A1.rename
  about: rename validation
  call: rename(item_text, new_text) -> Result
  columns: [item_text, new_text, expect]
  rows:
    - ["buy milk", "buy oat milk", ok]
    - ["buy milk", "",             BlankText]
    - ["buy milk", "   ",          BlankText]
    - ["buy milk", "x"*501,        TooLong]
```

**`expect` is the reserved last column.** Everything before it is input. It is the only key with
fixed positional meaning, and naming it is what stops ad-hoc keys creeping in.

**Value or exception is decided by case.** `ok` is a returned value; `BlankText` is a raised
exception type. Without that convention you cannot distinguish *returns the string BlankText* from
*raises BlankText*, and both are plausible readings.

**Fixtures go in a `given` block, never inline in a row.**

```yaml
  given: item(text="buy milk")
```

A row that constructs an object inline is prose wearing a table's clothes. Name a builder.

### Property — when the claim is an invariant over inputs

```yaml
- id: A2.identity
  about: rename preserves identity
  property: "for any item i and any valid text t: rename(i, t).id == i.id"
```

Stronger than three rows demonstrating the same thing, and it maps onto a property-testing library
directly. **Where a property is stateable, prefer it.** Where one is not, do not force it — a
manufactured invariant is the same defect as a manufactured assertion.

### Bare id — when neither fits

```yaml
- id: A3.toggle
  about: done state is settable both ways
```

One named line. Rung 0 still checks that a test exists, is named for the id, and fails on its own
assertion. It cannot check the shape, because there is no shape to check.

**Where the semantic is not stateable at all** — a rename, a configuration change, a scaffolding card
— the card has **no assertions**, and its contract says so. Forcing a table onto it produces exactly
the manufactured assertion the working agreement warns against.

---

## 3. What rung 0 checks

All on the host, where the card cannot reach.

| Check | Catches |
|---|---|
| One test per assertion id, named for it | A missing assertion, or one invented that nobody asked for |
| Each test fails on **its own** assertion | Red for the wrong reason — imports, fixtures, collection |
| `columns` match the test's parametrize argnames, in order | A test that reorders or renames arguments |
| Every row appears as a parametrize case | The easy-values failure: a row present in the table and absent from the test |
| Row arity matches `columns` | Structural error, caught by counting |
| `call` matches the implementation's signature | Drift between the assertion and the thing it asserts about |

**The row check is the one prose could never give you**, because a paragraph has no rows to count.
It is the reason the table earns its structure.

`call` also feeds the breaking-change detector: a card that changes the arity or name of a called
symbol is visible without anything self-declaring it.

---

## 4. The cap

**Five assertion ids per card.** More means the card is two.

This is a real cap, unlike at the story tier where a line cap is refused. The reasoning differs:
splitting a genuine story produces cards nobody can accept independently, which is a worse failure
than a long review. Splitting an over-assertioned card produces two ordinary cards, which is no
failure at all.

**Rows within one table are not capped.** Five rows are one parametrized test and one commit. It is
assertion *ids* that count, because each is a separate test function and a separate claim.

---

## 5. Structured or prose, never in between

**Every key on a card is either reserved with a checker that consumes it, or free text a human
reads.** Nothing sits in the middle.

| Key | Consumer |
|---|---|
| `id` | rung 0 |
| `call` | signature check, breaking-change detector |
| `columns` | parametrize argname check |
| `rows` | arity and case checks |
| `expect` | reserved last column |
| `property` | the property-test runner |
| `given` | fixture builder |
| **`about`** | **a human. Nothing checks it** |

**The test: if you deleted the key, would anything fail?** Delete `about` and nothing breaks. Delete
`columns` and the parametrize check has nothing to compare against.

A key that *looks* structured and has no consumer is the worst of both — it reads as a guarantee and
is a comment. Those are the keys that silently stop being true.

---

## 6. Why the epic tier stays prose

Two reasons, and both are about what `acceptance` is for at that level.

**It must stay under-decomposed.** Three to five entries for an epic that becomes twelve cards.
Structured acceptance cannot be vague — enumerating cases *is* the decomposition, so a structured
epic `acceptance` means the intake session hand-split the epic and left the splitter nothing to do.

**It answers a different question.** Card assertions say *what the system does*. Epic acceptance says
*what a reviewer would reject* — "judged on state transitions alone, not on storage". That has no
tabular form, and it is exactly the phrase that keeps two stories' touch sets apart.

Prose where a human is the consumer, structured where a checker is.

---

## 7. What this is not

**Not Gherkin, and no Given/When/Then.** The only part of that format any mechanism consumes is the
id; the three slots are prose with ceremony, and they force awkward phrasing on anything that is not
state → action → outcome. *SSN is encrypted at rest* has no natural *when*.

**No `.feature` files, no step definitions, no step registry, no runner.** Assertions are fields on a
card and the test is ordinary test code. The moment there is a parser and a step registry, the
scenarios are a second source of truth living outside the board, free to drift from the tests they
describe.

---

## 8. What it buys

**Coverage becomes a join, not a judgement.** Ids flow epic → card → test name → commit trailer, so
three queries replace a person reading a spec and squinting:

- acceptance criteria with no assertion under them
- assertions with no test
- tests belonging to no assertion

**`verify` gets something to do.** On a workload where the check ladder catches nearly everything,
verify has almost no residue and will rubber-stamp. Checking a diff against four named rows is a
real question. Checking it against a paragraph is not.

**Under-specification becomes visible at the review gate.** You can see that a four-row table has no
empty-string row. You cannot see the absence of a sentence.

---

## 9. What would change this

- **Rung 0's row check never fires** — either tables are being written after the tests, or the
  parametrize convention is not being followed and the check is passing vacuously. The second is
  worse and looks identical.
- **Cards routinely hit the five-assertion cap** — the split is emitting cards at story size, and
  the cap is masking it rather than surfacing it.
- **Properties are never used** — either the workload genuinely has no invariants, or the splitter
  defaults to tables because they are easier. One is a fact about the domain; the other is a jig
  problem.
- **`about` starts carrying meaning** — someone is parsing it, or reviewers are relying on it over
  the rows. Either way it has stopped being prose and needs a decision.
- **Assertion ids stop matching epic acceptance ids** — the join breaks silently, and coverage
  reverts to a judgement without anyone noticing. Worth its own rung-0 check if it happens once.
