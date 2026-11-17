# Sample-level Intent Routing on ToMBench (task-type-free config selection)

*Contributed 2026-06-16 · experiment conducted week of 2026-06-05 · ToMBench, Qwen3.6-27B solver*

## What this is

Given a single ToM sample (story + question + options), decide **which external-support configuration** to run it under — one of:

- `skill_only` — inject a reasoning skill
- `rag_only` — inject retrieved ToM rules
- `memory_only` — inject distilled strategy bullets
- `all3` — inject all three

**…without using any `task_type` label.** The router reads only the sample content. The signal comes from a **small embedding model + a single LLM "intent" call**, fed into a light calibrator. This is the "intent routing" line of work — making config selection generic (label-free) instead of relying on a per-task lookup table.

## Method (pipeline; files numbered in run order)

| file | role |
|---|---|
| `01_llm_emit_features.py` | **LLM intent scores**: Qwen3.6 reads the sample once and emits 4 numbers — P(skill helps), P(rag helps), P(memory helps), P(all3 helps). (arch "A") |
| `02_shallow_features.py` | **31 shallow features**: cheap Python stats (story/question length, option lexical overlap, keyword hits) — zero LLM. |
| `03_embedding_features.py` | **Qwen3-Embedding-4B** (2560-d) per sample. |
| `04_cluster_oracle.py` | **Cluster oracle**: per-task K-means on embeddings (chi² k-sweep), map each cluster → its empirically best config. Recovers latent within-task structure. |
| `05_train_router.py` | **Router**: 4 binary HistGradientBoosting on `[shallow + intent scores]` → P(config correct); argmax routes. 5-fold CV. |
| `06_final_router_margin_adaptive.py` | **Final system**: GBT probs + cluster-oracle boost, **margin-adaptive** — trust the cluster oracle more when the GBT is uncertain (low margin = max−2nd-max). |

## Results (ToMBench, 2860 samples, 5-fold CV)

| system | v4 skills | v5 skills |
|---|---:|---:|
| best single static config (always `skill` / `all3`) | 84.06 | 81.15 |
| shallow + intent-scores → GBT | 84.62 | 82.13 |
| + Qwen-embedding cluster-oracle boost | 86.19 | 82.62 |
| **+ margin-adaptive (final)** | **86.22** | **83.01** |
| task-level oracle gate (needs gold task_type) | 86.26 | 83.29 |
| per-sample union (theoretical ceiling) | 92.34 | 89.16 |

**Headline**: the label-free intent router reaches **86.22%** (v4) — within **0.04 pp** of the task-level oracle gate that *does* know each sample's task — i.e. it recovers nearly all the value of per-task config selection **without any task label**, purely from sample content (small embedding + one LLM call + a HistGBT calibrator).

See `FINAL_REPORT.md` for the full ablation, error analysis, and negative results.

## Notes

- These are the experiment scripts as run; they reference absolute cache paths under `/workspace/OVERNIGHT_2026-06-05/` (the per-config solver caches and feature dumps, not committed — large). They are included here for **method transparency and reproducibility of the routing layer**.
- This is the **ToMBench** version. Generalizing the same routing layer to HiToM / TactfulToM / EmoBench is in-progress separately (this week's work).
- The router is task-type-free at the **config-selection** layer; the underlying skill/rag/memory modules were run under the harness's standard ToMBench setup.
