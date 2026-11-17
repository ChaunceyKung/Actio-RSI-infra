"""Stage 2 of sample-level routing: 5-fold CV training.

Architecture (Q-table style):
  For each config c ∈ {skill, all3, rag, memory} we train a binary classifier
  P(config c will get this sample right | shallow features).
  At inference time, route to argmax_c P(correct | features).

Why 4 binary classifiers, not 1 multi-class:
  - Per-sample union shows 23 % of items are MIXED (some configs right, some
    wrong). Multi-class would force a single "correct" label per sample;
    binary per-config preserves the multi-label truth and lets argmax pick
    the highest-probability config even when several are correct.

We use Gradient Boosted Trees (sklearn HistGradientBoosting). They handle
mixed feature scales without normalisation and learn interactions.

Reported:
  * CV accuracy of each binary classifier
  * Routing accuracy = sum of "the cached config[argmax] got this sample right"
    over 2860 hold-out folds
  * Per-task breakdown
  * Ceilings: per-sample union 91.78 %, oracle gate 86.26 %
  * V4 / sample-level / Task 1 v2 / ensemble comparison
"""
import json, sys
import numpy as np
from sklearn.model_selection import KFold
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from collections import defaultdict, Counter

SHALLOW = "/workspace/OVERNIGHT_2026-06-05/task3_sample_level/shallow.jsonl"
GATE    = "/workspace/OVERNIGHT_2026-06-02/task7_quadrant/hardcoded_gate_per_task.json"
CFG_PATHS = {
    "skill":  "/workspace/OVERNIGHT_2026-06-02/task5_full/v4_skill_only_full/results.jsonl",
    "all3":   "/workspace/OVERNIGHT_2026-06-02/task5_full/v4_full/results.jsonl",
    "rag":    "/workspace/OVERNIGHT_2026-06-02/task7_quadrant/rag_only_full/results.jsonl",
    "memory": "/workspace/OVERNIGHT_2026-06-02/task7_quadrant/memory_only_full/results.jsonl",
}
CFGS = ["skill", "all3", "rag", "memory"]


def load_data():
    feats = {}
    for line in open(SHALLOW):
        d = json.loads(line)
        feats[d["id"]] = (d["true_task"], d["features"])
    cache = {c: {json.loads(l)["id"]: json.loads(l) for l in open(p)}
             for c, p in CFG_PATHS.items()}
    return feats, cache


