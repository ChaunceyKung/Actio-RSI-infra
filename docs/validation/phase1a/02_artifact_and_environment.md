# Artifact 与隔离环境

实际平台 Windows 11 `10.0.26200` AMD64，Python `3.12.10`，runtime 启动日志报告内置 Node `v24.21.0`。模型 fixture 不使用网络；MCP 使用 stdio，无本地监听端口。没有安装/启动 WSL、操作系统特性或全局 Node/Python 依赖。

| Pin | 实际结果 |
|---|---|
| DSH reference source | `5badb15009ae1756c3afe0ae0cef1faafc290ccc` / `dsh-v0.2.1-alpha.1`，只读 |
| 官方 SDK | `deepseek-harness-sdk==0.1.5rc1`；PyPI metadata 精确依赖 runtime-bin同版及 pydantic>=2.12,<3 |
| SDK wheel | 13,694 bytes；SHA256 `8d9897e97e8a95fd738cb2c3e2c563951d824e43847ec6f3b0fb172c0729b4d8` |
| 官方 Windows runtime wheel | 72,045,733 bytes；SHA256 `d031a5ab4919c572fd7e48c7ef19ec8b1896e93d93c44b0937bb958c528f8acf` |
| 实际 executable | `deepseek-harness-sdk-runtime-win-x64.exe`；SHA256 `7ff077cfa28b81aa33f96aca97911969f8b6499bc1f85e4a6d3ddd16b8aa67d6` |
| executable 位置 | `probes/phase1a/.local/venv/Lib/site-packages/deepseek_harness_runtime/runtime/`；启动由公开 bundled runtime resolver完成 |
| package 内部 metadata | `deepseek-harness-runtime.json` 为 `0.0.0-dev`；不作 release pin |
| handshake metadata | source常量 `serverInfo.version=0.0.1`，不是 release/build/patch证明 |
| Python SDK 比较 | installed api.py/client.py/models.py 与固定source归一化换行后文本相同，各自hash见 installed-artifacts.json |
| TS binary 对应 SHA | **UNPROVEN**。没有 build attestation。实际发现 source 类型/取消与 wheel 行为不同，不能推定同源 |
| Concordia | `google-deepmind/concordia@b71d202750e23444ce1bf28d9f114bcd88aa41db` 原样 git archive 隔离副本；导入真实 Engine，未安装全研究生态 |
| MCP server | 官方 `mcp==1.26.0` Python SDK；server version1，实际请求协议 `2025-11-25` |

官方 metadata：<https://pypi.org/pypi/deepseek-harness-sdk/0.1.5rc1/json>、<https://pypi.org/pypi/deepseek-harness-runtime-bin/0.1.5rc1/json>。本轮查询 latest 仍为0.1.5rc1。完整 download URL、size、hash、Requires-Dist、license 文件名见 [artifacts.json](evidence/artifacts.json)。先读取72MB大小，只下载 Windows x64，没有全平台下载。第一次 pip 流式下载 pandas 超时；随后官方URL有界Range下载并校验整文件hash成功，未换镜像/相近包/浮动main。

Python依赖40个wheel，全部用 SHA256锁定，安装用 `--require-hashes` 和 isolated venv。核心闭包包含 pydantic2.13.5、mcp1.26.0、anyio/httpx/jsonschema、absl-py2.3.1、termcolor3.3.0、numpy2.4.2、pandas2.3.3及依赖。Concordia仅安装此导入闭包，未声称符合完整上游 distribution 的所有模型/训练依赖。`pip check` 结果随最终验收记录。

许可证核对范围是实际安装/运行闭包：DSH SDK/runtime MIT 并有 wheel 内 `LICENSE` / `THIRD_PARTY_NOTICES.md`；MCP MIT；Concordia Apache-2.0；Python闭包主要 MIT/BSD/Apache/PSF，certifi为MPL-2.0，numpy有多许可组合，dateutil双许可。文件hash与distribution metadata均保留。DSH NOTICE是宽泛 npm清单，含未加载的可选商业SDK条目，不等于本profile使用了它们，也不是每个嵌入依赖都已完成再分发审查。**本次仅本地使用，不发布binary；binary SBOM/build映射与再分发闭包仍待后续 B01b。**

所有 runtime/home/workspace/temp 在新建 `D:\actio-p1a-*` 任务目录（复现时使用仓库所在盘根下唯一短目录）；其中单独测试中文及空格home。初次把缓存置于深仓库路径，Koffi原生模块超过Windows路径长度而失败；短根通过，见 [初次失败](evidence/initial-launch-failure.json)。这是配置限制，未修改注册表/长路径策略。

子进程环境由 `common.clean_env` 从零构建，只包含系统路径、任务HOME/USERPROFILE/APPDATA/TEMP、Python编码设置和禁用telemetry/primary runtime选项。没有枚举或继承provider keys、代理配置、用户PYTHONPATH。SDK本身仍会继承调用方环境，所以必须先把运行SDK的整个探针子进程放入这个allowlist环境。Windows Job Object在释放子进程启动闸门前绑定，记录正常退出或终止后的active process=0。

公开启动seam为 SDK `profile='sdk-minimal'`、`patches`、`dsh_home`；未用 `_launch_args`。外部 `.mjs` 通过 `ctx.llm.registerAdapter` 实现公开 provider 接口，不导入 executable 内私有包，不替代 DSH loop/storage。没有 source build、upstream patch、vendor checkout入Git。
