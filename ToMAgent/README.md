# tom_harness

> 面向心智理论 (Theory-of-Mind, ToM) 基准测试的轻量级、技能驱动的 Agent Harness。
> 单次推理运行时搭载 76 层级技能 (v5.2) 为默认模式；Plan-then-Execute 遗留架构保留用于多步研究。

English version: [README_en.md](README_en.md)

---

## 这是什么？

`tom_harness` 是一套 **Agent Harness** —— 即围绕大语言模型构建的基础设施，用来把"文本生成器"变成"特定任务上可靠的推理器"。这里的任务是**社会认知 / 心智理论**：回答关于角色心理状态、错误信念、隐藏情绪、语用推理等的选择题。

系统支持两种执行模式：

1. **单次推理运行时（默认）**：路由 → 组装 prompt（skill + RAG + playbook）→ 单次 LLM 调用 → 可选 L0 review → 验证器检查 → 返回答案。这是基准评测的标准路径。
2. **Legacy harness**（Plan → Execute → Finalize）：Planner 生成多阶段计划，Executor 通过 ReAct 循环逐步执行，Finalizer 综合得出答案。保留在 `tom_harness/legacy/` 中用于多步研究。

### 工具层

单次推理运行时提供三个可插拔模块：

- **Skills v5.2（默认）** — 76 个精选 SKILL.md 推理提示（20 macro + 56 micro）+ 4 阶段 LLM 路由器（`SkillV5Router`）
- **Skills v4（遗留）** — 22 个精选 SKILL.md 推理提示 + LLM 路由器（`SkillV4Router`），通过 `--skill-version v4` 选用
- **RAG v4** — 统一分类体系 FAISS 检索 + LLM 多标签路由（1490 条多标签知识文档，43 类统一分类，来源：ATOMIC、Social Chemistry、NormBank、EmoBench、HiToM 等）
- **Memory Playbook** — 基于选择器的策略注入（ACE 精炼的 playbook，通过 `memory_playbook` 包实现）

---

## 架构（单次推理运行时）

```
┌──────────────────────────────────────────────────────────────────────┐
│                     HarnessRuntime (single-shot)                     │
│                                                                      │
│  阶段 1-2: 路由                                                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │ SkillV5Router (默认) / SkillV4Router / NoOpRouter              │  │
│  │                                                                │  │
│  │ v5.2: micro-01 (路由准备) → 选取 macro → 展开 micro            │  │
│  │       route_modes: baseline | macro_only | micro_only          │  │
│  │                    | hierarchical (默认) | flat_all             │  │
│  │       inject_modes: full | light (默认)                        │  │
│  └────────────────────────────┬───────────────────────────────────┘  │
│                               │                                      │
│  ┌──────────────┐  ┌──────────┴───┐  ┌──────────────┐               │
│  │  RAGv2Engine │  │ Skill bodies │  │   Playbook   │               │
│  │ (FAISS+bge,  │  │ (注入 0-N    │  │  (选择器驱   │               │
│  │  1490 docs)  │  │  个技能)     │  │   动)        │               │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘               │
│         │                 │                  │                        │
│  阶段 3: 求解                                                        │
│  ┌──────▼─────────────────▼──────────────────▼───────────────────┐   │
│  │              Prompt 组装                                       │   │
│  │  [Skill body] + [RAG context] + [Playbook] +                 │   │
│  │  [Story] + [Question] + [Options] + [Format instruction]     │   │
│  └──────────────────────────┬────────────────────────────────────┘   │
│                              │                                       │
│  ┌───────────────────────────▼───────────────────────────────────┐   │
│  │                    LLM 调用 (single-shot)                      │   │
│  │  → 返回: reasoning + {"answer": "A"|"B"|"C"|"D"}             │   │
│  └───────────────────────────┬───────────────────────────────────┘   │
│                              │                                       │
│  阶段 4: L0 Review（可选，--review-mode on）                          │
│  ┌───────────────────────────▼───────────────────────────────────┐   │
│  │  micro-02（证据链）+ micro-03（解释竞争）+ micro-04（反偏置） │   │
│  │  → 思维链审查 → 可能覆盖初始答案                               │   │
│  └───────────────────────────┬───────────────────────────────────┘   │
│                              │                                       │
│  ┌───────────────────────────▼───────────────────────────────────┐   │
│  │              验证器（可选重试）                                 │   │
│  │  ScalarProceduralValidator: Scalar Implicature 算术校验        │   │
│  │  → 建议修正 / 触发 LLM 重试                                   │   │
│  └───────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 安装

需要 Python ≥ 3.10。

```bash
git clone <repo-url>
cd tom_harness
pip install -r requirements.txt
```

**额外依赖（RAG 模式）**：

```bash
pip install langchain-core langchain-community faiss-cpu sentence-transformers
```

依赖刻意保持最小：内核只需 **`pydantic>=2` 和 `requests`**。

---

## 数据准备

### 1. Benchmark 数据集

本仓库**不包含**基准测试数据文件，需自行获取并放入对应目录：

| 数据集 | 放置路径 | 格式 | 来源 |
|:-------|:---------|:-----|:-----|
| ToMBench | `benchmark/ToMBench/` | 每任务一个 `.jsonl` 文件（共 20 个） | [ToMBench](https://github.com/zhchen18/ToMBench) |
| CogToM | `benchmark/CogToM/` | `.jsonl` 文件 | [CogToM](https://github.com/Yinghao-Li/CogToM) |
| Tactful-ToM | `benchmark/tactful-tom/` | `.jsonl` 文件 | [Tactful-ToM](https://github.com/sled-group/Tactful-ToM) |
| ICTBench | `benchmark/ICTBench/` | `dataset_v4.json` | 内部数据集 |

放置完成后目录结构示例：

```
benchmark/
├── ToMBench/
│   ├── False Belief Task.jsonl
│   ├── Hinting Task Test.jsonl
│   └── ... (共 20 个文件)
├── CogToM/
│   ├── CogToM-en.jsonl
│   └── CogToM-zh.jsonl
├── tactful-tom/
│   └── ...
└── ICTBench/
    └── dataset_v4.json