def main():
    feats, cache = load_data()
    ids = list(feats.keys())
    n = len(ids)
    feat_names = sorted(next(iter(feats.values()))[1].keys())
    print(f"Loaded {n} samples × {len(feat_names)} features", flush=True)

    X = np.array([[feats[sid][1][k] for k in feat_names] for sid in ids], dtype=float)
    # Labels: for each sample × config → 1 if cache says correct
    Y = np.array([[int(bool(cache[c][sid].get("correct"))) for c in CFGS]
                  for sid in ids], dtype=int)
    # True task name (for per-task breakdown later)
    true_tasks = [feats[sid][0] for sid in ids]

    # Baseline ceilings
    union_correct = sum(1 for i in range(n) if Y[i].max() == 1)
    print(f"\nCeilings:")
    print(f"  per-sample union (any of 4 correct): {union_correct}/{n} = {union_correct/n*100:.2f}%")
    for j, c in enumerate(CFGS):
        a = Y[:, j].mean() * 100
        print(f"  always {c:<7}: {a:.2f}%")
    GATE_YAML = json.load(open(GATE))
    # oracle gate = take config[gate[task]]
    oracle = 0
    for i, sid in enumerate(ids):
        c = GATE_YAML[true_tasks[i]]
        oracle += int(bool(cache[c][sid].get("correct")))
    print(f"  oracle gate (knows task):            {oracle}/{n} = {oracle/n*100:.2f}%")

    # 5-fold CV
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    pred_probs = np.zeros((n, 4))
    fold_results = []
    for fold_idx, (tr, te) in enumerate(kf.split(X), 1):
        for j in range(4):
            # If a class has <2 distinct values in train, skip
            if len(set(Y[tr, j])) < 2:
                pred_probs[te, j] = Y[tr, j].mean()
                continue
            clf = HistGradientBoostingClassifier(max_iter=200, learning_rate=0.06,
                                                  max_depth=5, random_state=42)
            clf.fit(X[tr], Y[tr, j])
            if hasattr(clf, "predict_proba"):
                p = clf.predict_proba(X[te])[:, 1]
            else:
                p = clf.predict(X[te])
            pred_probs[te, j] = p
        fold_results.append(fold_idx)
        print(f"  fold {fold_idx}/5 done", flush=True)

    # Inference: argmax probability → config
    pred_cfg = np.argmax(pred_probs, axis=1)
    routing_correct = sum(int(Y[i, pred_cfg[i]] == 1) for i in range(n))
    print(f"\n=== Sample-level routing (5-fold CV, HistGBT, argmax of 4 P(correct)) ===")
    print(f"  Routing accuracy: {routing_correct}/{n} = {routing_correct/n*100:.2f}%")
    print(f"  vs oracle gate 86.26%, per-sample union 91.78%, T1 v2 85.31%")

    # Per-config calibration (when we routed to c, how often was c correct?)
    print(f"\n  Per-config conditional accuracy when routed:")
    for j, c in enumerate(CFGS):
        mask = pred_cfg == j
        n_routed = mask.sum()
        if n_routed == 0:
            print(f"    {c:<7}: 0 routed")
            continue
        acc = Y[mask, j].mean()
        print(f"    {c:<7}: {n_routed:>4} routed, {acc*100:.2f}% correct, "
              f"cache acc on these samples: skill={Y[mask,0].mean()*100:.1f}, "
              f"all3={Y[mask,1].mean()*100:.1f}, "
              f"rag={Y[mask,2].mean()*100:.1f}, "
              f"memory={Y[mask,3].mean()*100:.1f}")

    # Per-task breakdown
    by_task = defaultdict(lambda: [0, 0])  # [correct, n]
    for i in range(n):
        by_task[true_tasks[i]][1] += 1
        if Y[i, pred_cfg[i]] == 1:
            by_task[true_tasks[i]][0] += 1
    print(f"\n=== Per-task ===")
    print(f"{'task':<35} {'n':>4} {'samp%':>7} {'oracle%':>8}")
    # oracle per-task = always use gate config
    for t in sorted(by_task, key=lambda x: -by_task[x][1]):
        c, nn = by_task[t]
        gate_cfg = GATE_YAML[t]
        rows = [v for v in cache[gate_cfg].values() if v.get("task") == t]
        oracle_t = sum(1 for v in rows if v.get("correct"))/max(len(rows),1)*100
        print(f"{t:<35} {nn:>4} {c/nn*100:>6.2f}% {oracle_t:>7.1f}%")

    # Feature importance (rough): refit on full data with HistGBT, no built-in
    # importance. Use permutation_importance on a subset.
    from sklearn.inspection import permutation_importance
    print(f"\n=== Top-10 feature importance (permutation, target=skill correct) ===")
    clf = HistGradientBoostingClassifier(max_iter=200, learning_rate=0.06, max_depth=5,
                                          random_state=42)
    clf.fit(X, Y[:, 0])
    pi = permutation_importance(clf, X, Y[:, 0], n_repeats=5, random_state=42,
                                 n_jobs=4)
    order = np.argsort(-pi.importances_mean)
    for i in order[:10]:
        print(f"  {feat_names[i]:<28} {pi.importances_mean[i]:.4f} ± {pi.importances_std[i]:.4f}")

    # Save
    out = []
    for i, sid in enumerate(ids):
        out.append({
            "id": sid, "true_task": true_tasks[i],
            "pred_config": CFGS[pred_cfg[i]],
            "probs": {CFGS[j]: float(pred_probs[i, j]) for j in range(4)},
            "correct": bool(Y[i, pred_cfg[i]] == 1),
        })
    with open("/workspace/OVERNIGHT_2026-06-05/task3_sample_level/preds.jsonl", "w") as f:
        for d in out:
            f.write(json.dumps(d) + "\n")
    json.dump({
        "n": n,
        "routing_accuracy": routing_correct / n,
        "per_sample_union_ceiling": union_correct / n,
        "oracle_gate": oracle / n,
        "feature_count": len(feat_names),
        "model": "HistGBT, 5-fold CV, max_iter=200",
    }, open("/workspace/OVERNIGHT_2026-06-05/task3_sample_level/stats.json", "w"), indent=2)


if __name__ == "__main__":
    main()
