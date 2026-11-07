"""Mandate onboarding: branching, generic mode, and no overwrites."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import mandate  # noqa: E402
import validate_vault as vaultlib  # noqa: E402

PROFILES = ROOT / "examples" / "profiles"


def copy_profile(name: str, tmp: Path) -> Path:
    dest = tmp / name
    shutil.copytree(PROFILES / name, dest)
    return dest


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise AssertionError(f"{old!r} not in {path}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


class ExampleProfileTests(unittest.TestCase):
    def test_examples_validate(self):
        schema = mandate.load_schema()
        found = mandate.example_profiles()
        self.assertGreaterEqual(len(found), 4)
        for profile in found:
            report = mandate.validate_profile(profile, schema, example=True)
            self.assertEqual(
                report.issues,
                [],
                [f"{item.path}: {item.message}" for item in report.issues],
            )

    def test_branching_maps_differ(self):
        reed = mandate.select_workflows(PROFILES / "reed-harbor-direct")
        hearth = mandate.select_workflows(PROFILES / "hearth-lane-office")
        glass = mandate.select_workflows(PROFILES / "glass-keel")
        wicket = mandate.select_workflows(PROFILES / "wicket-seed")
        mixed = mandate.select_workflows(PROFILES / "split-oak")
        lamps = mandate.select_workflows(PROFILES / "two-lamp-mfo")

        def ids(result, workflow):
            return [item["strategy_id"] for item in result["workflows"] if item["id"] == workflow]

        self.assertEqual(reed["mode"], "confirmed")
        self.assertIn("reed-pe", ids(reed, "pe_diligence"))
        self.assertEqual(ids(reed, "fund_diligence"), [])
        self.assertIn("hearth-funds", ids(hearth, "fund_diligence"))
        self.assertEqual(ids(hearth, "pe_diligence"), [])
        self.assertEqual(ids(glass, "pe_diligence"), [])
        self.assertEqual(ids(wicket, "pe_diligence"), [])
        self.assertEqual(ids(wicket, "ic_memo"), [])
        self.assertIn("split-pe", ids(mixed, "pe_diligence"))
        self.assertIn("split-funds", ids(mixed, "fund_diligence"))
        self.assertTrue(any("recommend_only" in note for note in mixed["contradictions"]))
        self.assertEqual(ids(lamps, "pe_diligence"), [])
        self.assertIn("two-lamp-funds", ids(lamps, "fund_diligence"))

        schema = mandate.load_schema()
        reed_screen = next(item for item in reed["workflows"] if item["id"] == "screening")
        hearth_screen = next(item for item in hearth["workflows"] if item["id"] == "screening")
        glass_monitor = next(item for item in glass["workflows"] if item["id"] == "monitoring")
        wicket_monitor = next(item for item in wicket["workflows"] if item["id"] == "monitoring")
        self.assertEqual(reed_screen["asks"], schema["emphasis"]["pe"]["asks"])
        self.assertEqual(hearth_screen["asks"], schema["emphasis"]["fund_selection"]["asks"])
        self.assertNotEqual(reed_screen["asks"], hearth_screen["asks"])
        self.assertEqual(glass_monitor["monitor"], schema["emphasis"]["hedge_fund"]["monitor"])
        self.assertEqual(wicket_monitor["monitor"], schema["emphasis"]["vc"]["monitor"])
        self.assertNotEqual(glass_monitor["monitor"], wicket_monitor["monitor"])
        for item in reed["workflows"]:
            self.assertTrue((ROOT / item["prompt"]).is_file(), item["prompt"])

    def test_prompts_quote_the_schema(self):
        schema = mandate.load_schema()
        screening = (ROOT / "prompts/workflows/screening.md").read_text(encoding="utf-8")
        thesis = (ROOT / "prompts/workflows/thesis-counterthesis.md").read_text(encoding="utf-8")
        pe = (ROOT / "prompts/workflows/pe-diligence.md").read_text(encoding="utf-8")
        funds = (ROOT / "prompts/workflows/fund-manager-diligence.md").read_text(encoding="utf-8")
        for kind in ("pe", "vc", "hedge_fund", "fund_selection"):
            self.assertIn(schema["emphasis"][kind]["asks"], screening)
            self.assertIn(schema["emphasis"][kind]["counterthesis"], thesis)
        self.assertIn(schema["emphasis"]["pe"]["asks"], pe)
        self.assertNotIn(schema["emphasis"]["fund_selection"]["asks"], pe)
        self.assertIn(schema["emphasis"]["fund_selection"]["asks"], funds)
        self.assertNotIn(schema["emphasis"]["pe"]["asks"], funds)

    def test_readme_leads_with_onboarding(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        onboard_at = readme.index("prompts/onboard.md")
        loop_at = readme.index("## The loop")
        self.assertLess(onboard_at, loop_at)
        self.assertIn("generic mode", readme)
        diagram = (ROOT / "docs/diagrams/second-brain-loop.txt").read_text(encoding="utf-8")
        self.assertIn("not evidence", diagram)
        self.assertIn("generic mode", diagram)


class BranchAndGuardTests(unittest.TestCase):
    def test_unknown_activity_stays_generic(self):
        with tempfile.TemporaryDirectory() as tmp:
            profile = copy_profile("wicket-seed", Path(tmp))
            replace_once(profile / "mandate.md", "activity: direct", "activity: unknown")
            report = mandate.validate_profile(profile, example=True)
            self.assertEqual(report.issues, [], report.issues)
            chosen = mandate.select_workflows(profile)
            self.assertEqual(chosen["mode"], "generic")
            self.assertEqual(chosen["workflows"], [])
            self.assertIn("Activity is unknown", chosen["reason"])

    def test_missing_profile_is_generic(self):
        with tempfile.TemporaryDirectory() as tmp:
            chosen = mandate.select_workflows(Path(tmp))
            self.assertEqual(chosen["mode"], "generic")
            self.assertIn("onboard.md", chosen["reason"])

    def test_profile_rejects_identity_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            profile = copy_profile("wicket-seed", Path(tmp))
            replace_once(
                profile / "mandate.md",
                "title: Fictional VC direct mandate",
                "title: Fictional VC direct mandate\nfirm_name: Do Not Store",
            )
            report = mandate.validate_profile(profile, example=True)
            self.assertTrue(any("firm_name" in issue.message for issue in report.issues))

    def test_mfo_cannot_share_clients(self):
        with tempfile.TemporaryDirectory() as tmp:
            profile = copy_profile("two-lamp-mfo", Path(tmp))
            replace_once(
                profile / "mandate.md",
                "client_separation: separate_files",
                "client_separation: not_applicable",
            )
            report = mandate.validate_profile(profile, example=True)
            blob = "\n".join(issue.message for issue in report.issues)
            self.assertIn("separate_files", blob)
            self.assertIn("shared client", blob)

    def test_return_objective_is_not_invented(self):
        with tempfile.TemporaryDirectory() as tmp:
            profile = copy_profile("wicket-seed", Path(tmp))
            mandate_path = profile / "mandate.md"
            replace_once(mandate_path, "return_objective: not_stated", "return_objective: user_stated")
            missing = mandate.validate_profile(profile, example=True)
            self.assertTrue(any("return_objective_words" in issue.message for issue in missing.issues))
            replace_once(
                mandate_path,
                "return_objective: user_stated",
                'return_objective: user_stated\nreturn_objective_words: "match a public index, as the fictional user typed it"',
            )
            mandate_path.write_text(
                mandate_path.read_text(encoding="utf-8")
                + "\n## User-stated objective\n\nmatch a public index, as the fictional user typed it\n",
                encoding="utf-8",
            )
            stated = mandate.validate_profile(profile, example=True)
            self.assertEqual(stated.issues, [], stated.issues)
            replace_once(
                mandate_path,
                "return_objective: user_stated",
                "return_objective: not_stated",
            )
            leftover = mandate.validate_profile(profile, example=True)
            self.assertTrue(any("not user_stated" in issue.message for issue in leftover.issues))

    def test_kind_fields_do_not_cross(self):
        with tempfile.TemporaryDirectory() as tmp:
            profile = copy_profile("wicket-seed", Path(tmp))
            replace_once(
                profile / "strategies" / "wicket-vc.md",
                "synthetic: true",
                "deal_type: buyout\nsynthetic: true",
            )
            crossed = mandate.validate_profile(profile, example=True)
            self.assertTrue(any("unknown field 'deal_type'" in issue.message for issue in crossed.issues))

            pe = copy_profile("reed-harbor-direct", Path(tmp))
            text = (pe / "strategies" / "reed-pe.md").read_text(encoding="utf-8")
            line = 'downside: "what breaks the equity if cash misses, or unknown until a source says"\n'
            self.assertIn(line, text)
            (pe / "strategies" / "reed-pe.md").write_text(text.replace(line, ""), encoding="utf-8")
            missing = mandate.validate_profile(pe, example=True)
            self.assertTrue(any("missing required field 'downside'" in issue.message for issue in missing.issues))

    def test_revision_and_refuse_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            profile = copy_profile("reed-harbor-direct", Path(tmp))
            revision = profile / "revisions" / "2026-04-02-ownership.md"
            ok, message = mandate.check_new(revision)
            self.assertFalse(ok)
            self.assertIn("refusing to overwrite", message)
            revision.unlink()
            report = mandate.validate_profile(profile, example=True)
            self.assertTrue(any("prior_revision" in issue.message for issue in report.issues))

    def test_both_is_not_collapsed(self):
        with tempfile.TemporaryDirectory() as tmp:
            profile = copy_profile("reed-harbor-direct", Path(tmp))
            replace_once(profile / "mandate.md", "activity: direct", "activity: both")
            report = mandate.validate_profile(profile, example=True)
            self.assertTrue(any("activity is both" in issue.message for issue in report.issues))

    def test_pe_institution_can_select_funds(self):
        with tempfile.TemporaryDirectory() as tmp:
            profile = copy_profile("hearth-lane-office", Path(tmp))
            replace_once(profile / "mandate.md", "  - sfo", "  - pe")
            report = mandate.validate_profile(profile, example=True)
            self.assertEqual(report.issues, [], report.issues)
            chosen = mandate.select_workflows(profile)
            kinds = {item["id"] for item in chosen["workflows"]}
            self.assertIn("fund_diligence", kinds)
            self.assertNotIn("pe_diligence", kinds)

    def test_unqualified_output_is_not_silently_added(self):
        with tempfile.TemporaryDirectory() as tmp:
            profile = copy_profile("hearth-lane-office", Path(tmp))
            replace_once(
                profile / "mandate.md",
                "  - fund_diligence",
                "  - fund_diligence\n  - pe_diligence",
            )
            chosen = mandate.select_workflows(profile)
            self.assertFalse(any(item["id"] == "pe_diligence" for item in chosen["workflows"]))
            self.assertTrue(any("pe_diligence" in note for note in chosen["contradictions"]))

    def test_constraints_are_shown_and_not_rewritten(self):
        saved = {
            "leverage": "none",
            "holding_period": "seven_years_plus",
            "decision_authority": "recommend_only",
            "concentration": "one third of a fictional sleeve",
        }
        snapshot = dict(saved)
        conflicts = mandate.constraint_conflicts(
            saved,
            {
                "leverage": "used",
                "holding_period": "days",
                "decides": True,
                "concentration": "above_stated",
            },
        )
        self.assertEqual(saved, snapshot)
        blob = "\n".join(conflicts)
        self.assertIn("leverage is none", blob)
        self.assertIn("seven_years_plus", blob)
        self.assertIn("recommend_only", blob)
        self.assertIn("one third", blob)

    def test_init_and_scaffold_do_not_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dest = root / "profile"
            first = mandate.init_profile(dest)
            self.assertEqual(first[0][0], "copied")
            path = dest / "mandate.md"
            path.write_text(path.read_text(encoding="utf-8") + "\nKeep this draft.\n", encoding="utf-8")
            second = mandate.init_profile(dest)
            self.assertEqual(second[0][0], "skipped")
            self.assertIn("Keep this draft.", path.read_text(encoding="utf-8"))

            vault = root / "vault"
            lines = mandate.scaffold_profile(PROFILES / "reed-harbor-direct", vault)
            self.assertTrue(any(line.startswith("copied ") for line in lines))
            written = vault / "wiki" / "playbooks" / "wf-screening-reed-pe.md"
            original = written.read_text(encoding="utf-8")
            self.assertNotIn("{{", original)
            written.write_text(original + "\nEdited by a person.\n", encoding="utf-8")
            again = mandate.scaffold_profile(PROFILES / "reed-harbor-direct", vault)
            self.assertTrue(any("refusing to overwrite" in line for line in again))
            self.assertIn("Edited by a person.", written.read_text(encoding="utf-8"))
            schema = vaultlib.load_schema(ROOT / "schema" / "vault.schema.json")
            report = vaultlib.validate_vault(vault, schema, example=False)
            self.assertEqual(report.issues, [], [f"{item.path}: {item.message}" for item in report.issues])

    def test_profile_markdown_is_ignored_and_layout_is_not(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            keep = root / "vault" / "profile" / "strategies"
            keep.mkdir(parents=True)
            (keep / ".gitkeep").write_text("", encoding="utf-8")
            (root / "vault" / "profile" / "mandate.md").write_text("private\n", encoding="utf-8")
            shutil.copy(ROOT / ".gitignore", root / ".gitignore")
            init = subprocess.run(["git", "init"], cwd=root, capture_output=True, text=True, check=False)
            self.assertEqual(init.returncode, 0, init.stderr)
            ignored = subprocess.run(
                ["git", "check-ignore", "-q", "vault/profile/mandate.md"],
                cwd=root,
                check=False,
            )
            self.assertEqual(ignored.returncode, 0)
            tracked = subprocess.run(
                ["git", "check-ignore", "-q", "vault/profile/strategies/.gitkeep"],
                cwd=root,
                check=False,
            )
            self.assertNotEqual(tracked.returncode, 0)

    def test_research_validator_skips_profile_types(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp) / "vault"
            (vault / "raw").mkdir(parents=True)
            (vault / "profile").mkdir()
            (vault / "profile" / "mandate.md").write_text(
                "---\nid: not-a-source\ntype: mandate\n---\n\nnot a research record\n",
                encoding="utf-8",
            )
            schema = vaultlib.load_schema(ROOT / "schema" / "vault.schema.json")
            report = vaultlib.validate_vault(vault, schema, example=False)
            self.assertEqual(report.issues, [])
            self.assertEqual(report.scanned, 0)
            (vault / "profile" / "note.md").write_text("see https://example.com\n", encoding="utf-8")
            example = vaultlib.validate_vault(vault, schema, example=True)
            self.assertTrue(any("https://" in issue.message for issue in example.issues))


if __name__ == "__main__":
    unittest.main()
