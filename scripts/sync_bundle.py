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


def bundle_frontmatter(source_text: str, version: str) -> str:
    body_start = source_text.find("\n---", 3)
    if not source_text.startswith("---") or body_start == -1:
        raise ValueError("codex-skill/SKILL.md is missing expected frontmatter")
    body = source_text[body_start + 4 :].lstrip("\r\n")
    description = ""
    for line in source_text[4:body_start].splitlines():
        if line.startswith("description:"):
            description = line.split(":", 1)[1].strip()
            break
    homepage = github_homepage()
    frontmatter = [
        "---",
        "name: skill-usefulness-audit",
        "slug: skill-usefulness-audit",
        f"description: {description}",
        f"version: {version}",
        "tags: [audit, skills, ablation, codex, openclaw]",
    ]
    if homepage:
        frontmatter.append(f"homepage: {homepage}")
    frontmatter.extend(["---", ""])
    return "\n".join(frontmatter) + body


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
