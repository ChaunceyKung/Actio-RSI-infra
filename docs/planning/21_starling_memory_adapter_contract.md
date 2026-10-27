# Starling Memory Adapter 接口与功能合同草案

**状态：设计合同草案；供 P0/P1 实现和评审使用。**

这个文件把 `20_starling_memory_integration_plan.md` 里的方向收敛成可以实现、测试和回滚的接口。名字和字段在实现前允许通过 ADR 调整，但必须保留权威边界、幂等和回放语义。

## 1. 接入面和依赖方向

建议新增：

```text
src/actio/contracts/memory.py              # 纯数据合同、Protocol、错误码
src/actio/application/memory_projection.py # outbox/saga 编排
src/actio/adapters/memory/starling.py      # Python facade 或 owner-process client
src/actio/adapters/memory/README.md
src/actio/profiles/starling_memory.py      # capability/profile 校验
tests/test_starling_memory_adapter.py
tests/test_memory_projection.py
```

`contracts` 不得 import Starling；`application` 只依赖 `StarlingMemoryPort`；具体 `starling` import、pybind11、IPC、SQLite 路径和进程生命周期只出现在 `adapters.memory`。`evidence` 只读取 receipt/bundle，不启动 Starling runtime；`measurement` 不调用生产 memory 写路径。

## 2. 核心数据类型

下面是 Python 类型的方向性定义。它们是跨进程 wire 形状，必须使用 Actio canonical JSON 和固定 enum，不能直接序列化 pybind11 对象。

```python
from dataclasses import dataclass, field
from typing import Literal, Protocol

MemoryMode = Literal["off", "shadow", "frozen_context", "live_context"]
ProjectionState = Literal[
    "queued", "in_flight", "committed", "duplicate", "abstained",
    "degraded", "rejected", "needs_reconcile",
]

@dataclass(frozen=True)
class MemoryScope:
    project: str
    branch: str
    visibility: str
    environment: Literal["assistant", "social"]
    agent: str
    target: str | None = None
    tenant_id: str = ""

@dataclass(frozen=True)
class MemorySource:
    run_id: str
    stream_id: str
    seq: int
    slot: str                         # normally assistant.final
    mapper: str                       # pinned v1/v2
    source_hash: str                  # hash of certified raw occurrence
    observed_at: str
    source_kind: Literal["assistant_final", "tool_observation", "world_effect"]
    replay_of: str | None = None
    privacy_class: Literal["public", "internal", "personal", "sensitive"] = "internal"

@dataclass(frozen=True)
class MemoryObservation:
    source: MemorySource
    scope: MemoryScope
    text: str | None                  # None for metadata-only policy
    holder: str
    interlocutor: str | None = None
    event_time_start: str | None = None
    event_time_end: str | None = None
    payload_policy: Literal["text", "metadata_only", "redacted"] = "text"

@dataclass(frozen=True)
class MemoryReceipt:
    adapter: str
    adapter_version: str
    operation_id: str
    source_key: str
    state: ProjectionState
    tenant_id: str
    engram_ref: str | None = None
    statement_ids: tuple[str, ...] = ()
    context_hash: str | None = None
    retrieval_receipt: dict | None = None
    as_of: str | None = None
    error_code: str | None = None
    error_detail: str | None = None
    idempotent: bool = False
    started_at: str | None = None
    finished_at: str | None = None

@dataclass(frozen=True)
class MemoryContext:
    text: str
    context_hash: str
    abstained: bool
    abstention_reason: str | None
    receipt: MemoryReceipt
    sections: tuple[dict, ...] = ()

@dataclass(frozen=True)
class MemoryHealth:
    status: Literal["ready", "degraded", "unready", "disabled"]
    capabilities: frozenset[str] = frozenset()
    missing: tuple[str, ...] = ()
    writer_queue_depth: int = 0
    last_error_code: str | None = None

class StarlingMemoryPort(Protocol):
    def health(self) -> MemoryHealth: ...
    def project(self, item: MemoryObservation, *, idempotency_key: str) -> MemoryReceipt: ...
    def retrieve(self, scope: MemoryScope, *, query: str, intent: str,
                 perspective: str | None, goal: str | None, k: int,
                 as_of: str | None, mode: MemoryMode) -> MemoryContext: ...
    def working_set(self, scope: MemoryScope, *, interlocutor: str,
                   goal: str | None, token_budget: int,
                   as_of: str | None, mode: MemoryMode) -> MemoryContext: ...
    def tick(self, *, now: str, deadline_ms: int) -> dict: ...
    def forget(self, scope: MemoryScope, statement_ids: list[str], *, now: str) -> MemoryReceipt: ...
    def close(self, *, drain: bool = True) -> None: ...
```

