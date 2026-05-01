#!/usr/bin/env python3
"""
Sync codex skill sources into the ClawHub bundle.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = REPO_ROOT / "codex-skill"
BUNDLE_DIR = REPO_ROOT / "skill"
VERSION_FILE = REPO_ROOT / "VERSION"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def parse_frontmatter(text: str) -> tuple[dict[str, object], str]:
    if not text.startswith("---"):
        raise ValueError("codex-skill/SKILL.md is missing expected frontmatter")
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        raise ValueError("codex-skill/SKILL.md is missing expected frontmatter")

    end_index = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_index = index
            break
    if end_index is None:
        raise ValueError("codex-skill/SKILL.md is missing expected frontmatter")

    raw_yaml = "".join(lines[1:end_index])
    body = "".join(lines[end_index + 1 :]).lstrip("\r\n")
    data = yaml.safe_load(raw_yaml) or {}
    if not isinstance(data, dict):
        raise ValueError("codex-skill/SKILL.md frontmatter must be a mapping")
    return data, body


def bundle_frontmatter(source_text: str, version: str) -> str:
    source_frontmatter, body = parse_frontmatter(source_text)
    description = str(source_frontmatter.get("description", "") or "")
    homepage = github_homepage()
    output_frontmatter: dict[str, object] = {
        "name": "skill-usefulness-audit",
        "slug": "skill-usefulness-audit",
        "description": description,
        "version": version,
        "tags": ["audit", "skills", "ablation", "codex", "openclaw"],
    }
    if homepage:
        output_frontmatter["homepage"] = homepage
    rendered = yaml.safe_dump(
        output_frontmatter,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    )
    return "---\n" + rendered + "---\n" + body


def github_homepage() -> str | None:
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError:
        return None

    raw = result.stdout.strip()
    if not raw:
        return None
    if raw.startswith("https://github.com/"):
        return raw[:-4] if raw.endswith(".git") else raw
    if raw.startswith("git@github.com:"):
        path = raw.split(":", 1)[1]
        path = path[:-4] if path.endswith(".git") else path
        return f"https://github.com/{path}"
    return None


def assert_safe_bundle_path() -> None:
    repo = REPO_ROOT.resolve()
    source = SOURCE_DIR.resolve()
    bundle = BUNDLE_DIR.resolve()
    if not source.is_dir():
        raise RuntimeError(f"source directory does not exist: {SOURCE_DIR}")
    if source == bundle:
        raise RuntimeError("source and bundle directories must differ")
    if bundle.parent != repo or bundle.name != "skill":
        raise RuntimeError(f"refusing to sync unexpected bundle path: {BUNDLE_DIR}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sync codex skill sources into the ClawHub bundle.")
    parser.add_argument("--dry-run", action="store_true", help="Validate and preview sync without writing files.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    assert_safe_bundle_path()
    version = read_text(VERSION_FILE).strip()
    source_skill = read_text(SOURCE_DIR / "SKILL.md")
    bundle_skill = bundle_frontmatter(source_skill, version)

    if args.dry_run:
        print(f"Would sync {SOURCE_DIR} -> {BUNDLE_DIR}")
        print(f"Would write bundle SKILL.md for version {version} ({len(bundle_skill)} chars)")
        return 0

    if BUNDLE_DIR.exists():
        shutil.rmtree(BUNDLE_DIR)
    shutil.copytree(SOURCE_DIR, BUNDLE_DIR, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

    write_text(BUNDLE_DIR / "SKILL.md", bundle_skill)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
