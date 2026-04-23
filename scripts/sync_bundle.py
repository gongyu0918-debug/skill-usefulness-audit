#!/usr/bin/env python3
"""
Sync codex skill sources into the ClawHub bundle.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = REPO_ROOT / "codex-skill"
BUNDLE_DIR = REPO_ROOT / "skill"
VERSION_FILE = REPO_ROOT / "VERSION"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---"):
        raise ValueError("codex-skill/SKILL.md is missing expected frontmatter")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError("codex-skill/SKILL.md is missing expected frontmatter")

    raw_yaml = parts[1]
    body = parts[2].lstrip("\r\n")
    data: dict[str, str] = {}
    for line in raw_yaml.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"').strip("'")
    return data, body


def bundle_frontmatter(source_text: str, version: str) -> str:
    source_frontmatter, body = parse_frontmatter(source_text)
    description = source_frontmatter.get("description", "")
    homepage = github_homepage()
    output_lines = [
        "---",
        "name: skill-usefulness-audit",
        "slug: skill-usefulness-audit",
        f"description: {description}",
        f"version: {version}",
        "tags: [audit, skills, ablation, codex, openclaw]",
    ]
    if homepage:
        output_lines.append(f"homepage: {homepage}")
    output_lines.extend(["---", ""])
    return "\n".join(output_lines) + body


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


def main() -> int:
    if BUNDLE_DIR.exists():
        shutil.rmtree(BUNDLE_DIR)
    shutil.copytree(SOURCE_DIR, BUNDLE_DIR, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

    version = read_text(VERSION_FILE).strip()
    source_skill = read_text(SOURCE_DIR / "SKILL.md")
    write_text(BUNDLE_DIR / "SKILL.md", bundle_frontmatter(source_skill, version))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