`MemoryReceipt.state` 不是 Actio run 状态；它只描述 Starling projection/read operation。Actio run 成功、task failure、unknown、not_run 和 evidence validity 仍由现有模块决定。

## 3. Source mapping

### 3.1 Namespace → Starling scope

第一版建议把经过 `namespace()` 校验的值规范化为：

```text
tenant_id = actio:<project>:<branch>:<visibility>:<environment>
agent     = Actio agent id / Starling self Cognizer external_id
holder    = agent (除非显式导入他人陈述)
target    = social only when agent spec.memory_shares authorizes it
```

tenant 的构造必须用 canonical JSON + digest，不能直接拼接未经验证的用户字符串。若未来需要同一 tenant 里多个环境，必须让 Starling 的 typed visibility/scope join 承担隔离，并加入跨 tenant/holder 的负向测试。

### 3.2 Actio source → Engram/Statement

| Actio 字段 | Starling 字段 | 规则 |
|---|---|---|
| `stream, seq, slot, mapper` | `source id` / adapter metadata | 组成稳定 source key；重复 source 幂等 |
| `raw_hash` | Engram `content_hash` / provenance | 必须保留；不是只存文本摘要 |
| `assistant/message` 的 final 文本 | Engram payload | 只在 `payload_policy=text` 且 privacy 允许时保存 |
| `run.created` / event timestamp | `observed_at`、可选 `event_time` | 由 Actio Clock 规范为 UTC ISO8601 |
| Actio agent | `Cognizer(holder)` | self/agent 归属，不把 agent 当普通 object |
| A/B/用户/工具 | `Cognizer` 或 `Entity(subject/object)` | 类型需由 Adapter policy 决定 |
| `task_failure` 或技术错误 | 不自动写成事实 | 可写 metadata-only diagnostics，默认不进入 social memory |
| replay run | `SourceKind.REPLAY_OUTPUT` | 默认禁止写入；显式实验 profile 才允许，并带 `replay_of` |
| `GM_PRIVATE_FULL_LOG`、credentials、stderr | 禁止 | 通过 payload policy 和 secret scan 双重阻断 |

运行事实默认使用 `Modality.OCCURRED`；模型抽取出的“相信/知道/偏好/承诺”必须保留原 modality、polarity、confidence 和 provenance。Adapter 不得把一个 assistant 文本直接改写成 `KNOWS`。

## 4. Outbox 与 saga

### 4.1 Actio schema 草案

在现有 Store schema 版本上增加独立表，具体列名由 migration ADR 冻结：

```sql
CREATE TABLE memory_outbox (
    id TEXT PRIMARY KEY,
    source_key TEXT UNIQUE NOT NULL,
    run TEXT NOT NULL REFERENCES run(id),
    namespace TEXT NOT NULL,
    source_hash TEXT NOT NULL,
    payload TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    state TEXT NOT NULL,                 -- queued/in_flight/committed/...
    attempts INTEGER NOT NULL DEFAULT 0,
    lease_until INTEGER,
    receipt TEXT,
    error TEXT,
    created INTEGER NOT NULL,
    updated INTEGER NOT NULL
);
CREATE INDEX memory_outbox_state ON memory_outbox(state, updated);
```

`payload` 必须是 canonical JSON，不能保存 secret。`source_key` 至少包含 `stream/seq/slot/mapper`；`payload_hash` 绑定脱敏后的发送内容，防止同一个 source 被换内容重放。

### 4.2 正常路径

