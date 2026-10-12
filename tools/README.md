# 维护工具

当前工具位于 `tools/refactor/`：architecture 扫描递归依赖、根白名单与 evidence 分组；entrypoints 检查迁移身份、原测试方法/断言和导航；validate 顺序运行34个套件，记录实际 collected/executed IDs。

build_wheel 从干净源码副本构建；completion 检查同一 wheel/安装/源码、根三文件、旧API不可用、唯一console、资源搬迁和1048历史文件；packaging 用独立 minimal 环境测试离线成功及拒绝路径；freeze/formal_review 对最终本机矩阵冻结及独立复算；summarize/cleanup 清点本轮测试发送和清理。

history/history_c5 的当前外层按新 API 调用，嵌入的固定历史 reader 保持旧地址。必须指定新的 --output，不能覆写旧证据。vectors 的显式源参数选择固定旧源码，无参数选择当前安装；完整 JSON 比较，不过滤业务差异。

[0.2 验收命令](../docs/validation/refactor_entrypoints/CLI.md) · [接口迁移](../docs/architecture/MIGRATION_0_2.md)。历史 scripts 冻结，不批量改写。原始 DB、回执、venv、wheel、大日志只留受控本机目录；Git仅发布摘要与hash。
