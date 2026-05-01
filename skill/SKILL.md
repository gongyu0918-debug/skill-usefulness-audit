---
name: skill-usefulness-audit
slug: skill-usefulness-audit
description: Finds unused, overlapping, risky, or under-evidenced agent skills and
  produces a cleanup report.
version: 0.2.9
tags:
- audit
- skills
- ablation
- codex
- openclaw
homepage: https://github.com/gongyu0918-debug/skill-usefulness-audit
---
# Skill Usefulness Audit

## Overview

Use this skill to judge whether installed skills still deserve to stay installed.
It turns vague "this feels useless" opinions into a repeatable audit based on usage evidence, overlap, outcome impact, quality burden, confidence, community prior, and static risk hints.

用这个 skill 判断哪些已安装 skill 还值得保留。
它把“感觉没用”变成可复现的审计流程，基于使用证据、功能重叠、结果影响、质量负担、证据置信度、社区先验和静态风险提示来判断。

## Manual Trigger Only

Run this skill only after a direct user request.
Do not invoke it implicitly during normal task execution.

只在用户手动要求时运行。
正常任务执行过程中不要隐式触发。

## Audit Scope

Audit these layers in order:

1. Usage evidence with recency and source quality.
2. Installed skill metadata and instructions.
3. Functional overlap across skills.
4. Ablation impact on historical conversations for non-API and non-tool skills.
5. Quality burden from over-triggering, context-heavy resources, weak progressive disclosure, redundant references/assets, weak scripts, or private-looking bundled files.
6. Static health and risk signals.
7. Optional offline community or registry metrics.

Treat API and tool skills as protected capability skills during ablation.
Examples: Excel, DOCX, PDF, browser automation, deployment, OCR, external API wrappers, MCP/API gateway helpers.

按这个顺序审计：

1. 带近期信息和来源质量的使用证据
2. 已安装 skill 的元数据与说明
3. skill 之间的功能重叠
4. 非 API、非工具型 skill 在历史对话上的消融影响
5. 静态健康度与风险信号
6. 可选的离线社区或注册表指标

在消融阶段，把 API skill 和工具型 skill 当作受保护能力。
例如：Excel、DOCX、PDF、浏览器自动化、部署、OCR、外部 API 包装器、MCP/API 网关类 skill。

## Workflow

1. Collect installed skills.
   Search user-provided roots first.
   Fallback to host-local roots such as `./skills`, `$CODEX_HOME/skills`, or `~/.codex/skills`.
2. Collect usage evidence.
   Prefer native counters, logs, or telemetry.
   Read `calls`, `recent_30d_calls`, `recent_90d_calls`, `last_used_at`, and `active_days` when present.
   Also read optional burden fields: `executions`, `script_failures`, `repair_turns`, `reference_loads`, and `false_triggers`.
   Fallback to transcript mentions only when native counts are unavailable.
3. Read every installed `SKILL.md`.
   Extract `name`, `description`, headings, scripts, references, assets, resource size metrics, and source path.
4. Classify each skill.
   Use `api`, `tool`, or `general`.
   Use the protected path for `api` and `tool`.
5. Detect overlap.
   Compare descriptions, headings, and resource names.
   Keep the top overlap peer and similarity score for each skill.
6. Generate a cost-efficient ablation plan for `general` skills.
   Start with local triage signals instead of full replay.
   Prioritize low final score, high overlap, high quality burden, frequent activation, weak evidence, and missing ablation.
   Use `--ablation-plan-out` to write the candidate list, pairwise judge protocol, configurable early-stop rules, model-cost estimates, and accuracy tradeoff.
   Run actual replay only for candidates selected by that plan.
7. Score quality burden.
   Penalize over-triggering with low execution or low ablation impact.
   Penalize bloated `SKILL.md`, excessive reference loading, hidden reference files, vague resource names, long references without a table of contents, reference/assets dumps, executable assets, script count bloat, script maintenance smells, script failure, script syntax errors, and repeated agent repair.
8. Scan static risk and health signals.
   Record shell, network, protected-path, persistence, or dynamic-exec patterns as static hints, not as a safety proof.
9. Load optional community metrics.
   Accept local registry exports through `--community-file`.
   Treat these metrics as external prior, not local proof.
