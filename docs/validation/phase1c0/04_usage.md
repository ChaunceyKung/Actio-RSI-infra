# Phase 1C0 复现入口

从仓库根在 Windows/Python 3.12 执行。下列为本轮实测命令形态，完整实际绝对参数/退出码在 [manifest](evidence_manifest.json) 指向的记录中。

## 准备

core 保持原 `requirements.lock` 的 41 wheel。offline eval 独立锁为 [requirements-eval.lock](../../../requirements-eval.lock)，只需 Pydantic 闭包、json-repair 和构建用 setuptools；gin-config 仅用于完整上游 evaluator 的测试。首次无缓存可下载锁定 wheel，依赖准备允许联网；评估阶段没有网络。

```powershell
python -X utf8 scripts/bootstrap_eval.py --venv .local/phase1c0-release-venv --offline --characterization
```

本轮缓存位置为 `.local/wheels` 与 `.local/eval-wheels`。无缓存时省略 `--offline`；pip 仍使用 require-hashes 固定全部依赖。此最小环境以 `--no-deps` 安装 Actio，专供离线评估，未安装 core runtime 的项目依赖；不把该环境的全项目 `pip check` 当通过。另一个干净 core 环境执行原 bootstrap，再叠加 eval lock，完整 `pip check` 通过。

```powershell
python -X utf8 scripts/bootstrap.py --venv .local/phase1c0-runtime-venv --offline-wheels --concordia-source ../../codebase/15_concordia/repo
.local/phase1c0-runtime-venv/Scripts/python.exe -m pip --isolated install --no-index --require-hashes --only-binary=:all: -r requirements-eval.lock --find-links .local/wheels --find-links .local/eval-wheels
.local/phase1c0-runtime-venv/Scripts/python.exe -m pip --isolated check
```

## 一次测量

公开入口 `python -m actio.evaluation` 或安装后的 `actio-eval`。该入口不导入 runtime/DB；`python -m actio.verify` 仍是标准库包核验。

当前 dataset SHA 为 `7843afb624ca1b783b90b87822fb85efdd82985889a8463225a88837719ea9af`。spec 子命令打印内容寻址文件路径；将该路径用于 run。run 的 JSON 输出给出 record 路径、是否复用与三个轴；verify-record 的参数就是该路径。

```powershell
.local/phase1c0-release-venv/Scripts/python.exe -m actio.evaluation spec --mode deterministic --dataset-hash 7843afb624ca1b783b90b87822fb85efdd82985889a8463225a88837719ea9af --output .local/c0-specs
.local/phase1c0-release-venv/Scripts/python.exe -m actio.evaluation run --spec SPEC_PATH --bundle docs/validation/phase1b1/samples/assistant --output .local/c0-records
.local/phase1c0-release-venv/Scripts/python.exe -m actio.evaluation verify-record RECORD_PATH
```

`SPEC_PATH`、`RECORD_PATH` 是上一步实际 JSON 输出路径，不是可执行模板内容。受控路径将 `--bundle` 替换为 `--synthetic` 并提供 `--response`，使用 controlled_response spec。已封存 synthetic input 和预置响应见 [examples](examples/controlled-response.json) 及当前 dataset；实际完整命令在 delivery 证据中。CLI 无效测量/缺证退出 2，同时输出记录路径；这是已保存的失败，不是正常 0 分。

完整 campaign 无需 DB、原 runtime 根或参考仓库：

```powershell
.local/phase1c0-release-venv/Scripts/python.exe -m actio.evaluation campaign docs/validation/phase1c0/campaign/datasets/7843afb624ca1b783b90b87822fb85efdd82985889a8463225a88837719ea9af.json --output .local/c0-campaign-reproduction
```

源快照嵌在 dataset/record 中，原生 raw 字节作为 JSON 字符串保留。spec 和记录文件不可原位编辑：变更产生新 hash。相同请求读取旧记录；存在未完成 `.claim` 时拒绝自动再次执行。`.request.json` 指针和 `.claim` 是本地原子发布协议，不是 runtime 的第二数据库。结果算法只支持当前 exact pins；旧阶段报告与中间 pins 保留作历史。

## 验收

```powershell
.local/phase1c0-release-venv/Scripts/python.exe -X utf8 scripts/validate.py input_binding phase1c0
.local/phase1c0-release-venv/Scripts/python.exe -X utf8 scripts/validate.py sotopia phase1c0
.local/phase1c0-release-venv/Scripts/python.exe -X utf8 scripts/validate.py evaluation phase1c0
.local/phase1c0-runtime-venv/Scripts/python.exe -X utf8 scripts/validate.py runtime phase1c0
.local/phase1c0-runtime-venv/Scripts/python.exe -X utf8 scripts/validate.py reliability phase1c0
.local/phase1c0-runtime-venv/Scripts/python.exe -X utf8 scripts/validate.py evidence phase1c0
.local/phase1c0-runtime-venv/Scripts/python.exe -X utf8 scripts/validate.py schema phase1c0
.local/phase1c0-release-venv/Scripts/python.exe scripts/extract_sotopia.py ../../codebase/18_sotopia/repo --check
```

新的真实 replay fixture 可用 `scripts/phase1c0_fixtures.py` 生成，它只使用新合成身份。`scripts/phase1c0_campaign.py RUNTIME_SMOKE_EVIDENCE` 封存这些包及已公开样例；重复实跑会形成新的 source/run 身份，不替换已封存 campaign。共享机器上的参考仓库始终只读。
