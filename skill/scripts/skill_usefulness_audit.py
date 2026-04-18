#!/usr/bin/env python3
"""
Audit installed skills by usage, overlap, and impact.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
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
    "oauth",
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
    "auth",
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
    "id",
    "slug",
    "identifier",
    "skill_name",
    "skill_id",
    "skillid",
    "技能",
    "技能名",
    "技能名称",
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


def normalize_name(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-{2,}", "-", value)
    return value.strip("-")


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


def tokenize(text: str) -> set[str]:
    raw_tokens = re.findall(r"[a-z0-9][a-z0-9+.]*|[\u4e00-\u9fff]{1,}", text.lower().replace("-", " "))
    tokens = set()
    for token in raw_tokens:
        if token in STOPWORDS:
            continue
        if token.isascii() and len(token) == 1:
            continue
        tokens.add(token)
    return tokens


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


def scan_skill(skill_md: Path) -> dict[str, object]:
    root = skill_md.parent
    text = read_text(skill_md)
    frontmatter, body = parse_frontmatter(text)
    name = normalize_name(frontmatter.get("name", root.name) or root.name)
    description = frontmatter.get("description", "")
    headings = [line.lstrip("# ").strip() for line in body.splitlines() if line.startswith("#")]
    scripts_dir = root / "scripts"
    references_dir = root / "references"
    script_files = [item.name for item in scripts_dir.rglob("*") if item.is_file()] if scripts_dir.exists() else []
    reference_files = [item.name for item in references_dir.rglob("*") if item.is_file()] if references_dir.exists() else []
    fingerprint = " ".join(
        [name, description, " ".join(headings), " ".join(script_files), " ".join(reference_files)]
    )
    return {
        "name": name,
        "path": str(root),
        "source": guess_source(root),
        "description": description,
        "headings": headings,
        "scripts_count": len(script_files),
        "references_count": len(reference_files),
        "fingerprint": fingerprint,
        "tokens": tokenize(fingerprint),
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


def normalize_verdict(value) -> str:
    if value is None:
        return ""
    lowered = str(value).strip().lower()
    return VERDICT_ALIASES.get(lowered, lowered)


def collect_strings(node) -> list[str]:
    values: list[str] = []
    if isinstance(node, str):
        return [node]
    if isinstance(node, list):
        for item in node:
            values.extend(collect_strings(item))
        return values
    if isinstance(node, dict):
        for value in node.values():
            values.extend(collect_strings(value))
    return values


def add_usage(usage: dict[str, int], name: str, value) -> None:
    key = normalize_name(name)
    count = coerce_int(value)
    if not key or count is None:
        return
    usage[key] = usage.get(key, 0) + count


def consume_usage_node(node, usage: dict[str, int], hint_name: str | None = None, scalar_map: bool = False) -> None:
    if isinstance(node, list):
        for item in node:
            consume_usage_node(item, usage, hint_name=hint_name, scalar_map=scalar_map)
        return

    if isinstance(node, dict):
        name = first_present(node, NAME_KEYS)
        count = first_present(node, COUNT_KEYS)
        if name is not None and count is not None:
            add_usage(usage, str(name), count)
            return

        for key, value in node.items():
            key_text = str(key)
            key_norm = normalize_name(key_text)
            next_scalar_map = scalar_map or key_text in SCALAR_MAP_KEYS or key_norm in SCALAR_MAP_KEYS
            child_hint = hint_name
            if next_scalar_map and key_text not in COLLECTION_KEYS and key_norm not in COLLECTION_KEYS:
                child_hint = key_text
            consume_usage_node(value, usage, hint_name=child_hint, scalar_map=next_scalar_map)
        return

    if scalar_map and hint_name is not None:
        add_usage(usage, hint_name, node)


def load_usage_csv(path: Path) -> dict[str, int]:
    usage: dict[str, int] = {}
    delimiter = "\t" if path.suffix.lower() == ".tsv" else ","
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        for row in reader:
            add_usage(
                usage,
                str(first_present(row, NAME_KEYS) or ""),
                first_present(row, COUNT_KEYS),
            )
    return usage


def load_usage_json(path: Path) -> dict[str, int]:
    usage: dict[str, int] = {}
    payload = load_json_or_jsonl(path)
    consume_usage_node(payload, usage)
    return usage


def load_usage(paths: list[Path]) -> dict[str, int]:
    usage: dict[str, int] = {}
    for path in paths:
        if not path.exists():
            continue
        if path.suffix.lower() in {".csv", ".tsv"}:
            parsed = load_usage_csv(path)
        else:
            parsed = load_usage_json(path)
        for key, value in parsed.items():
            usage[key] = usage.get(key, 0) + value
    return usage


def infer_usage_from_history(paths: list[Path], skill_names: list[str]) -> dict[str, int]:
    usage = {name: 0 for name in skill_names}
    patterns = {
        name: re.compile(rf"(?<![a-z0-9])\$?{re.escape(name)}(?![a-z0-9])", re.IGNORECASE)
        for name in skill_names
    }
    for path in paths:
        if not path.exists():
            continue
        if path.suffix.lower() in {".json", ".jsonl"}:
            try:
                payload = load_json_or_jsonl(path)
                text = "\n".join(collect_strings(payload)).lower()
            except json.JSONDecodeError:
                text = read_text(path).lower()
        else:
            text = read_text(path).lower()
        for name, pattern in patterns.items():
            usage[name] += len(pattern.findall(text))
    return usage


def get_nested(entry: dict, *keys: str):
    current = entry
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


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
            name = normalize_name(str(first_present(item, NAME_KEYS) or ""))
            if not name:
                continue
            by_skill.setdefault(name, []).append(item)

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


def classify_skill(skill: dict[str, object]) -> str:
    tokens = set(skill["tokens"])
    if tokens & API_STRONG_KEYWORDS:
        return "api"
    if len(tokens & API_SUPPORT_KEYWORDS) >= 2:
        return "api"
    if tokens & TOOL_KEYWORDS:
        return "tool"
    if int(skill["scripts_count"]) >= 2 and tokens & {"browser", "csv", "docx", "excel", "ocr", "pdf", "xlsx"}:
        return "tool"
    return "general"


def usage_score(calls: int) -> float:
    if calls <= 0:
        return 0.0
    if calls <= 2:
        return 1.0
    if calls <= 9:
        return 2.0
    return 3.0


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


def delete_trigger(source: str, kind: str, total: float, calls: int, overlap: float) -> str | None:
    if source == "system":
        return None
    if kind in {"api", "tool"}:
        if total < 4.0 and calls == 0 and overlap >= 0.75:
            return "unused duplicate protected skill"
        return None
    if total < 3.0:
        return "very low total score"
    if total < 4.5 and overlap >= 0.65 and calls <= 1:
        return "low usage plus high overlap"
    return None


def build_basis(
    calls: int,
    overlap_peer: str | None,
    overlap_value: float,
    kind: str,
    ablation: dict[str, float] | None,
) -> str:
    parts = [f"calls={calls}"]
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
    return "; ".join(parts)


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines)


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
    usage_paths = [Path(item).expanduser().resolve() for item in (args.usage_file or [])]
    history_paths = [Path(item).expanduser().resolve() for item in (args.history_file or [])]
    ablation_paths = [Path(item).expanduser().resolve() for item in (args.ablation_file or [])]

    usage = load_usage(usage_paths) if usage_paths else {}
    history_usage = infer_usage_from_history(history_paths, names) if history_paths else {}
    ablation = load_ablation(ablation_paths) if ablation_paths else {}

    results: list[dict[str, object]] = []
    for skill in skills:
        kind = classify_skill(skill)
        best_peer = None
        best_overlap = 0.0
        for other in skills:
            if skill["name"] == other["name"]:
                continue
            overlap = jaccard(skill["tokens"], other["tokens"])
            if overlap > best_overlap:
                best_overlap = overlap
                best_peer = str(other["name"])

        calls = usage.get(skill["name"])
        usage_source = "usage"
        if calls is None:
            calls = history_usage.get(skill["name"], 0)
            usage_source = "history" if history_paths else "missing"

        ablation_summary = ablation.get(skill["name"])
        u_score = usage_score(calls)
        uniq_score = uniqueness_score(best_overlap)
        i_score = impact_score(kind, calls, best_overlap, skill, ablation_summary)
        total = round(u_score + uniq_score + i_score, 2)
        trigger = delete_trigger(str(skill["source"]), kind, total, calls, best_overlap)

        results.append(
            {
                "name": skill["name"],
                "source": skill["source"],
                "kind": kind,
                "path": skill["path"],
                "calls": calls,
                "usage_source": usage_source,
                "usage_score": u_score,
                "uniqueness_score": uniq_score,
                "impact_score": i_score,
                "total_score": total,
                "verdict": verdict(total),
                "delete_candidate": bool(trigger),
                "delete_trigger": trigger,
                "overlap_peer": best_peer,
                "overlap_value": round(best_overlap, 2),
                "basis": build_basis(calls, best_peer, best_overlap, kind, ablation_summary),
                "missing_usage": usage_source == "missing",
                "missing_ablation": kind == "general" and not ablation_summary,
            }
        )

    ranked = sorted(results, key=lambda item: (-float(item["total_score"]), str(item["name"])))
    delete_candidates = sorted(
        [item for item in ranked if item["delete_candidate"]],
        key=lambda item: (float(item["total_score"]), str(item["name"])),
    )
    missing = [item for item in ranked if item["missing_usage"] or item["missing_ablation"]]

    score_rows = []
    for index, item in enumerate(ranked, start=1):
        score_rows.append(
            [
                str(index),
                str(item["name"]),
                str(item["source"]),
                str(item["kind"]),
                str(item["calls"]),
                f"{item['usage_score']:.1f}",
                f"{item['uniqueness_score']:.1f}",
                f"{item['impact_score']:.1f}",
                f"{item['total_score']:.1f}",
                str(item["verdict"]),
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
        f"- Delete candidates: {len(delete_candidates)}",
        "",
        "## Score Table",
        "",
        markdown_table(
            ["Rank", "Skill", "Source", "Kind", "Calls", "Usage", "Unique", "Impact", "Total", "Verdict", "Basis"],
            score_rows,
        ),
    ]

    if delete_candidates:
        delete_rows = [
            [
                str(item["name"]),
                f"{item['total_score']:.1f}",
                str(item["kind"]),
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
                markdown_table(["Skill", "Total", "Kind", "Trigger", "Reason"], delete_rows),
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
            missing_rows.append([str(item["name"]), str(item["kind"]), ", ".join(gaps)])
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
    audit_parser.add_argument("--usage-file", action="append", help="JSON/JSONL/CSV/TSV file with usage counts.")
    audit_parser.add_argument("--history-file", action="append", help="Transcript export used for mention fallback.")
    audit_parser.add_argument("--ablation-file", action="append", help="JSON or JSONL file with ablation cases.")
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
