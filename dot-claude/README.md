# Claude Code setup for H3

**Companion to** `h3-project-breakdown.md`. The kit referenced here is in `h3-claude-kit/` —
copy its contents into the repo root.

Claude Code changes fast, and some of what follows will drift. When something looks wrong, ask
Claude Code about itself: it fetches `https://code.claude.com/docs/en/claude_code_docs_map.md`
and answers from current docs rather than from training data.

---

## 0. The shape of it

Your design already separates *what is settled* from *what is contested*, and *coaching* from
*crude gates in code*. Claude Code has the same seam, and the setup works best when you map onto
it rather than fighting it:

| In your design | In Claude Code | Why |
|---|---|---|
| Layer 1, house preamble | `CLAUDE.md` | Loaded every session, always in context |
| Layer 2, per-kind skills | `.claude/skills/` | Loaded on demand, priced only when used |
| Domain rules that apply to some files | `.claude/rules/*.md` with `paths:` | Load only when Claude touches matching files |
| **Rich coaching in the prompt** (rule 25) | CLAUDE.md + skills | Context. Claude may not follow it |
| **Crude gates in code** (rule 25) | **hooks** + `permissions` | Enforcement. Fires regardless of what Claude decides |
| Verify — a party that did not do the work | subagent, read-only | Separate context, separate tools |
| Test card the implementer cannot edit | subagent + `PreToolUse` hook | The hook is unreachable from the agent it constrains |
| The ledger's queries | MCP Postgres server (read-only) | Claude queries the board directly |

**The single most important line in that table is rule 25.** An instruction in CLAUDE.md is a
request. A `PreToolUse` hook is a guarantee — it fires before any permission check, in every
permission mode, and a `deny` from it blocks the tool even under `--dangerously-skip-permissions`.
Anything you would be genuinely upset to find in a diff belongs in a hook, not in prose.

---

## 1. Files in the kit

```
CLAUDE.md                              # project memory, ~150 lines
.claude/
  settings.json                        # permissions + hook registration (commit this)
  rules/
    python-postgres.md                 # paths: harness/**, tools/**, tests/**
    sql.md                             # paths: **/*.sql, migrations/**, queries/**
  hooks/
    guard_invariants.py                # PreToolUse Edit|Write — the enforced invariants
    format_python.py                   # PostToolUse Edit|Write — ruff format + fix
    tests_only.py                      # PreToolUse for the test-first subagent
  skills/
    adr/SKILL.md                       # /adr   — write an ADR in the house format
    rule/SKILL.md                      # /rule  — add a rule or risk, numbering checked
    red/SKILL.md                       # /red   — capture a RED case verbatim
    task/SKILL.md                      # /task  — start a work item with its exit criteria
  agents/
    design-conformance.md              # read-only reviewer against the design docs
    test-first.md                      # writes tests; blocked from writing implementation
```

Install:

```bash
cp -r h3-claude-kit/. /path/to/h3/
cd /path/to/h3
chmod +x .claude/hooks/*.py      # the copy may not preserve the executable bit
claude
/context                          # confirm CLAUDE.md and rules loaded
/hooks                            # confirm both hooks registered
/doctor                           # setup checkup, including CLAUDE.md size
```

Commit `.claude/settings.json`, `rules/`, `hooks/`, `skills/`, `agents/`. Keep
`.claude/settings.local.json` gitignored for anything machine-specific.

---

## 2. CLAUDE.md — and what deliberately is not in it

Target is **under 200 lines**. Longer files consume context every request and, more importantly,
adherence drops. The version in the kit is about 150.

What earns a place: the stack decisions, the nine invariants, the banned vocabulary, the deleted
mechanisms, the anti-milestones, the three landing places for changes, and a pointer table into
`docs/`.

**Do not `@`-import the design documents.** `@docs/harness-core-v3.md` would pull 40KB into every
session at launch, and the four core documents together are 223KB. They are reference material
Claude reads on demand — which is exactly what your own layer-2 argument says about cache scope:
what is written once and read by every call is priced differently from what is read once. Point at
the documents; let Claude open the section it needs.

`/doctor` will offer to trim a checked-in CLAUDE.md. Its instinct is to cut what Claude can derive
from the codebase — directory layouts, dependency lists — and keep pitfalls and conventions that
differ from tool defaults. That instinct is right for this file: the invariants stay, a description
of the package layout does not.

