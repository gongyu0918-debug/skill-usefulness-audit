# skill-usefulness-audit

手动触发的 skill 审计器。

它做三件事：

1. 统计已安装 skill 的调用次数
2. 读取所有 skill 说明，检查功能重叠
3. 对非 API、非工具型 skill 跑历史对话消融测试，判断有没有真实增益

最终输出 10 分制评分表、判定依据、删除或合并建议。

## 目录

- `codex-skill/`: 运行时 skill 源文件
- `skill/`: ClawHub 发布包
- `tests/`: 稳定性与可用性测试
- `scripts/sync_bundle.py`: 从 `codex-skill/` 同步生成 `skill/`

## 本地验证

```bash
python scripts/sync_bundle.py
python -m unittest discover -s tests -v
python codex-skill/scripts/skill_usefulness_audit.py audit --skills-root codex-skill --markdown-out test-output/report.md --json-out test-output/report.json
```

## 发布

先同步 bundle：

```bash
python scripts/sync_bundle.py
```

发布到 ClawHub：

```bash
clawhub publish ./skill --slug skill-usefulness-audit --name "skill-usefulness-audit" --version 0.1.0 --tags latest,audit,skills --changelog "Initial release"
```
