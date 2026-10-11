# 工程 Gate

**G1–G8 PASS**；产品提交已普通推送两分支并分别核对远端 SHA，见 completion/publication.json。

| Gate | 状态 | 当前证据 |
|---|---|---|
| G1 架构 | PASS | completion/architecture.json；SCC/root/violations均0；原检查器字节未改；应用、证据、validator新增依赖断言 |
| G2 差分 | PASS | completion/differential.json；555完整JSON一致 |
| G3 状态 | PASS | 最终state27、budget4、readiness6及全量竞争/receipt/usage/unknown断言通过 |
| G4 打包 | PASS | completion/installation-and-history.json与packaging.json；pip check、资源、4 console/module、minimal reader；TS child IPC在正式矩阵实测 |
| G5 历史 | PASS | 1048文件保全、固定reader、19claims；history-b78111dcff0b.json与runtime-recomputed-7f0cbe404cc2.json |
| G6 本机 | PASS | completion/formal-report.json、formal-cleanup.json、formal-scan.json；12/5/7/6，12Worker/9服务清理；官方runtime2项通过 |
| G7 回归 | PASS | completion/regression.json；34suite、164唯一方法通过；同wheel，failures6项原条件及candidate_runtime3项导入修复后隔离复核；首次超时不抹除 |
| G8 交付 | PASS | completion/publication.json；两分支普通推送、main快进、独立ls-remote核对一致；后续仅文档收据更新 |

旧实验与失败保持原结论；工程PASS也不代表研究成立或激活许可。真实key读取0，exact-secret比较NOT_RUN；不把模式扫描写成精确密钥比对。