**One correction worth making early.** CLAUDE.md is delivered as a user message after the system
prompt, not as part of it. There is no strict-compliance guarantee. If a rule must hold every time,
it is a hook. The kit's CLAUDE.md and `guard_invariants.py` deliberately overlap on the four rules
that matter most — the prose explains, the hook enforces.

---

## 3. Rules: the path-scoped half

`.claude/rules/*.md` files with `paths:` frontmatter load only when Claude reads a matching file.
This is how you keep CLAUDE.md short without losing specificity.

The two in the kit are split by where a mistake is expensive:

- `python-postgres.md` fires on `harness/**`, `tools/**`, `tests/**` — psycopg 3, no ORM, SQL in
  files, the `Lease` value object, pool settings, test style, and a short "things that look
  helpful and are not" list.
- `sql.md` fires on `**/*.sql`, `migrations/**`, `queries/**` — forward-only migrations, the
  three unretrofittable columns, prefix-scan cost, the lessons-queries-as-acceptance-test rule,
  and the never list.

A rule with no `paths:` loads every session at the same priority as `.claude/CLAUDE.md`. Use that
sparingly; the point of the directory is the scoping.

**Caveat worth carrying over from your own design.** Your R50 says a pinned skill set amortises
price but not attention — telling a model where to look makes it look there and, plausibly,
marginally less elsewhere. The same argument applies to rules. Keep each one short and keep the
set small, and if you add a third rule file, ask what it displaces.

---

## 4. Skills: four, and why only four

Custom commands and skills are the same thing now — `.claude/commands/deploy.md` and
`.claude/skills/deploy/SKILL.md` both produce `/deploy`. Skills are the better form because they
take a directory of supporting files and frontmatter that controls who can invoke them.

| Skill | Invocation | What it does |
|---|---|---|
| `/adr` | you only (`disable-model-invocation: true`) | Writes an ADR in the house format, with the two sections that carry the weight |
| `/rule` | you or Claude | Adds a rule or risk after checking the numbering authority |
| `/red` | you or Claude | Captures a RED case verbatim, before any jig is written |
| `/task` | you or Claude | Starts a work item: reads the breakdown row, states exit criteria, plans first |

`/adr` is user-only on purpose: an ADR is a decision, and Claude deciding to record a decision is
one step from Claude deciding the decision. `disable-model-invocation: true` also removes its
description from context entirely, so it costs nothing until you type it.

Two features the kit uses that are worth knowing about:

**Dynamic context injection.** A line like ``!`ls -1 docs/adr/` `` runs before Claude sees the
skill and is replaced by its output. `/adr` uses it to list existing ADRs; `/rule` uses it to grep
the highest assigned numbers; `/task` uses it for `git log` and `git status`. This is how a skill
arrives already grounded in the repo rather than asking Claude to go look. Note that a failed
command **aborts the whole invocation**, so append `|| true` to anything that legitimately exits
non-zero — the kit's skills already do.

**Skill content persists.** Once invoked, the rendered SKILL.md stays in the conversation for the
rest of the session. Write standing instructions, not one-time steps, and keep bodies short —
every line is a recurring cost. Under 500 lines; the kit's are well under.

### Skills you might add later, and their trigger

Do not add these now. Add each when the trigger fires, which is the same discipline your design
applies to mechanisms:

| Trigger | Add |
|---|---|
| You have explained the check ladder to Claude twice | `/ladder` — the four rungs, what each catches, what it costs |
| You are writing the Odoo module and keep restating conventions | `/odoo` — the file conventions from `odoo-adaptation` §2 |
| The `EXPLAIN ANALYZE` ritual for the claim query becomes routine | `/explain` — runs it at realistic graph size and reports against the R15 baseline |
| Gate A becomes a thing you rerun | `/gate-a` — the kill-test suite as a checklist |

---

## 5. Subagents: two, both of them structural

Subagents run in an isolated context and return only a summary. Two uses here are not about
context economy at all — they are about **who is allowed to do what**, which is your design's
argument applied to the tool building it.

**`design-conformance`** is read-only (`tools: Read, Grep, Glob, Bash` — no Write, no Edit). It
reads the diff, opens the governing design sections, and reports findings by severity. It is given
one instruction your own review documents insisted on: *a stated rationale never downgrades a
finding*. It has `memory: project`, so recurring divergences accumulate in
`.claude/agent-memory/design-conformance/` and become shareable via version control.

Invoke it explicitly after anything substantial:

```
@design-conformance review the diff against core §5
```

