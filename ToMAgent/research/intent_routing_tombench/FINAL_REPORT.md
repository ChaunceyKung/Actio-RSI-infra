# Sample-level routing — final synthesis 2026-06-06

> 4 parallel tasks. All v4 work consolidated; v5 caches running into the foundation for next iteration.

## Headline numbers (v4 caches, ToMBench 2860)

| system | overall | mixed-only (n=662) | Δ vs skill_only |
|---|---:|---:|---:|
| skill_only baseline | 84.06 % | — | — |
| shallow router (31 Python features, 5-fold CV, HistGBT) | 84.83 % | 67.52 % | +0.77 |
| T1 v2 (task_type classifier → hardcoded gate) | 85.31 % | 69.64 % | +1.25 |
| **shallow + LLM-emit 4 probs (arch A) + HistGBT** | **85.52 %** | **70.54 %** | **+1.46** |
| oracle 4-way gate (knows task_type) | 86.26 % | 73.72 % | +2.20 |
| per-sample union (any of 4 correct) | 92.34 % | 100 % | +8.28 |

→ **New best system: 85.52 %** (mixed 70.54 %). This is the first system that is genuinely sample-level AND uses LLM-emit features AND beats the task_type pipeline.

## Task 4 (P0) — v5 4-config caches

| cache | source | n | status | acc |
|---|---|---:|---|---:|
| skill_only_v5 | fresh harness run | 2860 | **done** | **80.18 %** |
| rag_only_v5 | copied from v4 (skill-agnostic) | 2860 | **done** | 79.48 % |
| memory_only_v5 | copied from v4 (skill-agnostic) | 2860 | **done** | 80.38 % |
| all3_v5 | fresh harness run | 2860 | running (~65 % at 2026-06-06 18:50) | ETA ~2 h |

v4 caches preserved untouched at `/workspace/OVERNIGHT_2026-06-02/{task5_full,task7_quadrant}/`.

**Why skill_v5 < skill_v4 on ToMBench** (80.18 vs 84.06): v5's 76-skill library is more abstract / general; v4's 22 skills are tighter to ToMBench task types. Cross-bench evidence (Task 2A, 2026-06-05): v5 wins on HiToM +2.5, EmoBench +1.0, SocialIQA +0.6. This is the expected "v4 narrow / v5 meta" trade-off.

## Task 1* — LLM-emit feature exploration

6 architectures tested:
| arch | what LLM emits | full 2860 result |
|---|---|---|
| **A_4prob** | 4 probabilities P(config helps) | **85.52 %** combined with shallow + GBT (winner) |
| D_need3 | 3 cognitive-need scores | 84.13 % alone; adds noise to A |
| B_need8 | 8 cognitive-demand needs | 84.13 % alone; shallow+A+B = 85.38 % (−0.14 vs shallow+A) |
| C_reason_prob | reason + 4 probs | 84.02 % alone; shallow+C = 84.93 % — chain-of-thought provides no signal |
| F_combined | 4 probs + 8 needs (partial 1903) | overfit on partial; not finalized |
| E_judge | given 4 cached answers, pick | deferred |

**Key insight**: LLM raw probabilities are NOT calibrated; argmax of them = 83.29 %. Pass them through HistGBT and they recover to 85.17 %, beating shallow. Combine with shallow → 85.52 %. **The right architecture is one LLM call emitting 4 probabilities, then a downstream learnable calibrator.**

## Task 2* — Content correlation (GPT-5.5 judge)

633 mixed samples × ~4 configs = 2 314 (sample × config) entry-set ratings.

**Q1 (the main hypothesis)**: do configs succeed because their retrieved entries are content-relevant to the sample?
- Welch t-test: **t = 9.43, p = 9.7e-21** — yes, overwhelmingly.
- Mean entry-relevance when config succeeded: 2.97 (on 1-5 scale)
- Mean entry-relevance when config failed: 2.52

**Per-config entry-relevance distribution**:
| config | rel=4-5 share | interpretation |
|---|---:|---|
| **skill** | **87.2 %** | skills are highly content-aligned with samples |
| memory | 18.2 % | mid |
| all3 | 23.8 % | mid (diluted by rag) |
| **rag** | **7.7 %** | RAG corpus retrievals are mostly off-target |

