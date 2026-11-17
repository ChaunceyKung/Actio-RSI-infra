#!/usr/bin/env bash
# ICTBench 消融实验：5 种模块组合 (skill × rag × memory)
#
# 用法:
#   bash examples/run_ictbench_ablation.sh                          # 全量数据
#   bash examples/run_ictbench_ablation.sh --limit 5                # 每 bucket 5 条试跑
#   bash examples/run_ictbench_ablation.sh --question-types Q1,Q2,Q3  # 跳过 Q4 省 judge 成本
#   bash examples/run_ictbench_ablation.sh --perspectives first_person
#
# 已完成的组合会自动跳过（检测 stats.json），删除对应目录可重跑。
#
# 环境变量:
#   TOM_API_BASE, TOM_API_KEY, TOM_MODEL     — 被测模型
#   HELPER_API_BASE, HELPER_API_KEY, HELPER_MODEL — skill 路由 / memory 选择
#   JUDGE_API_BASE, JUDGE_API_KEY, JUDGE_MODEL   — Q4 LLM-as-judge 评分

set -euo pipefail

EXTRA_ARGS="${*}"
BASE_DIR="results/ictbench_ablation_$(date +%m%d)"
RUNNER="python examples/run_ictbench_harness.py"

# 如果未指定 --limit，默认全量
if [[ ! "$EXTRA_ARGS" =~ "--limit" ]]; then
    EXTRA_ARGS="--limit 0 $EXTRA_ARGS"
fi

mkdir -p "$BASE_DIR"

NAMES=(
    "1_baseline"
    "2_skill"
    "3_rag"
    "4_memory"
    "5_skill_rag_memory"
)
FLAGS=(
    ""
    "--skill"
    "--rag"
    "--memory"
    "--skill --rag --memory"
)

