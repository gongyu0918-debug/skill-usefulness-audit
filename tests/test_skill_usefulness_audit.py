from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
AUDIT_SCRIPT = REPO_ROOT / "codex-skill" / "scripts" / "skill_usefulness_audit.py"
SYNC_SCRIPT = REPO_ROOT / "scripts" / "sync_bundle.py"


def write_skill(root: Path, name: str, description: str, extra_body: str = "") -> None:
    skill_dir = root / name
    (skill_dir / "scripts").mkdir(parents=True, exist_ok=True)
    (skill_dir / "references").mkdir(parents=True, exist_ok=True)
    text = (
        "---\n"
        f"name: {name}\n"
        f"description: {description}\n"
        "---\n\n"
        f"# {name}\n\n"
        f"{extra_body}\n"
    )
    (skill_dir / "SKILL.md").write_text(text, encoding="utf-8")


class SkillUsefulnessAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="skill-audit-test-"))

    def tearDown(self) -> None:
        shutil.rmtree(self.tempdir)

    def run_audit(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python", str(AUDIT_SCRIPT), "audit", *args],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=True,
        )

    def test_json_usage_and_ablation_drive_delete_candidate(self) -> None:
        skills_root = self.tempdir / "skills"
        write_skill(skills_root, "tone-polisher", "Rewrite text with polished tone and softer phrasing.")
        write_skill(skills_root, "tone-helper", "Rewrite text with polished tone and softer phrasing.")

        usage_path = self.tempdir / "usage.json"
        usage_path.write_text(json.dumps({"tone-polisher": 0, "tone-helper": 0}), encoding="utf-8")

        ablation_path = self.tempdir / "ablation.json"
        ablation_path.write_text(
            json.dumps(
                [
                    {
                        "skill": "tone-polisher",
                        "case_id": "1",
                        "with_skill": {"pass": True, "score": 0.80},
                        "without_skill": {"pass": True, "score": 0.80},
                        "verdict": "same",
                    }
                ]
            ),
            encoding="utf-8",
        )

        result = self.run_audit(
            "--skills-root",
            str(skills_root),
            "--usage-file",
            str(usage_path),
            "--ablation-file",
            str(ablation_path),
        )

        self.assertIn("Delete Candidates", result.stdout)
        self.assertIn("tone-polisher", result.stdout)

    def test_history_fallback_counts_mentions(self) -> None:
        skills_root = self.tempdir / "skills"
        write_skill(skills_root, "emotion-orchestrator", "Detect emotion and route reply style.")

        history_path = self.tempdir / "history.jsonl"
        history_path.write_text(
            "\n".join(
                [
                    json.dumps({"role": "user", "text": "请用 $emotion-orchestrator 看一下"}),
                    json.dumps({"role": "assistant", "text": "emotion-orchestrator 已运行"}),
                ]
            ),
            encoding="utf-8",
        )

        result = self.run_audit(
            "--skills-root",
            str(skills_root),
            "--history-file",
            str(history_path),
        )

        self.assertIn("| 1 | emotion-orchestrator |", result.stdout)
        self.assertIn("calls=2", result.stdout)

    def test_sync_bundle_writes_publish_manifest(self) -> None:
        subprocess.run(["python", str(SYNC_SCRIPT)], cwd=REPO_ROOT, check=True, text=True, capture_output=True)
        bundle_skill = (REPO_ROOT / "skill" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("slug: skill-usefulness-audit", bundle_skill)
        self.assertIn("version: 0.1.0", bundle_skill)
        self.assertFalse((REPO_ROOT / "skill" / "scripts" / "__pycache__").exists())

    def test_output_directories_are_created(self) -> None:
        skills_root = self.tempdir / "skills"
        write_skill(skills_root, "emotion-orchestrator", "Detect emotion and route reply style.")
        markdown_out = self.tempdir / "nested" / "report.md"
        json_out = self.tempdir / "nested" / "report.json"

        self.run_audit(
            "--skills-root",
            str(skills_root),
            "--markdown-out",
            str(markdown_out),
            "--json-out",
            str(json_out),
        )

        self.assertTrue(markdown_out.exists())
        self.assertTrue(json_out.exists())


if __name__ == "__main__":
    unittest.main()