1. `Facts.certify()` 成功后，`application.memory` 在同一个 Actio Store 事务中提交现有 effect，并插入 outbox `queued`。
2. 事务提交后，projection worker 按 source key 顺序 claim 一条 outbox，写 `in_flight` 和 lease。
3. `StarlingMemoryPort.project()` 调用 `Memory.remember()` 或未来的 typed ingest API；调用必须携带 source key/hash、now、tenant、holder/interlocutor。
4. 成功返回 `engram_ref/statement_ids/outcome` 后，worker 在另一个 Actio 事务中写 `committed` 和 receipt。
5. 重启或 lease 超时只允许以同一 source key 重试；Starling 返回 duplicate 时写 `duplicate`，不能追加第二份事实。

### 4.3 失败语义

| 情况 | outbox 状态 | Actio run | 是否自动重试 |
|---|---|---|---|
| Starling disabled | `degraded` | 不变 | 否，除非 profile 明确启用 |
| preflight UNREADY/DB locked | `needs_reconcile` | 不变 | 有限、指数退避，达到上限停止 |
| LLM extraction failed | `degraded` | 不变 | 只按显式 policy；保留原响应/usage |
| tenant/holder policy denied | `rejected` | 不变 | 否，需修复输入或 policy |
| duplicate source key | `duplicate` | 不变 | 否 |
| process crash after Starling commit | `in_flight` → reconcile | 不变 | 先 query idempotency/source key，再决定 |
| Actio receipt 写失败 | `needs_reconcile` | 不变 | 不允许盲目再次写入；做 reconcile |

没有一种 Starling 失败可以把已经认证的 Actio run 回滚成未知，也不能把 Starling “有 statement”当成执行成功。

## 5. Retrieval 和冻结合同

### 5.1 只读 retrieval

Adapter 将 Actio 的 query 映射到 Starling `Memory.query()`：

```python
ctx = port.retrieve(
    scope,
    query="what did B commit to?",
    intent="COMMITMENT_LOOKUP",
    perspective="first_person",
    goal="social episode planning",
    k=8,
    as_of=actio_clock_now,
    mode="shadow",
)
```

`query()` 的 `entries/source_entries/context_pack/abstained/abstention_reason/receipt` 必须完整转成 Actio `MemoryContext`，不能只取字符串丢掉 receipt。Starling abstention 是合法结果；不能用空列表伪装“没有记忆”。

### 5.2 进入 solver 前的 frozen_context

当且仅当 profile 是 `frozen_context`：

```json
{
  "memory": {
    "provider": "starling",
    "mode": "frozen_context",
    "context_pack": "...",
    "context_hash": "sha256:...",
    "as_of": "2026-10-27T04:00:00Z",
    "receipt": {"query_id":"...","abstained":false,"...":"..."},
    "source_hashes": ["..."],
    "adapter_version": "...",
    "capabilities": ["query", "working_set"]
  }
}
```

`application.scenarios.snapshot()`、`social_manifest()`、`scheduling()` 的冻结输入需要把该对象纳入 input hash；`validate_replay()` 必须要求它的字段、hash 和 provider pin 一致。replay 只消费上述 context，不重新读取 Starling。

`live_context` 只允许实验或交互式 dashboard，不允许用于需要可重放的 candidate/evaluation evidence，除非把每次 recall 的完整结果和 receipt 封存为输入。

## 6. Maintenance API

推荐新增 CLI（名称可在 ADR 中调整）：

```text
actio memory starling doctor --db <actio-db> --starling-db <path>
actio memory starling project --run <run-id> [--source-key ...]
actio memory starling reconcile --outbox <id|all>
actio memory starling query --agent A --environment social --intent FACT_LOOKUP
actio memory starling tick --now <UTC> --deadline-ms 5000
actio memory starling export --tenant <tenant> --output <dir>
```

规则：

- `doctor` 只读，输出 capability/preflight、DB schema/version、writer ownership、model/embedding pin 和未结 outbox。
- `project/reconcile` 需要显式 operator scope；不能由 episode finally 隐式调用无限重试。
- `tick` 使用真实或测试 Clock；必须把 `TickStats`、health 和 elapsed time 写成 diagnostics artifact。
- `export` 只导出 Starling receipt/statement/Engram 的可迁移子集，并标注是否含原文；不能绕过 Actio secret scan 和 retention policy。

## 7. Adapter 两种运行模式

