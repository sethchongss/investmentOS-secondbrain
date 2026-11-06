"""Validator behavior on synthetic fixtures, not the shipped example."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import validate_vault as vaultlib  # noqa: E402


def write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text).lstrip("\n"), encoding="utf-8")


def source(n: int, **overrides) -> str:
    data = {
        "id": f"src-{n}",
        "title": f"Note {n}",
        "link": f"synthetic://desk/{n}",
        "post_id": f"syn-{n}",
        "date_posted": "2026-01-14",
        "date_captured": "2026-01-15",
    }
    data.update(overrides)
    return f"""---
id: {data["id"]}
type: source
title: {data["title"]}
source: Desk
author: A. Quill
date_posted: {data["date_posted"]}
date_captured: {data["date_captured"]}
link: {data["link"]}
post_id: {data["post_id"]}
synthetic: true
---

Synthetic excerpt for the fixture.
"""


def library(n: int, **overrides) -> str:
    data = {
        "id": f"lib-{n}",
        "link": f"synthetic://desk/{n}",
        "post_id": f"syn-{n}",
        "stub": f"raw/src-{n}.md",
        "claim": f"Claim {n} is the filed sentence.",
        "status_lines": "",
    }
    data.update(overrides)
    return f"""---
id: {data["id"]}
type: library
title: Claim {n}
source: Desk
author: A. Quill
date_posted: 2026-01-14
date_captured: 2026-01-15
link: {data["link"]}
post_id: {data["post_id"]}
claim: "{data["claim"]}"
specifics:
  - "One specific."
category: note
tags:
  - synthetic
context: Filed in a unit test.
reading_status: filed
source_stub: {data["stub"]}
synthetic: true
{data["status_lines"]}---

Body of the library record.
"""


class ParserTests(unittest.TestCase):
    def test_block_list_bool_and_int(self):
        data, body = vaultlib.parse_frontmatter(
            "---\n"
            "id: abc\n"
            "synthetic: true\n"
            "conviction: 4\n"
            "tags:\n"
            "  - one\n"
            "  - two\n"
            "also: [a, b]\n"
            "---\n"
            "hello\n"
        )
        self.assertEqual(data["tags"], ["one", "two"])
        self.assertEqual(data["also"], ["a", "b"])
        self.assertIs(data["synthetic"], True)
        self.assertEqual(data["conviction"], 4)
        self.assertEqual(body, "hello\n")

    def test_missing_close_and_multiline(self):
        with self.assertRaises(vaultlib.FrontmatterError):
            vaultlib.parse_frontmatter("---\nid: x\n")
        with self.assertRaises(vaultlib.FrontmatterError):
            vaultlib.parse_frontmatter("---\nnote: |\n  hello\n---\n")


class VaultTests(unittest.TestCase):
    def setUp(self):
        self.schema = vaultlib.load_schema(ROOT / "schema" / "vault.schema.json")
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "raw").mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def errors(self, example=False):
        report = vaultlib.validate_vault(self.root, self.schema, example=example)
        return report

    def test_minimal_pair_passes(self):
        write(self.root, "raw/src-1.md", source(1))
        write(self.root, "library/lib-1.md", library(1))
        report = self.errors()
        self.assertEqual(report.issues, [], report.issues)

    def test_missing_claim_is_named(self):
        text = library(1).replace('claim: "Claim 1 is the filed sentence."\n', "")
        write(self.root, "raw/src-1.md", source(1))
        write(self.root, "library/lib-1.md", text)
        messages = [issue.message for issue in self.errors().issues]
        self.assertTrue(any("claim" in message for message in messages), messages)

    def test_bad_relation_word(self):
        write(self.root, "raw/src-1.md", source(1))
        write(self.root, "library/lib-1.md", library(1))
        write(
            self.root,
            "library/relations/rel-1.md",
            """---
id: rel-1
type: relation
relation: supports-ish
from: lib-1
to: lib-1
note: Not a real relation.
synthetic: true
---

