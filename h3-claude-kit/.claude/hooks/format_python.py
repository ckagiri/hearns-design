#!/usr/bin/env python3
"""PostToolUse hook on Edit|Write. Formats and lints the edited Python file.

Never blocks: always exits 0, so a lint complaint arrives as text Claude reads
rather than a wall it has to argue with.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return

    path = ((payload.get("tool_input") or {}).get("file_path") or "")
    if not path.endswith(".py") or not os.path.exists(path):
        return

    subprocess.run(
        ["uv", "run", "ruff", "format", path],
        capture_output=True,
        check=False,
    )
    result = subprocess.run(
        ["uv", "run", "ruff", "check", "--fix", path],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        print("\n".join((result.stdout or "").splitlines()[-20:]))


if __name__ == "__main__":
    main()
    sys.exit(0)
