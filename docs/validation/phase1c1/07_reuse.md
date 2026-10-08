# SOTOPIA 窄复用核对

只读本地固定 checkout 与 GitHub 原始内容在 `a0aaafb440e570e5e61b7c44a44e5e417c545383` 核对。[实际 URL、原始与规范化 hash、许可证据](evidence/reuse.json) 由 [核对脚本](../../../scripts/phase1c1_reuse.py) 生成；CRLF/LF 规范化差异单独记录。未 pull 参考仓库，未下载数据集。

采用 persistent_profile.py 的 scenario、agent_goals、relationship / background_story 合同语义，在本地转为公共情境、各 seat 冻结目标/约束、初始关系/背景；新增严格 TaskSpec、可见性、真实行为结果与来源绑定。上游 profile 是存储/平台模型，不直接作运行时事实权威，也不引入 Redis。

继续使用 C0 已按固定源码提取的实际 parser/schema，许可证和 provenance 保留在 src/actio/_vendor；严格原始 envelope 仍先于上游解析器，防止修复/coercion 把非法原始结果变成合法分数。完整 SOTOPIA 平台和完整 evaluator 未采用，C0 episode 兼容性失败仍保留。

代码 LICENSE 为 MIT（Hao Zhu 2023）；注册表中 SOTOPIA / SOTOPIA-pi 数据为 CC-BY-SA 4.0，agent_vs_script 数据另为 AI2 Impact License。不能从代码 MIT 推导数据许可。test_background.json 的 scenario=`<missing_info>`，并非可直接使用的完整任务。本轮未复制这些数据，而由 Actio 编写 cleanup-compatible / cleanup-conflict 两张 **Actio authored synthetic fixture / CC0-1.0** 任务卡。

这些卡只有两个时间槽和两步符号行动，没有上游 benchmark 的数据分布、丰富人设、真实对话或经校准的社会效度。新 goal/relationship anchors 为本轮任务专用、NOT_CALIBRATED，不能把复用 parser 等同复用上游评分效度。