No.
""",
        )
        messages = [issue.message for issue in self.errors().issues]
        self.assertTrue(any("relation" in message and "must be one of" in message for message in messages), messages)

    def test_dangling_reference_and_local_link(self):
        write(self.root, "raw/src-1.md", source(1))
        body = library(1) + "\nSee [missing](missing.md) and [[lib-missing]].\n"
        write(self.root, "library/lib-1.md", body)
        write(
            self.root,
            "library/relations/rel-1.md",
            """---
id: rel-1
type: relation
relation: supports
from: lib-1
to: lib-999
note: Points nowhere.
synthetic: true
---

No.
""",
        )
        messages = [issue.message for issue in self.errors().issues]
        self.assertTrue(any("dangling reference 'lib-999'" in message for message in messages), messages)
        self.assertTrue(any("local link target not found" in message for message in messages), messages)
        self.assertTrue(any("[[lib-missing]]" in message for message in messages), messages)

    def test_duplicate_post_id(self):
        write(self.root, "raw/src-1.md", source(1))
        write(self.root, "raw/src-2.md", source(2, post_id="syn-1", link="synthetic://desk/2"))
        messages = [issue.message for issue in self.errors().issues]
        self.assertTrue(any("duplicate post_id" in message for message in messages), messages)

    def test_example_mode_rejects_https_and_normal_mode_allows_it(self):
        write(
            self.root,
            "raw/src-1.md",
            source(1, link="https://example.com/notes/1", post_id="post-1"),
        )
        write(
            self.root,
            "library/lib-1.md",
            library(1, link="https://example.com/notes/1", post_id="post-1"),
        )
        self.assertEqual(self.errors(example=False).issues, [])
        messages = [issue.message for issue in self.errors(example=True).issues]
        self.assertTrue(any("https://" in message or "synthetic://" in message for message in messages), messages)

    def test_conviction_and_dates(self):
        write(self.root, "raw/src-1.md", source(1, date_posted="2026-02-01", date_captured="2026-01-01"))
        text = library(1) + ""
        # library() hardcodes dates that no longer match; rebuild with matching link only.
        write(
            self.root,
            "library/lib-1.md",
            """---
id: lib-1
type: library
title: Claim
source: Desk
author: A. Quill
date_posted: 2026-02-01
date_captured: 2026-01-01
link: synthetic://desk/1
post_id: syn-1
claim: "A claim."
specifics:
  - "One specific."
category: note
tags:
  - synthetic
context: Filed in a unit test.
reading_status: filed
source_stub: raw/src-1.md
synthetic: true
---

See [the principle](../wiki/principles/p.md).
""",
        )
        write(
            self.root,
            "wiki/principles/p.md",
            """---
id: prin-1
type: principle
title: P
thesis: "A thesis."
conviction: 7
evidence_for:
  - lib-1
evidence_against: []
current_belief: "Held loosely."
recall_question: "Q?"
recall_answer: "A."
last_shown: 2026-02-02
maturity: recurring
synthetic: true
---

Body.
""",
        )
        messages = [issue.message for issue in self.errors().issues]
        self.assertTrue(any("date_captured is earlier" in message for message in messages), messages)
        self.assertTrue(any("conviction" in message for message in messages), messages)
        self.assertTrue(any("recurring principle needs" in message for message in messages), messages)

    def test_superseded_without_relation(self):
        write(self.root, "raw/src-1.md", source(1))
        write(self.root, "raw/src-2.md", source(2))
        write(
            self.root,
            "library/lib-1.md",
            library(1, status_lines="claim_status: superseded\nsuperseded_by: lib-2\n"),
        )
        write(self.root, "library/lib-2.md", library(2))
        messages = [issue.message for issue in self.errors().issues]
        self.assertTrue(any("no supersedes relation" in message for message in messages), messages)

    def test_writeback_cannot_target_raw_or_journal(self):
        write(self.root, "raw/src-1.md", source(1))
        write(self.root, "library/lib-1.md", library(1))
        write(
            self.root,
            "wiki/journal/2026-01-15-note.md",
            """---
