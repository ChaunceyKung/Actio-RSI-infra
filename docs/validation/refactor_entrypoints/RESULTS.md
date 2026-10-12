# R15–R18 验收结果

本轮最终 wheel `a6b326be5726ccb0987a3c7b23803c800bc343c897c0246a1ce9aec83733b465` 已完成产品验证；G1–G7 PASS，G8 等待 Git 提交、任务分支和 main 的远端 SHA 核对。

- 根层从实际基线 25 个跟踪文件收拢为 `__init__.py`、`__main__.py`、`README.md`；旧 19 个根 API 与 `evidence.failure_observation` 明确删除。
- 架构 checker v3 递归扫描 159 模块/634 边，模块 SCC=0、evidence 分组环=0、违规=0；两个原漏检和根白名单反例均被拒绝。
- 同一 wheel 的 34 suites、169/169 方法通过，无 skip；原 165 方法全部保留，新增 4 个入口/边界测试。收据记录实际 collected/executed IDs 精确相等。
- 555 向量完整 JSON 相等；固定 C2/C3/C4/C5 reader 与 1,048 历史文件按对应 Git 版本核对；资源五份原字节不变，当前 wheel/安装/暂存产品文件逐字节一致。
- 正式本机 C5 仅 loopback：12 sends、5 settled、7 unknown、6 not_run；独立 Ledger/entry 重算 PASS，12 Worker、9 服务/端口清理，credential reads=0、external requests=0。

开发回归接收 295，正式矩阵另计 12；废弃 wheel 的失败和修复收据保留在 `failures-and-retests.json`，没有混入最终分母。历史 R11–R14 的 INCOMPLETE 结果不改写；实验仍停在 C5，C4=INCOMPLETE、C1=infrastructure_failure、research=UNESTABLISHED、activation=false。
