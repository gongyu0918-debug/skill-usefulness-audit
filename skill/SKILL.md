---
name: skill-usefulness-audit
slug: skill-usefulness-audit
description: Audit or inventory installed agent-skill packages for cleanup using usage, overlap, burden, risk, and optional ablation/community evidence. Trigger only on explicit requests to review installed agent skills, analyze installed skill usage, or run a structure-only skill inventory; not for ordinary repository code review, general security audit, or human skills.
version: 0.3.4
tags: ["audit","skills","ablation","openclaw"]
user-invocable: true
disable-model-invocation: true
argument-hint: --skills-root PATH --usage-file FILE
homepage: https://github.com/gongyu0918-debug/skill-usefulness-audit
metadata: {"openclaw":{"skillKey":"skill-usefulness-audit","requires":{"bins":["python"]},"homepage":"https://github.com/gongyu0918-debug/skill-usefulness-audit"}}
---
# Skill Usefulness Audit

## ClawHub / OpenClaw Edition

This ClawHub bundle is packaged for OpenClaw. Install it from an OpenClaw workspace with:

```bash
openclaw skills install skill-usefulness-audit
```

OpenClaw picks up installed workspace skills in the next session. For other agent hosts, use the GitHub repository instead: https://github.com/gongyu0918-debug/skill-usefulness-audit

本 ClawHub 包是 OpenClaw 专用发布包。其他 agent 版本请访问 GitHub 仓库：https://github.com/gongyu0918-debug/skill-usefulness-audit


## Overview

Use this skill to judge whether installed agent skills still deserve to stay installed.
It turns vague "this feels useless" opinions into a repeatable audit based on usage evidence, overlap, outcome impact, quality burden, confidence, community prior, and static risk hints.

## Manual Trigger Only

Run this skill only after a direct user request.
Do not invoke it implicitly during normal task execution.
Do not use it for ordinary repository/source-code review, general security audit, employee skill assessment, or normal task execution.
Valid direct requests include installed agent skill cleanup, installed skill usage analysis, duplicate/overlap checks, and structure-only inventories of an agent skill library.

## Safety

Never delete or quarantine skills automatically.
Treat all `delete`, `merge-delete`, and `quarantine-review` results as manual-review recommendations.
Do not delete skills based only on a structure-only report.
This tool does not automatically replay historical conversations; it generates ablation plans and reads ablation result files that the user provides.

## Borrowed Idea Gate

When borrowing ideas from another skill, change one idea at a time.
Record the source idea, expected benefit, baseline command, ablation command, and rollback condition.
Keep the change only when the same input fixture improves or clarifies the target behavior without making unrelated skills stricter.

## Audit Scope

Audit these layers in order:

1. Usage evidence with recency and source quality.
2. Installed skill metadata and instructions.
3. Functional overlap across skills.
4. Ablation impact from user-provided skill-on versus skill-off results for non-API and non-tool skills.
5. Quality burden from over-triggering, context-heavy resources, weak progressive disclosure, redundant references/assets, weak scripts, or private-looking bundled files.
6. Static health and risk signals.
7. Optional offline community or registry metrics.

Treat API and tool skills as protected capability skills during ablation.
Examples: Excel, DOCX, PDF, browser automation, deployment, OCR, external API wrappers, MCP/API gateway helpers.

## Workflow

1. Collect installed skills from user-provided roots first, then host-local defaults.
2. Load usage, history, ablation, and community evidence when provided.
3. Read installed `SKILL.md` files plus script/reference/asset metrics.
4. Classify skills as `api`, `tool`, or `general`; protect `api` and `tool` skills from fake no-tool ablation.
5. Score usage, overlap, impact, quality burden, confidence, community prior, and static risk.
6. Render a Markdown report with conservative human-review actions.
7. Write a cost-efficient ablation plan only when `--ablation-plan-out` is provided.

## Ablation Rules

Read `references/ablation-protocol.md` before running ablation.