id: j-1
type: journal
title: Note
date: 2026-01-15
append_only: true
synthetic: true
---

Left as written.
""",
        )
        write(
            self.root,
            "proposals/prop-raw.md",
            """---
id: prop-raw
type: writeback_proposal
title: Bad target
date: 2026-01-16
target: raw/src-1.md
status: proposed
proposal_note: Tries to edit a source.
synthetic: true
---

No.
""",
        )
        write(
            self.root,
            "proposals/prop-journal.md",
            """---
id: prop-journal
type: writeback_proposal
title: Also bad
date: 2026-01-16
target: wiki/journal/2026-01-15-note.md
status: proposed
proposal_note: Tries to edit the journal.
synthetic: true
---

No.
""",
        )
        messages = [issue.message for issue in self.errors().issues]
        self.assertGreaterEqual(sum("in-place wiki page" in message for message in messages), 2, messages)

    def test_approved_proposal_and_changelog_headings(self):
        write(self.root, "raw/src-1.md", source(1))
        write(self.root, "library/lib-1.md", library(1))
        write(
            self.root,
            "wiki/companies/acme.md",
            """---
id: co-acme
type: company
title: Acme
company: Acme
current_belief: "Unchanged."
conviction: 2
synthetic: true
---

Page.
""",
        )
        write(
            self.root,
            "proposals/prop-1.md",
            """---
id: prop-1
type: writeback_proposal
title: Edit
date: 2026-01-20
target: wiki/companies/acme.md
status: approved
proposal_note: Needs a reviewer.
synthetic: true
---

Missing reviewer.
""",
        )
        write(
            self.root,
            "changelog/chg-1.md",
            """---
id: chg-1
type: changelog
title: Edit
date: 2026-01-21
target: wiki/companies/acme.md
proposal: prop-1
approved_by: example-analyst
synthetic: true
---

## After

Only one side.
""",
        )
        messages = [issue.message for issue in self.errors().issues]
        self.assertTrue(any("human_reviewer" in message for message in messages), messages)
        self.assertTrue(any("missing heading '## Before'" in message for message in messages), messages)

    def test_journal_filename_and_link_mismatch(self):
        write(self.root, "raw/src-1.md", source(1))
        write(
            self.root,
            "library/lib-1.md",
            library(1, link="synthetic://desk/other"),
        )
        write(
            self.root,
            "wiki/journal/note.md",
            """---
id: j-1
type: journal
title: Note
date: 2026-01-15
append_only: true
synthetic: true
---

Wrong filename.
""",
        )
        messages = [issue.message for issue in self.errors().issues]
        self.assertTrue(any("filename must start with date" in message for message in messages), messages)
        self.assertTrue(any("must match the source stub" in message for message in messages), messages)

    def test_placeholder_template_fails_inside_a_vault(self):
        write(self.root, "raw/src-1.md", source(1))
        write(self.root, "library/lib-1.md", library(1))
        template = (ROOT / "templates" / "library-record.md").read_text(encoding="utf-8")
        write(self.root, "library/lib-drill.md", template)
        messages = [issue.message for issue in self.errors().issues]
        self.assertTrue(any("REPLACE_ME" in message for message in messages), messages)

    def test_not_a_vault_root(self):
        empty = self.root / "empty"
        empty.mkdir()
        report = vaultlib.validate_vault(empty, self.schema)
        self.assertTrue(any("not a vault root" in issue.message for issue in report.issues))


class CliTests(unittest.TestCase):
    def test_example_cli_passes(self):
        proc = subprocess.run(
            [sys.executable, "tools/validate_vault.py", "examples/low-oriole-metering", "--example"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("0 errors", proc.stdout)

    def test_missing_vault_is_usage(self):
        proc = subprocess.run(
            [sys.executable, "tools/validate_vault.py", "no-such-vault"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)

    def test_repo_root_is_not_a_vault(self):
        proc = subprocess.run(
            [sys.executable, "tools/validate_vault.py", "."],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("not a vault root", proc.stdout)


if __name__ == "__main__":
    unittest.main()
