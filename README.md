# skill-usefulness-audit

装的 skill 越多，清理就越容易靠感觉。

`skill-usefulness-audit` 会把每个 skill 的近期使用、功能重叠、消融收益、社区信号和执行风险放到一张表里，给出 `keep / review / merge-delete / quarantine-review` 建议。

`skill-usefulness-audit` audits installed skills with one goal: show which ones still earn their place. It combines local usage, overlap, ablation impact, offline community signals, and execution risk into one report.

## 适合谁

- 想清理挂载 skill，手里没有一份像样证据
- 想知道哪些 skill 只是功能重复
- 想把“本地常用”和“社区热门”分开看
- 想给团队留一份可复盘的技能盘点结果

## Who It Helps

- Teams cleaning up crowded skill lists
- Builders comparing overlapping skills
- People who want local evidence and registry signals side by side
- Anyone who wants an audit they can rerun and diff later

## 30 秒跑起来

```bash
python codex-skill/scripts/skill_usefulness_audit.py audit \
  --skills-root codex-skill \
  --markdown-out test-output/report.md \
  --json-out test-output/report.json
```

审计真实宿主里的技能时，直接把 `--skills-root` 指向你的 skill 目录。

```bash
python codex-skill/scripts/skill_usefulness_audit.py audit \
  --skills-root ~/.codex/skills \
  --markdown-out skill-audit-report.md \
  --json-out skill-audit-report.json
```

When auditing a real host, point `--skills-root` at the installed skill directories and keep the same output flags.

## 结果怎么看

- `local_score`: 本地 10 分主分，核心看 usage / overlap / impact
- `confidence_score`: 证据扎实程度
- `community_prior_score`: 离线社区先验，独立输出
- `risk_level`: 执行面风险，只看脚本和资源文件
- `action`: 最后建议动作

`history` 只是弱证据。原生日志最稳，历史对话只适合补位。

## Reading The Report

- `local_score`: main 10-point local score
- `confidence_score`: how strong the evidence is
- `community_prior_score`: optional offline registry signal
- `risk_level`: execution-surface risk from scripts and runnable resources
- `action`: keep, review, merge-delete, or quarantine-review

Native usage logs are stronger than transcript mentions. History fallback is there for partial evidence, not for final truth.

## 输入数据

支持这些输入：

- `usage`: JSON、JSONL、CSV、TSV，支持 `calls / recent_30d_calls / recent_90d_calls / last_used_at / active_days`
- `history`: 纯文本、JSON、JSONL，对话正文会过滤宿主注入提示
- `ablation`: JSON、JSONL，支持 `cases / results / items / data`
- `community`: JSON、JSONL、CSV、TSV，适合离线导出的 registry 指标

同名 skill 会优先按 `path / namespace / source` 解析。只给名字、又遇到重名时，这份证据会保守处理。

## Input Formats

Supported inputs:

- `usage`: JSON, JSONL, CSV, TSV
- `history`: plain text, JSON, JSONL
- `ablation`: JSON, JSONL
- `community`: JSON, JSONL, CSV, TSV

Duplicate skill names resolve through `path`, `namespace`, and `source` before falling back to name-only matching.

## 本地开发检查

```bash
python scripts/sync_bundle.py
python -m unittest discover -s tests -v
python codex-skill/scripts/skill_usefulness_audit.py audit \
  --skills-root codex-skill \
  --markdown-out test-output/report.md \
  --json-out test-output/report.json
```

## Local Dev Check

```bash
python scripts/sync_bundle.py
python -m unittest discover -s tests -v
python codex-skill/scripts/skill_usefulness_audit.py audit \
  --skills-root codex-skill \
  --markdown-out test-output/report.md \
  --json-out test-output/report.json
```

## 目录

- `codex-skill/`: 运行时 skill 源文件
- `skill/`: ClawHub 发布包
- `tests/`: 兼容性和回归测试
- `scripts/sync_bundle.py`: 从 `codex-skill/` 同步生成 `skill/`

## Layout

- `codex-skill/`: runtime skill source
- `skill/`: ClawHub publish bundle
- `tests/`: regression and compatibility tests
- `scripts/sync_bundle.py`: sync `codex-skill/` into `skill/`

## 发布

```bash
python scripts/sync_bundle.py
clawhub publish ./skill --slug skill-usefulness-audit --name "skill-usefulness-audit" --version 0.2.1 --tags latest,audit,skills --changelog "Fix duplicate-name evidence routing, doc-only risk false positives, host-prompt history inflation, and README quickstart"
```

## Publish

```bash
python scripts/sync_bundle.py
clawhub publish ./skill --slug skill-usefulness-audit --name "skill-usefulness-audit" --version 0.2.1 --tags latest,audit,skills --changelog "Fix duplicate-name evidence routing, doc-only risk false positives, host-prompt history inflation, and README quickstart"
```
