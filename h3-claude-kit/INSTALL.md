# Installing the H3 Claude Code kit

Unzip, then copy the contents into your repo root:

```bash
unzip h3-claude-kit.zip
cp -r h3-claude-kit/CLAUDE.md h3-claude-kit/.claude /path/to/h3/
cd /path/to/h3
chmod +x .claude/hooks/*.py     # in case the copy dropped the executable bit
```

Note the `cp` names `.claude` explicitly — `cp -r h3-claude-kit/* ` will silently skip it,
because it is a dotfolder.

Then start Claude Code and verify:

```
claude
/context      # CLAUDE.md and the two rules files should appear under Memory files
/hooks        # PreToolUse and PostToolUse should each show one hook
/doctor       # setup checkup
```

Test the guard hook directly rather than trusting it:

```bash
echo '{"tool_input":{"file_path":"harness/ledger/claim.py","new_string":"x = datetime.now()"}}' \
  | python3 .claude/hooks/guard_invariants.py; echo "exit=$?"   # expect 2

echo '{"tool_input":{"file_path":"harness/worker/loop.py","new_string":"def run(): pass"}}' \
  | python3 .claude/hooks/guard_invariants.py; echo "exit=$?"   # expect 0
```

## What is here

```
CLAUDE.md                          project memory, ~120 lines
.claude/settings.json              permissions + hook registration
.claude/rules/python-postgres.md   loads on harness/**, tools/**, tests/**
.claude/rules/sql.md               loads on **/*.sql, migrations/**, queries/**
.claude/hooks/guard_invariants.py  PreToolUse Edit|Write — the enforced invariants
.claude/hooks/format_python.py     PostToolUse Edit|Write — ruff format + fix, never blocks
.claude/hooks/tests_only.py        PreToolUse for the test-first subagent
.claude/skills/adr/SKILL.md        /adr
.claude/skills/rule/SKILL.md       /rule
.claude/skills/red/SKILL.md        /red
.claude/skills/task/SKILL.md       /task
.claude/agents/design-conformance.md
.claude/agents/test-first.md
.pre-commit-config.yaml            guards YOUR commits; Claude hooks only guard Claude's
hooks/check_invariants.py          same invariants, applied to the staged diff
hooks/check_no_new_docs.py         rule 63, applied to the staged diff
```

Install pre-commit as well — the Claude Code hooks do not see hand edits:

```bash
uv tool install pre-commit && pre-commit install
```

Commit all of it. Keep `.claude/settings.local.json` gitignored for anything machine-specific.

Full rationale is in `h3-claude-code-setup.md`.
