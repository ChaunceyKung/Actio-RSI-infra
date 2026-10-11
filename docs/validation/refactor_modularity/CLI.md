# 本轮执行与重现

当前最终 wheel：`D:/ar-complete-20261011/final-wheel05/actio_rsi-0.1.0-py3-none-any.whl`，SHA256 `867d85c6dfa6f3f30b224bb2b9f77dbd86970e87d0b03466c4526a9919bda37b`。final/minimal 均 repo 外非 editable 安装。依赖从既有固定环境离线复制，无升级或网络安装；完整环境单独通过 pip check，minimal 使用 --no-deps 且没有 DSH/Concordia。

```powershell
D:/ar-complete-20261011/final/Scripts/python.exe tools/refactor/validate.py all-local --output D:/ar-complete-20261011/final-regression05
D:/ar-complete-20261011/final/Scripts/python.exe tools/refactor/completion.py --wheel D:/ar-complete-20261011/final-wheel05/actio_rsi-0.1.0-py3-none-any.whl --output D:/ar-complete-20261011/completion05
D:/ar-complete-20261011/final/Scripts/python.exe tools/refactor/packaging.py --python D:/ar-complete-20261011/minimal/Scripts/python.exe --output D:/ar-complete-20261011/packaging05 --wheel D:/ar-complete-20261011/final-wheel05/actio_rsi-0.1.0-py3-none-any.whl
python tools/refactor/architecture.py D:/ar-complete-20261011/architecture-final05.json
```

输出目录必须是新的，不覆盖原收据。34 suite 原 163 方法保留，新增一个 Clock 边界方法，总计 164；suite_evidence 使用同次 suite_runtime 结果。不得拼接开发安装结果。

```powershell
D:/ar-complete-20261011/final/Scripts/python.exe tools/refactor/history.py
D:/ar-complete-20261011/final/Scripts/python.exe tools/refactor/history_c5.py
D:/ar-complete-20261011/final/Scripts/python.exe -I -B tools/refactor/vectors.py D:/ar-mod-20261011/baseline-source
D:/ar-complete-20261011/final/Scripts/python.exe -I -B tools/refactor/vectors.py
```

vectors 在两个独立进程比较完整 JSON。history 只使用工具写死的 Git SHA，原 reader 与历史 artifacts 不变。C2/C4 的受控 delivery/DB、C3 的公开包、C5 原矩阵分开认证；19 claims 逐字节 hash 核对。

正式矩阵已发起，**不默认重复**。在 repo 外执行：

```powershell
D:/ar-complete-20261011/final/Scripts/python.exe -I -B -m actio.transport_diagnostics run-local --root D:/ar-complete-20261011/formal-completion05 --freeze D:/ar-complete-20261011/freeze-completion05.json
```

最终源码只使用这一次正式矩阵。旧 `formal-completion` 的诊断 field-bound FAIL、12 次额外 loopback 与旧 wheel 单列保留；不并入最终 12 次或历史实验分母。旧 `formal-completion04` 在末尾空行规范化之前已 PASS，其额外12次同样单列，不能作为最终源码收据。所有开发 tests 的额外 fixture sends 也单列。

publication_scan 仅执行凭据模式和受控 raw/reasoning 拷贝排除，不读取真实 key；exact_secret_scan 明确 NOT_RUN。普通 git fetch/commit/push 后分别用 ls-remote 验证任务分支和 main。完整最终 SHA 在本机 publication.json 和交付回复中记录，避免提交自指 hash。

C6、真实 provider、目录 GET、外部 MCP、judge、训练、部署和激活继续暂停。
