# 后续 pilot 预注册草案（非授权）

当前 live provider **BLOCKED**，预算与请求为 0。配置模板在 [pilot-config.json](pilot-config.json)，执行 `python -m actio.preflight <config>` 始终退出 2。即使所有字段非空且预算正数，也只可能 configuration_valid=true，provider_compatibility=UNVERIFIED、live_ready=false。当前模块没有 transport、密钥读取、provider SDK、客户端创建或 Worker 启动路径。

未来启用前逐项确认 solver / GM / judge 的 provider、精确模型版本、采样参数、工具权限、发送字段范围、独立进程和上下文，以及 judge 与 solver 的依赖关系。GM 若继续确定性运行，应明确不调用模型；不要为通过检查而伪造预算。当前 preflight 只是准备性合同，真实启用仍需独立实现与审核。judge 同一模型的不同上下文不代表统计独立判断。

| 调用类别 | 本轮上限 calls / tokens / cost | 未来待确认 |
|---|---|---|
| solver | 0 / 0 / 0 | 每行动计数、输入输出 token 合计、精确价格版本 |
| GM | 0 / 0 / 0 | 继续确定性或独立模型；发送范围 |
| judge | 0 / 0 / 0 | 每 episode/维度的请求数；独立上下文及依赖关系 |
| retries | 0 / 0 / 0 | 独立预算，失败也计费入账；默认禁止自动重试 |
| other | 0 / 0 / 0 | embedding、工具、训练等当前均禁用 |

不包含 secret。价格未知时 currency/quote 保持 null，报价待人工确认，不填当前市场价格猜测。授权使用可审计的批准引用，不以环境登录态或已有 key 代替。账本归属、token 统计和实际账单偏差的处理均待确认。

建议第一批仅在人工校准及费用授权后，使用 **6 个新增、独立来源且经审核的任务族 × 2 个任务卡 × 2 次重复**，共 24 个工程试运行 episode，用于发现接口、延迟、成本和缺失模式。当前这一已公开 family 不算新增独立单位。两次重复只用于测量随机波动，不新增研究单位；可根据费用先缩为 2 个 family 作连接检查，但它不提供效度推断。

后续 pilot 默认仅 baseline。预先冻结 family 分组与 seat 置换规则、固定 seeds、每个登记 unit、预期缺失及停止规则。公开/作者已见内容只进入 development；独立、未见且许可明确的内容才可能成为未来 holdout，需另行治理，不在本轮宣称。

以全部登记调用为工程失败率分母，区分 admission 拒绝、基础设施失败、task failure、measurement invalid/error/timeout；报告 attempted 和 not_run 分母，不丢失败。任何未授权发送、预算任一上限耗尽、账本不一致、source/spec 失配立即停止；连续 3 个基础设施失败暂停人工审阅。停止阈值为草案，需在调用前冻结。

两名独立人工标注者按 [指南](05_annotation.md) 标注，维度分别统计。pilot 完成后依据真实缺失率、成本、family 内相关、目标最小效应与人类一致性决定正式样本量；不依据 preset 的“高分”选卡。当前不报告效应、显著性、相关系数或所需研究样本量的实测估计。
