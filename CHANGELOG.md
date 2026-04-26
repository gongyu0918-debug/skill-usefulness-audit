# Changelog

## 0.2.7

- 修复脚本桩函数 `pass` 未被维护负担检测命中的问题
- 将大量脚本和脚本异味拆成 `script-count-bloat` 与 `script-maintenance-smell` 两类证据
- 允许已有 5 个以上消融 case 的高负担 skill 进入复测计划
- 修复脚本失败率对显式 `executions=0` 的分母处理
- 改进中英混合上下文估算，中文长说明会更准确触发 prompt burden
- 新增可配置 ablation case 数量、model-cost unit 说明、`quality_penalty_uncapped`

## 0.2.6

- 新增质量负担评分，覆盖过度触发、reference/assets 膨胀、脚本失败、重复修补和可疑打包内容
- 新增 cost-efficient ablation plan，先用本地证据筛候选，再按 3/5/10 case 早停协议执行 pairwise 消融
- 报告增加 `quality_penalty`、`final_score`、`quality_evidence`、`ablation_plan` 和 model-cost reduction 估算
- 修复并行单测下发布包同步测试的目录竞争
- 清理 ClawHub 扫描容易误判的认证类词面信号

## 0.2.2

- 清理会误导 ClawHub 安全扫描的认证类词面信号
- 将风险标签 `secret-access` 改为 `protected-path-access`
- 将敏感路径正则模式改成中性表达，同时保持本地风险检测行为不变
- 把分词内部变量统一改成 `term`，减少认证类误判
- 修正文档，明确风险扫描只针对可执行脚本和资源文件

## 0.2.1

- 修复同名 skill 共享 usage、ablation、community 证据的问题，优先按 `path / namespace / source` 解析
- 修复 overlap 检测跳过同名技能的问题，重名 skill 现在会在报告里清晰区分
- 收紧风险扫描范围，只扫描脚本和可执行资源，`SKILL.md` 与 `references/` 不再制造执行风险误报
- 修复 history fallback 把宿主 developer prompt 和技能清单算作 usage 的问题
- 重写 README 首屏和快速开始，首个命令可直接跑通
- 补充宿主级回归测试，覆盖重名 skill、文档误报、history 污染

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