**`test-first`** writes tests and is blocked by a `PreToolUse` hook in its own frontmatter from
writing anything outside `tests/`. This is rules 82–83 enforced rather than requested. The
frontmatter hook needs the folder trusted once — accept the workspace trust dialog and it runs.

Beyond those two, use the built-ins rather than defining more. `Explore` for "where is X handled",
`Plan` during plan mode. Both skip CLAUDE.md to stay cheap, so if a rule must reach them, restate
it in the delegation prompt.

**Do not build a fleet.** Your design deleted `judge` partly because it never fired, and the same
test applies here: a subagent that costs a definition and fires twice is a subagent to delete.

---

## 6. Hooks: the enforced half

`guard_invariants.py` blocks five things on `Edit|Write`:

1. Editing an existing migration — forward-only.
2. `datetime.now()` / `time.time()` under `harness/ledger/` — all time comes from the store's clock.
3. A class named `*Orchestrator|Coordinator|Manager|Controller|Router|Supervisor`, or `TaskCard`.
4. Creating a new `docs/*.md` that is not an ADR — rule 63, no new design documents.
5. Editing a generated Odoo file — rule 78.

Each exits 2 with the reason on stderr, which Claude reads as feedback and adjusts to. All five
cases plus the pass cases are tested; the script is Python rather than bash + `jq` so it has no
dependency the repo lacks.

Number 4 is the one that will surprise you, and it is the one most worth having. "We need a
document to hold these changes" is the sentence your register says starts every one of these
cycles, and an agent that has just done good work is exactly the party most likely to write it.

`format_python.py` runs `ruff format` and `ruff check --fix` on the edited file after every write
and **never blocks** — it exits 0 always, so a lint complaint arrives as text Claude reads rather
than a wall it argues with.

### Two hooks worth considering, not in the kit

**A `Stop` prompt-hook asking the rule-62 question.** Cheap to add, uses Haiku, fires when Claude
finishes responding:

```json
{ "hooks": { "Stop": [ { "hooks": [ { "type": "prompt",
  "prompt": "If this turn added a mechanism, does the transcript name its detector? If a mechanism was added with no detector and no acknowledgement that none exists, respond {\"ok\": false, \"reason\": \"<which mechanism>\"}. Otherwise {\"ok\": true}." } ] } ] } }
```

It will occasionally be wrong and it costs a call per turn. Try it for a week; if it never fires,
delete it — that is principle 8 applied to your own tooling.

**A `SessionStart` hook with matcher `compact`** re-injecting the invariants after compaction.
Project-root CLAUDE.md is re-read after `/compact` automatically, so this is only worth it if you
find the path-scoped rules going missing in long sessions — those are *not* re-injected and reload
only when Claude next touches a matching file.

---

## 7. Permissions and modes

The kit's `settings.json` allows the test/lint/type loop and read-only git without prompting, asks
on `docker`, `createdb`, `dropdb` and `git push`, and denies `.env`, edits to applied migrations,
edits to existing ADRs, `rm -rf` and force-push.

`Edit(docs/adr/**)` is denied rather than asked because an ADR of record is not edited — it is
superseded by a new one. That is your design's rule, expressed as a permission.

**Permission modes.** Plan mode as the default for ledger, reaper, workspace and config-hash work
is worth the friction. `acceptEdits` is fine for test writing and docs. Reach for
`bypassPermissions` roughly never on this project: the hooks still fire, but the deny list stops
protecting you and the whole point of the current phase is that the substrate is the part that has
to be right.

**Checkpoints.** `/rewind` restores files Claude edited, but not changes made by Bash commands and
not subagent edits. On a project where the workspace layer runs `docker` and `dropdb`, git is your
real undo. Commit early and often.

---

## 8. MCP: the ledger as a queryable thing

Once the schema exists, connect a read-only Postgres MCP server so Claude can answer questions
against the board directly rather than by writing throwaway scripts:

```json
{
  "mcpServers": {
    "ledger": {
      "type": "stdio",
      "command": "uvx",
      "args": ["postgres-mcp", "--access-mode=restricted"],
      "env": { "DATABASE_URI": "${H3_LEDGER_RO_URL}" }
    }
  }
}
```

Three cautions, in order of how much they matter:

1. **Use a role with `SELECT` only, on the ledger database only.** Not the workspace cluster, not
   a superuser. `env` in `.mcp.json` expands `${VAR}` from your environment, so the URL never
   lands in the repo.
2. This is a convenience for *you*, not part of H3. Nothing the harness does should depend on an
   MCP server existing.
