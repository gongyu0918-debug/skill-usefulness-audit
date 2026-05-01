from __future__ import annotations

from .common import *
from .scoring import *

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
    quality_penalty_value: float,
    quality_flags: list[str],
    evidence_note: str | None,
) -> str:
    parts = [f"calls={int(usage_record.get('calls', 0) or 0)}"]
    history_mentions = int(usage_record.get("history_mentions", 0) or 0)
    if history_mentions:
        parts.append(f"history_mentions={history_mentions}")
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
    if quality_penalty_value > 0:
        parts.append(f"burden={quality_penalty_value:.2f}")
    if quality_flags:
        parts.append(f"quality={short_risk_flags(quality_flags)}")
    if evidence_note:
        parts.append(f"note={evidence_note}")
    return "; ".join(parts)


def escape_markdown_cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    escaped_headers = [escape_markdown_cell(header) for header in headers]
    lines = ["| " + " | ".join(escaped_headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    lines.extend("| " + " | ".join(escape_markdown_cell(cell) for cell in row) + " |" for row in rows)
    return "\n".join(lines)


def fmt_optional_int(value) -> str:
    coerced = coerce_int(value)
    return "-" if coerced is None else str(coerced)


def fmt_optional_float(value, digits: int = 2) -> str:
    coerced = coerce_float(value)
    return "-" if coerced is None else f"{coerced:.{digits}f}"


def fmt_breakdown_components(breakdown: dict[str, float]) -> str:
    if not breakdown:
        return "-"
    order = [
        "rating",
        "current_installs_or_downloads",
        "installs_all_time",
        "trending_7d",
        "stars",
        "comments_count",
        "maintenance",
    ]
    ordered_keys = [key for key in order if key in breakdown]
    ordered_keys.extend(sorted(key for key in breakdown if key not in set(order)))
    return ", ".join(f"{key}={breakdown[key]:.3f}" for key in ordered_keys)


def summarize_quality_evidence(evidence: list[dict[str, object]], limit: int = 3) -> str:
    if not evidence:
        return "-"
    parts = []
    for item in evidence[:limit]:
        label = str(item.get("label", "quality"))
        reason = str(item.get("reason", "")).strip()
        penalty = fmt_optional_float(item.get("penalty"))
        parts.append(f"{label}({penalty}): {reason}" if reason else f"{label}({penalty})")
    if len(evidence) > limit:
        parts.append(f"+{len(evidence) - limit} more")
    return "; ".join(parts)


def determine_report_mode(
    usage_paths: list[Path],
    history_paths: list[Path],
    ablation_paths: list[Path],
    results: list[dict[str, object]],
) -> str:
    if not usage_paths and not history_paths and not ablation_paths:
        return "structure-only"
    if any(item["missing_usage"] or item["missing_ablation"] for item in results):
        return "partial-evidence"
    return "strong-evidence"


def ablation_priority(item: dict[str, object]) -> tuple[float, list[str]]:
    if item["kind"] != "general":
        return 0, []
    ablation = item.get("score_breakdown", {}).get("impact", {}).get("ablation")  # type: ignore[union-attr]
    cases = int((ablation or {}).get("cases", 0)) if isinstance(ablation, dict) else 0
    consistency = float((ablation or {}).get("consistency_rate", 0.0)) if isinstance(ablation, dict) else 0.0
    better = float((ablation or {}).get("better_rate", 0.0)) if isinstance(ablation, dict) else 0.0
    has_review_signal = (
        float(item["final_score"]) < 6.0
        or float(item["overlap_value"]) >= 0.65
        or float(item["quality_penalty"]) > 0
        or str(item["action"]) not in {"keep", "keep-narrow", "keep-system"}
    )
    if cases >= 5 and not has_review_signal:
        return 0, ["already has enough ablation cases"]

    score = 0.0
    reasons: list[str] = []
    if cases >= 5:
        score += 1.0
        reasons.append("refresh existing ablation")
        if consistency >= 0.85 and better <= 0.10:
            score += 1.0
            reasons.append("prior no-impact ablation")
    if item["missing_ablation"]:
        score += 2
        reasons.append("missing ablation")
    if float(item["final_score"]) < 6.0:
        score += 2
        reasons.append("weak final score")
    if float(item["overlap_value"]) >= 0.65:
        score += 2
        reasons.append("high overlap")
    if float(item["quality_penalty"]) >= 0.6:
        score += 2
        reasons.append("high quality burden")
    elif float(item["quality_penalty"]) > 0:
        score += 1
        reasons.append("some quality burden")
    if int(item["calls"]) >= 5:
        score += 1
        reasons.append("frequent activation")
    if str(item["usage_source"]) == "missing":
        score += 1
        reasons.append("missing usage evidence")
    elif str(item["usage_source"]) == "history":
        score += 0.5
        reasons.append("history-only usage evidence")
    if float(item["confidence_score"]) < 0.55:
        score += 1
        reasons.append("low confidence")
    if str(item["action"]) not in {"keep", "keep-narrow", "keep-system"}:
        score += 1
        reasons.append(f"action={item['action']}")
    return score, reasons


def estimate_model_cost(case_count: int) -> dict[str, int]:
    return {name: case_count * per_case for name, per_case in ABLATION_COST_PROFILES.items()}


def reduction_percent(planned: int, baseline: int) -> float:
    if baseline <= 0:
        return 0.0
    return round(clamp(1.0 - planned / baseline, 0.0, 1.0) * 100, 1)


def accuracy_impact(candidates: list[dict[str, object]], deferred: list[dict[str, object]]) -> dict[str, object]:
    risky_deferred = [
        item
        for item in deferred
        if item["kind"] == "general"
        and item["missing_ablation"]
        and (float(item["final_score"]) < 6.0 or float(item["overlap_value"]) >= 0.65 or float(item["quality_penalty"]) >= 0.6)
    ]
    if not candidates:
        level = "high"
        reason = "no general skill was selected for ablation"
    elif risky_deferred:
        level = "medium"
        reason = f"{len(risky_deferred)} deferred general skills still carry weak-score, overlap, or burden signals"
    else:
        level = "low"
        reason = "deferred skills have stronger local evidence or lower ablation priority"
    return {
        "expected_accuracy_impact": level,
        "reason": reason,
        "mitigations": [
            "use pairwise A/B comparison instead of single-output grading",
            "expand from 3 to 5 cases when the first batch is mixed",
            "expand to 10 cases only for decision-boundary skills",
            "cache replay outputs by skill, case, model, prompt, and artifact hash",
            "review deferred skills when new usage or quality-burden evidence appears",
        ],
    }


def build_ablation_plan(
    results: list[dict[str, object]],
    max_candidates: int = ABLATION_DEFAULT_MAX_CANDIDATES,
    baseline_cases_per_skill: int = ABLATION_BASELINE_CASES,
    initial_cases_per_candidate: int = ABLATION_INITIAL_CASES,
    expand_to_cases: int = ABLATION_EXPAND_CASES,
    max_cases_per_candidate: int = ABLATION_MAX_CASES,
) -> dict[str, object]:
    baseline_cases_per_skill = max(1, baseline_cases_per_skill)
    initial_cases_per_candidate = max(1, initial_cases_per_candidate)
    expand_to_cases = max(initial_cases_per_candidate, expand_to_cases)
    max_cases_per_candidate = max(expand_to_cases, max_cases_per_candidate)
    general = [item for item in results if item["kind"] == "general"]
    scored: list[tuple[float, dict[str, object], list[str]]] = []
    for item in general:
        score, reasons = ablation_priority(item)
        scored.append((score, item, reasons))

    scored.sort(key=lambda entry: (-entry[0], float(entry[1]["final_score"]), str(entry[1]["display_name"])))
    positive = [entry for entry in scored if entry[0] >= 3]
    if not positive:
        positive = [entry for entry in scored if entry[0] > 0][:ABLATION_MIN_CANDIDATES]
    candidate_entries = positive[:max_candidates]
    candidate_paths = {str(entry[1]["path"]) for entry in candidate_entries}

    candidates = []
    for priority, item, reasons in candidate_entries:
        candidates.append(
            {
                "skill": item["display_name"],
                "path": item["path"],
                "priority_score": priority,
                "priority_reasons": reasons,
                "initial_cases": initial_cases_per_candidate,
                "expand_to": expand_to_cases,
                "max_cases": max_cases_per_candidate,
                "recommended_judge": "pairwise A/B comparison with pass/fail and same/better/worse labels",
                "case_selection": [
                    "prefer real production/history prompts where the skill triggered",
                    "include tasks near the skill boundary or with prior repair burden",
                    "deduplicate prompts by normalized text and artifact hash",
                ],
            }
        )

    deferred = []
    deferred_entries = [entry for entry in scored if str(entry[1]["path"]) not in candidate_paths]
    deferred_items = [entry[1] for entry in deferred_entries]
    for priority, item, reasons in deferred_entries:
        deferred.append(
            {
                "skill": item["display_name"],
                "path": item["path"],
                "priority_score": priority,
                "defer_reasons": reasons or ["low ablation priority"],
                "local_score": item["local_score"],
                "quality_penalty": item["quality_penalty"],
                "final_score": item["final_score"],
            }
        )

    eligible_count = len(general)
    candidate_count = len(candidates)
    baseline_cases = eligible_count * baseline_cases_per_skill
    initial_cases = candidate_count * initial_cases_per_candidate
    expected_cases = candidate_count * expand_to_cases
    max_cases = candidate_count * max_cases_per_candidate
    baseline_cost = estimate_model_cost(baseline_cases)
    initial_cost = estimate_model_cost(initial_cases)
    expected_cost = estimate_model_cost(expected_cases)
    max_cost = estimate_model_cost(max_cases)

    return {
        "strategy": "triage-pairwise-early-stop",
        "eligible_general_skills": eligible_count,
        "candidate_skills": candidate_count,
        "deferred_general_skills": len(deferred),
        "case_policy": {
            "baseline_cases_per_general_skill": baseline_cases_per_skill,
            "initial_cases_per_candidate": initial_cases_per_candidate,
            "expand_to_cases": expand_to_cases,
            "max_cases_per_candidate": max_cases_per_candidate,
        },
        "stop_rules": {
            "stop_delete_candidate": f"{initial_cases_per_candidate}/{initial_cases_per_candidate} cases are same and better_rate is 0",
            "stop_keep_candidate": f"{math.ceil(initial_cases_per_candidate * 2 / 3)}/{initial_cases_per_candidate} or better show clear improvement and no worse cases",
            "expand": "mixed first batch or final_score is between 3.0 and 6.5",
            "max": "only for high-impact or deletion-boundary decisions",
        },
        "judge_protocol": {
            "mode": "pairwise",
            "bias_control": "randomize A/B order and spot-check reversed order on boundary cases",
            "labels": ["better", "same", "worse"],
            "deterministic_metrics": ["pass", "score", "tool_cost", "latency", "repair_turns"],
        },
        "cache_keys": ["skill", "case_id", "model", "prompt_hash", "artifact_hash", "skill_version"],
        "model_cost_estimates": {
            "unit": ABLATION_COST_UNIT,
            "profiles_per_case_units": ABLATION_COST_PROFILES,
            "baseline_full_protocol": {
                "cases": baseline_cases,
                "model_cost_units": baseline_cost,
            },
            "planned_initial": {
                "cases": initial_cases,
                "model_cost_units": initial_cost,
                "reduction_vs_baseline_percent": {
                    name: reduction_percent(initial_cost[name], baseline_cost[name]) for name in ABLATION_COST_PROFILES
                },
            },
            "planned_expected": {
                "cases": expected_cases,
                "model_cost_units": expected_cost,
                "reduction_vs_baseline_percent": {
                    name: reduction_percent(expected_cost[name], baseline_cost[name]) for name in ABLATION_COST_PROFILES
                },
            },
            "planned_max": {
                "cases": max_cases,
                "model_cost_units": max_cost,
                "reduction_vs_baseline_percent": {
                    name: reduction_percent(max_cost[name], baseline_cost[name]) for name in ABLATION_COST_PROFILES
                },
            },
        },
        "accuracy_tradeoff": accuracy_impact([entry[1] for entry in candidate_entries], deferred_items),
        "candidates": candidates,
        "deferred": deferred,
    }
