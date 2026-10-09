# C2C3 离线CLI

Windows x64 / Python3.12，仓库根目录。纯诊断不需要旧runtime依赖、TokenKey凭据、DSH或Concordia安装。公开入口为 `python -m actio.task_diagnostics`，与旧candidate execute分开，没有live子命令。

## 最小安装与实测命令

安装器只创建新venv并复制14个固定纯模块/数据文件，检查源码一致性；with_pip=false，无下载。下面是本机已实际执行的命令。已有目标目录会被拒绝；其他机器可以把首个Python路径换成自己的Python3.12，安装/输出路径换为尚不存在的新目录。

```powershell
& .local/phase1c2c2-runtime-venv/Scripts/python.exe -X utf8 -I -B scripts/install_task_diagnostics.py .local/phase1c2c3-public-env
& .local/phase1c2c3-public-env/Scripts/python.exe -X utf8 -I -B -m actio.task_diagnostics plan
& .local/phase1c2c3-public-env/Scripts/python.exe -X utf8 -I -B -m actio.task_diagnostics analyze --source docs/validation/phase1c2c2 --output .local/phase1c2c3-public-analysis --source-receipt docs/validation/phase1c2c3/historical-source.json --dataset docs/validation/phase1c2c3/frozen-design/dataset.json
& .local/phase1c2c3-public-env/Scripts/python.exe -X utf8 -I -B -m actio.task_diagnostics verify .local/phase1c2c3-public-analysis
& .local/phase1c2c3-public-env/Scripts/python.exe -X utf8 -I -B -m actio.task_diagnostics verify docs/validation/phase1c2c3/package
```

`plan`只读固定代码/合同并输出JSON。`analyze`读取代码信任表中固定hash的原公开report、预注册、decision、lineage及引用，只写指定的新目录，不覆盖旧文件。省略`--dataset`使用同一固定生成器；省略`--source-receipt`明确返回`public_projection_only`，仍可完成描述性重算。

`verify`仅依赖包中的10个白名单相对JSON文件和对应版本的可信reader，不依赖源实验盘符、现场DB、受控delivery或网络。可复制整个package到其他目录核验，artifact不能指定任意reader/插件。未知schema、缺world、重复identity、错binding、改行动、来源断裂、篡改报告、伪造认证、路径引用和额外代码文件均拒绝。退出码0表示包与诊断内部重算一致；必须同时读各Gate，不等于模型获益、研究有效性或旧raw重新认证。

`source-assurance.json`保留本机固定旧reader认证结果与hash，不是供应商签名。复制该记录不会在新机器上重跑原raw认证。公开verify始终报告`raw_authentication_repeated=false`；完整历史raw复核仍需C2C2受信reader和受控原包，不能由新诊断包代替。

## 实际验收记录

- [7项纯测试](evidence/tests-d4dd34039d2b.json)：完整source/argv与测试日志。
- [8条guard内CLI](evidence/cli-b6e40881b375.json)：plan、analyze、verify、移址复核、覆盖拒绝、来源降级和重复参数拒绝；禁止key/env/network/process/runtime，plan/verify禁止写，analyze只允许指定新目录。
- [最小安装及4条literal命令](evidence/literal-cli-027c3161315a.json)：真实`-m`入口、退出码、stdout hash和安装文件一致性。
- [guard开发失败](evidence/cli-eadb83bc86b5.json)：最初将公开controlled-delivery引用文件误当raw delivery拦截；只修正测试guard匹配，产品源码未变。

最小安装环境的完整绝对argv保存在验收证据；可移植package本身不含这些本机路径。后续源码变化时使用C2C3固定reader版本，不能刷新历史包pins使旧证据看似仍对应新实现。测试入口为`python -X utf8 -I -B scripts/phase1c2c3_validate.py`；它只运行本轮纯测试，不启动runtime。C2C2正式live claim已消耗，不运行旧execute。