TOTAL=${#NAMES[@]}

for i in $(seq 0 $((TOTAL - 1))); do
    name="${NAMES[$i]}"
    flag="${FLAGS[$i]}"
    OUT_DIR="$BASE_DIR/$name"
    NUM=$((i + 1))

    echo ""
    echo "============================================================"
    echo "[$NUM/$TOTAL] $name"
    echo "  Flags: ${flag:-(none)}"
    echo "  Output: $OUT_DIR"
    echo "============================================================"

    if [ -f "$OUT_DIR/stats.json" ]; then
        echo "  → Already completed, skipping. Delete $OUT_DIR/stats.json to re-run."
        continue
    fi

    mkdir -p "$OUT_DIR"
    $RUNNER $EXTRA_ARGS $flag --out_dir "$OUT_DIR" 2>&1 | tee "$OUT_DIR/console.log"

    echo "  → Done."
done

# ── 汇总表 ──────────────────────────────────────────────────────────
echo ""
echo "============================================================"
echo " ICTBench Ablation Summary — $(date)"
echo " Results dir: $BASE_DIR"
echo "============================================================"
echo ""

python3 - "$BASE_DIR" "${NAMES[@]}" << 'PYEOF'
import json, sys, os

base_dir = sys.argv[1]
names = sys.argv[2:]

# ── Overall ──────────────────────────────────────────────────────────
header = f"{'Config':<25s} {'Total':>6s} {'Correct':>7s} {'Acc':>8s} {'Errors':>6s} {'Q2-F1':>7s} {'Q4-Ratio':>9s}"
sep    = f"{'-'*25} {'-'*6} {'-'*7} {'-'*8} {'-'*6} {'-'*7} {'-'*9}"
print(header)
print(sep)

for name in names:
    stats_path = os.path.join(base_dir, name, "stats.json")
    if not os.path.exists(stats_path):
        print(f"{name:<25s} {'(not run)':>6s}")
        continue
    with open(stats_path) as f:
        s = json.load(f)
    o = s["overall"]
    q2f1 = s.get("q2_avg_f1", 0)
    q4r = s.get("q4_avg_score_ratio", 0)
    print(f"{name:<25s} {o['total']:6d} {o['correct']:7d} {o['accuracy']*100:7.2f}% {o['errors']:6d} {q2f1*100:6.1f}% {q4r*100:8.1f}%")

# ── Per question type ─────────────────────────────────────────────────
print()
print("Per-question-type accuracy:")
print()

all_qt = set()
config_qt = {}
for name in names:
    stats_path = os.path.join(base_dir, name, "stats.json")
    if not os.path.exists(stats_path):
        continue
    with open(stats_path) as f:
        s = json.load(f)
    config_qt[name] = s.get("per_question_type", {})
    all_qt.update(s.get("per_question_type", {}).keys())

if all_qt and config_qt:
    short_names = [n.split("_", 1)[1] if "_" in n else n for n in names if n in config_qt]
    col_w = max(10, max(len(sn) for sn in short_names) + 1)
    header2 = f"{'Question Type':<15s}" + "".join(f"{sn:>{col_w}s}" for sn in short_names)
    print(header2)
    print("-" * len(header2))

    for qt in sorted(all_qt):
        row = f"{qt:<15s}"
        for name in names:
            if name not in config_qt:
                continue
            qs = config_qt[name].get(qt)
            if qs:
                row += f"{qs['accuracy']*100:>{col_w}.1f}"
            else:
                row += f"{'—':>{col_w}s}"
        print(row)

# ── Per perspective ───────────────────────────────────────────────────
print()
print("Per-perspective accuracy:")
print()

all_persp = set()
config_persp = {}
for name in names:
    stats_path = os.path.join(base_dir, name, "stats.json")
    if not os.path.exists(stats_path):
        continue
    with open(stats_path) as f:
        s = json.load(f)
    config_persp[name] = s.get("per_perspective", {})
    all_persp.update(s.get("per_perspective", {}).keys())

if all_persp and config_persp:
    short_names = [n.split("_", 1)[1] if "_" in n else n for n in names if n in config_persp]
    col_w = max(10, max(len(sn) for sn in short_names) + 1)
    header3 = f"{'Perspective':<15s}" + "".join(f"{sn:>{col_w}s}" for sn in short_names)
    print(header3)
    print("-" * len(header3))

    for p in sorted(all_persp):
        row = f"{p:<15s}"
        for name in names:
            if name not in config_persp:
                continue
            ps = config_persp[name].get(p)
            if ps:
                row += f"{ps['accuracy']*100:>{col_w}.1f}"
            else:
                row += f"{'—':>{col_w}s}"
        print(row)

# ── Per category (cognitive dimension) ────────────────────────────────
print()
print("Per-category (cognitive dimension) accuracy:")
print()

all_cats = set()
config_cats = {}
for name in names:
    stats_path = os.path.join(base_dir, name, "stats.json")
    if not os.path.exists(stats_path):
        continue
    with open(stats_path) as f:
        s = json.load(f)
    config_cats[name] = s.get("per_category", {})
    all_cats.update(s.get("per_category", {}).keys())

if all_cats and config_cats:
    short_names = [n.split("_", 1)[1] if "_" in n else n for n in names if n in config_cats]
    col_w = max(10, max(len(sn) for sn in short_names) + 1)
    header4 = f"{'Category':<30s}" + "".join(f"{sn:>{col_w}s}" for sn in short_names)
    print(header4)
    print("-" * len(header4))

    for cat in sorted(all_cats):
        row = f"{cat:<30s}"
        for name in names:
            if name not in config_cats:
                continue
            cs = config_cats[name].get(cat)
            if cs:
                row += f"{cs['accuracy']*100:>{col_w}.1f}"
            else:
                row += f"{'—':>{col_w}s}"
        print(row)

# ── Per eval mode ─────────────────────────────────────────────────────
print()
print("Per-eval-mode accuracy:")
print()

all_em = set()
config_em = {}
for name in names:
    stats_path = os.path.join(base_dir, name, "stats.json")
    if not os.path.exists(stats_path):
        continue
    with open(stats_path) as f:
        s = json.load(f)
    config_em[name] = s.get("per_eval_mode", {})
    all_em.update(s.get("per_eval_mode", {}).keys())

if all_em and config_em:
    short_names = [n.split("_", 1)[1] if "_" in n else n for n in names if n in config_em]
    col_w = max(10, max(len(sn) for sn in short_names) + 1)
    header5 = f"{'Eval Mode':<15s}" + "".join(f"{sn:>{col_w}s}" for sn in short_names)
    print(header5)
    print("-" * len(header5))

    for em in sorted(all_em):
        row = f"{em:<15s}"
        for name in names:
            if name not in config_em:
                continue
            es = config_em[name].get(em)
            if es:
                row += f"{es['accuracy']*100:>{col_w}.1f}"
            else:
                row += f"{'—':>{col_w}s}"
        print(row)

PYEOF

echo ""
echo "Done. Full results in: $BASE_DIR/"
