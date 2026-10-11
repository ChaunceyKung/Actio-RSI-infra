# 本轮当前命令

Windows x64 / Python 3.12；不执行真实provider、目录GET或外部MCP。历史脚本保留原路径，不用其发布入口写旧phase目录。

## 安装与wheel

```powershell
# 现有bootstrap只用本地锁定wheel与固定Concordia Git archive。
python -X utf8 scripts/bootstrap.py --venv D:/ar-new/runtime --offline --concordia-source ../../codebase/15_concordia/repo
D:/ar-new/runtime/Scripts/python.exe -m pip --isolated install --no-index --require-hashes --find-links .local/eval-wheels --find-links .local/wheels -r requirements-eval.lock -r requirements-eval-test.lock
D:/ar-new/runtime/Scripts/python.exe -X utf8 tools/refactor/build_wheel.py --output D:/ar-new/build
# 标准wheel在全新源码副本中构建，避免setuptools build/lib残留已删除模块。
D:/ar-new/runtime/Scripts/python.exe -m pip --isolated install --no-index --no-deps --force-reinstall D:/ar-new/build/actio_rsi-0.1.0-py3-none-any.whl
D:/ar-new/runtime/Scripts/python.exe -m pip --isolated check
```

本次实际环境为 `D:/ar-mod-20261011/final`，wheel位于 `wheels11`。bootstrap是非editable标准安装，最终又安装了独立wheel；不能用旧venv的源码兜底。

## 当前runner与suite

```powershell
D:/ar-mod-20261011/final/Scripts/python.exe -X utf8 -B tools/refactor/validate.py pure --output D:/ar-new/pure
D:/ar-mod-20261011/final/Scripts/python.exe -X utf8 -B tools/refactor/validate.py state --output D:/ar-new/state
D:/ar-mod-20261011/final/Scripts/python.exe -X utf8 -B tools/refactor/validate.py runtime-local --output D:/ar-new/runtime-tests
D:/ar-mod-20261011/final/Scripts/python.exe -X utf8 -B tools/refactor/validate.py all-local --output D:/ar-new/all
D:/ar-mod-20261011/final/Scripts/python.exe -X utf8 tools/refactor/architecture.py D:/ar-new/architecture.json
```

每次output必须不存在。runner校验整个安装源码清单，日志/完整测试证据仅留受控新目录。suite清单在runner的SUITES及migration-map.json。`--only`用于失败修复后的明确范围，不伪称全量。architecture目前正确返回1/INCOMPLETE，不能用其四项局部boundary测试替代完整DAG。

`runtime-local`实际启用官方本机Worker与fixture，会产生额外开发sends，不属于正式12次。`suite_evidence`依赖同次`suite_runtime`生成的新pilot；不复用旧phase的pilot。旧readiness成功路径受原报价时限阻塞，原错误不改skip。tools不默认访问外部provider。

## 历史、打包和差分

```powershell
D:/ar-mod-20261011/final/Scripts/python.exe -X utf8 -B tools/refactor/history.py
D:/ar-mod-20261011/final/Scripts/python.exe -X utf8 -B tools/refactor/history_c5.py
D:/ar-mod-20261011/final/Scripts/python.exe -X utf8 -I -B tools/refactor/vectors.py
D:/ar-mod-20261011/final/Scripts/python.exe -X utf8 -B tools/refactor/packaging.py --python D:/ar-mod-20261011/minimal/Scripts/python.exe --output D:/ar-new/packaging --wheel D:/ar-mod-20261011/wheels11/actio_rsi-0.1.0-py3-none-any.whl
```

history外层只从代码固定commit归档，内部reader在原GUARD下只读。C2/C4需要本机受控原始delivery/DB；缺失不能从summary重建。C3公开投影与C2/C4 raw核验范围分别记录。C5对原196e8a6实测做固定reader认证，再离线重算；不发送请求。vectors可传受信C5归档根目录作为唯一位置参数，在独立进程比较完整JSON；实际555项完全相等。不要把artifact路径作为源码执行授权。

minimal环境以`--no-deps`安装同wheel，无DSH/Concordia；它的纯guard通过不代表完整依赖`pip check`。后者在final环境单独通过。

## 新正式矩阵（已经执行，不默认重复）

冻结产品提交 `d64264f` 推送任务分支后，repo外cwd实际运行：

```powershell
D:/ar-mod-20261011/final/Scripts/python.exe -X utf8 -I -B -m actio.transport_diagnostics run-local --root D:/ar-mod-20261011/formal11 --freeze <repo>/docs/validation/refactor_modularity/freeze11.json
```

不传`--project`，产品无需tests/scripts/source checkout；传project时仍核对源码镜像。freeze包含完整安装源码、case/fixture、wheel和外层工具hash。已PASS的正式矩阵不再重跑，产品或运行工具变动才评估重验范围。本次因Git LF与旧wheel CRLF字节差异而重建11并重验；freeze.json仍原样保留为10，freeze09.json亦保留。

保留四console scripts、`python -m actio`、各登记reader/host/eval/MCP/budget IPC，详见compatibility.json。旧私有task/oracle import已移除，当前tests调用实际新实现。

## 汇总、清理与发布扫描

全部suite退出后执行：

```powershell
D:/ar-mod-20261011/final/Scripts/python.exe -X utf8 -B tools/refactor/summarize.py --root D:/ar-mod-20261011 --final-matrix formal11 --output docs/validation/refactor_modularity/regression-summary.json
D:/ar-mod-20261011/final/Scripts/python.exe -X utf8 -B tools/refactor/cleanup.py --summary docs/validation/refactor_modularity/regression-summary.json --output docs/validation/refactor_modularity/development-cleanup.json
D:/ar-mod-20261011/final/Scripts/python.exe -X utf8 -B tools/refactor/publication_scan.py --live-root D:/actio-c2c4-live-v1
```

summarize拒绝将RUNNING receipt发布为最终汇总；按本轮测试元数据的root去重，不从artifact内部任意路径扫描历史目录。cleanup只查询这些根目录的SQLite和命名Job、用exclusive bind检查本机端口；绑定失败时查询该端口TCP状态，区分端口复用与残留监听，不终止进程或发送请求。scanner仅在内存读取既有凭据用于精确发布比对，亦禁止历史reasoning、请求和error.message的原文/JSON转义副本；它不执行provider调用。

发布前`git diff --check`与staged检查；普通push任务分支，fetch确认main可快进后merge --ff-only并push main，分别ls-remote核对。发布工具和汇总工具的后续修改不属于已安装run-local执行闭包；当前hash在最终证据manifest中，冻结时hash仍保留。
