#!/usr/bin/env python3
"""PreToolUse hook used by the test-first subagent.

Mirrors rules 82-83: whatever writes the test may not edit the implementation.
This is the design's own argument applied to the tool that builds it — the check
is hidden from the party being checked.
"""

from __future__ import annotations

import json
import re
import sys

TEST_PATHS = re.compile(r"(^|/)tests?/|_test\.py$|/conftest\.py$")


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    path = ((payload.get("tool_input") or {}).get("file_path") or "").replace("\\", "/")
    if not path or TEST_PATHS.search(path):
        sys.exit(0)

    print(
        "BLOCKED: this agent writes tests only. The implementation is a separate step, "
        "and the implementing step must not be able to edit the test (rules 82-83). "
        f"Attempted: {path}",
        file=sys.stderr,
    )
    sys.exit(2)


if __name__ == "__main__":
    main()
