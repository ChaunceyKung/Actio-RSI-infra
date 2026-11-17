"""Cluster-oracle upper bound:

For each task, use the within-task best k (from chi² sweep) to k-means cluster.
For each cluster, look up which config has highest success rate ON TRAIN data.
At inference, route by cluster_id → mapped config.

5-fold CV: train per-cluster best config on train fold, evaluate on test.
"""
import json
import numpy as np
from pathlib import Path
from collections import defaultdict
from sklearn.cluster import KMeans
from sklearn.model_selection import KFold
from scipy.stats import chi2_contingency

QWEN_EMB = "/workspace/OVERNIGHT_2026-06-05/task3_embed_qwen/embeddings_qwen4b.npy"
QWEN_IDS = "/workspace/OVERNIGHT_2026-06-05/task3_embed_qwen/ids_qwen4b.json"
CFG_V4 = {
    "skill":  "/workspace/OVERNIGHT_2026-06-02/task5_full/v4_skill_only_full/results.jsonl",
    "all3":   "/workspace/OVERNIGHT_2026-06-02/task5_full/v4_full/results.jsonl",
    "rag":    "/workspace/OVERNIGHT_2026-06-02/task7_quadrant/rag_only_full/results.jsonl",
    "memory": "/workspace/OVERNIGHT_2026-06-02/task7_quadrant/memory_only_full/results.jsonl",
}
CFG_V5 = {
    "skill":  "/workspace/OVERNIGHT_2026-06-05/v5_cache/skill_only/results.jsonl",
    "all3":   "/workspace/OVERNIGHT_2026-06-05/v5_cache/all3/results.jsonl",
    "rag":    "/workspace/OVERNIGHT_2026-06-05/v5_cache/rag_only/results.jsonl",
    "memory": "/workspace/OVERNIGHT_2026-06-05/v5_cache/memory_only/results.jsonl",
}
CFGS = ["skill", "all3", "rag", "memory"]

X = np.load(QWEN_EMB)
ids = json.load(open(QWEN_IDS))

def load_cache(paths):
    out = {c: {} for c in CFGS}
    for c, p in paths.items():
        for line in open(p):
            d = json.loads(line)
            out[c][d["id"]] = d
    return out


def get_best_k(Xt, Yt, mixed_mask, k_range=range(2, 9)):
    """Return (best_k, best_p). Find k that minimises chi² p."""
    best_p, best_k = 1.0, 1
    for k in k_range:
        if len(Xt) < k + 1: continue
        labels = KMeans(n_clusters=k, n_init=10, random_state=42).fit(Xt).labels_
        best_cfg = np.argmax(Yt, axis=1)
        cont = np.zeros((k, 4), int)
        for cl, bc, mm in zip(labels, best_cfg, mixed_mask):
            if mm: cont[cl, bc] += 1
        cont = cont[cont.sum(1) > 0, :][:, cont.sum(0) > 0]
        if cont.shape[0] < 2 or cont.shape[1] < 2:
            continue
        try: _, p, _, _ = chi2_contingency(cont)
        except: p = 1.0
        if p < best_p:
            best_p, best_k = p, k
    return best_k, best_p


def cluster_oracle(Y, label):
    """In-sample: per task pick best k by chi², per cluster pick best config by
    success rate on the training data, then evaluate."""
    cache = load_cache(CFG_V4 if label == "v4" else CFG_V5)
    tasks = [cache["skill"][s]["task"] for s in ids]
    task_arr = np.array(tasks)
    n = len(ids)
    unique_tasks = sorted(set(tasks))

    # 5-fold CV
    kf = KFold(5, shuffle=True, random_state=42)
    pred_cfg = np.zeros(n, dtype=int)
    for tr_idx, te_idx in kf.split(np.arange(n)):
        tr_mask = np.zeros(n, dtype=bool); tr_mask[tr_idx] = True
        # For each task, find best k on TRAIN data only, fit k-means on train,
        # assign train+test cluster labels, then look up per-cluster best config
        for t in unique_tasks:
            mask = task_arr == t
            tr_t = mask & tr_mask
            te_t = mask & ~tr_mask
            if tr_t.sum() < 10:
                # not enough train data; fallback default skill
                pred_cfg[te_t] = 0
                continue
            Xt_tr = X[tr_t]
            Yt_tr = Y[tr_t]
            mixed_tr = (Yt_tr.sum(1) > 0) & (Yt_tr.sum(1) < 4)
            if mixed_tr.sum() < 5:
                # fallback: pick most-successful config on this task
                best_cfg = int(np.argmax(Yt_tr.sum(0)))
                pred_cfg[te_t] = best_cfg
                continue
            # Find best k on train
            best_k, best_p = get_best_k(Xt_tr, Yt_tr, mixed_tr)
            if best_k < 2 or best_p >= 0.05:
                # No significant cluster structure → assign per-task best config
                best_cfg = int(np.argmax(Yt_tr.sum(0)))
                pred_cfg[te_t] = best_cfg
                continue
            # Refit k-means with best_k on train, predict on test
            km = KMeans(n_clusters=best_k, n_init=10, random_state=42).fit(Xt_tr)
            tr_labels = km.labels_
            # Per-cluster best config on train
            cluster_best_cfg = {}
            for cl in range(best_k):
                m = tr_labels == cl
                if m.sum() == 0:
                    cluster_best_cfg[cl] = 0
                    continue
                # success rate per config
                succ = Yt_tr[m].mean(0)
                cluster_best_cfg[cl] = int(np.argmax(succ))
            # Assign test samples
            te_X = X[te_t]
            te_labels = km.predict(te_X)
            te_pred = np.array([cluster_best_cfg[cl] for cl in te_labels])
            pred_cfg[te_t] = te_pred

    # Eval
    ok = sum(int(Y[i, pred_cfg[i]] == 1) for i in range(n))
    mixed = (Y.sum(1) > 0) & (Y.sum(1) < 4)
    mok = sum(int(Y[i, pred_cfg[i]] == 1) for i in range(n) if mixed[i])
    print(f"\n=== Cluster-oracle routing ({label}) ===")
    print(f"  Overall: {ok}/{n} = {ok/n*100:.2f}%   Mixed: {mok}/{mixed.sum()} = {mok/mixed.sum()*100:.2f}%")
    return ok/n, mok/mixed.sum()


def main():
    # v4
    cache_v4 = load_cache(CFG_V4)
    Y4 = np.array([[int(bool(cache_v4[c][s].get("correct"))) for c in CFGS] for s in ids], dtype=int)
    cluster_oracle(Y4, "v4")
    # v5
    cache_v5 = load_cache(CFG_V5)
    Y5 = np.array([[int(bool(cache_v5[c][s].get("correct"))) for c in CFGS] for s in ids], dtype=int)
    cluster_oracle(Y5, "v5")
    # Compare to ref
    print("\nReferences (v4): shallow alone 84.93, T1 v2 85.31, shallow+A 85.52, oracle gate 86.26, oracle ensemble 87.17, union 92.34")
    print("Reference  (v5): shallow alone ~82, shallow+A ~82.1, all3_v5 81.4, union v5 ~89.16")


if __name__ == "__main__":
    main()
