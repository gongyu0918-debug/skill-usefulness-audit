# skill-usefulness-audit

Your agent has too many skills. This shows which ones still earn their place.

`skill-usefulness-audit` scans installed agent skills and produces a cleanup report: recent use, overlap, ablation impact, context cost, bundle hygiene, static risk flags, confidence, and optional community signals. The output is meant for human-reviewed decisions: keep, review, merge, delete, or quarantine.

The skill follows the AgentSkills folder layout used by OpenClaw, Hermes, Claude Code, and Codex. The ClawHub package is still the OpenClaw publishing entry, and the runtime source in `codex-skill/` can be copied into other agents' skills directories.

## Compatibility

| Host | Current fit | Install note |
| --- | --- | --- |
| OpenClaw | Native ClawHub bundle with OpenClaw metadata and Python requirement. | Use `openclaw skills install skill-usefulness-audit` or copy `skill/` through your OpenClaw skill workflow. |
| Hermes | AgentSkills-compatible structure with Hermes metadata and terminal requirement. | Copy the skill contents into `~/.hermes/skills/skill-usefulness-audit/` or a configured external skills directory. |
| Claude Code | AgentSkills-compatible `SKILL.md`; manual invocation is preferred. | Copy the skill contents into `~/.claude/skills/skill-usefulness-audit/` or `.claude/skills/skill-usefulness-audit/`. |
| Codex | Existing runtime source remains in `codex-skill/`. | Copy `codex-skill/` into a Codex skills directory or run the script directly from the repo. |

When manually installing into Hermes or Claude Code, keep the target folder name as `skill-usefulness-audit`.

## Safe First Run

Start with an inventory-only report:

```bash
python codex-skill/scripts/skill_usefulness_audit.py audit \
  --markdown-out skill-audit-report.md \
  --json-out skill-audit-report.json
```

This mode is `structure-only`. Use it to find broken scripts, bloated references, vague routing, private-looking artifacts, and static risk hints.

Do not delete skills based only on a structure-only report.
For cleanup decisions, rerun with real `--usage-file`; for general skills near the delete/merge boundary, generate an ablation plan and add `--ablation-file` results.

## Borrowed Idea Gate

When absorbing ideas from another skill, keep the change small and measurable.
Record the source idea, expected benefit, baseline command, ablation command, and rollback condition before merging.
Use the same input fixture against the current baseline and the changed version; revert the change if unrelated skills receive stricter actions or existing risk/quality behavior regresses.

## Quick Start

Audit your local Codex skills:

```bash
python codex-skill/scripts/skill_usefulness_audit.py audit \
  --skills-root ~/.codex/skills \
  --markdown-out skill-audit-report.md \
  --json-out skill-audit-report.json
```

Audit common OpenClaw, Hermes, Claude Code, and Codex locations with default discovery:

```bash
python codex-skill/scripts/skill_usefulness_audit.py audit \
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
| `shell-installer` | 6.4 | `quarantine-review` | useful, but high-risk execution pattern (`risk_score >= 4.0`) |

The Markdown report is for humans. It starts with a Decision Summary that groups skills into keep, observe, human-review, merge/remove, and new-install-gate buckets before the evidence tables. The JSON report is for automation and keeps the same evidence in machine-readable form. The cost-efficient ablation plan is written only when `--ablation-plan-out` is provided.

## How To Read The Report

- `local_score`: the 10-point usefulness score from usage, uniqueness, and impact.
- `quality_penalty`: `0.0-2.5` burden from over-triggering, context-heavy resources, weak scripts, or suspicious bundled artifacts.
- `quality_penalty_uncapped`: raw burden before the display/action cap; use it to see when the cap is hiding extra maintenance cost.
- `final_score`: `local_score - quality_penalty`, used for ranking and action suggestions.
- `confidence_score`: how much evidence backs the score.
- `report_mode`: `strong-evidence`, `partial-evidence`, or `structure-only`.
- `Decision Summary`: the front-of-report human summary for what is useful, what needs more evidence, and what needs review before use or removal.
- `score_breakdown`: per-skill explanation of each score component.
- `risk_level` / `static_risk_level`: static execution-surface hints from scripts and runnable resources.
- `community_prior_score`: optional registry signal for review priority and replacement checks.
- `action_advice`: plain-language recommendation for the human reviewer.
- `history_mentions` / `suspected_invocations`: weak transcript fallback evidence. These do not count as direct `calls`.

Use `action` / `action_advice` as the final human-facing recommendation. `verdict` is only a `final_score` band, so risk, quality burden, confidence, or community signals can deliberately make `action` stricter than `verdict`. The `basis` column is a compact explanation for humans, while JSON `score_breakdown` is the complete machine-readable evidence.

Actions are conservative recommendations, not automatic operations. Low-confidence skills usually go to `observe-30d`, unless static risk needs review. High-risk skills (`risk_score >= 4.0`) go to `quarantine-review` even when they score well locally, medium-risk skills go to risk review when they are not already in a keep-with-risk branch, and `delete` / `merge-delete` always require manual review before removal.

## Inputs

The tool works with no extra files, but direct evidence gives better results.

| Input | Formats | Useful Fields |
| --- | --- | --- |
| `--usage-file` | JSON, JSONL, CSV, TSV | `calls`, `recent_30d_calls`, `recent_90d_calls`, `last_used_at`, `active_days`, `executions`, `script_failures`, `repair_turns`, `reference_loads`, `false_triggers`, `path`, `namespace` |
| `--history-file` | text, JSON, JSONL | transcript text used as weak fallback evidence; mentions are reported separately from direct `calls` |
| `--ablation-file` | JSON, JSONL | skill-on versus skill-off cases |
| `--community-file` | JSON, JSONL, CSV, TSV | `rating`, `downloads`, `installs_current`, `installs_all_time`, `trending_7d`, `stars`, `comments_count`, `last_updated` |
| `--ablation-plan-out` | JSON | cost-efficient ablation plan with candidate skills, early-stop rules, and model-cost estimates |

Minimal `usage.json`:

```json
[
  {
    "name": "pdf-helper",
    "calls": 12,
    "recent_30d_calls": 4,
    "last_used_at": "2026-06-01",
    "executions": 10,
    "script_failures": 1,
    "reference_loads": 6,
    "false_triggers": 0
  }
]
```

This tool does not automatically replay historical conversations. It creates an ablation plan and reads ablation result files that you provide.

History and usage files may contain sensitive conversations, local paths, project names, and customer data. Prefer local execution and redact secrets before sharing reports. JSON output may include local paths and evidence notes.

Missing env means not configured in the current audit process, not proof that the skill is broken in every host.

Planning defaults are `3` initial cases, expand to `5`, cap at `10`, and compare against a `10` case full protocol. Tune them with `--ablation-initial-cases`, `--ablation-expand-cases`, `--ablation-max-cases`, and `--ablation-baseline-cases`.

Duplicate skill names resolve through `path`, `namespace`, and `source`. If an input file only provides a name and that name appears in several installed roots, the report keeps the evidence conservative and adds an `evidence_note`.

## What It Checks

- Usage: recent calls, all-time calls, active days, last-used date, weak history mentions, and evidence source.
- Overlap: the closest installed peer by instruction and resource fingerprint.
- Impact: ablation result for general skills; missing ablation with no usage uses a low-evidence score; protected-capability scoring for API and tool skills.
- Ablation planning: triage-only candidates, pairwise judging protocol, configurable early-stop rules, model-cost estimates, and expected reduction versus a full protocol.
- Quality burden: over-triggering, high reference loading, bloated SKILL.md, overlong descriptions, bloated references/assets, weak progressive disclosure, vague resource names, suspicious bundled artifacts, executable assets, script failure and repair burden.
- Static risk hints: shell execution, install hooks, packaging execution surfaces, network download, protected path access, private-looking bundled content, dynamic execution, and similar patterns. This is lint-style evidence, not a safety proof.
- Community: optional offline registry signals kept separate from local usefulness.

## 中文说明

这个 skill 用来清理已经装多了的 agent skills。它会把每个 skill 的使用情况、功能重复、消融收益、上下文成本、reference/assets 负担、脚本维护负担、静态风险提示、证据置信度放进一份报告，并给出 `keep / review / merge-delete / quarantine-review` 人工复核建议。

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
clawhub publish ./skill --slug skill-usefulness-audit --name "skill-usefulness-audit" --version 0.3.2 --tags latest,audit,skills,openclaw --changelog "Make ablation planning opt-in, preserve medium-risk review, and trim runtime context"
```
