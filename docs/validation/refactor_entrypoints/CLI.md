# 0.2.0 验收命令

所有当前调用使用已安装 wheel，Python 3.12，仓库外运行带 `-I -B`。full 固定依赖，minimal 仅 `--no-deps` 离线 reader；不读取真实凭据、不发外部实验请求。以下工具路径相对于仓库，产物在 `D:/ar-entry-20261012`。

```powershell
python tools/refactor/build_wheel.py --output D:/ar-entry-20261012/NEW_WHEEL
python -m pip install --no-index --no-deps <wheel>
python -m pip check
python -I -B tools/refactor/validate.py all-local --output <NEW_REPORT_DIR>
python tools/refactor/architecture.py <NEW_REPORT_JSON>
python tools/refactor/entrypoints.py --output <NEW_REPORT_JSON>
python -I -B tools/refactor/completion.py --wheel <wheel> --output <NEW_DIR>
python -I -B tools/refactor/packaging.py --python <minimal-python> --wheel <wheel> --output <NEW_DIR>
python -I -B tools/refactor/history.py --output <NEW_JSON>
python -I -B tools/refactor/history_c5.py --output <NEW_JSON>
python -I -B tools/refactor/vectors.py D:/ar-mod-20261011/baseline-source
python -I -B tools/refactor/vectors.py
python -I -B tools/refactor/freeze.py --output <NEW_FREEZE> --wheel <wheel>
python -I -B -m actio diagnostics transport run-local --root <NEW_ROOT> --freeze <NEW_FREEZE>
```

正式矩阵仅在源码稳定后运行一次。vector 输出必须完整 JSON 比较，不归一化业务字段。suite_evidence 消费同一 runner 中 suite_runtime 的结果，不能单独借旧产物通过。

用户命令与内部协议的完整映射见[迁移指南](../../architecture/MIGRATION_0_2.md)。历史 reader 的旧 imports 是固定 Git archive 内代码，不能机械替换。正式运行的目录、wheel SHA、失败与复核以[结果](RESULTS.md)和机器收据为准。
