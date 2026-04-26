# skill-usefulness-audit

Your agent has too many skills. This shows which ones still earn their place.

`skill-usefulness-audit` scans installed agent skills and produces a cleanup report: recent use, overlap, ablation impact, context cost, bundle hygiene, risk flags, confidence, and optional community signals. The output is meant for decisions: keep, review, merge, delete, or quarantine.

## Quick Start

Audit your local Codex skills:

```bash
python codex-skill/scripts/skill_usefulness_audit.py audit \
  --skills-root ~/.codex/skills \
  --markdown-out skill-audit-report.md \
  --json-out skill-audit-report.json
```

Audit multiple roots:

```bash
python codex-skill/scripts/skill_usefulness_audit.py audit \
  --skills-root ~/.codex/skills \
  --skills-root ~/.codex/plugins/cache \
  --include-system \
  --markdown-out skill-audit-report.md \
  --json-out skill-audit-report.json \
  --ablation-plan-out skill-ablation-plan.json
```

## Example Output

| Skill | Score | Action | Why |
| --- | ---: | --- | --- |
| `gmail` | 9.6 | `keep` | recent use, unique API capability |
| `frontend-skill@user` | 4.8 | `merge-or-review` | overlaps with plugin copy |
| `old-tone-helper` | 2.8 | `delete` | no recent use, high overlap, no ablation gain |
| `bloated-helper` | 5.2 | `review-burden` | high activation, little impact, heavy references/assets |
| `shell-installer` | 6.4 | `quarantine-review` | useful, but high-risk execution pattern |

The Markdown report is for humans. The JSON report is for automation and keeps the same evidence in machine-readable form.

## How To Read The Report

- `local_score`: the 10-point usefulness score from usage, uniqueness, and impact.
- `quality_penalty`: `0.0-2.0` burden from over-triggering, context-heavy resources, weak scripts, or suspicious bundled artifacts.
- `final_score`: `local_score - quality_penalty`, used for ranking and action suggestions.
- `confidence_score`: how much evidence backs the score.
- `report_mode`: `strong-evidence`, `partial-evidence`, or `structure-only`.
- `score_breakdown`: per-skill explanation of each score component.
- `risk_level`: execution-surface risk from scripts and runnable resources.
- `community_prior_score`: optional registry signal for review priority and replacement checks.

Actions are conservative. Low-confidence skills usually go to `observe-30d`. High-risk skills go to `quarantine-review` even when they score well locally.

## Inputs

The tool works with no extra files, but direct evidence gives better results.

| Input | Formats | Useful Fields |
| --- | --- | --- |
| `--usage-file` | JSON, JSONL, CSV, TSV | `calls`, `recent_30d_calls`, `recent_90d_calls`, `last_used_at`, `active_days`, `executions`, `script_failures`, `repair_turns`, `reference_loads`, `false_triggers`, `path`, `namespace` |
| `--history-file` | text, JSON, JSONL | transcript text used as weak fallback evidence |
| `--ablation-file` | JSON, JSONL | skill-on versus skill-off cases |
| `--community-file` | JSON, JSONL, CSV, TSV | `rating`, `downloads`, `installs_current`, `installs_all_time`, `trending_7d`, `stars`, `comments_count`, `last_updated` |
| `--ablation-plan-out` | JSON | cost-efficient ablation plan with candidate skills, early-stop rules, and model-cost estimates |

Planning defaults are `3` initial cases, expand to `5`, cap at `10`, and compare against a `10` case full protocol. Tune them with `--ablation-initial-cases`, `--ablation-expand-cases`, `--ablation-max-cases`, and `--ablation-baseline-cases`.

Duplicate skill names resolve through `path`, `namespace`, and `source`. If an input file only provides a name and that name appears in several installed roots, the report keeps the evidence conservative and adds an `evidence_note`.

## What It Checks

- Usage: recent calls, all-time calls, active days, last-used date, and evidence source.
- Overlap: the closest installed peer by instruction and resource fingerprint.
- Impact: ablation result for general skills; protected-capability scoring for API and tool skills.
- Ablation planning: triage-only candidates, pairwise judging protocol, configurable early-stop rules, model-cost estimates, and expected reduction versus a full protocol.
- Quality burden: over-triggering, high reference loading, bloated SKILL.md, bloated references/assets, weak progressive disclosure, vague resource names, suspicious bundled artifacts, executable assets, script failure and repair burden.
- Risk: shell execution, network download, persistence hooks, protected path access, dynamic execution, and similar patterns.
- Community: optional offline registry signals kept separate from local usefulness.

## 中文说明

这个 skill 用来清理已经装多了的 agent skills。它会把每个 skill 的使用情况、功能重复、消融收益、上下文成本、reference/assets 负担、脚本维护负担、风险信号、证据置信度放进一份报告，并给出 `keep / review / merge-delete / quarantine-review` 建议。

最推荐的用法是先接入真实 usage 数据，再生成 `--ablation-plan-out`，只对候选 general skill 做少量 pairwise 消融。只有历史对话时也能跑，但报告会标成较低置信度。

## Development

```bash
python scripts/sync_bundle.py
git diff --exit-code -- skill/
python -m unittest discover -s tests -v
python codex-skill/scripts/skill_usefulness_audit.py audit \
  --skills-root codex-skill \
  --markdown-out test-output/report.md \
  --json-out test-output/report.json
```

## Repository Layout

- `codex-skill/`: runtime skill source.
- `skill/`: ClawHub publish bundle kept in sync with the runtime source.
- `tests/`: regression and compatibility tests.
- `scripts/sync_bundle.py`: syncs `codex-skill/` into `skill/`.

## Publish

```bash
python scripts/sync_bundle.py
clawhub publish ./skill --slug skill-usefulness-audit --name "skill-usefulness-audit" --version 0.2.7 --tags latest,audit,skills --changelog "Fix script burden detection, refresh stale ablation candidates, and improve mixed-language context estimates"
```
