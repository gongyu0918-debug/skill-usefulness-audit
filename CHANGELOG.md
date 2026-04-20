# Changelog

## 0.2.0

- 调用证据升级为近期使用模型，支持 `recent_30d_calls`、`recent_90d_calls`、`last_used_at`、`active_days`
- 新增 `confidence_score`，把 usage 来源、近期字段、ablation 覆盖、community 元数据纳入证据完整度
- 新增离线 `--community-file` 输入，支持本地 JSON、JSONL、CSV、TSV 社区指标
- 新增静态风险扫描，输出 `risk_level`、`risk_flags`、`action`
- Markdown 与 JSON 报告增加 `community / confidence / risk / action` 字段

## 0.1.1

- 扩展输入兼容层，支持更多 usage、history、ablation 导出形态
- 增加中文字段别名与中英文 verdict 兼容
- 支持从嵌套对话 JSON 里提取文本并做历史提及统计
- README、运行时 SKILL、ClawHub 发布包改为中英双语介绍

## 0.1.0

- 初始发布
- 支持按调用次数、功能重叠、消融影响三维度为 skill 打分
- 支持 Markdown 与 JSON 报告输出
- 支持 ClawHub 发布包同步
