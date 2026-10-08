# 合成审计样例

五个精确导出目录来自本轮 `test_evidence` 的真实 DSH fixture 与真实 Concordia 场景。总 evidence 内容约 201 KiB，不含 DB、runtime、缓存或真实用户数据。ID/进程号/任务时间是这次合成运行的实际值；测试注入仅在 tests。

| 目录 | 预期核验 |
|---|---|
| assistant | valid / consistent / complete / success |
| social | valid / consistent / complete / success；含 A 的前序 memory 最小来源证明 |
| rejected | valid / consistent / complete / task_failure；非法 action 在 world 前拒绝 |
| partial | valid / partial / partial / infrastructure_failure；B 完成后 A 初始化失败 |
| unknown | valid / partial / partial / infrastructure_failure；真实 flush 后、canonical 导入前异常 |

从仓库根执行（安装后的 interpreter 可替换）：

```powershell
.local/phase1b1-delivery-venv/Scripts/python.exe -m actio.verify docs/validation/phase1b1/samples/social
.local/phase1b1-delivery-venv/Scripts/python.exe -m actio.verify docs/validation/phase1b1/samples/partial
```

目录可以复制到其他位置再核验。包是审计材料，包含必要的合成 private markers，不用于 agent 上下文。原始 native 字节未改写；所有 hash 可重新计算。核验脚本不跟随原生文本中出现的任务路径。
