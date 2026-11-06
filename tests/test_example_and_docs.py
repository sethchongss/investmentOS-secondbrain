"""The shipped example, the diagrams, and the private-vault ignore rule."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import validate_vault as vaultlib  # noqa: E402

EXAMPLE = ROOT / "examples" / "low-oriole-metering"


def fences(text: str, lang: str) -> list[str]:
    found = []
    needle = f"```{lang}\n"
    start = 0
    while True:
        index = text.find(needle, start)
        if index < 0:
            return found
        index += len(needle)
        end = text.find("\n```", index)
        if end < 0:
            raise AssertionError(f"unclosed {lang} fence")
        found.append(text[index:end])
        start = end + 4


class ExampleStoryTests(unittest.TestCase):
    def test_example_validates(self):
        schema = vaultlib.load_schema(ROOT / "schema" / "vault.schema.json")
        report = vaultlib.validate_vault(EXAMPLE, schema, example=True)
        self.assertEqual(report.issues, [], [f"{item.path}: {item.message}" for item in report.issues])
        self.assertGreater(report.scanned, 20)

    def test_private_skeleton_validates(self):
        schema = vaultlib.load_schema(ROOT / "schema" / "vault.schema.json")
        report = vaultlib.validate_vault(ROOT / "vault", schema, example=False)
        self.assertEqual(report.issues, [], report.issues)

    def test_story_keeps_before_and_after(self):
        company = (EXAMPLE / "wiki/companies/low-oriole-metering.md").read_text(encoding="utf-8")
        change = (EXAMPLE / "changelog/2026-03-21-backlog-correction.md").read_text(encoding="utf-8")
        proposal = (EXAMPLE / "proposals/2026-03-20-backlog-correction.md").read_text(encoding="utf-8")
        january = (EXAMPLE / "raw/src-lom-20260114.md").read_text(encoding="utf-8")
        journal = (EXAMPLE / "wiki/journal/2026-01-15-first-pass.md").read_text(encoding="utf-8")
        memo = (EXAMPLE / "output/memos/2026-03-21-low-oriole-backlog.md").read_text(encoding="utf-8")

        self.assertIn("Core backlog is $112 million", company)
        self.assertNotIn("Conviction 4", company)
        self.assertIn("## Before", change)
        self.assertIn("## After", change)
        self.assertIn("Conviction 4", change)
        self.assertIn("Core backlog is $112 million", change)
        self.assertIn("status: approved", proposal)
        self.assertIn("unreliable", proposal)
        self.assertIn("$180 million", january)
        self.assertIn("Synthetic", january)
        self.assertIn("$180 million", journal)
        self.assertNotIn("superseded", journal)
        self.assertIn("## Sources", memo)
        self.assertIn("## Inference", memo)

    def test_all_five_relations_are_used(self):
        schema = vaultlib.load_schema(ROOT / "schema" / "vault.schema.json")
        found = set()
        for path in (EXAMPLE / "library/relations").glob("*.md"):
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.startswith("relation: "):
                    found.add(line.split(": ", 1)[1].strip())
        self.assertEqual(found, set(schema["relation_vocabulary"]))

    def test_relations_doc_lists_the_vocabulary(self):
        schema = vaultlib.load_schema(ROOT / "schema" / "vault.schema.json")
        text = (ROOT / "schema/relations.md").read_text(encoding="utf-8")
        for word in schema["relation_vocabulary"]:
            self.assertIn(f"`{word}`", text)


class DiagramTests(unittest.TestCase):
    def test_readme_and_architecture_share_the_maps(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        architecture = (ROOT / "docs/architecture.md").read_text(encoding="utf-8")
        plain = (ROOT / "docs/diagrams/second-brain-loop.txt").read_text(encoding="utf-8").strip("\n")
        self.assertIn(plain, [block.strip("\n") for block in fences(readme, "text")])
        self.assertIn(plain, [block.strip("\n") for block in fences(architecture, "text")])
        self.assertEqual(fences(readme, "mermaid"), fences(architecture, "mermaid"))
        self.assertIn("approved writeback, wiki only", fences(readme, "mermaid")[0])
        self.assertIn("docs/diagrams/second-brain-loop.svg", readme)

    def test_svg_is_standalone_and_returns_to_the_wiki(self):
        svg_path = ROOT / "docs/diagrams/second-brain-loop.svg"
        text = svg_path.read_text(encoding="utf-8")
        without_namespace = text.replace("http://www.w3.org/2000/svg", "")
        self.assertNotIn("http://", without_namespace)
        self.assertNotIn("https://", without_namespace)
        root = ET.parse(svg_path).getroot()
        xml = "{http://www.w3.org/2000/svg}"
        title = "".join(root.find(f"{xml}title").itertext())
        desc = "".join(root.find(f"{xml}desc").itertext())
        self.assertIn("loop", title.lower())
        self.assertIn("wiki", desc.lower())
        self.assertIn("no background service", desc.lower())
        self.assertIn("stroke-dasharray", text)
        self.assertIn("wiki only", text)


class QuickstartAndIgnoreTests(unittest.TestCase):
    def test_drill_script(self):
        proc = subprocess.run(
            [sys.executable, "tools/quickstart_drill.py"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("REPLACE_ME", proc.stdout)
        self.assertIn("not modified", proc.stdout)

    def test_private_markdown_is_ignored_and_layout_is_not(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "vault" / "raw").mkdir(parents=True)
            (root / "vault" / "raw" / ".gitkeep").write_text("", encoding="utf-8")
            (root / "vault" / "README.md").write_text("layout\n", encoding="utf-8")
            (root / "vault" / "raw" / "do-not-commit.md").write_text("nope\n", encoding="utf-8")
            shutil.copy(ROOT / ".gitignore", root / ".gitignore")
            init = subprocess.run(
                ["git", "init"],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(init.returncode, 0, init.stderr)
            ignored = subprocess.run(
                ["git", "check-ignore", "-q", "vault/raw/do-not-commit.md"],
                cwd=root,
                check=False,
            )
            self.assertEqual(ignored.returncode, 0)
            readme = subprocess.run(
                ["git", "check-ignore", "-q", "vault/README.md"],
                cwd=root,
                check=False,
            )
            self.assertNotEqual(readme.returncode, 0)
            keep = subprocess.run(
                ["git", "check-ignore", "-q", "vault/raw/.gitkeep"],
                cwd=root,
                check=False,
            )
            self.assertNotEqual(keep.returncode, 0)


if __name__ == "__main__":
    unittest.main()
