"""Sample-level uncertainty estimation + escalation routing.

Pipeline:
  1. Get per-sample GBT P(config correct) — already calibrated via 5-fold CV
  2. Compute uncertainty signals:
       - margin = max(P) - 2nd_max(P)
       - entropy = -Σ P log P
       - router disagreement = 4 - max-vote count among {GBT, cluster_oracle, k-NN, Fisher_co}
  3. For low-confidence samples, ESCALATE to:
       - all3 (safe default — most context)
       - or run 2-config ensemble (skill + cluster_oracle's pick, then vote)
       - or run with self-consistency on solver (NOT POSSIBLE here without re-solving)
  4. Measure: does escalation recover any of the per-sample union ceiling gap?

Tested on BOTH v4 and v5.
"""
import json
import numpy as np
from sklearn.cluster import KMeans
from sklearn.model_selection import KFold
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.ensemble import HistGradientBoostingClassifier
from scipy.stats import f_oneway

QWEN_EMB = '/workspace/OVERNIGHT_2026-06-05/task3_embed_qwen/embeddings_qwen4b.npy'
QWEN_IDS = '/workspace/OVERNIGHT_2026-06-05/task3_embed_qwen/ids_qwen4b.json'
SHALLOW = '/workspace/OVERNIGHT_2026-06-05/task3_sample_level/shallow.jsonl'
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
CFGS = ['skill', 'all3', 'rag', 'memory']


def load_cache(paths):
    out = {c: {} for c in CFGS}
    for c, p in paths.items():
        for line in open(p):
            d = json.loads(line)
            out[c][d['id']] = d
    return out


def fisher_weights(X_emb, Y, tr_mask):
    mixed = (Y.sum(1) > 0) & (Y.sum(1) < 4)
    tr_mixed = tr_mask & mixed
    w = np.zeros(X_emb.shape[1])
    for d in range(X_emb.shape[1]):
        fs = []
        for c_idx in range(4):
            pos = X_emb[tr_mixed & (Y[:, c_idx] == 1), d]
            neg = X_emb[tr_mixed & (Y[:, c_idx] == 0), d]
            if len(pos) < 5 or len(neg) < 5:
                fs.append(0.0); continue
            try:
                F, _ = f_oneway(pos, neg)
                fs.append(F if not np.isnan(F) else 0.0)
            except: fs.append(0.0)
        w[d] = np.sqrt(max(fs))
    return w / (w.mean() + 1e-9)


def fisher_co(X_emb_orig, Y, K):
    """Fisher-weighted global K-means cluster oracle, 5-fold CV."""
    n = len(Y); pred = np.zeros(n, dtype=int)
    kf = KFold(5, shuffle=True, random_state=42)
    for tr_idx, te_idx in kf.split(np.arange(n)):
        tr_mask = np.zeros(n, dtype=bool); tr_mask[tr_idx] = True
        w = fisher_weights(X_emb_orig, Y, tr_mask)
        Xw = X_emb_orig * w[None, :]
        km = KMeans(n_clusters=K, n_init=10, random_state=42).fit(Xw[tr_mask])
        cbc = {cl: int(np.argmax(Y[tr_mask][km.labels_ == cl].mean(0)))
               if (km.labels_ == cl).sum() else 0 for cl in range(K)}
        te_labels = km.predict(Xw[~tr_mask])
        for i, cl in zip(np.where(~tr_mask)[0], te_labels):
            pred[i] = cbc[cl]
    return pred


def task_co(X_emb, Y, tasks):
    """Task-conditional cluster oracle (per-task K-means)."""
    from scipy.stats import chi2_contingency
    n = len(Y); pred = np.zeros(n, dtype=int)
    kf = KFold(5, shuffle=True, random_state=42)
    ta = np.array(tasks)
    for tr_idx, te_idx in kf.split(np.arange(n)):
        tr_mask = np.zeros(n, dtype=bool); tr_mask[tr_idx] = True
        for t in sorted(set(tasks)):
            mask = ta == t; tr_t = mask & tr_mask; te_t = mask & ~tr_mask
            if tr_t.sum() < 10: pred[te_t] = 0; continue
            Xtr, Ytr = X_emb[tr_t], Y[tr_t]
            mt = (Ytr.sum(1) > 0) & (Ytr.sum(1) < 4)
            if mt.sum() < 5: pred[te_t] = int(np.argmax(Ytr.sum(0))); continue
            best_k, best_p = 1, 1.0
            for k in range(2, 9):
                if len(Xtr) < k + 1: continue
                km = KMeans(n_clusters=k, n_init=10, random_state=42).fit(Xtr)
                bc = np.argmax(Ytr, axis=1)
                cont = np.zeros((k, 4), int)
                for cl, b, mm in zip(km.labels_, bc, mt):
                    if mm: cont[cl, b] += 1
                cont = cont[cont.sum(1) > 0, :][:, cont.sum(0) > 0]
                if cont.shape[0] < 2 or cont.shape[1] < 2: continue
                try: _, p, _, _ = chi2_contingency(cont)
                except: p = 1.0
                if p < best_p: best_p, best_k = p, k
            if best_k < 2 or best_p >= 0.05:
                pred[te_t] = int(np.argmax(Ytr.sum(0))); continue
            km = KMeans(n_clusters=best_k, n_init=10, random_state=42).fit(Xtr)
            cbc = {cl: int(np.argmax(Ytr[km.labels_ == cl].mean(0)))
                   if (km.labels_ == cl).sum() else 0 for cl in range(best_k)}
            pred[te_t] = np.array([cbc[cl] for cl in km.predict(X_emb[te_t])])
    return pred


