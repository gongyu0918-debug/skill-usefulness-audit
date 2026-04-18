# skill-usefulness-audit

手动触发的 skill 审计器。
Manual-triggered skill auditor for installed agent skills.

它做三件事：

1. 统计已安装 skill 的调用次数
2. 读取所有 skill 说明，检查功能重叠
3. 对非 API、非工具型 skill 跑历史对话消融测试，判断有没有真实增益

最终输出 10 分制评分表、判定依据、删除或合并建议。

It does three things:

1. Count installed skill usage
2. Read installed skill manifests and detect overlap
3. Run history-based ablation for non-API and non-tool skills to measure real impact

It outputs a 10-point score table, evidence, and delete or merge recommendations.

## 目录

- `codex-skill/`: 运行时 skill 源文件
- `skill/`: ClawHub 发布包
- `tests/`: 稳定性与可用性测试
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
python codex-skill/scripts/skill_usefulness_audit.py audit --skills-root codex-skill --markdown-out test-output/report.md --json-out test-output/report.json
```

## Local Validation

```bash
python scripts/sync_bundle.py
python -m unittest discover -s tests -v
python codex-skill/scripts/skill_usefulness_audit.py audit --skills-root codex-skill --markdown-out test-output/report.md --json-out test-output/report.json
```

## 兼容性

当前兼容这些输入形态：

- `usage`: JSON、JSONL、CSV、TSV
- `history`: 纯文本、JSON、JSONL、嵌套 `content/parts/messages` 结构
- `ablation`: 列表、`cases/results/items/data` 容器、英文与中文 verdict 字段

## Compatibility

Current compatibility surface:

- `usage`: JSON, JSONL, CSV, TSV
- `history`: plain text, JSON, JSONL, nested `content/parts/messages` exports
- `ablation`: list payloads, `cases/results/items/data` containers, English and Chinese verdict labels

## 发布

先同步 bundle：

```bash
python scripts/sync_bundle.py
```

发布到 ClawHub：

```bash
clawhub publish ./skill --slug skill-usefulness-audit --name "skill-usefulness-audit" --version 0.1.0 --tags latest,audit,skills --changelog "Initial release"
```

## Publish

Sync the bundle first:

```bash
python scripts/sync_bundle.py
```

Publish to ClawHub:

```bash
clawhub publish ./skill --slug skill-usefulness-audit --name "skill-usefulness-audit" --version 0.1.1 --tags latest,audit,skills --changelog "Compatibility expansion and bilingual introduction"
```
