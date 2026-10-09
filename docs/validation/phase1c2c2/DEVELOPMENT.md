# C2C2 开发与验收记录

全部本机执行都使用 literal loopback、内存 fake credential、官方 DSH/Concordia；没有为调试额外调用真实 provider。正式 live 仅使用已发布冻结的唯一计划与独立 claim。

| 快照 / 尝试 | 结果与范围 |
|---|---|
| 初版纯测试及单 episode 接线 | 2 项纯测试及 2 次本机 seat 发送通过 |
| 初版完整矩阵 | 24 episodes、47 sends，非法 A 导致 1 个 B 正确跳过；unknown=0；保留该源码快照的记录，不当作最终源码验收 |
| 加入固定旧谱系 hash、细分 domain 指标及依法拒绝解释 | 重新安装后 4 项 runtime 测试通过：完整矩阵、unknown 停止、controller/verifier 同时失败；共 50 次本机发送，含 1 次故意 unknown |
| 受限公开 CLI 探针 | 发现 argparse 的 gettext 会读取 locale 环境变量；在 guard 下失败。记录为 evidence/cli-development-failure.json。辅助探针最初的 stderr 解码也失败，加入明确 UTF-8 后定位；均无 Worker/发送 |
| CLI 修正后的最终源码 | 3 项新纯测试、4 项 runtime 测试通过；完整矩阵 24/47，unknown 停止与无发送 controller 故障分开记录。另 13 项受影响 suite/pilot 纯回归通过 |
| 旧 candidate 纯回归 | 前一源码快照的 5 项通过；不标为最终 implementation 的全量回归。通道代码未再改变，最终新模式 runtime 与原边界证据共同保留 |
| prepare 提前调用 | 在完整 CLI 成功记录尚不存在时按准入条件退出，未生成冻结计划；CLI 通过后重新运行成功 |
| 最终公开 CLI / 完整导出 | 6 个实际命令、禁止 key/env/network/process/runtime import/write 的完整 delivery 核验、4 种重新 seal 的篡改拒绝全部通过 |
| 固定历史 reader | C0/C1/C2A.1/C2B0/C2B1 固定注册表通过；C2B2/C2C0/C2C1 原报告精确重现 |

发布前本机总计 149 sent、147 usage、2 unknown；149 个具名 Job inactive/reaped、8 个本机服务 joined、活动 authorized/reserved/sending=0。它们不进入 live 分母。详细 source hashes、实际 argv、每次根目录、账本、服务端口、数据库及原始归档 hashes 见 evidence 中测试记录和 census-05fc01650693.json。

重复完整矩阵是因为旧谱系来源、指标字段和 CLI 修正改变了严格 source-bound plan hash；原记录均保留，没有改 ID 伪装成新证据。最终 local-acceptance 只认可匹配冻结 implementation 的测试。沿用 C2C0 的 31 秒期限历史证据，未改期限传递，也未重复旧慢期限 suite。

静态 bad proposal/未知 parent/事务失败测试属于合成校验；本轮没有真实 C2 或其他候选。完整本机矩阵故意包含行为错误，得到 engineering PASS 和 candidate reject，是分类验收而非 C1 真实性能结论。只有随后独立执行的 live 结果进入本轮真实评估。