```

### 2. Embedding 模型（RAG 模式需要）

RAG 模式使用 [BAAI/bge-m3](https://huggingface.co/BAAI/bge-m3) 作为 embedding 模型。需自行下载到本地：

```bash
# 方式一：使用 huggingface-cli（推荐）
pip install huggingface_hub
huggingface-cli download BAAI/bge-m3 --local-dir model/bge-m3

# 方式二：使用 git lfs
git lfs install
git clone https://huggingface.co/BAAI/bge-m3 model/bge-m3
```

下载后目录结构：

```
model/
└── bge-m3/
    ├── config.json
    ├── tokenizer.json
    ├── model.safetensors
    └── ...
```

> 也可以通过 `--rag_model` 参数指定其他路径或 HuggingFace 模型名称（需联网自动下载）。

### 3. 构建 FAISS 索引（RAG 模式需要）

FAISS 索引会在**首次启用 `--rag` 运行时自动构建**，无需手动操作。构建条件：

- `tom_harness/tools/rag_v2_data/merged_kb_unified.jsonl` 存在（已随仓库提供，1490 条多标签知识）
- `tom_harness/tools/rag_v2_data/unified_taxonomy_flat.json` 存在（43 类统一分类体系）
- embedding 模型已就绪（步骤 2）

首次运行会生成索引缓存到 `tom_harness/tools/rag_v2_index/`，后续运行直接加载，无需重复构建。

如需强制重建索引（例如更换了 embedding 模型），删除索引目录后重新运行即可：

```bash
rm -rf tom_harness/tools/rag_v2_index/
python examples/run_tombench_harness.py --rag --limit 1
```

---

## 配置

Harness 通过 OpenAI 兼容格式的 Chat Completions 接口调用 LLM。设置环境变量（或把 `.env.example` 复制成 `.env` 填上）：

```bash
# 测试模型（被评测的模型）
export TOM_API_BASE="https://dashscope.aliyuncs.com/compatible-mode/v1"
export TOM_API_KEY="<你的 key>"
export TOM_MODEL="qwen3.5-27b"
export TOM_TEMPERATURE="0.0"       # 可选，默认 0.0

# 辅助端点凭证（用于选择器/分类器；模型名复用被评测模型）
export HELPER_API_BASE="..."       # 可选；ToMEval 入口默认复用 experiment_config.yaml 的 api_url
export HELPER_API_KEY="..."        # 可选；ToMEval 入口默认复用 experiment_config.yaml 的 api_key
```

---

## 标准化测评（ToMEval 对齐）

> **推荐方式**：使用 `eval/` 下的脚本进行基准测评。这些脚本完全对齐 ToMEval 的评测流程（数据加载 → prompt 构建 → `\boxed{}` 答案提取 → rule-based / LLM judge → per-dataset metrics），同时支持通过 CLI 开关注入 agent 增强模块。

### 数据与模型配置

ToMEval 对齐测评默认读取 `ToMEval/experiment_config.yaml`：

```yaml
llm:
  model_name: Qwen3-8B
  api_key: not-needed
  api_url: http://0.0.0.0:8000/v1
  max_workers: 16

