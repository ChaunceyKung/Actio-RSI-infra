# 模块化重构验收

状态：INCOMPLETE（实施及回归进行中）。不能把已提取的纯模块和fixture适配器视为整个九层架构完成。

基线 main：6ba6573，C5产品：c5aeec2。产品、测试、工具、历史摘要见 baseline.json。
当前已提取 contracts、domain 的候选/namespace/计账、tasks、独立 measurement、filesystem、SQLite Ledger、正式loopback fixture；保留现有CLI/IPC。无数据库schema变化。Store及campaign/profile/evidence/application的整体拆分尚未完成，AST报告保留全部循环，不设忽略白名单。

本机开发回归持续记录在 D:/ar-mod-20261011。真实provider/目录GET/外部MCP为0。已有历史真实172/GET1不变。

已有555项纯向量与C5完全相同；固定C2/C3/C4 reader及19 claims PASS；原C5固定reader认证及最终诊断离线重算PASS，不等于新wheel实测。新正式矩阵尚待当前冻结提交后运行。

开发失败保留：最小wheel的CLI过早导入MCP（已延迟导入）；setuptools旧build/lib残留（新建构建源码副本）；源身份表引用已删除私有模块（改为完整当前闭包）；旧v3 PROFILE局部遮蔽（修复）；评估可选依赖遗漏（按原锁离线安装）。priced rehearsal原报价在2026-10-10T16:00Z到期，当前系统时间正确拒绝发送，未更新旧报价或放宽断言。

G1/G7尚未通过，整体不得标PASS。正式矩阵和最终结论随后追加。
