---
name: drift
description: Detect drift between the design documents, the register and the code — stale ADR index, rule numbers cited that do not exist, transcribed SQL that no longer matches, mechanisms in code that no document names. Use at phase boundaries, before a commit that touches the ledger, or when the user says "drift", "are the docs still true", or "check the register".
argument-hint: [optional: adr | rules | sql | all]
---

## Signals

!`ls -1 docs/adr/*.md 2>/dev/null | sed 's|.*/||' || echo "(no ADRs)"`
!`ls -1 harness/ledger/sql/*.sql 2>/dev/null | sed 's|.*/||' || echo "(no ledger SQL yet)"`

## Task

Detect drift: $ARGUMENTS (default: all)

**Drift here is not the usual docs-vs-code problem.** In this repo the design documents
*transcribe* load-bearing artifacts — the claim query, the readiness predicate, the reaper — and
the register is the numbering authority for everything that cites a rule. When those diverge, one
of the two is wrong and there is no way to tell which from the outside. That is the failure this
skill exists to catch.

Report findings; do not fix them silently. Each finding names which side is likely wrong.

### 1. ADR index

```bash
echo "--- in README table:"
grep -oE 'adr/[0-9]{4}-[a-z0-9-]+\.md' README.md | sed 's|adr/||' | sort -u
echo "--- on disk:"
ls -1 docs/adr/ 2>/dev/null | grep -E '^[0-9]{4}-' | sort -u
```

Diff them. An ADR on disk but not in README's "Decisions of record" table is invisible to the
next reader, which defeats the point of writing it. A row pointing at a missing file is worse.

Also check each ADR's **Status** line against reality: an ADR marked `Accepted` whose
*What would change our mind* trigger has since fired should have been superseded, not left standing.

### 2. Rule and risk citations

```bash
# Numbers cited anywhere in the repo
grep -rhoE '\b[Rr]ule ([0-9]{1,3})\b' --include='*.md' --include='*.py' --include='*.sql' . \
  | grep -oE '[0-9]+' | sort -un > /tmp/cited_rules
grep -rhoE '\bR([0-9]{1,3})\b' --include='*.md' --include='*.py' . \
  | grep -oE '[0-9]+' | sort -un > /tmp/cited_risks

# Numbers that exist in the register
grep -oE '^\| ([0-9]{1,3}) \|' docs/rules-and-risks.md | grep -oE '[0-9]+' | sort -un > /tmp/real_rules
grep -oE '^\| R([0-9]{1,3}) \|' docs/rules-and-risks.md | grep -oE '[0-9]+' | sort -un > /tmp/real_risks

echo "--- cited but not in register (dangling):"
comm -23 /tmp/cited_rules /tmp/real_rules
echo "--- in register but never cited anywhere:"
comm -13 /tmp/cited_rules /tmp/real_rules
```

**Dangling citations** are the urgent half — a rule number that resolves to nothing, or worse to a
*different* rule after a renumbering. The register has already resolved three collisions, so this
is not hypothetical.

**Never-cited rules are the interesting half.** That list is the standing review question from
`rules-and-risks` §8 — *which rules have never been consulted?* — computed rather than
remembered. A rule nobody has ever needed to cite is a candidate for deletion (rules 121 and 132
are the model). Do not propose deleting anything here; just surface the list, because the register
is a live instance of R56 and growth arriving as a table row is still growth.

### 3. Transcribed SQL

The claim query, the readiness predicate and the reaper appear in `docs/harness-core-v3.md` §5 as
fenced SQL blocks, and again in `harness/ledger/sql/`. Extract each block and diff it against the
corresponding file, normalising whitespace only.

A difference is a **blocking** finding. Decide which side is right by reading the surrounding
argument in core §5 — if the code is a deliberate improvement, the document changes with it in the
same commit; if it is an accident, the code is wrong. Never resolve it by editing whichever is
easier.

### 4. Section cross-references

```bash
grep -rhoE '(core|policy) §[0-9]+(\.[0-9]+)*' --include='*.md' . | sort -u
```

Check each resolves to a real heading in the named document. `odoo-adaptation` uses v2 section
numbers with a legend at its head — those are expected to differ and are not findings.

### 5. Jigs shipped without a RED pass

```bash
grep -rl 'GREEN-PENDING-RED' jigs/ 2>/dev/null
```

Any jig still carrying that tag is untested against the behaviour it was written to prevent, and
presents as coverage while being none (policy §1.4). List them with their kind.

### 6. Mechanisms with no home

Read the diff since the last phase boundary and list anything that behaves like a mechanism — a
check, a gate, a retry, a fallback, a config axis — and find the design section that names it.

Anything with no section is a finding, **including improvements**. This is the highest-base-rate
failure in this project: version 1 failed by elaboration, and elaboration arrives one defensible
addition at a time. The three landing places are an existing document, an ADR, or the register
(rule 133); if the mechanism deserves to exist, it deserves one of those.

### 7. "Where things stand" in README

Manual. Read the section and check each claim against the repo: what is settled, what is decided
but unmeasured, what is known to have no proof. This is the file most likely to describe an
earlier version of the project, and it is the first thing a new reader trusts.

## Output

Group as **Blocking** (transcription mismatch, dangling citation), **Finding** (index drift,
unhomed mechanism, stale status line), **Observation** (never-cited rules, unresolved
cross-references). For each: what diverged, which side is likely wrong, and the smallest fix.

If nothing drifted, say so in one line.