3. Tool search is on by default, so an idle server costs little context. Run `/mcp` to see status
   and per-server token cost.

The `queries/lessons.sql` catalogue is the better interface for anything you ask twice — a field
nobody can write a query against is a field to remove, and that test only works if the queries are
committed.

---

## 9. Models, effort and context

Your design's own tiering argument transfers almost directly.

- **Design work, ADRs, the split-jig-shaped problems** — Opus, high effort. One call per subtree
  is the cheapest place in the system to think hard, and the same is true of the sessions where
  you are deciding shape.
- **Implementation against a complete contract** — Sonnet. The edit is enumerated; thinking is
  cost. This is most of Phase 1.
- **Exploration** — the built-in `Explore` agent, or a project-level `Explore` override with
  `model: haiku` if you want to pin it cheap.

`ultrathink` anywhere in a prompt buys deeper reasoning for that turn. Use it on the predicate,
the fencing argument and anything about `config_hash` — those are the three places in your design
where a subtle wrong answer survives review.

**Context hygiene.** Run `/context` when a session feels degraded; it shows what actually loaded.
Delegate verbose work — running the container suite, reading a 1,000-line design section for one
fact — to subagents so the output stays out of your window. Start a fresh session at task
boundaries rather than compacting; your tasks have written exit criteria, which makes the boundary
obvious.

---

## 10. Parallel work

`git worktree` is already in your design as the isolation mechanism for cards. The same primitive
works for you: run separate Claude Code sessions in separate worktrees when two tasks genuinely do
not touch the same files — say P1-8 (content store) and P1-2 (claim).

Apply your own four tests before doing it: disjoint touch sets, no cross-references, safe retry,
and the two together accounting for the parent. If they fail, do the tasks in sequence. The
temptation to parallelise because the tool permits it is the same temptation your design spends
several sections resisting.

---

## 11. Order of adoption

Do not install everything on day one. The triggers matter more than the list.

**Now.** `CLAUDE.md`, the two rules files, `settings.json`, `guard_invariants.py`,
`format_python.py`. That is the enforced core and it pays immediately.

**Week one.** `/task` and `/adr`. Both encode a discipline you would otherwise retype.

**When triggered.**

| Trigger | Add |
|---|---|
| Claude adds something the design does not name, twice | `design-conformance`, invoked routinely |
| You start writing jigs | `/red`, and the corpus directory |
| You are about to implement a behaviour with a stateable semantic | `test-first` |
| The schema exists and you are querying it by hand | the ledger MCP server |
| You keep explaining the same thing a third time | a skill for it |

**When to remove.** At each phase boundary, run your own standing review on the tooling too:
which of these has never fired? A hook that has blocked nothing in a month is either perfectly
deterrent or unnecessary, and the debug log (`claude --debug-file /tmp/claude.log`) tells you
which.

---

## 12. What not to do

- **Do not put the design documents in CLAUDE.md.** They are 223KB. Point at them.
- **Do not write a rule for something a hook can enforce.** Prose is a request.
- **Do not build a subagent per role in your design.** `splitter`, `verifier`, `integrator` are
  components of H3, not Claude Code agents. Modelling them in `.claude/agents/` would mean
  building a shadow harness inside the tool you are using to build the harness, and the shadow
  would drift.
- **Do not let Claude Code write ADRs unprompted.** `/adr` is user-invocable only for this reason.
- **Do not add a fifth skill because four looks thin.** Six jigs is your ceiling for a reason, and
  the same reasoning applies here: skill descriptions load every request, and a listing that
  overflows its budget gets descriptions silently truncated.

---

## 13. Verifying the setup works

| Command | Confirms |
|---|---|
| `/context` | Which memory files, rules and skills actually loaded |
| `/hooks` | Both hooks registered under the right events |
| `/doctor` | Setup checkup, CLAUDE.md size, skill listing cost, duplicate agent names |
| `/memory` | What auto memory has saved, and lets you edit it |
| `claude --debug-file /tmp/claude.log` | Hook exit codes, stdout, stderr — the only way to see a silently failing hook |

Test the guard hook directly rather than trusting it:

```bash
echo '{"tool_input":{"file_path":"harness/ledger/claim.py","new_string":"x = datetime.now()"}}' \
  | python3 .claude/hooks/guard_invariants.py; echo "exit=$?"   # expect 2
```

All eight cases in the kit were tested this way before shipping. If you change the script, retest —
a hook that silently exits 0 looks exactly like a hook that is working.
