#!/usr/bin/env python3
"""Run the README drill on a temporary copy of the example vault.

The curated example in the repository is not modified.
"""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

import validate_vault

ROOT = Path(__file__).resolve().parents[1]

JOURNAL = """---
id: j-drill-20260403
type: journal
title: Quickstart drill entry
date: 2026-04-03
append_only: true
synthetic: true
---

Synthetic drill. I read the memo of 21 Mar 2026 and did not edit the wiki.
See [the memo](../../output/memos/2026-03-21-low-oriole-backlog.md).
"""


def main() -> int:
    schema = validate_vault.load_schema(ROOT / "schema" / "vault.schema.json")
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp) / "vault-drill"
        shutil.copytree(ROOT / "examples" / "low-oriole-metering", vault)
        print("1. Copied examples/low-oriole-metering to a temp folder.")

        base = validate_vault.validate_vault(vault, schema, example=True)
        if base.issues:
            _print_issues(base)
            return 1
        print(f"2. Validated the copy with --example: ok, {base.scanned} files.")

        shutil.copy(
            ROOT / "templates" / "library-record.md",
            vault / "library" / "lib-drill.md",
        )
        print("3. Copied templates/library-record.md onto that copy.")

        bad = validate_vault.validate_vault(vault, schema, example=True)
        blob = "\n".join(issue.message for issue in bad.issues)
        if not bad.issues or "REPLACE_ME" not in blob:
            print("Expected the unfinished template to fail validation.")
            _print_issues(bad)
            return 1
        print(f"4. Validator rejected it ({len(bad.issues)} errors), including REPLACE_ME.")

        (vault / "library" / "lib-drill.md").unlink()
        dest = vault / "wiki" / "journal" / "2026-04-03-drill.md"
        dest.write_text(JOURNAL, encoding="utf-8")
        print("5. Removed the template and wrote wiki/journal/2026-04-03-drill.md.")

        good = validate_vault.validate_vault(vault, schema, example=True)
        if good.issues:
            _print_issues(good)
            return 1
        print(f"6. Validated again: ok, {good.scanned} files.")
    print("Done. The example in the repository was not modified.")
    return 0


def _print_issues(report: validate_vault.Report) -> None:
    for issue in report.issues:
        loc = issue.path or "(vault)"
        print(f"{loc}: {issue.message}")


if __name__ == "__main__":
    sys.exit(main())