normalized_datasets_path: datasets
results_path: results
```

- **数据集位置**：`normalized_datasets_path` 默认是 `datasets`。因为脚本会切到 `ToMEval/` 目录运行，所以实际路径是 `ToMEval/datasets/<Dataset>/test-*.parquet`。当前仓库如果没有 `ToMEval/datasets/`，需要先按 ToMEval 的 `download_datasets.sh` / `docs/datasets.md` 准备标准化 parquet 数据，或用 `--datasets-root` 指向已有数据目录。
- **被评测模型**：按照 ToMEval 原生方式，直接写在 `ToMEval/experiment_config.yaml` 的 `llm` 段：`model_name`、`api_url`、`api_key`、`max_workers`。`eval/run_tomeval_harness.py` 不再用 `TOM_API_BASE` / `TOM_API_KEY` / `TOM_MODEL` 覆盖主评测模型，避免和 ToMEval 配置来源不一致。
- **辅助端点**：`--skill` 的路由器、`--rag` 的类别分类器、`--memory` 的 selector 仍属于 agent harness 增强模块。默认复用 `ToMEval/experiment_config.yaml` 的 `llm.model_name`、`llm.api_url`、`llm.api_key`；只有需要把这些辅助调用发到另一个 endpoint/key 时，才设置 `HELPER_API_BASE`、`HELPER_API_KEY` 或 `--helper_api_base`、`--helper_api_key`。模型名不再单独配置。

主评测模型配置示例：

```yaml
# ToMEval/experiment_config.yaml
llm:
  model_name: qwen3-32b
  api_key: <your-key>
  api_url: https://dashscope.aliyuncs.com/compatible-mode/v1
  max_workers: 16
```

辅助端点覆盖示例（可选，写在项目根目录 `.env`）：

```bash
HELPER_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
HELPER_API_KEY=<your-helper-key>
```

### 单次运行

```bash
# 基线（不启用任何 agent 模块）
python eval/run_tomeval_harness.py --datasets HiToM

# 启用 skill routing
python eval/run_tomeval_harness.py --datasets HiToM --skill

# 启用 RAG 检索
python eval/run_tomeval_harness.py --datasets HiToM --rag

# 启用 Memory Playbook
python eval/run_tomeval_harness.py --datasets HiToM --memory

# 全部模块组合
python eval/run_tomeval_harness.py --datasets HiToM --skill --rag --memory

# 多数据集
python eval/run_tomeval_harness.py --datasets HiToM ToMBench TactfulToM EmoBench SocialToM --skill --rag

# 按 ToMEval 四种 protocol 分别跑：direct / direct_think / cot / del_tom
python eval/run_tomeval_harness.py --datasets HiToM --protocols all --max_samples 5

# 只跑指定 protocol
python eval/run_tomeval_harness.py --datasets HiToM --protocols direct cot --max_samples 5

# 只跑双语数据集中的英文样本
python eval/run_tomeval_harness.py --datasets ToMBench EmoBench --lang-filter en
```

### 消融实验

每个 benchmark 有独立的消融脚本，自动跑 5 种模块组合（baseline / skill / rag / memory / skill+rag+memory），跳过已完成的组合。结束后按 protocol 分组打印对比表：同一行是同一个 protocol，列是 5 种模块组合的准确率。

```bash
bash eval/run_tomeval_hitom_ablation.sh
bash eval/run_tomeval_tombench_ablation.sh
bash eval/run_tomeval_tactfultom_ablation.sh
bash eval/run_tomeval_emobench_ablation.sh
bash eval/run_tomeval_socialtom_ablation.sh

# 传递额外参数（如限制样本数）
bash eval/run_tomeval_hitom_ablation.sh --max_samples 50

# 跑 ToMEval 四种 protocol，并按 protocol 比较 5 种模块组合
bash eval/run_tomeval_hitom_ablation.sh --protocols all --max_samples 50

