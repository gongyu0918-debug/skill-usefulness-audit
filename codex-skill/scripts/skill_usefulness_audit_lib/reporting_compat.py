from __future__ import annotations

from . import reporting as _reporting

_ORIGINAL_DECISION_SUMMARY = _reporting.decision_summary


def _summary_group(title_key: str, items: list[dict[str, object]], limit: int, language: str) -> list[str]:
    normalized_language = _reporting.normalize_report_language(language)
    lines = [f"### {_reporting.report_text(normalized_language, title_key)}", ""]
    if not items:
        lines.append(f"- {_reporting.report_text(normalized_language, 'none')}")
        return lines

    sentence_end = "。" if normalized_language == "zh-CN" else "."
    action_end = "。" if normalized_language == "zh-CN" else "."
    terminal_marks = (".", "。", "!", "！", "?", "？")
    for item in items[:limit]:
        reason = _reporting._summary_reason(item, normalized_language)
        reason_end = "" if reason.endswith(terminal_marks) else sentence_end
        lines.append(
            f"- {_reporting._item_display_name(item)}: `{_reporting._item_action(item)}`{action_end} "
            f"{reason}{reason_end}"
        )
    if len(items) > limit:
        lines.append(f"- {_reporting.report_text(normalized_language, 'more').format(count=len(items) - limit)}")
    return lines


def decision_summary(ranked: list[dict[str, object]], limit: int = 5, language: str = "en") -> list[str]:
    return _ORIGINAL_DECISION_SUMMARY(ranked, limit=limit, language=language)


def patch_reporting_module() -> None:
    _reporting._summary_group = _summary_group
    _reporting.decision_summary = decision_summary


def patch_namespace(namespace: dict[str, object]) -> None:
    namespace["decision_summary"] = decision_summary
