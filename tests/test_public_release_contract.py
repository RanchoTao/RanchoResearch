"""Public software release boundary; historical science assets are not tested here."""

from pathlib import Path
import tomllib
import unittest


ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = (
    "ICLR2027_HANDOFF",
    "arc02",
    "arc21",
    "archive",
    "meta_arc02",
    "meta_arc05",
    "paper",
    "research",
    "gap_mining",
    "knowledge_base",
    "run_inputs",
    "tmp",
    "releases",
    "reproduce.py",
    "doctor-report.json",
    "frontend-legacy",
    "image",
    "website",
)


class PublicReleaseContractTests(unittest.TestCase):
    def test_no_historical_workspaces_in_default_source_tree(self):
        for name in EXCLUDED:
            with self.subTest(name=name):
                self.assertFalse((ROOT / name).exists())

    def test_readme_is_software_facing(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertTrue(readme.startswith("# RanchoResearch"))
        self.assertNotIn("ICLR2027_HANDOFF", readme)
        self.assertNotIn("arxiv.org/abs/2610.", readme)
        self.assertLess(len(readme.splitlines()), 240)

    def test_package_identity_and_compatibility(self):
        project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
        self.assertEqual(project["name"], "ranchoresearch")
        self.assertEqual(project["scripts"]["researchclaw"], project["scripts"]["ranchoresearch"])

    def test_upstream_license_kept(self):
        license_text = (ROOT / "LICENSES/AutoResearchClaw-MIT.txt").read_text(encoding="utf-8")
        self.assertIn("MIT License", license_text)
        self.assertIn("Copyright (c) 2026 Aiming Lab", license_text)
        self.assertTrue((ROOT / "THIRD_PARTY_NOTICES.md").exists())


if __name__ == "__main__":
    unittest.main()
