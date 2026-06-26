# Changelog

## 0.3.5

- Preserve CJK skill names during skill identity normalization
- Parse simple block-list frontmatter without PyYAML in fallback environments
- Compact zh-CN Decision Summary output to five rows per group with Chinese punctuation
- Keep the OpenClaw bundle synced from source after the minimal audit fixes

## 0.3.4

- Clarify trigger boundaries for installed skill usage analysis and structure-only skill inventory requests
- Add a prompt-matrix regression test covering trigger, non-trigger, and boundary scenarios

## 0.3.3

- Add a front-of-report Decision Summary so humans see keep, observe, review, removal, and install-gate buckets before evidence tables
- Add `--report-language` for English and Simplified Chinese Markdown reports while keeping JSON, action codes, and risk flags stable
- Make raw JSON output opt-in in the docs and skill workflow; default user-facing output is Markdown plus conversational follow-up
- Add a short report narration prompt so agents can summarize audit results without pasting raw JSON or full tables by default
- Keep default English Markdown and JSON outputs backward-compatible under the same inputs

## 0.3.2

- Keep medium-risk skills in risk review even when local evidence confidence is low
- Make the cost-efficient ablation plan opt-in through `--ablation-plan-out` instead of adding it to default reports
- Trim runtime skill instructions below the self-audit prompt-bloat threshold
- Use sandbox-friendly test temp directories for local Windows validation

## 0.3.1

- Avoid double-counting Python subprocess calls across regex and AST risk checks
- Promote bundled credential-like content into risk review instead of only quality burden
- Cap broken script/tool skills below keep tier when syntax errors or high failure rates are present
- Show `insufficient-evidence` verdict for low-confidence low-score skills instead of a delete-looking verdict
- Read each risk-scanned file once per pass

## 0.3.0

- Add `--version` and `--strict-inputs` CLI guards for safer local runs
- Show searched roots and expected `SKILL.md` layout when no skills are found
- Narrow skill routing copy to installed agent-skill package cleanup, not code review or human skills
- Add Safe First Run, ablation boundary, usage sample, privacy, and missing-env caveats to README/SKILL docs

## 0.2.18

- 跳过无负面信号的 clean keep 技能，不再把它们写入 ablation 计划
- 无调用且缺少 ablation 证据的 general skill 使用低证据 impact 分，避免中性分掩盖未验证状态；已有真实使用记录的技能保持中性兼容
- quality burden 上限提升到 2.5，并在 Markdown 报告中展示 uncapped penalty
- OpenClaw/ClawHub 发布包不再包含 Codex 专用 `agents/` 配置
- README 和 scoring rubric 补充 action/verdict/risk 语义与 quality penalty 范围说明

## 0.2.17

- 恢复 MIT-0 license 文件，并将同一 license 文件纳入 ClawHub/OpenClaw 发布包

## 0.2.16

- 修复 readiness required-env 解析边界，raw frontmatter 顶层 `ENV` / `API_KEYS` / `SECRETS` 等普通元数据不再被误当作必需环境变量
- 支持显式 required env 中的 camelCase key/token/secret 名称，同时保持 dict key 扫描保守，避免把 `skillKey` 等元数据当环境变量
- 修复 object 形式 required env 中 `name` 展示名遮蔽 `env` / `envVar` / `variable` 的漏检问题，并保留 `name` 直接声明变量名的兼容
- 增加 12 个 readiness 边界样例回归，覆盖 false positive、camelCase、object schema 与 name-only 兼容

## 0.2.15

- 收窄安装身份去重，只用 ClawHub `_meta.json` 和 OpenClaw `skillKey` 等强身份去重，避免同名但不同用途的 OpenClaw 手装 skill 被误合并
- 识别 metadata / `_meta.json` 中声明的 required env、API key、secret 变量，缺失时作为 `missing-required-env` readiness 负担写入报告
- 增加同名 OpenClaw 变体、缺失 API key、已配置 API key、描述含 API 但未声明 env、registry metadata requires 的回归测试

## 0.2.14

- 读取 ClawHub `_meta.json` 与 OpenClaw frontmatter metadata，保留 skillKey、requires、version、owner 等安装身份信息
- 修复同一 skill 在多个 root 或源码/发布包双形态下重复进入排名、overlap 和消融候选的问题
- 增加带 usage、recent calls、false triggers 与 ablation 的发布前烟测回归，覆盖 OpenClaw 适配去重场景

## 0.2.13

- 精简运行时 skill 说明，减少自审时的文档负担
- 给 scoring 与 ablation reference 补充目录，避免长 reference 被标记为缺少导览
- 报告增加面向用户的 `action_advice`，让推荐动作更直白
- 改进 ClawHub 发布包同步逻辑，降低后续代码调整时的同步脆弱性
- 增加伪技能回归测试，覆盖无用重复技能、过长 description、坏 Python 脚本和混乱 reference

## 0.2.12

- 新增轻量安装入口、Python 调用关系和私密内容提示，不扩展破坏性命令字面规则
- Markdown 与 JSON 报告增加风险复核说明，帮助人工判断风险信号
- 增加旧版对比样本验证，确认新版不把冗长或安慰剂类 skill 误判为执行风险
- 保持 ClawHub 发布包为 OpenClaw 特化版本，其他 agent 只在 GitHub 仓库说明中维护

## 0.2.11

- 增加 OpenClaw、Hermes、Claude Code 的 skill metadata 与安装说明
- 默认扫描位置扩展到常见的 Codex、OpenClaw、Hermes、Claude Code skill 目录
- 修复多行 frontmatter description、Python 缓存文件计数和自审风险误报问题

## 0.2.10

- 将 ClawHub 发布包特化为 OpenClaw 入口，使用单行 frontmatter、OpenClaw metadata 与手动触发标记
- 在 ClawHub 包说明中标注其他 agent 版本请访问 GitHub 仓库

## 0.2.9

- 将静态风险检测签名从带 shebang 的 `constants.py` 中拆出，按执行、敏感路径、网络、编码风险分组
- 保留原有风险规则行为，同时降低 ClawHub 静态扫描将检测规则误判为外传脚本的概率

## 0.2.8

- 将审计入口拆成模块化包，保留原 CLI wrapper 和参数兼容
- 修复 history fallback 把文本提及计入真实 `calls` 的问题，新增 `history_mentions` 与 `suspected_invocations` 弱证据字段
- 用 YAML parser 处理发布包 frontmatter，并为同步脚本新增路径护栏与 `--dry-run`
- 新增 `static_risk_level`、`static_risk_flags` 等兼容字段，强调风险扫描是静态提示而不是安全证明
- 更新文档，明确 `delete`、`merge-delete`、`quarantine-review` 都是人工复核建议

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