# ToMBench / EmoBench 只跑英文样本，跳过中文样本
bash eval/run_tomeval_tombench_ablation.sh --protocols all --lang-filter en
bash eval/run_tomeval_emobench_ablation.sh --protocols all --lang-filter en
```

输出结构遵循 ToMEval 规范，默认写入 `ToMEval/results/`：

```
ToMEval/results/<Dataset>_ablation_<MMDD>/
├── summary.md                  ← 按 protocol 横向比较 5 种模块组合准确率
├── summary.json                ← summary 的结构化版本
├── 1_baseline/
│   ├── <dataset>/<model>/exp_<timestamp>/          # 单 protocol 时
│   │   ├── prediction.jsonl    ← ToMEval 标准格式
│   │   ├── metrics.json        ← ToMEval 标准格式（含 accuracy）
│   │   └── config.json
│   ├── direct/<dataset>/<model>/exp_<timestamp>/   # --protocols all 时
│   ├── direct_think/<dataset>/<model>/exp_<timestamp>/
│   ├── cot/<dataset>/<model>/exp_<timestamp>/
│   ├── del_tom/<dataset>/<model>/exp_<timestamp>/
│   └── console.log
├── 2_skill/
├── 3_rag/
├── 4_memory/
└── 5_skill_rag_memory/
```

### eval/ CLI 参考

| 参数 | 默认值 | 说明 |
|:---|:---|:---|
| `--experiment-config` | `ToMEval/experiment_config.yaml` | ToMEval 实验配置 |
| `--datasets` | 配置文件中的全部数据集 | 指定要跑的数据集（空格分隔） |
| `--datasets-root` | `ToMEval/datasets` | 标准化 parquet 数据集根目录 |
| `--max-samples` / `--max_samples` | 配置文件中的值 | 每个数据集最多抽样数量（0 = 全量） |
| `--results-path` | 配置文件中的 `results_path` | 结果输出目录 |
| `--protocols` | 配置文件中的 `protocol` | 指定 ToMEval protocol；`all` = direct/direct_think/cot/del_tom |
| `--lang-filter` | 不过滤 | 只运行指定语言样本；可选 `en` / `zh`，适用于 ToMBench、EmoBench 等双语数据集 |
| `--skill` | 关闭 | 启用 Skill Routing（v5.2） |
| `--rag` | 关闭 | 启用 RAG v4 检索 |
| `--memory` | 关闭 | 启用 Memory Playbook |
| `--route-mode` | `hierarchical` | Skill 路由模式 |
| `--inject-mode` | `light` | Skill 注入模式 |

---

## 快速上手（原有 Harness 脚本）

### 跑 ToMBench 基准测试（默认 v5.2 层级路由）

```bash
# 全部任务，每任务 20 样本（基线，不启用任何模块）
python examples/run_tombench_harness.py --limit 20

# 启用技能路由（v5.2, 76 个技能, hierarchical 模式）
python examples/run_tombench_harness.py --skill --limit 20

# 启用 RAG v4 检索
python examples/run_tombench_harness.py --rag --limit 20

# 启用 Memory Playbook（选择器驱动）
python examples/run_tombench_harness.py --memory --limit 20

# 全部模块组合
python examples/run_tombench_harness.py --skill --rag --memory --limit 20

# Skill + L0 review（思维链审查）
python examples/run_tombench_harness.py --skill --review-mode on --limit 20

# 指定路由模式（flat_all 从全部 72 个候选中选取）
python examples/run_tombench_harness.py --skill --route-mode flat_all --limit 20

# 使用遗留 v4 技能路由（22 个技能）
python examples/run_tombench_harness.py --skill --skill-version v4 --limit 20

# 指定任务
python examples/run_tombench_harness.py --tasks "False Belief Task,Hinting Task Test" --limit 10

# 全部样本（不限制数量）
python examples/run_tombench_harness.py --limit 0

# 显示详细日志
python examples/run_tombench_harness.py --tasks "False Belief Task" --limit 5 -v
```

### 跑消融实验

```bash
# 全量数据
bash examples/run_ablation.sh

