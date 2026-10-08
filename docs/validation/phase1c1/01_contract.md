# Phase 1C1 冻结合同

基线 C0 `1e85d8c2fb4a756de81acb333905190df9e97592`；远端交接 `4f942fd77fbaf382de2b93a6016a384206fb249e`。任务分支 phase1c1-task-contract-and-calibration。用户本轮明确要求最终发布到 main，优先于 Prompt 的默认不合并约定：验收后普通推送任务分支，再快进发布 main 并核对两个 SHA；禁止强推。预算 0，所有模型/judge/embedding/训练调用 0。

一个 authored synthetic 两人共同排程任务族，两个卡：可达成和约束冲突。A 提出 morning/afternoon，B 看见真实公开提议后 accept/decline。合法不等于达成：只有 accept 且提议时间在双方冻结可用集合内才成功；非法行动在该行动的 world 效果前拒绝，基础设施中断保留 partial。两个卡均开发组，无独立研究单位/holdout。

TaskSpec v1 含 task/family/variant、CC0 authored 来源、公用情境、绑定 seat/agent/spec、私有可用时间/偏好/目标、初始关系、完整 ActionSpec、顺序/seed/终止/判据、memory scope、可见性、工程分组。先校验再 begin；TaskSpec hash 与冻结私有自我 view、公用历史一并绑定每步 dispatch/native。fixture 输出脚本独立存 manifest，不进入 judge/标注 view。新合同独立分派，旧 fixture-input v1/v2 规则不放宽，不增 DB schema。

继续使用现有 RuntimePort 和真实 Concordia Sequential/Entity/ActionSpec，扩展 adapter，不新增 solver/scheduler。Engine 每步向两人 observe；第二 actor 收到初始观察及第一步后的公开行动观察。在线 seal/离线 verifier 共用 task 语义与世界结果规则，校验冻结 TaskSpec→观察→dispatch→native→receipt/world→terminal。

新版本 EvalSpec 仍精确锁源码；原 C0 12 记录用固定提交的受控源码副本/旧环境离线复核，新实现明确 unsupported old pins。新 task judge view 按明确 metric grant 读取冻结 goals/关系和必要约束；旧 social 不补目标。goal 0..10、relationship -5..5 仅 preset 结构检查，新 anchors 明确未校准。

新增只读 campaign 验证入口，封存 dataset/source/spec/record/view/alias、family→group、完整文件 inventory 和状态计数；执行与验证分离，重复请求保留登记但不重复测量，historical 文件显式列出且排除当前分母。记录 task card / episode / repeat / replay / baseline arm / evaluation request，不以 run UUID 切 split。

标注包输出盲化 Markdown/JSONL 与空模板，稳定匿名 seat；不包含 provider/model/candidate/arm、历史 scores、fixture script 或期望任务结果。内部绑定 task/trace/rubric/view/alias/group。导入拒绝错版本/重复冲突，缺标报告 insufficient，synthetic_label_fixture 不当 human gold。真实人工校准 BLOCKED。

只读 provider preflight 永远 BLOCKED（含正预算）；无网络 transport、凭据读取或 client/Worker 创建。给出未来分项预算与 pilot 草案，不报价、不授权支出。研究效度/演化晋升 BLOCKED。保留所有历史及本轮失败，最终 manifest 绑定实际源码/安装包、命令、raw archive、Job 清理和分层 Gate。