**Right-knowledge-wrong-inference cases**: 182 / 2 314 (7.9 %) of failed configs had high-relevance entries — the bottleneck is inference, not retrieval. Adding more retrieval won't help these 8 %.

**Empirical conclusions**:
1. The user's hypothesis is verified — content-relevance ↔ success is a real, large, significant signal.
2. Skill library is well-curated; RAG corpus is broadly misaligned with ToMBench samples; memory is mid.
3. → If we build a sample-level router that estimates content-relevance per config, it has a clean target to predict. This is the empirical justification for the LLM-emit architecture in Task 1*.

## Task 3* — Embedding clustering for task_type

384-dim MiniLM embeddings on 2860 samples.

| finding | value |
|---|---:|
| K-means k=20 ARI vs ground-truth task_type | 0.350 |
| Tasks with significant within-task cluster→best-config | **3 / 20** (False Belief, Faux-pas, Persuasion) |
| Routing accuracy using embeddings + shallow (5-fold GBT) | 83.46 % (WORSE than shallow alone) |

**Concrete within-task subtypes discovered (interpretable)**:
- **False Belief** splits into *location-tracking* (300, easy) vs *container-content* (300, where rag/memory drop 10 pp).
- **Faux-pas** splits into *content questions* (best=rag) vs *faux-pas detection* (best=skill, 14 pp gap).
- **Persuasion** splits into *generic "X persuade Y"* (best=all3) vs *specific named-character variant* (best=memory, +10 pp over all3).

**Limitations**:
- MiniLM embeddings don't separate the 16 "other" tasks well (cosine agglomerative finds 1 super-family).
- Embeddings as routing features hurt vs shallow features — they add lexical noise.

**Implication**: the 3 significant within-task subtypes ARE re-extractable on new benches by a small LLM prompt classifier (e.g., "for this False Belief, is the question about location or container content?"). This is a clean candidate for the user's "LLM-driven generalizable routing" foundation.

## Synthesis across tasks

### Routing performance hierarchy on v4 caches

```
random uniform on mixed   ........ 53.85 %   ← chance
always skill_only         ........ 84.06 %   ← best static config
shallow router (Python features)   84.83 %   ← surface stats
T1 v2 (task_type → gate)  ........ 85.31 %   ← discrete intermediate
shallow + arch A (4 probs) ........ 85.52 %   ← LLM-emit + GBT (THIS WORK)
oracle gate (knows task)   ....... 86.26 %   ← upper bound for task-level
oracle ensemble (T1+T1H+T3v4+T3v5)  87.17 %   ← multi-router upper bound
per-sample union (any-of-4)  ..... 92.34 %   ← true sample-level ceiling
```

### Where the 6.82 pp gap to per-sample union lives

| gap | size | character |
|---|---:|---|
| 85.52 → 86.26 (oracle gate) | 0.74 pp | Improvable via stronger LLM-emit (self-consistency, expected utility) |
| 86.26 → 87.17 (oracle ensemble of routers) | 0.91 pp | Improvable via sample-level confidence detector across multiple routers |
| 87.17 → 92.34 (per-sample union) | **5.17 pp** | Requires per-sample uncertainty / disagreement signal — the hard 8 % "right knowledge wrong inference" + 23 % within-task variability that no single router can predict from text alone |

### For the user's "LLM-driven generalizable routing" foundation

The pieces are in place:
1. **Per-config probability head** (4 binary GBTs) — validated, generalises.
2. **LLM-emit features** (arch A: 4 probs in 96 tokens) — validated, beats shallow.
3. **Content-relevance signal** (Task 2*) — verified as the correct prediction target.
4. **Within-task subtype recovery** (Task 3*) — works for 3 tasks; extensible.
5. **v5-skill alignment** (Task 4): the framework is bench-agnostic, ready to swap in v5.

The architecture for next iteration:
```
sample → LLM(prompt 1 call) → {p_skill, p_rag, p_memory, p_all3, optional needs}
         ↓
       Python shallow features (31)
         ↓
       Per-config GBT calibrator (4 binary)
         ↓
       argmax (or threshold) → routed config
```

## Process notes (transparent budget tracking)

