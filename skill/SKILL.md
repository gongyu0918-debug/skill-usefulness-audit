---
name: skill-usefulness-audit
slug: skill-usefulness-audit
description: Audit whether installed skills still create real value. 审计已安装 skill 是否还有真实价值。Use only when the user explicitly asks to review, score, rank, consolidate, or delete installed skills across Codex, OpenClaw, Claude Code, or similar agent hosts. 当用户明确要求审查、评分、排序、合并或删除已安装 skill 时使用。This skill checks call frequency, loads installed skill instructions, detects functional overlap, runs ablation on history for non-API and non-tool skills, then outputs a 10-point score table, evidence, and deletion recommendations. 它会检查调用次数、读取已装 skill 说明、识别功能重叠、对非 API 与非工具型 skill 跑历史消融，并输出 10 分制评分表、判定依据和删除建议。
version: 0.1.1
tags: [audit, skills, ablation, codex, openclaw]
homepage: https://github.com/gongyu0918-debug/skill-usefulness-audit
---
# Skill Usefulness Audit

## Overview

Use this skill to judge whether installed skills still deserve to stay installed.
It turns vague "this feels useless" opinions into a repeatable audit based on usage, overlap, and outcome impact.

用这个 skill 判断哪些已安装 skill 还值得保留。
它把“感觉没用”变成可复现的审计流程，基于调用频率、功能重叠和结果影响来判断。

## Manual Trigger Only

Run this skill only after a direct user request.
Do not invoke it implicitly during normal task execution.

只在用户手动要求时运行。
正常任务执行过程中不要隐式触发。

## Audit Scope

Audit these layers in order:

1. Call count or invocation evidence.
2. Installed skill metadata and instructions.
3. Functional overlap across skills.
4. Ablation impact on historical conversations for non-API and non-tool skills.

Treat API and tool skills as protected capability skills during ablation.
Examples: Excel, DOCX, PDF, browser automation, deployment, OCR, external API wrappers, MCP/API gateway helpers.

按这个顺序审计：

1. 调用次数或调用证据
2. 已安装 skill 的元数据与说明
3. skill 之间的功能重叠
4. 非 API、非工具型 skill 在历史对话上的消融影响

在消融阶段，把 API skill 和工具型 skill 当作受保护能力。
例如：Excel、DOCX、PDF、浏览器自动化、部署、OCR、外部 API 包装器、MCP/API 网关类 skill。

## Workflow

1. Collect installed skills.
   Search user-provided roots first.
   Fallback to host-local roots such as `./skills`, `$CODEX_HOME/skills`, or `~/.codex/skills`.
2. Collect usage evidence.
   Prefer native counters, logs, or telemetry.
   Fallback to transcript mentions only when native counts are unavailable.
3. Read every installed `SKILL.md`.
   Extract `name`, `description`, headings, scripts, references, and source path.
4. Classify each skill.
   Use `api`, `tool`, or `general`.
   Use the protected path for `api` and `tool`.
5. Detect overlap.
   Compare descriptions, headings, and resource names.
   Keep the top overlap peer and similarity score for each skill.
6. Run ablation for every `general` skill.
   Use fresh runs or isolated threads when the host supports them.
   Replay representative historical prompts with the target skill enabled and disabled.
7. Score every skill on a 10-point scale.
   Read `references/scoring-rubric.md`.
8. Produce the final report as tables.
   Include a full ranking table, a deletion-candidate table, and a short evidence note for each skill.

## Ablation Rules

Read `references/ablation-protocol.md` before running ablation.

For each eligible skill:

- Sample historical tasks where that skill plausibly matters.
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
  --markdown-out ./skill-audit-report.md \
  --json-out ./skill-audit-report.json
```

Input contracts:

- `--usage-file`: JSON, JSONL, CSV, or TSV with per-skill invocation counts.
- `--history-file`: raw transcript export used only when direct usage counts are weak or missing.
- `--ablation-file`: normalized JSON or JSONL with skill-on versus skill-off case results.

Run without extra files only when you need a structure-only audit.
Call counts and ablation impact become lower-confidence in that mode.

## Output Contract

Always return these tables:

1. Full score table with:
   `rank`, `skill`, `source`, `kind`, `calls`, `usage`, `uniqueness`, `impact`, `total`, `verdict`, `basis`
2. Deletion or merge candidates with:
   `skill`, `total`, `kind`, `trigger`, `reason`
3. Missing-evidence table when usage or ablation data is incomplete.

Keep deletion advice conservative for system or host-core skills.
Recommend narrowing or merging before deletion when two high-overlap skills still serve distinct host integrations.

## Resources

- `scripts/skill_usefulness_audit.py`: collect metadata, score skills, and render Markdown/JSON tables.
- `references/scoring-rubric.md`: 10-point scoring rules and delete thresholds.
- `references/ablation-protocol.md`: normalized replay method for historical conversation tests.
