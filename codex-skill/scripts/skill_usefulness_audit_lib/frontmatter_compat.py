from __future__ import annotations

import re

from . import common as _common

_CJK_NAME_PATTERN = re.compile(r"[^a-z0-9\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]+")


def normalize_name(value: str) -> str:
    """Normalize skill identifiers without dropping CJK skill names."""
    text = str(value).strip().lower()
    text = _CJK_NAME_PATTERN.sub("-", text)
    text = re.sub(r"-{2,}", "-", text)
    return text.strip("-")


def _consume_block_list(yaml_lines: list[str], index: int) -> tuple[list[object] | None, int]:
    items: list[object] = []
    cursor = index
    while cursor < len(yaml_lines):
        line = yaml_lines[cursor]
        stripped = line.strip()
        if not stripped:
            cursor += 1
            continue
        if not line[:1].isspace():
            break
        if not stripped.startswith("- "):
            break
        raw_item = stripped[2:].strip()
        items.append(_common.parse_frontmatter_scalar(raw_item))
        cursor += 1
    return (items, cursor) if items else (None, index)


def parse_frontmatter(text: str) -> tuple[dict[str, object], str]:
    """Parse frontmatter fields needed for skill discovery.

    This mirrors the lightweight parser in common.py and adds one missing
    fallback case: indented YAML lists such as `tags:` followed by `- audit`.
    PyYAML, when installed, remains the primary parser.
    """
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return {}, text

    end_index = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_index = index
            break
    if end_index is None:
        return {}, text

    raw_yaml = "".join(lines[1:end_index])
    body = "".join(lines[end_index + 1 :]).lstrip("\r\n")
    parsed = _common.safe_frontmatter_mapping(raw_yaml)
    if parsed is not None:
        return parsed, body

    data: dict[str, object] = {}
    yaml_lines = raw_yaml.splitlines()
    index = 0
    while index < len(yaml_lines):
        line = yaml_lines[index]
        stripped = line.strip()
        index += 1
        if not stripped or stripped.startswith("#") or line[:1].isspace():
            continue
        if ":" not in stripped:
            continue
        key, raw_value = stripped.split(":", 1)
        key = key.strip()
        raw_value = raw_value.strip()
        if raw_value in {">", "|"}:
            parts: list[str] = []
            while index < len(yaml_lines) and (yaml_lines[index][:1].isspace() or not yaml_lines[index].strip()):
                part = yaml_lines[index].strip()
                if part:
                    parts.append(part)
                index += 1
            data[key] = (" " if raw_value == ">" else "\n").join(parts)
            continue
        if raw_value == "":
            items, next_index = _consume_block_list(yaml_lines, index)
            if items is not None:
                data[key] = items
                index = next_index
            continue
        data[key] = _common.parse_frontmatter_scalar(raw_value)
    return data, body


def patch_common_module() -> None:
    _common.normalize_name = normalize_name
    _common.parse_frontmatter = parse_frontmatter


def patch_namespace(namespace: dict[str, object]) -> None:
    namespace["normalize_name"] = normalize_name
    namespace["parse_frontmatter"] = parse_frontmatter