# 快速测试（每任务 2 样本）
bash examples/run_ablation.sh --limit 2
```

### 跑 CogToM 基准测试

```bash
python examples/run_cogtom_v2_harness.py --limit 20
python examples/run_cogtom_v2_harness.py --category "Belief" --limit 10
python examples/run_cogtom_v2_harness.py --category "Belief,Emotion,Desire" --limit 5
```

### 跑 Tactful-ToM 基准测试

```bash
python examples/run_tactful_tom_harness.py --limit 20
bash examples/run_tactful_tom_ablation.sh --limit 5
```

### 重跑失败样本 / 恢复中断的运行

```bash
python examples/rerun_failed.py results/some_run/ --skill
python examples/rerun_failed.py results/some_run/ --skill --rag --resume
```

### 计算详细统计

```bash
python examples/compute_detailed_stats.py results/ablation_0507
python examples/compute_detailed_stats.py results/ablation_0507/2_skill
```

可用的 ToMBench 任务（`--tasks` 参数需使用精确名称）：

```
Ambiguous Story Task          Completion of Failed Actions
Discrepant Desires            Discrepant Emotions
Discrepant Intentions         Emotion Regulation
False Belief Task             Faux-pas Recognition Test
Hidden Emotions               Hinting Task Test
Knowledge-Attention Links     Knowledge-Pretend Play Links
Moral Emotions                Multiple Desires
Percepts-Knowledge Links      Persuasion Story Task
Prediction of Actions         Scalar Implicature Test
Strange Story Task            Unexpected Outcome Test
```

---

## 技能路由 (v5.2)

默认技能系统使用 **SkillV5Router**：一个 4 阶段 LLM 路由器，覆盖 `skills_v5.2/skills/` 下的 76 个技能（20 macro + 56 micro）。

### 路由模式

| 模式 | 候选数 | 说明 |
|:-----|:-------|:-----|
| `baseline` | 0 | 不路由，不注入技能 |
| `macro_only` | 20 macro | 仅从 macro 技能中选取 |
| `micro_only` | 52 非 L0 micro | 仅从 micro 技能中选取 |
| `hierarchical`（默认） | 20 → 展开 | 第 1 步选 macro；第 2 步从其展开集中选 micro |
| `flat_all` | 72 | 从全部候选中选取（20 macro + 52 非 L0 micro） |

### 注入模式

| 模式 | 说明 |
|:-----|:-----|
| `light`（默认） | 注入解题核心摘要（判定变量、工作流、特殊案例、常见失误、边界退出） |
| `full` | light + 辨别/迁移内容（minimal_pair、do_not_use_when、generalization_note） |

### L0 技能（基础设施层）

| 技能 | 角色 |
|:-----|:-----|
| `micro-01` | 路由准备 — 始终注入为路由器 system prompt |
| `micro-02` | 证据链 — 用于 L0 review |
| `micro-03` | 解释竞争 — 用于 L0 review |
| `micro-04` | 反偏置检查 — 用于 L0 review |

### 遗留 v4 路由

22 个精选技能位于 `tom_harness/tools/skills_v4/`，通过 `--skill-version v4` 选用。使用 `SkillV4Router`，单次 LLM 调用选取一个技能。

---

## RAG 检索（`--rag`）

RAG v4 提供基于统一分类体系的多标签知识检索，使用 LLM 多标签路由 + FAISS 向量检索 + 关键词重排序。

### 数据

1490 条多标签知识文档，覆盖 43 个统一分类类别，来自多个知识源：
- **ATOMIC** — 常识因果知识
- **Social Chemistry** — 社会规范
- **NormBank** — 行为准则
- **EmoBench** — 情绪理解
- **HiToM** — 高阶心智理论
- 及其他扩展知识源

分类体系：`tom_harness/tools/rag_v2_data/unified_taxonomy_flat.json`（43 类，含描述与示例）
知识库：`tom_harness/tools/rag_v2_data/merged_kb_unified.jsonl` | 索引缓存：`tom_harness/tools/rag_v2_index/`
标签缓存：`tom_harness/tools/rag_v2_data/cache/query_tags_unified.jsonl`（5619 条预计算标签）

### 检索流程

1. **LLM 多标签路由**：`UnifiedQueryTagger` 根据问题 + 故事 + 选项，从 43 类中选取 1-3 个最相关类别
2. **候选池过滤**：按类别标签筛选候选文档集
3. **FAISS 向量检索**：在候选池内执行语义相似度搜索
4. **关键词重排序**：基于查询关键词对结果重新排序
5. **兜底保障**：若候选池过滤后无结果，自动退回全库检索，确保每个问题都能获得 RAG 结果

### 用法

```bash
python examples/run_tombench_harness.py --rag --limit 20
```

| 参数 | 默认值 | 说明 |
|:---|:---|:---|
| `--rag` | 关闭 | 启用 RAG v4 检索 |
| `--rag_data_dir` | `tom_harness/tools/rag_v2_data` | RAG 数据目录 |
| `--rag_index_dir` | `tom_harness/tools/rag_v2_index` | FAISS 索引缓存目录 |
| `--rag_model` | `model/bge-m3` | Embedding 模型路径或 HuggingFace 名称 |

---

## Memory Playbook（`--memory`）

基于选择器的策略注入，使用 `memory_playbook` 包。辅助 LLM 对问题进行子任务分类，从 playbook 中选取相关策略条目。

```bash
python examples/run_tombench_harness.py --memory --limit 20
python examples/run_tombench_harness.py --memory --memory_playbook memory_playbook/playbook/final_playbook_pruned.txt
```

| 参数 | 默认值 | 说明 |
|:---|:---|:---|
| `--memory` | 关闭 | 启用 Memory Playbook 注入 |
| `--memory_playbook` | `memory_playbook/playbook/...` | Playbook 文件路径 |

---

## 输出结构

每次运行在 `results/<out_dir>/` 下产出以下文件：

```
results/<out_dir>/
├── results.jsonl              ← 逐样本记录
├── stats.json                 ← 按任务/类别 + 总体准确率统计
├── stats_detailed.json        ← （可选）8 类任务 + 6 能力维度细分
├── run.log                    ← 详细框架日志
└── llm_cache/
    └── llm_interactions.jsonl ← 原始 LLM 请求/响应缓存