def knn_predict(X_emb, Y, K_neighbors):
    from sklearn.neighbors import NearestNeighbors
    n = len(Y); pred = np.zeros(n, dtype=int)
    kf = KFold(5, shuffle=True, random_state=42)
    for tr_idx, te_idx in kf.split(np.arange(n)):
        tr_mask = np.zeros(n, dtype=bool); tr_mask[tr_idx] = True
        Xtr, Ytr = X_emb[tr_mask], Y[tr_mask]
        Xte = X_emb[~tr_mask]
        nn = NearestNeighbors(n_neighbors=K_neighbors, metric='cosine').fit(Xtr)
        _, idx = nn.kneighbors(Xte)
        for j, neighbors in enumerate(idx):
            scores = Ytr[neighbors].sum(0)
            pred[np.where(~tr_mask)[0][j]] = int(np.argmax(scores))
    return pred


def eval_pred(Y, p):
    n = len(Y); ok = sum(int(Y[i, p[i]] == 1) for i in range(n))
    mix = (Y.sum(1) > 0) & (Y.sum(1) < 4)
    mok = sum(int(Y[i, p[i]] == 1) for i in range(n) if mix[i])
    return ok/n, mok/mix.sum()


def main():
    X = np.load(QWEN_EMB)
    ids = json.load(open(QWEN_IDS))
    Xp = PCA(n_components=128, random_state=42).fit_transform(StandardScaler().fit_transform(X))

    shallow = {json.loads(l)['id']: json.loads(l)['features']
               for l in open(SHALLOW)}
    sn = sorted(next(iter(shallow.values())).keys())
    Xs = np.array([[shallow[s][k] for k in sn] for s in ids], dtype=float)
    arch_a = {json.loads(l)['id']: (json.loads(l).get('features') or {})
              for l in open('/workspace/OVERNIGHT_2026-06-05/task1_llm_emit/A_4prob.jsonl')}
    Xa = np.array([[float((arch_a.get(s, {}).get(f"p_{c}") or 0)) for c in CFGS] for s in ids])

    for label, paths in [('v4', CFG_V4), ('v5', CFG_V5)]:
        print(f"\n{'='*70}\n[{label}] sample-level uncertainty experiments\n{'='*70}")
        cache = {c: {json.loads(l)['id']: json.loads(l) for l in open(p)} for c, p in paths.items()}
        Y = np.array([[int(bool(cache[c][s].get('correct'))) for c in CFGS] for s in ids], dtype=int)
        n = len(Y)
        tasks = [cache['skill'][s]['task'] for s in ids]
        mixed = (Y.sum(1) > 0) & (Y.sum(1) < 4)

        # Train shallow+A GBT to get calibrated P
        kf = KFold(5, shuffle=True, random_state=42)
        X_sa = np.hstack([Xs, Xa])
        pp_sa = np.zeros((n, 4))
        for tr, te in kf.split(X_sa):
            for j in range(4):
                if len(set(Y[tr, j])) < 2:
                    pp_sa[te, j] = Y[tr, j].mean(); continue
                clf = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05,
                                                      max_depth=6, random_state=42)
                clf.fit(X_sa[tr], Y[tr, j])
                pp_sa[te, j] = clf.predict_proba(X_sa[te])[:, 1]
        pred_sa = np.argmax(pp_sa, axis=1)
        ok_sa, mok_sa = eval_pred(Y, pred_sa)
        print(f"\n  base: shallow+A GBT                 overall {ok_sa*100:5.2f}%  mixed {mok_sa*100:5.2f}%")

        # Compute uncertainty signals from pp_sa
        margin = np.sort(pp_sa, axis=1)[:, -1] - np.sort(pp_sa, axis=1)[:, -2]
        # entropy
        p_norm = pp_sa / (pp_sa.sum(1, keepdims=True) + 1e-9)
        entropy = -(p_norm * np.log(p_norm + 1e-9)).sum(1)

        # Other routers
        print(f"  computing cluster oracle, k-NN, Fisher_co (5-fold each)...")
        co_task = task_co(X, Y, tasks)
        co_fisher = fisher_co(Xp, Y, 50)
        co_knn = knn_predict(Xp, Y, 50)

        # Compute multi-router agreement
        all_picks = np.vstack([pred_sa, co_task, co_fisher, co_knn])
        agreement = np.zeros(n, dtype=int)
        for i in range(n):
            from collections import Counter
            c = Counter(all_picks[:, i])
            agreement[i] = c.most_common(1)[0][1]  # max vote count

        # Sample union: any of {pred_sa, co_task, co_fisher, co_knn} is correct
        union_correct = 0
        for i in range(n):
            cfgs = set(all_picks[:, i])
            if any(Y[i, c] == 1 for c in cfgs):
                union_correct += 1
        print(f"  4-router union ceiling                overall {union_correct/n*100:5.2f}%")

        # ── METHOD A: margin-based escalation ──
        # Sort by margin; lowest margin samples switched to "all3" (safe default)
        print(f"\n  --- METHOD A: low-margin → escalate to all3 ---")
        for frac in [0.05, 0.10, 0.15, 0.20, 0.30, 0.50]:
            cutoff = np.quantile(margin, frac)
            pred_esc = pred_sa.copy()
            pred_esc[margin <= cutoff] = CFGS.index('all3')
            ok, mok = eval_pred(Y, pred_esc)
            print(f"    escalate bottom {int(frac*100)}% margin → all3:   overall {ok*100:5.2f}%  mixed {mok*100:5.2f}%")

        # ── METHOD A': low-margin → switch to cluster_oracle's pick ──
        print(f"\n  --- METHOD A': low-margin → escalate to cluster_oracle pick ---")
        for frac in [0.05, 0.10, 0.15, 0.20, 0.30]:
            cutoff = np.quantile(margin, frac)
            pred_esc = pred_sa.copy()
            mask_low = margin <= cutoff
            pred_esc[mask_low] = co_task[mask_low]
            ok, mok = eval_pred(Y, pred_esc)
            print(f"    escalate bottom {int(frac*100)}% margin → co_task:  overall {ok*100:5.2f}%  mixed {mok*100:5.2f}%")

        # ── METHOD B: disagreement-based escalation ──
        print(f"\n  --- METHOD B: low-agreement → escalate ---")
        # agreement counts the max-vote across {pred_sa, co_task, co_fisher, co_knn}
        # agreement=4: full agreement; agreement=1: all 4 disagree (impossible since only 4 configs)
        # agreement levels: 4, 3, 2 (or sometimes lower in rare cases)
        from collections import Counter
        print(f"    agreement distribution: {dict(Counter(agreement.tolist()))}")
        # For samples with agreement < 4, escalate to all3
        for thresh in [4, 3, 2]:
            mask = agreement < thresh
            pred_esc = pred_sa.copy()
            pred_esc[mask] = CFGS.index('all3')
            ok, mok = eval_pred(Y, pred_esc)
            n_esc = mask.sum()
            print(f"    agreement<{thresh} ({n_esc} samples) → all3:        overall {ok*100:5.2f}%  mixed {mok*100:5.2f}%")

        # ── METHOD B': use majority vote among 4 routers ──
        print(f"\n  --- METHOD B': majority vote of 4 routers (no escalation) ---")
        majority_pred = np.zeros(n, dtype=int)
        for i in range(n):
            c = Counter(all_picks[:, i])
            majority_pred[i] = c.most_common(1)[0][0]
        ok, mok = eval_pred(Y, majority_pred)
        print(f"    majority vote                              overall {ok*100:5.2f}%  mixed {mok*100:5.2f}%")

        # ── METHOD B'': weighted vote by per-router historical accuracy ──
        # On each fold, weight router by its train-fold accuracy
        # For simplicity: equal weights with tie-break by router order [pred_sa, co_task, co_fisher, co_knn]
        # (tie -> co_task wins, since it's strongest individually)
        print(f"  --- METHOD B'': tie-break = co_task ---")
        wpred = np.zeros(n, dtype=int)
        for i in range(n):
            c = Counter(all_picks[:, i])
            top_count = c.most_common(1)[0][1]
            top_cfgs = [k for k, v in c.items() if v == top_count]
            if len(top_cfgs) == 1:
                wpred[i] = top_cfgs[0]
            else:
                # break tie by co_task
                wpred[i] = co_task[i] if co_task[i] in top_cfgs else top_cfgs[0]
        ok, mok = eval_pred(Y, wpred)
        print(f"    majority + co_task tiebreak                overall {ok*100:5.2f}%  mixed {mok*100:5.2f}%")

        # ── METHOD C: k-NN neighborhood best_config consistency (already tried elsewhere) ──
        # (Skipped — duplicates earlier k-NN routing)

        # ── METHOD E: routing-confidence-weighted boost ──
        # For samples where shallow+A is uncertain (low margin), trust cluster_oracle more
        print(f"\n  --- METHOD E: confidence-adaptive co_boost ---")
        # boost_w = 0.1 + α * (1 - margin)
        for alpha in [0.0, 0.1, 0.2, 0.3, 0.5]:
            adaptive_boost = 0.1 + alpha * (1 - margin)  # bigger boost for low-margin
            pp_boost = pp_sa.copy()
            for i in range(n):
                pp_boost[i, co_task[i]] += adaptive_boost[i]
            pred_b = np.argmax(pp_boost, axis=1)
            ok, mok = eval_pred(Y, pred_b)
            print(f"    adaptive co_task boost α={alpha}:           overall {ok*100:5.2f}%  mixed {mok*100:5.2f}%")


if __name__ == "__main__":
    main()
