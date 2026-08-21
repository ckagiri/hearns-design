#!/usr/bin/env python3
"""Pre-commit check: rule 63 — no new design documents.

Findings land in an existing document, an ADR, the register, or code. There is no
fifth place, and "we need a document to hold these changes" is the sentence that
starts the failure loop this project has already been through twice.
"""

from __future__ import annotations

import re
import subprocess
import sys

ALLOWED = re.compile(r"^docs/adr/\d{4}-[a-z0-9-]+\.md$")


def tracked(path: str) -> bool:
    result = subprocess.run(
        ["git", "ls-files", "--error-unmatch", path],
        capture_output=True,
        check=False,
    )
    return result.returncode == 0


def main() -> int:
    bad = [
        p
        for p in sys.argv[1:]
        if p.startswith("docs/") and p.endswith(".md")
        and not ALLOWED.match(p)
        and not tracked(p)
    ]
    for p in bad:
        print(
            f"BLOCKED: {p} is a new design document (rule 63). Land this in an existing "
            f"doc, a new ADR under docs/adr/, or docs/rules-and-risks.md.",
            file=sys.stderr,
        )
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