### A. Embedded（优先用于 Linux/offline 测试）

Actio 进程内初始化一个长期存在的 Starling owner/runtime/adapter，所有调用通过队列串行化。禁止每个 episode `Memory.open()` 一个 writer。适合低并发、可直接 mock `Memory` facade 的单测。

### B. Sidecar owner process（Windows/生产优先候选）

Starling 单独运行，通过 Actio 已有受控 worker/IPC 设计传递 canonical JSON。Sidecar 独占 Starling SQLite，Actio 只保存 operation id/source key/receipt。需要定义：启动/健康/ready/drain、最大 payload、deadline、协议版本、认证 token、stdout/stderr 脱敏、进程回收和升级回滚。

首轮不建议直接调用 Starling dashboard 的内部 FastAPI route；dashboard 是观察和交互面，不应成为 Actio 的稳定 SDK。若未来需要远程 sidecar，应先冻结独立 RPC contract。

## 8. 测试矩阵

### Contract/unit

- namespace canonicalization、tenant digest、agent/holder mapping；
- source key/hash 幂等、重复 outbox、payload secret scan、16 KiB/byte budget；
- `MemoryReceipt` wire round-trip、未知 enum、未知 capability、错误码；
- `mode=off/shadow/frozen_context/live_context` 的准入和 replay schema。

### Integration/offline

- `remember` 使用 `make_stub_llm` 写入，`query` 返回 receipt，`tick` 使用固定 now，working set 可渲染；
- Starling UNREADY、LLMNotConfigured、extraction_failed、DB locked、sidecar crash、graceful drain；
- Actio run 成功 + Starling 失败，Actio run 失败 + queued outbox，双写 commit 后进程崩溃；
- source key duplicate 不产生第二个 Engram/Statement；correction 形成新 version/supersedes；
- cross-agent/environment/tenant 正常与拒绝；replay 不读取 live Starling。

### Evidence/measurement

- bundle 能验证 Actio source 与 Starling receipt/source_hash 的关系；
- projection lag、abstention、candidate/excluded、embedding failure、tick stage timings 单独计数；
- memory provider A/B 不改变同一 frozen input 的 task/evidence 分母；
- 失败保持 unknown/degraded/rejected 的原始原因，不能转成 usage=0 或空成功。

### Build/release

- Python 3.12 wheel 与 Starling extension ABI；
- Windows 直连或 sidecar 安装、CMake/SQLite/OpenSSL/ICU/pybind11 pin；
- 没有 Starling optional extra 时 Actio wheel、`actio --help`、既有测试和 minimal reader 仍能工作；
- adapter/version/source hash 写入 diagnostic package，支持回滚到 `off`。

## 9. 版本与迁移策略

- 新增 profile/capability 必须是 additive；默认 `starling=off`，旧 manifest 不自动解释为 `frozen_context`。
- Actio schema migration 与 Starling migration 分开；先备份/校验 Actio DB，再升级 sidecar，失败可回滚到旧 adapter。
- 每个 projection receipt 同时保存 Actio schema version、Starling schema/migration version、adapter source hash、embedding model/dim 和 extraction policy hash。
- Starling DB 不纳入 Actio Store 的 WAL/backup 假设；导出时建立独立 manifest，恢复时先做 source/key reconciliation。
- 任何修改 Statement modality、tenant mapping、context rendering 或 source policy 的版本都要新建 provider/profile identity，禁止原地改写旧 evidence。

## 10. 尚待用户/项目决策确认的选项

1. 第一运行平台采用 Windows embedded、Windows sidecar，还是 Linux sidecar；P0 探针完成前不选默认路径。
2. Starling extraction 是否允许真实 LLM；若允许，使用哪个 profile/预算/usage receipt，是否只做离线批处理。
3. 首批允许进入 Starling 的 source 类型：仅 `assistant.final`，还是加入 tool observation/world effect；默认推荐仅前者。
4. social memory 是否跨 episode/跨 agent 共享；推荐第一版按 tenant + explicit target 授权，禁止全局共享。
5. P3 是否允许 Starling working set 进入 solver；推荐先 shadow，等 replay 和 evidence gate 通过再开放 frozen_context。\n