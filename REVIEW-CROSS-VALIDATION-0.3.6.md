# Review Cross-Validation for 0.3.6

Date: 2026-06-28

Scope:
- Source report reviewed: `C:\Users\admin\Desktop\skill-usefulness-audit-REVIEW-REPORT.md`
- Baseline: `main` at `f4ec1e1`, tag `v0.3.6`
- Policy: accept only issues with local evidence; fix only reproducible product bugs

## Report Findings

Accepted as maintenance debt, not release-blocking bugs:
- `run_audit()` is large: `codex-skill/scripts/skill_usefulness_audit_lib/cli.py:46`
- `reporting.py` is large and mixes report rendering, text tables, and planning helpers
- `type: ignore` usage exists, but the report overstated the count in `cli.py`
- star imports exist in package modules and wrapper files

Accepted as expected self-audit signal:
- self-audit still reports `description-bloat` for this skill's own routing description

Rejected or deferred:
- Hermes scanner `persistence` and `exfiltration` findings were not reproducible locally because Hermes CLI is unavailable in this sandbox.
- Source review supports treating them as scanner false positives: `HOST_PROMPT_MARKERS` is used to filter host prompts, and `missing_required_env()` checks only whether env names are configured.

Report accuracy issues:
- The report claims 110 tests after 13 additions, but this repository had 97 tests before this fix and now has 98.
- Several named "new" tests in the report are not present in the repository.
- The trigger-boundary matrix count in the report is inaccurate for current main.

## Reproduced Product Bug

Bug:
- Without PyYAML, fallback frontmatter parsing did not support YAML-style inline lists such as `[INLINE_API_KEY, SECOND_TOKEN]`.
- With PyYAML, the same metadata parsed correctly.
- Impact: skills that declare required env vars using common YAML inline list syntax could lose `required_env` and `missing_required_env` evidence in no-PyYAML environments.

Minimal fixture:

```yaml
---
name: inline-env
description: Call APIs.
metadata:
  requires:
    env: [INLINE_API_KEY, SECOND_TOKEN]
---
# Inline Env
```

Before fix:

```text
with_yaml=INLINE_API_KEY,SECOND_TOKEN
fallback=
```

After fix:

```text
with_yaml=INLINE_API_KEY,SECOND_TOKEN
fallback=INLINE_API_KEY,SECOND_TOKEN
```

## Fix

Changed:
- `codex-skill/scripts/skill_usefulness_audit_lib/common.py`
- `skill/scripts/skill_usefulness_audit_lib/common.py`
- `scripts/sync_bundle.py`
- `tests/test_skill_usefulness_audit.py`

Behavior:
- Fallback scalar parsing now supports simple YAML inline sequences with bare or quoted scalar items.
- Existing JSON-style inline lists still use `json.loads` first.
- Unterminated quoted inline lists continue to fall back to the original raw value.

## Verification

Commands run:

```powershell
git pull --ff-only origin main
python -m unittest -v tests.test_skill_usefulness_audit
python scripts\sync_bundle.py --dry-run
git diff --check
python codex-skill\scripts\skill_usefulness_audit.py --version
python codex-skill\scripts\skill_usefulness_audit.py audit --skills-root codex-skill --json-out .test-tmp\self-audit-after-fix.json --markdown-out .test-tmp\self-audit-after-fix.md
```

Focused checks also passed for:
- reference ads, tool upsells, skill recommendations, and unrelated reference text
- clean ablation reference false-positive guard
- meaningless or empty skill contract
- missing local Python import
- broken reference link
- broken tool script cap
- trigger-boundary matrix
- bundle-copy fallback parser

Final status:
- Full test suite: 98 tests passed
- `git diff --check`: passed
- self-audit: `risk_level=none`, `delete_candidates=0`, only existing `description-bloat`