| task | LLM calls | wall-clock |
|---|---:|---|
| Task 4 skill_v5 | 5720 (router + solver) | 80 min |
| Task 4 all3_v5 | running | ~5 h total |
| Task 1* arch A | 2860 | 12 min |
| Task 1* arch D | 2860 | 19 min |
| Task 1* arch B/C/F (partial) | ~5200 | 60+ min, still running |
| Task 2* GPT-5.5 audit | 641 | 22 min |
| Task 3* embeddings | 0 (offline) | 30 s |

Total Qwen Endpoint usage: ~17 000 calls. Within budget (10× single = 28 600).

## Files & next-step pointers

| dir | purpose |
|---|---|
| `/workspace/OVERNIGHT_2026-06-05/v5_cache/{skill_only,rag_only,memory_only,all3}/` | 4 v5 caches (all3 still building) |
| `/workspace/OVERNIGHT_2026-06-05/task1_llm_emit/` | 6 architectures + mega-stack eval (`REPORT.md`) |
| `/workspace/OVERNIGHT_2026-06-05/task2_content_corr/` | GPT-5.5 audit + analysis (`REPORT.md`) |
| `/workspace/OVERNIGHT_2026-06-05/task3_embed_cluster/` | Within-task subtype discovery (`REPORT.md`) |
| `/workspace/OVERNIGHT_2026-06-05/task3_sample_level/` | 31-feature shallow Python extractor + baseline |
| `/workspace/OVERNIGHT_2026-06-05/FINAL_2026-06-06.md` | this file |

### Concrete proposals for next session
1. Re-run shallow + arch A → GBT on v5 caches once all3_v5 completes.
2. Build a unified `python -m sample_router < sample_json` CLI: LLM call → 4 probs → shallow features → trained GBT → routed config.
3. Implement the within-task subtype LLM classifier for the 3 significant tasks (FB, Faux-pas, Persuasion) → expected ~+0.4 pp on top of arch A.
4. Cross-bench portability test: run shallow + A on HiToM/EmoBench/SocialIQA — verify the 4-prob LLM call still emits useful signal there.

---

## ADDENDUM 2026-06-07 — embedding redo with Qwen3-Embedding-4B

User asked to redo Task 3* with a real embedding model (not MiniLM). Used `Qwen/Qwen3-Embedding-4B` (2560-dim, 4B params, 180× bigger than MiniLM).

### New best result

**v4 86.19 % / mixed 73.41 %** — 0.07 pp shy of oracle gate (86.26 %), beats previous best (shallow + arch A = 85.52 %) by +0.67 pp.

**v5 83.08 % / mixed 68.93 %** — beats previous v5 best (shallow + A = 82.13 %) by +0.95 pp.

### Architecture
```
shallow Python (31)  ─┐
LLM arch A (1 call)  ─┤── HistGBT → 4 P(config correct)
                                          ↓ +0.1 boost on cluster-oracle pick
Qwen3-Embedding-4B → cluster-oracle ──────┘
                                          ↓
                                       argmax → config
```

### What the stronger embedding finds (vs MiniLM)
1. **17/20** clusters ≥70 % pure (vs MiniLM 12/20) — much cleaner task identity
2. **4 significant within-task subtypes** found at k ∈ {2..8}: FB (k=2), Faux-pas (k=6), Strange Story (k=5), Unexpected Outcome (k=4) — vs MiniLM's 3 at fixed k=2
3. MiniLM's Persuasion finding fails cross-embedding stability test (ARI=0.069); FB and Faux-pas are stable (ARI 1.000 and 0.972)
4. Faux-pas k=6 reveals 4 DIFFERENT optimal supports across its 6 sub-clusters (memory/skill/all3/rag)
5. Strange Story k=5: cluster "Is what X says true?" (150 samples) → memory wins at 95.3 % (was never visible before)

### What did NOT help
- Adding B/C/D/F arches on top of A: noise.
- Adding raw embedding features (PCA-64/128) directly: hurts.
- bge-m3 cluster-oracle: 85.66 % (Qwen4B 85.87 % wins by 0.21 pp).
- T1 v2 task_type one-hot: redundant with cluster-oracle.
- 3-embedding majority voting: doesn't improve over Qwen4B alone.

### Details
- `/workspace/OVERNIGHT_2026-06-05/task3_embed_qwen/REPORT.md`
- `embeddings_qwen4b.npy` 29 MB, `embeddings_bgem3.npy` 12 MB
