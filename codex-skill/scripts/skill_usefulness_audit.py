#!/usr/bin/env python3
"""
Audit installed skills by usage, overlap, impact, confidence, and risk.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
import sys
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path


STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "help",
    "how",
    "in",
    "into",
    "is",
    "it",
    "its",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "use",
    "uses",
    "using",
    "when",
    "with",
    "your",
}

API_STRONG_KEYWORDS = {
    "connector",
    "connectors",
    "gateway",
    "github",
    "gmail",
    "mcp",
    "sdk",
    "slack",
    "stripe",
    "supabase",
    "vercel",
    "webhook",
}

API_SUPPORT_KEYWORDS = {
    "api",
    "apis",
    "http",
    "https",
    "provider",
    "providers",
}

TOOL_KEYWORDS = {
    "browser",
    "csv",
    "deploy",
    "deployment",
    "docx",
    "excel",
    "git",
    "image",
    "ocr",
    "pdf",
    "playwright",
    "pptx",
    "shell",
    "spreadsheet",
    "xlsx",
    "xml",
}

NAME_KEYS = (
    "skill",
    "name",
    "skill_name",
    "技能",
    "技能名",
    "技能名称",
)

IDENTIFIER_KEYS = (
    "id",
    "identifier",
    "skill_id",
    "skillid",
    "技能id",
    "技能标识",
)

SLUG_KEYS = (
    "slug",
    "skill_slug",
    "技能slug",
    "技能短名",
)

PATH_KEYS = (
    "path",
    "skill_path",
    "skill_root",
    "root",
    "directory",
    "dir",
    "location",
    "路径",
    "目录",
    "技能路径",
)

SOURCE_KEYS = (
    "source",
    "origin",
    "来源",
)

NAMESPACE_KEYS = (
    "namespace",
    "plugin",
    "plugin_name",
    "package",
    "namespace_name",
    "命名空间",
    "插件",
    "插件名",
)

COUNT_KEYS = (
    "calls",
    "count",
    "uses",
    "usage",
    "invocations",
    "call_count",
    "usage_count",
    "invoke_count",
    "调用次数",
    "调用数",
    "使用次数",
    "次数",
)

RECENT_30D_KEYS = (
    "recent_30d_calls",
    "recent30_calls",
    "recent_calls_30d",
    "calls_30d",
    "last_30d_calls",
    "30d_calls",
    "近30天调用",
    "最近30天调用",
    "近30天调用次数",
)

RECENT_90D_KEYS = (
    "recent_90d_calls",
    "recent90_calls",
    "recent_calls_90d",
    "calls_90d",
    "last_90d_calls",
    "90d_calls",
    "近90天调用",
    "最近90天调用",
    "近90天调用次数",
)

LAST_USED_KEYS = (
    "last_used_at",
    "last_used",
    "last_invoked_at",
    "last_invocation_at",
    "recent_use_at",
    "上次使用时间",
    "最后使用时间",
    "最近使用时间",
    "最近调用时间",
)

FIRST_SEEN_KEYS = (
    "first_seen_at",
    "installed_at",
    "first_used_at",
    "created_at",
    "首次出现时间",
    "安装时间",
    "首次使用时间",
)

ACTIVE_DAYS_KEYS = (
    "active_days",
    "days_active",
    "used_days",
    "usage_days",
    "活跃天数",
    "使用天数",
)

COLLECTION_KEYS = {
    "skills",
    "items",
    "results",
    "records",
    "entries",
    "data",
    "usage",
    "counts",
    "metrics",
    "cases",
    "rows",
    "messages",
    "conversations",
    "threads",
    "history",
    "community",
    "registry",
}

SCALAR_MAP_KEYS = {
    "usage",
    "counts",
    "metrics",
    "skill_usage",
    "skill_usages",
    "skill_counts",
    "skill_calls",
    "调用统计",
    "按技能调用",
}

WITH_SKILL_KEYS = ("with_skill", "with", "enabled", "treatment", "experiment", "skill_run", "启用技能")
WITHOUT_SKILL_KEYS = ("without_skill", "without", "disabled", "baseline", "control", "no_skill", "基线", "未启用技能")

FLAT_WITH_SCORE_KEYS = ("with_skill_score", "score_with_skill", "skill_score", "enabled_score", "实验分数", "启用技能分数")
FLAT_WITHOUT_SCORE_KEYS = (
    "without_skill_score",
    "score_without_skill",
    "baseline_score",
    "control_score",
    "基线分数",
    "未启用技能分数",
)
FLAT_WITH_PASS_KEYS = ("with_skill_pass", "pass_with_skill", "skill_pass", "enabled_pass", "实验通过", "启用技能通过")
FLAT_WITHOUT_PASS_KEYS = (
    "without_skill_pass",
    "pass_without_skill",
    "baseline_pass",
    "control_pass",
    "基线通过",
    "未启用技能通过",
)

COMMUNITY_RATING_KEYS = ("rating", "score", "community_rating", "registry_rating", "评分", "社区评分")
COMMUNITY_STARS_KEYS = ("stars", "star_count", "likes", "点赞", "收藏数")
COMMUNITY_DOWNLOADS_KEYS = ("downloads", "download_count", "下载量", "下载次数")
COMMUNITY_INSTALLS_CURRENT_KEYS = (
    "installs",
    "installs_current",
    "active_installs",
    "当前安装",
    "当前安装数",
    "安装数",
)
COMMUNITY_INSTALLS_ALL_TIME_KEYS = (
    "installs_all_time",
    "total_installs",
    "all_time_installs",
    "累计安装",
    "累计安装数",
)
COMMUNITY_TRENDING_KEYS = ("trending_7d", "trending", "trend_score", "7日趋势", "趋势分")
COMMUNITY_COMMENTS_KEYS = ("comments", "comments_count", "评论数", "评论数量")
COMMUNITY_UPDATED_KEYS = (
    "last_updated",
    "updated_at",
    "published_at",
    "更新时间",
    "最后更新时间",
    "发布时间",
)

VERDICT_ALIASES = {
    "same": "same",
    "equal": "same",
    "equivalent": "same",
    "一致": "same",
    "相同": "same",
    "无差异": "same",
    "持平": "same",
    "better": "better",
    "improved": "better",
    "improve": "better",
    "更好": "better",
    "更优": "better",
    "提升": "better",
    "worse": "worse",
    "degraded": "worse",
    "regressed": "worse",
    "更差": "worse",
    "退化": "worse",
    "变差": "worse",
}

TEXT_FILE_SUFFIXES = {
    "",
    ".json",
    ".jsonl",
    ".md",
    ".py",
    ".sh",
    ".ps1",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".txt",
}

RISK_SCAN_SUFFIXES = {
    "",
    ".cfg",
    ".ini",
    ".js",
    ".jsx",
    ".ps1",
    ".py",
    ".sh",
    ".toml",
    ".ts",
    ".tsx",
    ".yaml",
    ".yml",
}

RISK_SCAN_DIRS = {"scripts", "resources", "bin", "hooks"}

MAX_SCAN_BYTES = 512 * 1024
HISTORY_EVIDENCE_WEIGHT = 0.45
ALLOWED_HISTORY_ROLES = {"user", "assistant"}
HISTORY_SKIP_FIELDS = {
    "developer-instructions",
    "developer-prompt",
    "environment-context",
    "sandbox-policy",
    "skills",
    "tool-definitions",
    "tools",
    "turn-context",
    "user-instructions",
}
HOST_PROMPT_MARKERS = (
    "# agents.md instructions",
    "### available skills",
    "### how to use skills",
    "<app-context>",
    "<environment_context>",
    "<instructions>",
    "\"type\":\"turn_context\"",
    "developer_instructions",
    "user_instructions",
)

RISK_RULES = (
    {
        "label": "curl-pipe-shell",
        "severity": 2.0,
        "patterns": (
            r"curl\b[^\n|]{0,300}\|\s*(?:bash|sh)\b",
            r"wget\b[^\n|]{0,300}\|\s*(?:bash|sh)\b",
        ),
    },
    {
        "label": "dynamic-exec",
        "severity": 2.0,
        "patterns": (
            r"\binvoke-expression\b",
            r"\biex\b",
            r"\beval\s*\(",
            r"\bexec\s*\(",
        ),
    },
    {
        "label": "protected-path-access",
        "severity": 2.0,
        "patterns": (
            r"\.s" + r"sh(?:[\\/]|$)",
            r"\.a" + r"ws(?:[\\/]|$)",
            r"\.e" + r"nv\b",
            r"\bid" + r"_rsa\b",
            r"\bcred" + r"entials\b",
        ),
    },
    {
        "label": "persistence-hook",
        "severity": 2.0,
        "patterns": (
            r"\bcrontab\b",
            r"\bsystemctl\b",
            r"\bschtasks\b",
            r"\blaunchctl\b",
        ),
    },
    {
        "label": "external-post",
        "severity": 1.0,
        "patterns": (
            r"requests\.post\s*\(",
            r"curl\b[^\n]{0,120}-x\s+post\b",
            r"invoke-webrequest\b[^\n]{0,120}-method\s+post\b",
            r"method\s*:\s*[\"']post[\"']",
        ),
    },
    {
        "label": "shell-exec",
        "severity": 1.0,
        "patterns": (
            r"subprocess\.(?:run|popen)\s*\(",
            r"os\.system\s*\(",
            r"shell\s*=\s*true",
            r"child_process\.(?:exec|spawn)\s*\(",
        ),
    },
    {
        "label": "network-download",
        "severity": 1.0,
        "patterns": (
            r"\bcurl\s+https?://",
            r"\bwget\s+https?://",
            r"invoke-webrequest\s+https?://",
        ),
    },
    {
        "label": "base64-payload",
        "severity": 1.0,
        "patterns": (
            r"frombase64string",
            r"base64\s+(?:-d|--decode)",
            r"\batob\s*\(",
        ),
    },
)


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def normalize_name(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-{2,}", "-", value)
    return value.strip("-")


def normalize_pathish(value) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    resolved = Path(text).expanduser().resolve()
    return resolved.as_posix().lower()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    raw_yaml = parts[1]
    body = parts[2].lstrip("\r\n")
    data: dict[str, str] = {}
    for line in raw_yaml.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"').strip("'")
    return data, body


def extract_terms(text: str) -> set[str]:
    raw_terms = re.findall(r"[a-z0-9][a-z0-9+.]*|[\u4e00-\u9fff]{1,}", text.lower().replace("-", " "))
    terms = set()
    for term in raw_terms:
        if term in STOPWORDS:
            continue
        if term.isascii() and len(term) == 1:
            continue
        terms.add(term)
    return terms


def jaccard(left: set[str], right: set[str]) -> float:
    if not left and not right:
        return 0.0
    union = left | right
    if not union:
        return 0.0
    return len(left & right) / len(union)


def guess_source(path: Path) -> str:
    joined = "/".join(part.lower() for part in path.parts)
    if "/.system/" in joined:
        return "system"
    if "/plugins/cache/" in joined:
        return "plugin"
    if "/skills/" in joined:
        return "user"
    return "other"


def guess_namespace(path: Path) -> str:
    lowered = [part.lower() for part in path.parts]
    if "plugins" in lowered and "cache" in lowered:
        cache_index = lowered.index("cache")
        if cache_index + 2 < len(path.parts):
            return normalize_name(path.parts[cache_index + 2])
    source = guess_source(path)
    if source in {"system", "user"}:
        return source
    return "other"


def parse_dateish(value) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        stamp = float(value)
        if stamp > 1_000_000_000_000:
            stamp = stamp / 1000.0
        try:
            return datetime.fromtimestamp(stamp, tz=timezone.utc).date()
        except (OverflowError, OSError, ValueError):
            return None
    if not isinstance(value, str):
        return None

    text = value.strip()
    if not text:
        return None

    normalized = text.replace("Z", "+00:00").replace("z", "+00:00")
    try:
        return datetime.fromisoformat(normalized).date()
    except ValueError:
        pass

    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def normalize_dateish(value) -> str | None:
    parsed = parse_dateish(value)
    if parsed is None:
        return None
    return parsed.isoformat()


def days_since(value) -> int | None:
    parsed = parse_dateish(value)
    if parsed is None:
        return None
    return (date.today() - parsed).days


def load_json_or_jsonl(path: Path):
    text = read_text(path)
    if path.suffix.lower() == ".jsonl":
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    return json.loads(text)


def coerce_int(value) -> int | None:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(float(value))
        except ValueError:
            return None
    return None


def coerce_float(value) -> float | None:
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def coerce_bool(value) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "yes", "1", "pass", "passed", "success", "succeeded", "ok", "成功", "通过"}:
            return True
        if lowered in {"false", "no", "0", "fail", "failed", "error", "errored", "失败", "未通过"}:
            return False
    return None


def first_present(mapping: dict, keys: tuple[str, ...] | list[str]) -> object | None:
    lowered = {str(key).lower(): value for key, value in mapping.items()}
    for key in keys:
        if key in mapping:
            return mapping[key]
        if key.lower() in lowered:
            return lowered[key.lower()]
    return None


def extract_record_identity(mapping: dict, hint_name: str | None = None) -> dict[str, str]:
    explicit_name = normalize_name(str(first_present(mapping, NAME_KEYS) or ""))
    slug = normalize_name(str(first_present(mapping, SLUG_KEYS) or ""))
    identifier = normalize_name(str(first_present(mapping, IDENTIFIER_KEYS) or ""))
    source = normalize_name(str(first_present(mapping, SOURCE_KEYS) or ""))
    namespace = normalize_name(str(first_present(mapping, NAMESPACE_KEYS) or ""))
    path = normalize_pathish(first_present(mapping, PATH_KEYS)) or ""
    name = explicit_name or slug or identifier or normalize_name(str(hint_name or ""))
    return {
        "name": name,
        "slug": slug,
        "identifier": identifier,
        "source": source,
        "namespace": namespace,
        "path": path,
    }


def record_lookup_key(identity: dict[str, str]) -> str | None:
    if identity["path"]:
        return f"path:{identity['path']}"
    if identity["namespace"] and identity["slug"]:
        return f"namespace:{identity['namespace']}:{identity['slug']}"
    if identity["namespace"] and identity["name"]:
        return f"namespace:{identity['namespace']}:{identity['name']}"
    if identity["source"] and identity["slug"]:
        return f"source:{identity['source']}:{identity['slug']}"
    if identity["source"] and identity["name"]:
        return f"source:{identity['source']}:{identity['name']}"
    if identity["slug"]:
        return f"slug:{identity['slug']}"
    if identity["identifier"]:
        return f"id:{identity['identifier']}"
    if identity["name"]:
        return f"name:{identity['name']}"
    return None


def skill_lookup_keys(skill: dict[str, object]) -> list[str]:
    keys = [f"path:{normalize_pathish(skill['path'])}"]
    namespace = str(skill.get("namespace") or "")
    source = str(skill.get("source") or "")
    slug = str(skill.get("slug") or "")
    name = str(skill.get("name") or "")
    if namespace and slug:
        keys.append(f"namespace:{namespace}:{slug}")
    if namespace and name:
        keys.append(f"namespace:{namespace}:{name}")
    if source and slug:
        keys.append(f"source:{source}:{slug}")
    if source and name:
        keys.append(f"source:{source}:{name}")
    if slug:
        keys.append(f"slug:{slug}")
    if name:
        keys.append(f"name:{name}")
    return [key for key in keys if key]


def resolve_record(
    store: dict[str, dict[str, object]],
    skill: dict[str, object],
    alias_counts: Counter[str],
) -> dict[str, object] | None:
    for key in skill_lookup_keys(skill):
        if alias_counts.get(key, 0) > 1:
            continue
        record = store.get(key)
        if record is not None:
            return record
    return None


def skill_display_name(skill: dict[str, object], alias_counts: Counter[str]) -> str:
    name = str(skill["name"])
    if alias_counts.get(f"name:{name}", 0) <= 1:
        return name
    namespace = str(skill.get("namespace") or "")
    if namespace and namespace not in {"system", "user", "other"}:
        return f"{name}@{namespace}"
    parent_hint = normalize_name(Path(str(skill["path"])).parent.name)
    if parent_hint and parent_hint not in {"skills", ".system"}:
        return f"{name}@{parent_hint}"
    return f"{name}@{skill['source']}"


def normalize_verdict(value) -> str:
    if value is None:
        return ""
    lowered = str(value).strip().lower()
    return VERDICT_ALIASES.get(lowered, lowered)


def looks_like_host_prompt(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in HOST_PROMPT_MARKERS)


def sanitize_history_text(text: str) -> str:
    lines = [line for line in text.splitlines() if not looks_like_host_prompt(line)]
    return "\n".join(lines)


def extract_history_strings(node, inherited_role: str | None = None) -> list[str]:
    if isinstance(node, str):
        if inherited_role in ALLOWED_HISTORY_ROLES and not looks_like_host_prompt(node):
            return [node]
        return []

    if isinstance(node, list):
        values: list[str] = []
        for item in node:
            values.extend(extract_history_strings(item, inherited_role))
        return values

    if isinstance(node, dict):
        node_type = normalize_name(str(node.get("type") or ""))
        if node_type == "turn-context":
            return []

        role = str(node.get("role") or inherited_role or "").lower()
        if role in {"developer", "system", "tool"}:
            return []

        values: list[str] = []
        next_role = role if role in ALLOWED_HISTORY_ROLES else inherited_role
        for key, value in node.items():
            key_norm = normalize_name(str(key))
            if key_norm in HISTORY_SKIP_FIELDS or key_norm == "role":
                continue
            values.extend(extract_history_strings(value, next_role))
        return values

    return []


def empty_usage_record() -> dict[str, object]:
    return {
        "calls": 0,
        "recent_30d_calls": None,
        "recent_90d_calls": None,
        "active_days": None,
        "first_seen_at": None,
        "last_used_at": None,
    }


def sum_optional(left: int | None, right: int | None) -> int | None:
    if left is None:
        return right
    if right is None:
        return left
    return left + right


def max_optional(left: int | None, right: int | None) -> int | None:
    if left is None:
        return right
    if right is None:
        return left
    return max(left, right)


def merge_dates(existing: str | None, incoming: str | None, pick: str) -> str | None:
    if existing is None:
        return incoming
    if incoming is None:
        return existing
    existing_date = parse_dateish(existing)
    incoming_date = parse_dateish(incoming)
    if existing_date is None:
        return incoming
    if incoming_date is None:
        return existing
    if pick == "min":
        return min(existing_date, incoming_date).isoformat()
    return max(existing_date, incoming_date).isoformat()


def usage_record_from_mapping(mapping: dict, hint_name: str | None = None) -> tuple[str, dict[str, object]] | None:
    identity = extract_record_identity(mapping, hint_name=hint_name)
    lookup_key = record_lookup_key(identity)
    if not lookup_key:
        return None

    calls = coerce_int(first_present(mapping, COUNT_KEYS))
    recent_30d_calls = coerce_int(first_present(mapping, RECENT_30D_KEYS))
    recent_90d_calls = coerce_int(first_present(mapping, RECENT_90D_KEYS))
    active_days = coerce_int(first_present(mapping, ACTIVE_DAYS_KEYS))
    first_seen_at = normalize_dateish(first_present(mapping, FIRST_SEEN_KEYS))
    last_used_at = normalize_dateish(first_present(mapping, LAST_USED_KEYS))

    if calls is None and recent_90d_calls is not None:
        calls = recent_90d_calls
    if calls is None and recent_30d_calls is not None:
        calls = recent_30d_calls

    has_any_field = any(
        value is not None
        for value in (calls, recent_30d_calls, recent_90d_calls, active_days, first_seen_at, last_used_at)
    )
    if not has_any_field:
        return None

    return (
        lookup_key,
        {
            "calls": max(0, calls or 0),
            "recent_30d_calls": recent_30d_calls,
            "recent_90d_calls": recent_90d_calls,
            "active_days": active_days,
            "first_seen_at": first_seen_at,
            "last_used_at": last_used_at,
        },
    )


def merge_usage_record(store: dict[str, dict[str, object]], name: str, incoming: dict[str, object]) -> None:
    target = store.setdefault(name, empty_usage_record())
    target["calls"] = int(target.get("calls", 0)) + int(incoming.get("calls", 0) or 0)
    target["recent_30d_calls"] = sum_optional(
        coerce_int(target.get("recent_30d_calls")),
        coerce_int(incoming.get("recent_30d_calls")),
    )
    target["recent_90d_calls"] = sum_optional(
        coerce_int(target.get("recent_90d_calls")),
        coerce_int(incoming.get("recent_90d_calls")),
    )
    target["active_days"] = max_optional(
        coerce_int(target.get("active_days")),
        coerce_int(incoming.get("active_days")),
    )
    target["first_seen_at"] = merge_dates(
        target.get("first_seen_at"),  # type: ignore[arg-type]
        incoming.get("first_seen_at"),  # type: ignore[arg-type]
        "min",
    )
    target["last_used_at"] = merge_dates(
        target.get("last_used_at"),  # type: ignore[arg-type]
        incoming.get("last_used_at"),  # type: ignore[arg-type]
        "max",
    )


def consume_usage_node(
    node,
    usage: dict[str, dict[str, object]],
    hint_name: str | None = None,
    scalar_map: bool = False,
) -> None:
    if isinstance(node, list):
        for item in node:
            consume_usage_node(item, usage, hint_name=hint_name, scalar_map=scalar_map)
        return

    if isinstance(node, dict):
        record = usage_record_from_mapping(node, hint_name=hint_name if scalar_map else None)
        if record:
            name, payload = record
            merge_usage_record(usage, name, payload)
            return

        scalar_items = []
        for key, value in node.items():
            key_text = str(key)
            key_norm = normalize_name(key_text)
            if key_text in COLLECTION_KEYS or key_norm in COLLECTION_KEYS:
                scalar_items = []
                break
            count = coerce_int(value)
            if count is None:
                scalar_items = []
                break
            scalar_items.append((key_text, count))
        if scalar_items:
            for key_text, count in scalar_items:
                identity = {"name": normalize_name(key_text), "slug": "", "identifier": "", "source": "", "namespace": "", "path": ""}
                lookup_key = record_lookup_key(identity)
                if lookup_key:
                    merge_usage_record(usage, lookup_key, {"calls": count})
            return

        for key, value in node.items():
            key_text = str(key)
            key_norm = normalize_name(key_text)
            next_scalar_map = scalar_map or key_text in SCALAR_MAP_KEYS or key_norm in SCALAR_MAP_KEYS
            child_hint = hint_name
            if not next_scalar_map and isinstance(value, dict) and key_text not in COLLECTION_KEYS and key_norm not in COLLECTION_KEYS:
                nested_record = usage_record_from_mapping(value, hint_name=key_text)
                if nested_record:
                    name, payload = nested_record
                    merge_usage_record(usage, name, payload)
                    continue
            if next_scalar_map and key_text not in COLLECTION_KEYS and key_norm not in COLLECTION_KEYS:
                child_hint = key_text
            consume_usage_node(value, usage, hint_name=child_hint, scalar_map=next_scalar_map)
        return

    if scalar_map and hint_name is not None:
        count = coerce_int(node)
        if count is None:
            return
        identity = {"name": normalize_name(hint_name), "slug": "", "identifier": "", "source": "", "namespace": "", "path": ""}
        lookup_key = record_lookup_key(identity)
        if lookup_key:
            merge_usage_record(usage, lookup_key, {"calls": count})


def load_usage_csv(path: Path) -> dict[str, dict[str, object]]:
    usage: dict[str, dict[str, object]] = {}
    delimiter = "\t" if path.suffix.lower() == ".tsv" else ","
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        for row in reader:
            record = usage_record_from_mapping(row)
            if record is None:
                continue
            name, payload = record
            merge_usage_record(usage, name, payload)
    return usage


def load_usage_json(path: Path) -> dict[str, dict[str, object]]:
    usage: dict[str, dict[str, object]] = {}
    payload = load_json_or_jsonl(path)
    consume_usage_node(payload, usage)
    return usage


def load_usage(paths: list[Path]) -> dict[str, dict[str, object]]:
    usage: dict[str, dict[str, object]] = {}
    for path in paths:
        if not path.exists():
            continue
        if path.suffix.lower() in {".csv", ".tsv"}:
            parsed = load_usage_csv(path)
        else:
            parsed = load_usage_json(path)
        for key, value in parsed.items():
            merge_usage_record(usage, key, value)
    return usage


def infer_usage_from_history(paths: list[Path], skill_names: list[str]) -> dict[str, dict[str, object]]:
    usage = {f"name:{name}": {"calls": 0} for name in skill_names}
    patterns = {
        f"name:{name}": re.compile(rf"(?<![a-z0-9])\$?{re.escape(name)}(?![a-z0-9])", re.IGNORECASE)
        for name in skill_names
    }
    for path in paths:
        if not path.exists():
            continue
        if path.suffix.lower() in {".json", ".jsonl"}:
            try:
                payload = load_json_or_jsonl(path)
                text = "\n".join(extract_history_strings(payload)).lower()
            except json.JSONDecodeError:
                text = sanitize_history_text(read_text(path)).lower()
        else:
            text = sanitize_history_text(read_text(path)).lower()
        for name, pattern in patterns.items():
            usage[name]["calls"] = int(usage[name]["calls"]) + len(pattern.findall(text))
    return usage


def pick_arm(entry: dict, keys: tuple[str, ...]) -> dict:
    for key in keys:
        value = entry.get(key)
        if isinstance(value, dict):
            return value
    lowered = {str(key).lower(): value for key, value in entry.items()}
    for key in keys:
        value = lowered.get(key.lower())
        if isinstance(value, dict):
            return value
    return {}


def flat_metric(entry: dict, keys: tuple[str, ...], coercer):
    value = first_present(entry, keys)
    return coercer(value)


def ablation_items_from_node(node, items: list[dict]) -> None:
    if isinstance(node, list):
        for item in node:
            ablation_items_from_node(item, items)
        return
    if not isinstance(node, dict):
        return

    has_name = first_present(node, NAME_KEYS) is not None
    has_verdict = first_present(node, ("verdict", "结果", "结论")) is not None
    has_arms = pick_arm(node, WITH_SKILL_KEYS) or pick_arm(node, WITHOUT_SKILL_KEYS)
    has_flat_metrics = (
        first_present(node, FLAT_WITH_SCORE_KEYS + FLAT_WITHOUT_SCORE_KEYS) is not None
        or first_present(node, FLAT_WITH_PASS_KEYS + FLAT_WITHOUT_PASS_KEYS) is not None
    )
    if has_name and (has_verdict or has_arms or has_flat_metrics):
        items.append(node)
        return

    for value in node.values():
        ablation_items_from_node(value, items)


def load_ablation(paths: list[Path]) -> dict[str, dict[str, float]]:
    by_skill: dict[str, list[dict]] = {}
    for path in paths:
        if not path.exists():
            continue
        payload = load_json_or_jsonl(path)
        items: list[dict] = []
        ablation_items_from_node(payload, items)
        for item in items:
            if not isinstance(item, dict):
                continue
            identity = extract_record_identity(item)
            lookup_key = record_lookup_key(identity)
            if not lookup_key:
                continue
            by_skill.setdefault(lookup_key, []).append(item)

    summary: dict[str, dict[str, float]] = {}
    for name, items in by_skill.items():
        same_count = 0
        better_count = 0
        worse_count = 0
        deltas: list[float] = []
        for item in items:
            verdict = normalize_verdict(first_present(item, ("verdict", "结果", "结论")))
            with_arm = pick_arm(item, WITH_SKILL_KEYS)
            without_arm = pick_arm(item, WITHOUT_SKILL_KEYS)
            with_pass = coerce_bool(first_present(with_arm, ("pass", "passed", "success", "结果", "通过")))
            without_pass = coerce_bool(first_present(without_arm, ("pass", "passed", "success", "结果", "通过")))
            with_score = coerce_float(first_present(with_arm, ("score", "quality", "quality_score", "分数", "质量分")))
            without_score = coerce_float(first_present(without_arm, ("score", "quality", "quality_score", "分数", "质量分")))
            if with_pass is None:
                with_pass = flat_metric(item, FLAT_WITH_PASS_KEYS, coerce_bool)
            if without_pass is None:
                without_pass = flat_metric(item, FLAT_WITHOUT_PASS_KEYS, coerce_bool)
            if with_score is None:
                with_score = flat_metric(item, FLAT_WITH_SCORE_KEYS, coerce_float)
            if without_score is None:
                without_score = flat_metric(item, FLAT_WITHOUT_SCORE_KEYS, coerce_float)

            delta = None
            if with_score is not None and without_score is not None:
                delta = with_score - without_score
            elif with_pass is not None and without_pass is not None:
                delta = float(with_pass) - float(without_pass)
            if delta is not None:
                deltas.append(delta)

            if verdict == "same":
                same_count += 1
                continue
            if verdict == "better":
                better_count += 1
                continue
            if verdict == "worse":
                worse_count += 1
                continue

            if delta is None:
                if with_pass is not None and without_pass is not None and with_pass == without_pass:
                    same_count += 1
                continue

            if abs(delta) < 0.05:
                same_count += 1
            elif delta > 0:
                better_count += 1
            else:
                worse_count += 1

        total = len(items)
        summary[name] = {
            "cases": float(total),
            "consistency_rate": same_count / total if total else 0.0,
            "better_rate": better_count / total if total else 0.0,
            "worse_rate": worse_count / total if total else 0.0,
            "avg_delta": sum(deltas) / len(deltas) if deltas else 0.0,
        }
    return summary


def empty_community_record() -> dict[str, object]:
    return {
        "rating": None,
        "stars": None,
        "downloads": None,
        "installs_current": None,
        "installs_all_time": None,
        "trending_7d": None,
        "comments_count": None,
        "last_updated": None,
    }


def normalize_rating(value) -> float | None:
    rating = coerce_float(value)
    if rating is None:
        return None
    if 0.0 <= rating <= 1.0:
        rating = rating * 5.0
    return rating


def community_record_from_mapping(mapping: dict, hint_name: str | None = None) -> tuple[str, dict[str, object]] | None:
    identity = extract_record_identity(mapping, hint_name=hint_name)
    lookup_key = record_lookup_key(identity)
    if not lookup_key:
        return None

    record = {
        "rating": normalize_rating(first_present(mapping, COMMUNITY_RATING_KEYS)),
        "stars": coerce_int(first_present(mapping, COMMUNITY_STARS_KEYS)),
        "downloads": coerce_int(first_present(mapping, COMMUNITY_DOWNLOADS_KEYS)),
        "installs_current": coerce_int(first_present(mapping, COMMUNITY_INSTALLS_CURRENT_KEYS)),
        "installs_all_time": coerce_int(first_present(mapping, COMMUNITY_INSTALLS_ALL_TIME_KEYS)),
        "trending_7d": coerce_int(first_present(mapping, COMMUNITY_TRENDING_KEYS)),
        "comments_count": coerce_int(first_present(mapping, COMMUNITY_COMMENTS_KEYS)),
        "last_updated": normalize_dateish(first_present(mapping, COMMUNITY_UPDATED_KEYS)),
    }
    if not any(value is not None for value in record.values()):
        return None
    return lookup_key, record


def merge_community_record(store: dict[str, dict[str, object]], name: str, incoming: dict[str, object]) -> None:
    target = store.setdefault(name, empty_community_record())
    for key in ("stars", "downloads", "installs_current", "installs_all_time", "trending_7d", "comments_count"):
        target[key] = max_optional(coerce_int(target.get(key)), coerce_int(incoming.get(key)))
    target["rating"] = coerce_float(incoming.get("rating")) if incoming.get("rating") is not None else target.get("rating")
    target["last_updated"] = merge_dates(
        target.get("last_updated"),  # type: ignore[arg-type]
        incoming.get("last_updated"),  # type: ignore[arg-type]
        "max",
    )


def consume_community_node(node, community: dict[str, dict[str, object]], hint_name: str | None = None) -> None:
    if isinstance(node, list):
        for item in node:
            consume_community_node(item, community, hint_name=hint_name)
        return

    if isinstance(node, dict):
        record = community_record_from_mapping(node, hint_name=hint_name)
        if record:
            name, payload = record
            merge_community_record(community, name, payload)
            return

        for key, value in node.items():
            key_text = str(key)
            key_norm = normalize_name(key_text)
            child_hint = None
            if key_text not in COLLECTION_KEYS and key_norm not in COLLECTION_KEYS and isinstance(value, dict):
                child_hint = key_text
            consume_community_node(value, community, hint_name=child_hint)


def load_community_csv(path: Path) -> dict[str, dict[str, object]]:
    community: dict[str, dict[str, object]] = {}
    delimiter = "\t" if path.suffix.lower() == ".tsv" else ","
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        for row in reader:
            record = community_record_from_mapping(row)
            if record is None:
                continue
            name, payload = record
            merge_community_record(community, name, payload)
    return community


def load_community_json(path: Path) -> dict[str, dict[str, object]]:
    community: dict[str, dict[str, object]] = {}
    payload = load_json_or_jsonl(path)
    consume_community_node(payload, community)
    return community


def load_community(paths: list[Path]) -> dict[str, dict[str, object]]:
    community: dict[str, dict[str, object]] = {}
    for path in paths:
        if not path.exists():
            continue
        if path.suffix.lower() in {".csv", ".tsv"}:
            parsed = load_community_csv(path)
        else:
            parsed = load_community_json(path)
        for key, value in parsed.items():
            merge_community_record(community, key, value)
    return community


def community_prior_score(entry: dict[str, object] | None) -> tuple[float | None, float | None]:
    if not entry:
        return None, None

    score = 0.0
    confidence = 0.0
    rating = coerce_float(entry.get("rating"))
    if rating is not None:
        score += clamp(rating / 5.0, 0.0, 1.0) * 0.35
        confidence += 0.20

    volume = coerce_int(entry.get("installs_current"))
    if volume is None:
        volume = coerce_int(entry.get("downloads"))
    if volume is not None:
        score += clamp(math.log1p(volume) / math.log1p(5000), 0.0, 1.0) * 0.25
        confidence += 0.20

    trending = coerce_int(entry.get("trending_7d"))
    if trending is not None:
        score += clamp(math.log1p(trending) / math.log1p(250), 0.0, 1.0) * 0.20
        confidence += 0.20

    stars = coerce_int(entry.get("stars"))
    if stars is not None:
        score += clamp(math.log1p(stars) / math.log1p(250), 0.0, 1.0) * 0.10
        confidence += 0.15

    last_updated_days = days_since(entry.get("last_updated"))
    if last_updated_days is not None:
        if last_updated_days <= 180:
            maintenance = 1.0
        elif last_updated_days <= 365:
            maintenance = 0.7
        elif last_updated_days <= 730:
            maintenance = 0.4
        else:
            maintenance = 0.1
        score += maintenance * 0.10
        confidence += 0.15

    return round(clamp(score, 0.0, 1.0), 2), round(clamp(confidence, 0.0, 1.0), 2)


def scan_risk(root: Path) -> dict[str, object]:
    hits: dict[str, dict[str, object]] = {}
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if "__pycache__" in path.parts:
            continue
        relative_path = path.relative_to(root)
        relative_parts = {part.lower() for part in relative_path.parts}
        if "references" in relative_parts:
            continue
        if path.name == "SKILL.md":
            continue
        if path.suffix.lower() not in RISK_SCAN_SUFFIXES:
            continue
        if relative_path.parent != Path(".") and not any(part.lower() in RISK_SCAN_DIRS for part in relative_path.parts[:-1]):
            continue
        try:
            if path.stat().st_size > MAX_SCAN_BYTES:
                continue
        except OSError:
            continue
        text = read_text(path).lower()
        relative = str(relative_path)
        for rule in RISK_RULES:
            if any(re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE) for pattern in rule["patterns"]):
                hit = hits.setdefault(
                    str(rule["label"]),
                    {"severity": float(rule["severity"]), "files": []},
                )
                files = hit["files"]
                if isinstance(files, list) and relative not in files and len(files) < 3:
                    files.append(relative)

    risk_score = round(sum(float(item["severity"]) for item in hits.values()), 2)
    if risk_score >= 4.0:
        risk_level = "high"
    elif risk_score >= 2.0:
        risk_level = "medium"
    elif risk_score > 0:
        risk_level = "low"
    else:
        risk_level = "none"

    evidence = [
        {"label": label, "severity": item["severity"], "files": item["files"]}
        for label, item in sorted(hits.items())
    ]
    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "risk_flags": [item["label"] for item in evidence],
        "risk_evidence": evidence,
    }


def scan_skill(skill_md: Path) -> dict[str, object]:
    root = skill_md.parent
    text = read_text(skill_md)
    frontmatter, body = parse_frontmatter(text)
    name = normalize_name(frontmatter.get("name", root.name) or root.name)
    slug = normalize_name(frontmatter.get("slug", ""))
    description = frontmatter.get("description", "")
    headings = [line.lstrip("# ").strip() for line in body.splitlines() if line.startswith("#")]
    scripts_dir = root / "scripts"
    references_dir = root / "references"
    script_files = [item.name for item in scripts_dir.rglob("*") if item.is_file()] if scripts_dir.exists() else []
    reference_files = [item.name for item in references_dir.rglob("*") if item.is_file()] if references_dir.exists() else []
    fingerprint = " ".join(
        [name, description, " ".join(headings), " ".join(script_files), " ".join(reference_files)]
    )
    risk = scan_risk(root)
    return {
        "name": name,
        "slug": slug,
        "path": str(root),
        "source": guess_source(root),
        "namespace": guess_namespace(root),
        "description": description,
        "headings": headings,
        "scripts_count": len(script_files),
        "references_count": len(reference_files),
        "fingerprint": fingerprint,
        "terms": extract_terms(fingerprint),
        "risk_score": risk["risk_score"],
        "risk_level": risk["risk_level"],
        "risk_flags": risk["risk_flags"],
        "risk_evidence": risk["risk_evidence"],
    }


def discover_skill_files(roots: list[Path], include_system: bool) -> list[Path]:
    files: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        if not root.exists():
            continue
        for skill_md in root.rglob("SKILL.md"):
            if not include_system and "/.system/" in skill_md.as_posix().lower():
                continue
            resolved = str(skill_md.resolve())
            if resolved in seen:
                continue
            seen.add(resolved)
            files.append(skill_md)
    return sorted(files)


def default_roots() -> list[Path]:
    roots: list[Path] = []
    cwd_skills = Path.cwd() / "skills"
    if cwd_skills.exists():
        roots.append(cwd_skills)
    codex_home = os.environ.get("CODEX_HOME")
    home_skills = Path(codex_home).expanduser() / "skills" if codex_home else Path.home() / ".codex" / "skills"
    if home_skills.exists():
        roots.append(home_skills)
    return roots


def classify_skill(skill: dict[str, object]) -> str:
    terms = set(skill["terms"])
    if terms & API_STRONG_KEYWORDS:
        return "api"
    if len(terms & API_SUPPORT_KEYWORDS) >= 2:
        return "api"
    if terms & TOOL_KEYWORDS:
        return "tool"
    if int(skill["scripts_count"]) >= 2 and terms & {"browser", "csv", "docx", "excel", "ocr", "pdf", "xlsx"}:
        return "tool"
    return "general"


def usage_evidence_weight(source: str) -> float:
    if source == "usage":
        return 1.0
    if source == "history":
        return HISTORY_EVIDENCE_WEIGHT
    return 0.0


def usage_score(usage_record: dict[str, object], evidence_weight: float) -> float:
    if evidence_weight <= 0:
        return 0.0

    calls = int(usage_record.get("calls", 0) or 0)
    recent_30d_calls = coerce_int(usage_record.get("recent_30d_calls"))
    recent_90d_calls = coerce_int(usage_record.get("recent_90d_calls"))
    active_days = coerce_int(usage_record.get("active_days"))
    last_used_days = days_since(usage_record.get("last_used_at"))

    if recent_30d_calls is not None:
        if recent_30d_calls >= 8:
            base = 3.0
        elif recent_30d_calls >= 3:
            base = 2.0
        elif recent_30d_calls >= 1:
            base = 1.0
        else:
            base = 0.0
    elif recent_90d_calls is not None:
        if recent_90d_calls >= 10:
            base = 2.5
        elif recent_90d_calls >= 3:
            base = 1.5
        elif recent_90d_calls >= 1:
            base = 0.75
        else:
            base = 0.0
    elif calls <= 0:
        base = 0.0
    elif calls <= 2:
        base = 1.0
    elif calls <= 9:
        base = 2.0
    else:
        base = 3.0

    if last_used_days is not None:
        if last_used_days <= 7:
            base += 0.5
        elif last_used_days <= 30:
            base += 0.25
        elif last_used_days > 180:
            base -= 0.5

    if active_days is not None:
        if active_days >= 10:
            base += 0.25
        elif active_days >= 3:
            base += 0.10

    return round(clamp(base * evidence_weight, 0.0, 3.0), 2)


def uniqueness_score(overlap: float) -> float:
    if overlap >= 0.85:
        return 0.0
    if overlap >= 0.65:
        return 1.0
    if overlap >= 0.40:
        return 2.0
    return 3.0


def impact_score(
    kind: str,
    calls: int,
    overlap: float,
    skill: dict[str, object],
    ablation: dict[str, float] | None,
) -> float:
    if kind in {"api", "tool"}:
        score = 2.0
        if int(skill["scripts_count"]) > 0 or int(skill["references_count"]) > 0:
            score += 1.0
        if overlap < 0.35:
            score += 0.5
        if calls >= 3:
            score += 0.5
        if overlap >= 0.75:
            score -= 1.0
        if calls == 0:
            score -= 0.5
        return max(0.0, min(4.0, round(score, 2)))

    if not ablation or ablation.get("cases", 0) <= 0:
        return 2.0

    consistency = ablation["consistency_rate"]
    better = ablation["better_rate"]
    worse = ablation["worse_rate"]
    if consistency >= 0.85:
        score = 0.0
    elif consistency >= 0.70:
        score = 1.0
    elif consistency >= 0.55:
        score = 2.0
    elif consistency >= 0.35:
        score = 3.0
    else:
        score = 4.0

    if better - worse >= 0.30:
        score += 1.0
    elif worse > better:
        score -= 1.0
    return max(0.0, min(4.0, round(score, 2)))


def confidence_score(
    usage_source: str,
    usage_record: dict[str, object],
    kind: str,
    ablation: dict[str, float] | None,
    community_entry: dict[str, object] | None,
    skill_count: int,
) -> float:
    score = 0.0
    if usage_source == "usage":
        score += 0.35
    elif usage_source == "history":
        score += 0.15

    if usage_record.get("recent_30d_calls") is not None or usage_record.get("last_used_at") is not None:
        score += 0.20
    elif int(usage_record.get("calls", 0) or 0) > 0 and usage_source == "usage":
        score += 0.10

    if kind == "general":
        cases = int((ablation or {}).get("cases", 0))
        if cases >= 5:
            score += 0.25
        elif cases >= 1:
            score += 0.15
    else:
        score += 0.25

    score += 0.10 if skill_count > 1 else 0.05
    if community_entry:
        score += 0.10
    return round(clamp(score, 0.0, 1.0), 2)


def verdict(total: float) -> str:
    if total >= 8.0:
        return "keep"
    if total >= 6.0:
        return "keep-narrow"
    if total >= 4.5:
        return "review"
    if total >= 3.0:
        return "merge-delete"
    return "delete"


def recommend_action(
    source: str,
    kind: str,
    total: float,
    confidence: float,
    risk_level: str,
    calls: int,
    overlap: float,
    community_prior: float | None,
) -> tuple[str, str, bool]:
    if source == "system":
        if risk_level == "high":
            return "review-system", "system skill with high-risk patterns", False
        return "keep-system", "system skill", False

    if risk_level == "high":
        return "quarantine-review", "high-risk patterns require manual review", False
    if risk_level == "medium" and total >= 6.0:
        return "keep-review-risk", "useful locally with medium-risk patterns", False

    if total >= 8.0:
        return "keep", "high local score", False
    if total >= 6.0:
        if overlap >= 0.65 and calls <= 1:
            return "keep-narrow", "high overlap suggests narrower scope", False
        return "keep-narrow", "good local score", False

    if confidence < 0.55:
        return "observe-30d", "evidence confidence is low", False

    if risk_level == "medium":
        return "review-risk", "medium-risk patterns require review", False

    if total >= 4.5:
        if overlap >= 0.65:
            return "merge-or-review", "mid score with high overlap", False
        if community_prior is not None and community_prior >= 0.6:
            return "review-vs-community", "community signal is stronger than local score", False
        return "review", "mid local score", False

    if kind in {"api", "tool"}:
        if calls == 0 and overlap >= 0.75:
            return "merge-delete", "unused duplicate protected skill", True
        if community_prior is not None and community_prior >= 0.6:
            return "review-vs-community", "protected skill has strong community signal", False
        return "merge-or-review", "protected skill scores low locally", False

    if community_prior is not None and community_prior >= 0.6:
        return "review-vs-community", "community signal suggests benchmark before removal", False
    if total < 3.0:
        return "delete", "very low local score", True
    if overlap >= 0.65 and calls <= 1:
        return "merge-delete", "low usage plus high overlap", True
    return "merge-delete", "low local score", True


def short_risk_flags(flags: list[str]) -> str:
    if not flags:
        return ""
    return ",".join(flags[:2])


def build_basis(
    usage_record: dict[str, object],
    usage_source: str,
    evidence_weight: float,
    overlap_peer: str | None,
    overlap_value: float,
    kind: str,
    ablation: dict[str, float] | None,
    community_prior: float | None,
    risk_flags: list[str],
) -> str:
    parts = [f"calls={int(usage_record.get('calls', 0) or 0)}"]
    recent_30d_calls = coerce_int(usage_record.get("recent_30d_calls"))
    if recent_30d_calls is not None:
        parts.append(f"30d={recent_30d_calls}")
    if usage_record.get("last_used_at"):
        parts.append(f"last={usage_record['last_used_at']}")
    parts.append(f"usage={usage_source}@{evidence_weight:.2f}")
    if overlap_peer:
        parts.append(f"overlap={overlap_peer}({overlap_value:.2f})")
    if kind == "general":
        if ablation and ablation.get("cases", 0) > 0:
            parts.append(f"same={ablation['consistency_rate']:.2f}")
            parts.append(f"better={ablation['better_rate']:.2f}")
        else:
            parts.append("ablation=missing")
    else:
        parts.append("impact=protected-capability")
    if community_prior is not None:
        parts.append(f"community={community_prior:.2f}")
    if risk_flags:
        parts.append(f"risk={short_risk_flags(risk_flags)}")
    return "; ".join(parts)


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines)


def fmt_optional_int(value) -> str:
    coerced = coerce_int(value)
    return "-" if coerced is None else str(coerced)


def fmt_optional_float(value, digits: int = 2) -> str:
    coerced = coerce_float(value)
    return "-" if coerced is None else f"{coerced:.{digits}f}"


def run_audit(args: argparse.Namespace) -> int:
    roots = [Path(item).expanduser().resolve() for item in (args.skills_root or [])]
    if not roots:
        roots = [root.resolve() for root in default_roots()]
    skill_files = discover_skill_files(roots, args.include_system)
    if not skill_files:
        print("No skills found.", file=sys.stderr)
        return 1

    skills = [scan_skill(path) for path in skill_files]
    names = [skill["name"] for skill in skills]
    alias_counts = Counter(key for skill in skills for key in skill_lookup_keys(skill))
    usage_paths = [Path(item).expanduser().resolve() for item in (args.usage_file or [])]
    history_paths = [Path(item).expanduser().resolve() for item in (args.history_file or [])]
    ablation_paths = [Path(item).expanduser().resolve() for item in (args.ablation_file or [])]
    community_paths = [Path(item).expanduser().resolve() for item in (args.community_file or [])]

    usage = load_usage(usage_paths) if usage_paths else {}
    history_usage = infer_usage_from_history(history_paths, names) if history_paths else {}
    ablation = load_ablation(ablation_paths) if ablation_paths else {}
    community = load_community(community_paths) if community_paths else {}

    results: list[dict[str, object]] = []
    for skill in skills:
        kind = classify_skill(skill)
        best_peer = None
        best_overlap = 0.0
        for other in skills:
            if skill["path"] == other["path"]:
                continue
            overlap = jaccard(skill["terms"], other["terms"])
            if overlap > best_overlap:
                best_overlap = overlap
                best_peer = skill_display_name(other, alias_counts)

        usage_record = resolve_record(usage, skill, alias_counts)
        usage_source = "usage"
        if usage_record is None:
            usage_record = resolve_record(history_usage, skill, alias_counts) or {"calls": 0}
            usage_source = "history" if history_paths else "missing"

        evidence_weight = usage_evidence_weight(usage_source)
        calls = int(usage_record.get("calls", 0) or 0)
        ablation_summary = resolve_record(ablation, skill, alias_counts)
        community_entry = resolve_record(community, skill, alias_counts)
        community_prior, community_conf = community_prior_score(community_entry)

        u_score = usage_score(usage_record, evidence_weight)
        uniq_score = uniqueness_score(best_overlap)
        i_score = impact_score(kind, calls, best_overlap, skill, ablation_summary)
        total = round(u_score + uniq_score + i_score, 2)
        confidence = confidence_score(
            usage_source,
            usage_record,
            kind,
            ablation_summary,
            community_entry,
            len(skills),
        )
        action, action_reason, delete_candidate = recommend_action(
            str(skill["source"]),
            kind,
            total,
            confidence,
            str(skill["risk_level"]),
            calls,
            best_overlap,
            community_prior,
        )

        results.append(
            {
                "name": skill["name"],
                "display_name": skill_display_name(skill, alias_counts),
                "source": skill["source"],
                "namespace": skill["namespace"],
                "slug": skill["slug"],
                "kind": kind,
                "path": skill["path"],
                "calls": calls,
                "recent_30d_calls": coerce_int(usage_record.get("recent_30d_calls")),
                "recent_90d_calls": coerce_int(usage_record.get("recent_90d_calls")),
                "active_days": coerce_int(usage_record.get("active_days")),
                "first_seen_at": usage_record.get("first_seen_at"),
                "last_used_at": usage_record.get("last_used_at"),
                "usage_source": usage_source,
                "evidence_weight": evidence_weight,
                "usage_score": u_score,
                "uniqueness_score": uniq_score,
                "impact_score": i_score,
                "local_score": total,
                "total_score": total,
                "confidence_score": confidence,
                "verdict": verdict(total),
                "action": action,
                "action_reason": action_reason,
                "delete_candidate": delete_candidate,
                "delete_trigger": action_reason if delete_candidate else None,
                "overlap_peer": best_peer,
                "overlap_value": round(best_overlap, 2),
                "community": community_entry,
                "community_prior_score": community_prior,
                "community_confidence": community_conf,
                "risk_level": skill["risk_level"],
                "risk_score": skill["risk_score"],
                "risk_flags": skill["risk_flags"],
                "risk_evidence": skill["risk_evidence"],
                "basis": build_basis(
                    usage_record,
                    usage_source,
                    evidence_weight,
                    best_peer,
                    best_overlap,
                    kind,
                    ablation_summary,
                    community_prior,
                    list(skill["risk_flags"]),
                ),
                "missing_usage": usage_source == "missing",
                "missing_ablation": kind == "general" and not ablation_summary,
                "missing_community": bool(community_paths) and community_entry is None,
            }
        )

    ranked = sorted(results, key=lambda item: (-float(item["local_score"]), str(item["display_name"])))
    recommended_actions = sorted(
        [item for item in ranked if str(item["action"]) not in {"keep", "keep-narrow", "keep-system"}],
        key=lambda item: (str(item["action"]), float(item["local_score"]), str(item["display_name"])),
    )
    delete_candidates = sorted(
        [item for item in ranked if item["delete_candidate"]],
        key=lambda item: (float(item["local_score"]), str(item["display_name"])),
    )
    missing = [item for item in ranked if item["missing_usage"] or item["missing_ablation"] or item["missing_community"]]

    score_rows = []
    for index, item in enumerate(ranked, start=1):
        score_rows.append(
            [
                str(index),
                str(item["display_name"]),
                str(item["source"]),
                str(item["kind"]),
                str(item["calls"]),
                fmt_optional_int(item["recent_30d_calls"]),
                f"{item['usage_score']:.1f}",
                f"{item['uniqueness_score']:.1f}",
                f"{item['impact_score']:.1f}",
                fmt_optional_float(item["community_prior_score"]),
                fmt_optional_float(item["confidence_score"]),
                str(item["risk_level"]),
                f"{item['local_score']:.1f}",
                str(item["verdict"]),
                str(item["action"]),
                str(item["basis"]),
            ]
        )

    report_parts = [
        "# Skill Usefulness Audit",
        "",
        f"- Skills audited: {len(ranked)}",
        f"- Usage files: {len(usage_paths)}",
        f"- History files: {len(history_paths)}",
        f"- Ablation files: {len(ablation_paths)}",
        f"- Community files: {len(community_paths)}",
        f"- Recommended actions: {len(recommended_actions)}",
        f"- Delete candidates: {len(delete_candidates)}",
        "",
        "## Score Table",
        "",
        markdown_table(
            [
                "Rank",
                "Skill",
                "Source",
                "Kind",
                "Calls",
                "Recent30",
                "Usage",
                "Unique",
                "Impact",
                "Comm",
                "Conf",
                "Risk",
                "Total",
                "Verdict",
                "Action",
                "Basis",
            ],
            score_rows,
        ),
    ]

    if recommended_actions:
        action_rows = [
            [
                str(item["display_name"]),
                f"{item['local_score']:.1f}",
                fmt_optional_float(item["confidence_score"]),
                str(item["risk_level"]),
                str(item["action"]),
                str(item["action_reason"]),
            ]
            for item in recommended_actions
        ]
        report_parts.extend(
            [
                "",
                "## Recommended Actions",
                "",
                markdown_table(["Skill", "Total", "Confidence", "Risk", "Action", "Reason"], action_rows),
            ]
        )

    if delete_candidates:
        delete_rows = [
            [
                str(item["display_name"]),
                f"{item['local_score']:.1f}",
                str(item["kind"]),
                str(item["action"]),
                str(item["delete_trigger"]),
                str(item["basis"]),
            ]
            for item in delete_candidates
        ]
        report_parts.extend(
            [
                "",
                "## Delete Candidates",
                "",
                markdown_table(["Skill", "Total", "Kind", "Action", "Trigger", "Reason"], delete_rows),
            ]
        )

    if missing:
        missing_rows = []
        for item in missing:
            gaps = []
            if item["missing_usage"]:
                gaps.append("usage")
            if item["missing_ablation"]:
                gaps.append("ablation")
            if item["missing_community"]:
                gaps.append("community")
            missing_rows.append([str(item["display_name"]), str(item["kind"]), ", ".join(gaps)])
        report_parts.extend(
            [
                "",
                "## Missing Evidence",
                "",
                markdown_table(["Skill", "Kind", "Missing"], missing_rows),
            ]
        )

    report = "\n".join(report_parts) + "\n"

    if args.markdown_out:
        markdown_path = Path(args.markdown_out).expanduser().resolve()
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text(report, encoding="utf-8")
    else:
        print(report)

    if args.json_out:
        payload = {
            "skills_audited": len(ranked),
            "usage_files": len(usage_paths),
            "history_files": len(history_paths),
            "ablation_files": len(ablation_paths),
            "community_files": len(community_paths),
            "recommended_actions": len(recommended_actions),
            "delete_candidates": len(delete_candidates),
            "results": ranked,
        }
        json_path = Path(args.json_out).expanduser().resolve()
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit installed skill usefulness.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    audit_parser = subparsers.add_parser("audit", help="Audit skills and render a report.")
    audit_parser.add_argument("--skills-root", action="append", help="Root directory containing skill folders.")
    audit_parser.add_argument("--usage-file", action="append", help="JSON/JSONL/CSV/TSV file with usage evidence.")
    audit_parser.add_argument("--history-file", action="append", help="Transcript export used for mention fallback.")
    audit_parser.add_argument("--ablation-file", action="append", help="JSON or JSONL file with ablation cases.")
    audit_parser.add_argument("--community-file", action="append", help="Offline JSON/JSONL/CSV/TSV file with registry metrics.")
    audit_parser.add_argument("--markdown-out", help="Write the Markdown report to this file.")
    audit_parser.add_argument("--json-out", help="Write machine-readable JSON output to this file.")
    audit_parser.add_argument("--include-system", action="store_true", help="Include system skills during discovery.")
    audit_parser.set_defaults(func=run_audit)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
