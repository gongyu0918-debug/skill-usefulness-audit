#!/usr/bin/env python3
"""
Sync codex skill sources into the ClawHub bundle.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

try:
    import yaml
except ModuleNotFoundError:
    yaml = None


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = REPO_ROOT / "codex-skill"
BUNDLE_DIR = REPO_ROOT / "skill"
VERSION_FILE = REPO_ROOT / "VERSION"
TEXT_SUFFIXES = {".json", ".md", ".py", ".txt", ".yaml", ".yml"}
OPENCLAW_NOTICE = """## ClawHub / OpenClaw Edition

This ClawHub bundle is packaged for OpenClaw. Install it from an OpenClaw workspace with:

```bash
openclaw skills install skill-usefulness-audit
```

OpenClaw picks up installed workspace skills in the next session. If you need Codex, Claude Code, or another agent-specific version, use the GitHub repository instead: https://github.com/gongyu0918-debug/skill-usefulness-audit

"""


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def normalize_text_tree(root: Path) -> None:
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        raw = path.read_bytes()
        if b"\0" in raw:
            continue
        text = raw.decode("utf-8", errors="replace")
        if "\r" in text:
            write_text(path, text.replace("\r\n", "\n").replace("\r", "\n"))


def strip_yaml_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def fallback_safe_load(raw_yaml: str) -> dict[str, object]:
    data: dict[str, object] = {}
    lines = raw_yaml.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        index += 1
        if not stripped or stripped.startswith("#"):
            continue
        if ":" not in stripped:
            continue
        key, raw_value = stripped.split(":", 1)
        key = key.strip()
        raw_value = raw_value.strip()
        if raw_value in {">", "|"}:
            parts: list[str] = []
            while index < len(lines) and (lines[index].startswith(" ") or not lines[index].strip()):
                parts.append(lines[index].strip())
                index += 1
            data[key] = "\n".join(part for part in parts if part).replace("\n", " ")
            continue
        if raw_value == "":
            items: list[str] = []
            while index < len(lines):
                item_line = lines[index]
                item_stripped = item_line.strip()
                if not item_stripped:
                    index += 1
                    continue
                if not item_line.startswith(" ") or not item_stripped.startswith("- "):
                    break
                items.append(strip_yaml_quotes(item_stripped[2:]))
                index += 1
            data[key] = items
            continue
        data[key] = strip_yaml_quotes(raw_value)
    return data


def fallback_safe_dump(data: dict[str, object]) -> str:
    lines: list[str] = []
    for key, value in data.items():
        if isinstance(value, dict):
            lines.append(f"{key}: {json.dumps(value, ensure_ascii=True, separators=(',', ':'))}")
            continue
        if isinstance(value, list):
            lines.append(f"{key}: {json.dumps(value, ensure_ascii=True, separators=(',', ':'))}")
            continue
        if isinstance(value, bool):
            lines.append(f"{key}: {str(value).lower()}")
            continue
        text = str(value)
        if "\n" in text:
            lines.append(f"{key}: >")
            for part in text.splitlines():
                lines.append(f"  {part}")
        else:
            lines.append(f"{key}: {text}")
    return "\n".join(lines) + "\n"


def safe_load_frontmatter(raw_yaml: str) -> dict[str, object]:
    if yaml is not None:
        data = yaml.safe_load(raw_yaml) or {}
    else:
        data = fallback_safe_load(raw_yaml)
    if not isinstance(data, dict):
        raise ValueError("codex-skill/SKILL.md frontmatter must be a mapping")
    return data


def safe_dump_frontmatter(data: dict[str, object]) -> str:
    return fallback_safe_dump(data)


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
    return safe_load_frontmatter(raw_yaml), body


def bundle_frontmatter(source_text: str, version: str) -> str:
    source_frontmatter, body = parse_frontmatter(source_text)
    description = " ".join(str(source_frontmatter.get("description", "") or "").split())
    homepage = github_homepage()
    output_frontmatter: dict[str, object] = {
        "name": "skill-usefulness-audit",
        "slug": "skill-usefulness-audit",
        "description": description,
        "version": version,
        "tags": ["audit", "skills", "ablation", "openclaw"],
        "user-invocable": True,
        "disable-model-invocation": True,
    }
    metadata: dict[str, object] = {"openclaw": {"skillKey": "skill-usefulness-audit"}}
    if homepage:
        output_frontmatter["homepage"] = homepage
        metadata["openclaw"]["homepage"] = homepage
    output_frontmatter["metadata"] = metadata
    rendered = safe_dump_frontmatter(output_frontmatter)
    return "---\n" + rendered + "---\n" + inject_openclaw_notice(body)


def inject_openclaw_notice(body: str) -> str:
    if "## ClawHub / OpenClaw Edition" in body:
        return body
    lines = body.splitlines(keepends=True)
    if lines and lines[0].startswith("# "):
        return lines[0] + "\n" + OPENCLAW_NOTICE + "".join(lines[1:])
    return OPENCLAW_NOTICE + body


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
    normalize_text_tree(BUNDLE_DIR)

    write_text(BUNDLE_DIR / "SKILL.md", bundle_skill)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
