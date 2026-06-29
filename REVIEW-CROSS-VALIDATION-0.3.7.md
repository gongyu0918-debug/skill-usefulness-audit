# Review Cross-Validation for 0.3.7

Date: 2026-06-29/2026-06-30

Scope:
- Source reports reviewed:
  - `C:\Users\admin\Desktop\skill-usefulness-audit-REVIEW-UPDATE-v0.3.7.md`
  - `C:\Users\admin\Desktop\skill-usefulness-audit-REVIEW.md`
- Baseline: `main` at `v0.3.7`
- Policy: accept only locally reproducible product bugs; run cross-version ablation and read-only real-environment checks before final judgment

## Accepted Findings

Accepted and fixed:
- Nested YAML inline lists were not equivalent between PyYAML and fallback parsing.
- Example: `env: [[NESTED_API_KEY, SECOND_TOKEN]]`
- v0.3.7 fallback parsed metadata as a nested list but did not extract `required_env`.
- Current fallback now matches PyYAML metadata shape and extracts `NESTED_API_KEY,SECOND_TOKEN`.

Accepted as cleanup:
- Trailing commas in fallback inline lists produced empty string elements in parsed metadata.
- This did not break `required_env`, because empty env names were filtered, but it made fallback metadata differ from PyYAML.
- Current fallback now skips empty trailing elements and matches PyYAML.

## Rejected or Deferred Findings

Rejected as a product bug:
- `sync_bundle.py` duplicates the inline sequence fallback parser.
- This is maintenance duplication, but the sync script intentionally runs without importing the bundled runtime package. It is covered by sync tests and mirrored by bundle verification.

Rejected as stated:
- The report says v0.3.7 changed "only 7 files" but lists 9 entries.
- The report says 13 supplemental tests were "deleted"; they were never committed to this repository.
- Many of the named supplemental scenarios already have equivalent coverage, including no-skill exit, strict inputs, version, Chinese usage/verdicts, community CSV, overtrigger, zh-CN output, self-audit risk, API/tool classification, and near-duplicate quality flags.

Deferred:
- None for Hermes install blocking. The block was reproduced locally in an isolated `HERMES_HOME`, then mitigated in the generated package without changing runtime behavior.

## Hermes Install Blocking

Isolated reproduction:
- Hermes version: `Hermes Agent v0.17.0`
- Temporary home: `.test-tmp/hermes-install-repro`
- Command: `hermes skills install skill-usefulness-audit --yes`
- Result: installation was blocked, installed list stayed empty, and `.hub/audit.log` recorded `BLOCKED skill-usefulness-audit clawhub:community dangerous 2_findings`

Reproduced findings:
- `CRITICAL persistence scripts\skill_usefulness_audit_lib\constants.py:447 "# agents.md instructions"`
- `HIGH exfiltration scripts\skill_usefulness_audit_lib\common.py:376 return [name for name in required_env if not os.environ.get(`

Scanner source review:
- Hermes `tools/skills_guard.py` treats any literal `AGENTS.md` reference as `agent_config_mod` / `critical persistence`.
- Hermes also flags broad `os.environ` access and secret-shaped `os.environ.get(...)` reads as exfiltration.

Local mitigation:
- Keep the runtime host-prompt marker behavior intact, but construct the `agents.md` marker without a contiguous `AGENTS.md` source literal.
- Keep `missing_required_env()` semantics intact, including treating empty env values as missing, but use `os.getenv(name)` instead of `os.environ.get(name)` / `os.environ[name]` patterns that Hermes flags.

Validation:
- Direct local Hermes scanner import against generated `skill/`: `verdict=safe`, `finding_count=0`
- Regression tests preserve host-prompt filtering and required-env behavior.
- Important caveat: the published ClawHub `0.3.7` package still contains the old blocked source until a new version is published.

## Cross-Version Ablation

Fixture matrix:
- `v0.3.2`
- `v0.3.5`
- `v0.3.6`
- `v0.3.7`
- current working tree

Artifacts:
- `.test-tmp/ablation-matrix-v037-review/ablation-matrix.csv`
- `.test-tmp/ablation-matrix-v037-review/ablation-summary.txt`

Key outcomes:
- `nested-block-env`: fixed by v0.3.6 and remains fixed.
- `flat-inline-env`: fixed by v0.3.7 and remains fixed.
- `nested-inline-env`: still missed `required_env` in v0.3.7; fixed in current working tree.
- `trailing-inline-env`: v0.3.7 extracted `required_env` but kept an empty metadata element; fixed in current working tree.
- `reference-sponsored`: pollution flag appears from v0.3.6 onward.
- `meaningless-md`: `empty-skill-contract` appears from v0.3.6 onward.
- `broken-tool`: broken script behavior remained stable across tested versions.

## Real Environment Check

Read-only roots discovered:
- `C:\Users\admin\.codex\skills` with 16 `SKILL.md` files

Artifacts:
- `.test-tmp/real-env-v037-review/real-env-normal.json`
- `.test-tmp/real-env-v037-review/real-env-no-yaml.json`
- `.test-tmp/real-env-v037-review/summary.json`

Results:
- Normal PyYAML scan: 11 audited skills
- No-PyYAML scan: 11 audited skills
- Field-level diff across `required_env`, `missing_required_env`, `quality_flags`, `risk_flags`, `action`, and `final_score`: 0 differences
- Delete candidates: 0 in both runs
- Non-none risk skills: 2 in both runs

## Verification

Commands run:

```powershell
git pull --ff-only origin main
python -m py_compile codex-skill\scripts\skill_usefulness_audit.py scripts\sync_bundle.py tests\test_skill_usefulness_audit.py
python -m unittest discover -s tests -v
python scripts\sync_bundle.py --dry-run
git diff --check
```

Focused checks:
- PyYAML vs fallback metadata equality for nested inline lists
- PyYAML vs fallback metadata equality for trailing comma inline lists
- CLI subprocess with PyYAML disabled through isolated `PYTHONPATH`
- Bundle-copy fallback parser against nested and trailing inline list fixtures
- Cross-version ablation against historical tags
- Read-only scan of actual installed Codex skills

Final local test status:
- 103 tests passed