```

### results.jsonl 格式

```json
{
  "id": "False Belief Task_0001",
  "task": "False Belief Task",
  "answer": "B",
  "predicted": "B",
  "correct": true,
  "skill_id": "macro-05",
  "skill_ids": ["macro-05", "micro-12"],
  "draft_predicted": "B",
  "review_changed": false,
  "n_llm_calls": 2,
  "elapsed_sec": 5.12,
  "error": null
}
```

### 准确率计算

- `predicted=""`（解析失败）或 `error != null` 的记录计为**错误**
- 准确率 = `correct / (total - errors)` — 错误从分母中排除

---

## CLI 参考

### `run_tombench_harness.py`

| 参数 | 默认值 | 说明 |
|:---|:---|:---|
| `--data_dir` | `benchmark/ToMBench/` | ToMBench JSONL 目录 |
| `--tasks` | 全部任务 | 逗号分隔的任务名 |
| `--limit` | 20 | 每任务最大样本数（0 = 不限制） |
| `--offset` | 0 | 每任务跳过前 N 个样本 |
| `--workers` | 8 | 并行 worker 数 |
| `--verbose` / `-v` | 关闭 | 在控制台显示详细框架日志 |
| `--out_dir` | `results` | 输出根目录 |
| `--skill` | 关闭 | 启用技能注入 |
| `--skill-version` | `v5` | 技能版本：`v4`（22 技能）或 `v5`（76 技能，默认） |
| `--route-mode` | `hierarchical` | 路由模式：baseline / macro_only / micro_only / hierarchical / flat_all |
| `--inject-mode` | `light` | 注入模式：full / light |
| `--review-mode` | `off` | L0 review：on / off |
| `--lang` | `en` | 路由器提示词语言：en / zh |
| `--rag` | 关闭 | 启用 RAG v4 检索 |
| `--rag_data_dir` | `tom_harness/tools/rag_v2_data` | RAG 数据目录 |
| `--rag_index_dir` | `tom_harness/tools/rag_v2_index` | RAG 索引目录 |
| `--rag_model` | `model/bge-m3` | Embedding 模型 |
| `--memory` | 关闭 | 启用 Memory Playbook（选择器驱动） |
| `--memory_playbook` | `memory_playbook/playbook/...` | Playbook 文件路径 |

---

## 项目结构

```
tom_harness/
├── README.md
├── README_zh.md
├── requirements.txt
├── .env.example
│
├── benchmark/                           ← 数据加载器 & 数据集
│   ├── load_tombench.py                 ← ToMBench JSONL 加载器
│   ├── load_cogtom.py                   ← CogToM JSONL 加载器
│   ├── load_tactful_tom.py              ← Tactful-ToM 加载器
│   ├── ToMBench/                        ← ToMBench 数据（20 个任务 .jsonl 文件）
│   ├── CogToM/                          ← CogToM 数据
│   ├── tactful-tom/                     ← Tactful-ToM 数据
│   └── ICTBench/                        ← ICTBench 数据
│
├── skills_v5.2/                         ← v5.2 技能包（默认）
│   └── skills/
│       ├── macro-01..20/                ← 20 个 macro 技能（各含 SKILL.md + unit_pack.json）
│       └── micro-01..56/               ← 56 个 micro 技能（4 L0 + 52 领域）
│
├── memory_playbook/                     ← 静态 playbook 文件
│   └── playbook/
│       └── final_playbook_pruned.txt    ← ACE 精炼的策略
│
├── tom_harness/                         ← 核心包
│   ├── __init__.py                      ← 公共 API：LLMClient, build_default_runtime
│   ├── llm.py                           ← LLM 客户端 + 交互缓存 + JSON 解析
│   ├── runtime.py                       ← HarnessRuntime（单次推理管线）
│   │
│   ├── routing/                         ← 技能路由器
│   │   ├── __init__.py                  ← 重导出：SkillV5Router, SkillV4Router, NoOpRouter
│   │   ├── base.py                      ← Router ABC + RouteDecision
│   │   ├── skill_v5_router.py           ← 4 阶段 LLM 路由器（76 技能, v5.2）
│   │   ├── skill_v4_router.py           ← LLM 路由器（22 技能, v4）
│   │   ├── l0_review.py                 ← L0 Review（micro-02/03/04 思维链审查）
│   │   └── oracle_picks.py              ← 静态查表路由（用于消融对照）
│   │
│   ├── validators/                      ← 程序化验证器
│   │   ├── base.py                      ← Validator ABC + ValidationResult
│   │   └── scalar_procedural.py         ← Scalar Implicature 算术校验
│   │
│   ├── tools/
│   │   ├── base.py                      ← Tool 抽象基类 + ToolResult 封装
│   │   ├── memory.py                    ← MemoryStore（向量索引的任务-计划对, v1）
│   │   ├── playbook.py                  ← MemoryPlaybook（静态策略加载器）
│   │   ├── rag_v2.py                    ← RAGv2Engine（统一分类 FAISS 检索 + LLM 多标签路由）
│   │   ├── rag_v2_data/                 ← 1490 条多标签知识文档 + 43 类统一分类体系
│   │   ├── rag_v2_index/                ← FAISS 索引缓存
│   │   └── skills_v4/                   ← 22 个 v4 SKILL.md 技能（遗留）
│   │
│   ├── plugins/                         ← 插件系统（遗留 hooks）
│   │   └── tom/                         ← ToM 专属插件
│   │       ├── install.py               ← 一键安装 ToM hooks
│   │       ├── validators.py            ← after_step 验证器（信念阶、知识门）
│   │       ├── failure_handlers.py      ← 失败分类 → 恢复技能注入
│   │       └── memory_index.py          ← TaskSignature 提取 + 记忆元数据充实
│   │
│   └── legacy/                          ← Plan-then-Execute 架构（保留）
│       ├── __init__.py
│       ├── schemas.py                   ← Pydantic 数据模型（Plan, Step, Phase 等）
│       ├── context.py                   ← ContextManager（三级上下文）
│       ├── registry.py                  ← ToolRegistry（二维分发）
│       ├── hooks.py                     ← 插件钩子系统（7 个扩展点）
│       ├── planner.py                   ← Planner Agent（问题 → 结构化 Plan）
│       ├── executor.py                  ← Executor Agent（ReAct 循环）
│       └── scheduler.py                ← Scheduler（编排器 + 重规划 + 记忆持久化）
│
├── eval/                                ← ToMEval 对齐测评脚本（推荐）
│   ├── run_tomeval_harness.py           ← ToMEval 桥接 runner（agent 增强 + ToMEval 评测流程）
│   ├── run_tomeval_hitom_ablation.sh    ← HiToM 消融实验
│   ├── run_tomeval_tombench_ablation.sh ← ToMBench 消融实验
│   ├── run_tomeval_tactfultom_ablation.sh ← TactfulToM 消融实验
│   ├── run_tomeval_emobench_ablation.sh ← EmoBench 消融实验
│   └── run_tomeval_socialtom_ablation.sh ← SocialToM 消融实验
│
├── examples/                            ← 原有 Harness 脚本
│   ├── run_tombench_harness.py          ← ToMBench runner（v5.2 默认, --skill-version v4 可选旧版）
│   ├── run_cogtom_v2_harness.py         ← CogToM 基准测试 runner
│   ├── run_tactful_tom_harness.py       ← Tactful-ToM 基准测试 runner
│   ├── run_oracle_skill_experiment.py   ← oracle 技能实验（消融对照）
│   ├── run_ablation.sh                  ← ToMBench 消融实验脚本
│   ├── run_cogtom_ablation.sh           ← CogToM 消融实验脚本
│   ├── run_tactful_tom_ablation.sh      ← Tactful-ToM 消融实验脚本
│   ├── rerun_failed.py                  ← 重跑失败样本 / 恢复中断运行（v5.2 适配）
│   ├── compute_detailed_stats.py        ← 8 任务 + 6 能力维度细分统计
│   └── error_analysis_0507.py           ← 错误模式分析
│
├── docs/                                ← 分析与设计文档
└── results/                             ← 输出（gitignored）
```

---

## 核心组件

### HarnessRuntime (`runtime.py`)

单次推理管线：`route → build_prompt → LLM call → L0 review → validators → answer`。

- `answer_one(question, story, options, task_type)` → `RuntimeResult`
- `build_default_runtime(llm, router, ...)` — 便捷工厂方法，自动接线默认验证器栈

### LLM Client (`llm.py`)

面向 OpenAI 兼容 Chat Completions API 的轻量适配器。

- JSON 解析含鲁棒降级：直接解析 → 代码块提取 → 首个平衡 `{...}` 对象
- 指数退避重试（默认 3 次）
- 剥离 `<think>...</think>` 内联标签
- 可选 JSONL 交互缓存用于调试
- 支持通过 `TOM_TEMPERATURE` 环境变量配置温度

### SkillV5Router (`routing/skill_v5_router.py`)

4 阶段 LLM 路由器。路由管线：

1. **阶段 1（路由准备）**：micro-01 始终注入为路由器 system prompt
2. **阶段 2（路由）**：根据 `route_mode` 选取 0+ 个技能
   - `hierarchical`：选 macro → 展开为 micro → 选 micro
   - 若无 macro 被选中则退化为 `micro_only`
3. **技能渲染**：将选中技能渲染后注入 prompt（`inject_mode`：full 或 light）
4. **阶段 4（L0 review）**：可选的思维链审查，使用 micro-02/03/04

### 验证器 (`validators/`)

- `Validator` ABC：`applies(task_type)` + `validate(...)` → `ValidationResult`
- `ScalarProceduralValidator`：Scalar Implicature 任务的算术校验；可建议答案或触发带反馈的 LLM 重试

---

## Legacy 架构 (`legacy/`)

Plan-then-Execute 架构保留在 `tom_harness/legacy/` 中用于多步研究场景。包含：

| 组件 | 文件 | 用途 |
|:-----|:-----|:-----|
| Schemas | `schemas.py` | Pydantic 模型：Plan, Step, Phase, ExecutionTrace, Memory 等 |
| Context Manager | `context.py` | 三级上下文治理 |
| Tool Registry | `registry.py` | 二维分发 (tool_type, tool_name) |
| Hook System | `hooks.py` | 7 个扩展点 |
| Planner | `planner.py` | 问题 → 结构化多阶段 Plan |
| Executor | `executor.py` | 每步 ReAct 循环 |
| Scheduler | `scheduler.py` | 编排器 + 重规划 + 记忆持久化 |

---

## 插件系统 (`plugins/tom/`)

ToM 专属 hooks，通过 `install.py` 注册：

| Hook | 文件 | 用途 |
|:-----|:-----|:-----|
| `on_step_failure` | `failure_handlers.py` | 失败分类（10+ 类型）→ 恢复技能注入 |
| `enrich_memory` | `memory_index.py` | 提取 TaskSignature → 充实记忆元数据 |
| `after_step` | `validators.py` | 信念阶和知识门一致性检查（警告不中断） |

**TaskSignature**（`memory_index.py`）：纯函数, <1ms, 无 LLM 调用 — 通过正则提取 `task_type`, `question_kind`, `character_count`, `belief_order` 等双语特征。

---

## 设计原则

1. **内核是领域无关的。** `tom_harness/`（`plugins/tom/` 除外）不出现信念、情绪、失言等字眼。
2. **外部知识驱动推理。** 所有 ToM 逻辑存在于技能文件中，不在代码里。
3. **默认单次推理。** Plan-then-Execute 保留但不再是默认路径。
4. **技能版本可切换。** `--skill-version {v4,v5}` 允许显式选择版本。
5. **不引入大型框架。** 内核不依赖 LangChain/AutoGen（仅 RAG 后端使用）。
6. **双语支持。** 特征提取、技能内容、路由器提示词均支持中英文。
7. **线程安全。** Runner 通过 ThreadPoolExecutor 支持并行执行。
8. **可断点续跑。** `rerun_failed.py` 可恢复中断的运行并补全缺失样本。

---

## 全部脚本

### eval/（ToMEval 对齐，推荐）

| 脚本 | 说明 |
|:-----|:-----|
| `eval/run_tomeval_harness.py` | ToMEval 桥接 runner，支持 `--skill`/`--rag`/`--memory` agent 增强 |
| `eval/run_tomeval_hitom_ablation.sh` | HiToM 消融实验（5 种模块组合） |
| `eval/run_tomeval_tombench_ablation.sh` | ToMBench 消融实验 |
| `eval/run_tomeval_tactfultom_ablation.sh` | TactfulToM 消融实验 |
| `eval/run_tomeval_emobench_ablation.sh` | EmoBench 消融实验 |
| `eval/run_tomeval_socialtom_ablation.sh` | SocialToM 消融实验 |

### examples/（原有 Harness 脚本）

| 脚本 | 说明 |
|:-----|:-----|
| `examples/run_tombench_harness.py` | ToMBench 单次推理 runner（v5.2 默认, `--skill-version` 可选 v4） |
| `examples/run_cogtom_v2_harness.py` | CogToM 基准测试 runner |
| `examples/run_tactful_tom_harness.py` | Tactful-ToM 基准测试 runner |
| `examples/run_oracle_skill_experiment.py` | Oracle 技能实验（消融对照） |
| `examples/run_ablation.sh` | ToMBench 消融实验（模块组合） |
| `examples/run_cogtom_ablation.sh` | CogToM 消融实验 |
| `examples/run_tactful_tom_ablation.sh` | Tactful-ToM 消融实验 |
| `examples/rerun_failed.py` | 重跑失败/空预测样本、恢复中断运行（v5.2） |
| `examples/compute_detailed_stats.py` | 8 任务类型 + 6 能力维度细分统计 |
| `examples/error_analysis_0507.py` | 错误模式分析 |

---

## 许可

研究代码 — 见 `LICENSE`（待加）。

---

## 参考文献

- [XSkill](https://arxiv.org/abs/2603.12056) — 经验+技能双流持续学习。
- [Externalization in LLM Agents](https://arxiv.org/abs/2604.08224) — Harness 工程综述。
- [Natural-Language Agent Harnesses](https://arxiv.org/abs/2603.25723) — Harness 作为自然语言 artifact。
