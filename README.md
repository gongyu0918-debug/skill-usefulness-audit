# skill-usefulness-audit

手动触发的 skill 审计器。
Manual-triggered skill auditor for installed agent skills.

它现在做六件事：

1. 读取使用证据，并优先看近期调用
2. 给不同证据来源加权，区分原生日志和历史提及
3. 读取所有已安装 skill 说明，检查功能重叠
4. 对非 API、非工具型 skill 读取历史消融结果
5. 扫描风险与健康信号
6. 读取可选的离线 community 指标

最终输出 10 分制本地评分、`confidence_score`、`community_prior_score`、`risk_level`、`action`，以及删除或合并建议。

It now does six things:

1. Read usage evidence with recency fields
2. Weight evidence sources differently for native logs and transcript fallback
3. Read installed skill manifests and detect overlap
4. Read history-based ablation results for non-API and non-tool skills
5. Scan static risk and health signals
6. Read optional offline community metrics

It outputs a 10-point local score plus `confidence_score`, `community_prior_score`, `risk_level`, `action`, and delete or merge recommendations.

## 目录

- `codex-skill/`: 运行时 skill 源文件
- `skill/`: ClawHub 发布包
- `tests/`: 稳定性与兼容性测试
- `scripts/sync_bundle.py`: 从 `codex-skill/` 同步生成 `skill/`

## Layout

- `codex-skill/`: runtime skill source
- `skill/`: ClawHub publish bundle
- `tests/`: stability and compatibility tests
- `scripts/sync_bundle.py`: sync `codex-skill/` into `skill/`

## 本地验证

```bash
python scripts/sync_bundle.py
python -m unittest discover -s tests -v
python codex-skill/scripts/skill_usefulness_audit.py audit \
  --skills-root codex-skill \
  --community-file test-output/community.json \
  --markdown-out test-output/report.md \
  --json-out test-output/report.json
```

## Local Validation

```bash
python scripts/sync_bundle.py
python -m unittest discover -s tests -v
python codex-skill/scripts/skill_usefulness_audit.py audit \
  --skills-root codex-skill \
  --community-file test-output/community.json \
  --markdown-out test-output/report.md \
  --json-out test-output/report.json
```

## 兼容性

当前兼容这些输入形态：

- `usage`: JSON、JSONL、CSV、TSV，支持 `calls / recent_30d_calls / recent_90d_calls / last_used_at / active_days` 及中英文字段别名
- `history`: 纯文本、JSON、JSONL、嵌套 `content/parts/messages` 结构
- `ablation`: 列表、`cases/results/items/data` 容器、英文与中文 verdict 字段
- `community`: JSON、JSONL、CSV、TSV，本地离线 registry 指标

## Compatibility

Current compatibility surface:

- `usage`: JSON, JSONL, CSV, TSV with `calls / recent_30d_calls / recent_90d_calls / last_used_at / active_days` and Chinese aliases
- `history`: plain text, JSON, JSONL, nested `content/parts/messages` exports
- `ablation`: list payloads, `cases/results/items/data` containers, English and Chinese verdict labels
- `community`: JSON, JSONL, CSV, TSV offline registry metrics

## 发布

先同步 bundle：

```bash
python scripts/sync_bundle.py
```

发布到 ClawHub：

```bash
clawhub publish ./skill --slug skill-usefulness-audit --name "skill-usefulness-audit" --version 0.2.0 --tags latest,audit,skills --changelog "Recency-weighted evidence, confidence score, risk scan, and offline community metrics"
```

## Publish

Sync the bundle first:

```bash
python scripts/sync_bundle.py
```

Publish to ClawHub:

```bash
clawhub publish ./skill --slug skill-usefulness-audit --name "skill-usefulness-audit" --version 0.2.0 --tags latest,audit,skills --changelog "Recency-weighted evidence, confidence score, risk scan, and offline community metrics"
```