10. Score every skill on a 10-point local scale and subtract quality burden for `final_score`.
   Read `references/scoring-rubric.md`.
11. Produce the final report as tables.
   Include a full ranking table, a recommended-actions table, a delete-candidate table, and a short evidence note for each skill.
   Include `report_mode`, `score_breakdown`, `quality_penalty`, `quality_evidence`, and `community_breakdown` in JSON output.

## Ablation Rules

Read `references/ablation-protocol.md` before running ablation.

For each eligible skill:

- Generate the ablation plan first.
- Sample historical tasks only for candidate skills in that plan.
- Keep the prompt and artifacts identical between the skill-on and skill-off runs.
- Judge pass/fail, quality delta, tool efficiency, and whether the final answer materially changed.
- Mark high consistency between skill-on and skill-off runs as evidence that the skill contributes little.

Do not ablate `api` or `tool` skills through fake no-tool simulations.
Use the protected-capability branch in the rubric for those skills.

## Commands

Run the audit script after collecting evidence:

```bash
python scripts/skill_usefulness_audit.py audit \
  --skills-root ./skills \
  --usage-file ./usage.json \
  --history-file ./history.jsonl \
  --ablation-file ./ablation.json \
  --community-file ./community.json \
  --markdown-out ./skill-audit-report.md \
  --json-out ./skill-audit-report.json \
  --ablation-plan-out ./skill-ablation-plan.json
```

Input contracts:

- `--usage-file`: JSON, JSONL, CSV, or TSV with per-skill usage evidence.
- `--history-file`: raw transcript export used only when direct usage counts are weak or missing. Mentions become `history_mentions` / `suspected_invocations`, not direct `calls`.
- `--ablation-file`: normalized JSON or JSONL with skill-on versus skill-off case results.
- `--community-file`: optional offline JSON, JSONL, CSV, or TSV registry metrics.
- `--ablation-plan-out`: optional JSON plan that estimates model cost and narrows ablation to high-value candidates.
- `--ablation-baseline-cases`, `--ablation-initial-cases`, `--ablation-expand-cases`, `--ablation-max-cases`: optional case-count overrides for the ablation plan.

Run without extra files only when you need a structure-only audit.
Usage, community, and ablation evidence become lower-confidence in that mode.

## Output Contract

Always return these tables:

1. Full score table with:
   `rank`, `skill`, `source`, `kind`, `calls`, `recent_30d`, `usage`, `uniqueness`, `impact`, `community`, `confidence`, `risk`, `local`, `burden`, `final`, `verdict`, `action`, `basis`
2. Recommended actions with:
   `skill`, `local`, `burden`, `final`, `confidence`, `risk`, `action`, `reason`
3. Deletion or merge candidates with:
   `skill`, `local`, `burden`, `final`, `kind`, `action`, `trigger`, `reason`
4. Missing-evidence table when usage, ablation, or optional community data is incomplete.
5. Quality-burden table when a skill has context, asset, reference, script, or over-triggering burden.

Always include these JSON fields:

- `report_mode`: `strong-evidence`, `partial-evidence`, or `structure-only`.
- `score_breakdown`: per-skill usage, uniqueness, impact, community, static risk, quality, and confidence details.
- `quality_penalty`: `0.0-2.0` deduction from `local_score`.
- `quality_penalty_uncapped`: raw quality burden before the `2.0` cap.
- `quality_evidence`: concrete burden flags and evidence.
- `community_breakdown`: registry signal components when community data is present.
- `ablation_plan`: cost-efficient plan with candidate skills, model-cost estimates, stop rules, and expected accuracy impact.

Keep deletion advice conservative for system or host-core skills.
Recommend narrowing or merging before deletion when two high-overlap skills still serve distinct host integrations.
Treat `delete`, `merge-delete`, and `quarantine-review` as manual-review recommendations only; never remove or isolate a skill automatically from this report.

## Resources

- `scripts/skill_usefulness_audit.py`: compatibility wrapper for the modular audit package.
- `scripts/skill_usefulness_audit_lib/`: collect metadata, score skills, scan static risk hints, and render Markdown/JSON tables.
- `references/scoring-rubric.md`: 10-point scoring rules, confidence logic, community prior, and action thresholds.
- `references/ablation-protocol.md`: normalized replay method for historical conversation tests.
