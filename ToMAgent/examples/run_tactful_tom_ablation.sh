#!/usr/bin/env bash
# TactfulToM 消融实验：5 种模块组合 (skill × rag × memory)
#
# 用法:
#   bash examples/run_tactful_tom_ablation.sh                     # 全量数据
#   bash examples/run_tactful_tom_ablation.sh --limit 5           # 每 question type 5 条试跑
#   bash examples/run_tactful_tom_ablation.sh --categories "belief,comprehension"
#
# 已完成的组合会自动跳过（检测 stats.json），删除对应目录可重跑。

set -euo pipefail

EXTRA_ARGS="${*}"
BASE_DIR="results/tactful_tom_ablation_$(date +%m%d)"
RUNNER="python examples/run_tactful_tom_harness.py"

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
    "8_skill_rag_memory"
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
echo " TactfulToM Ablation Summary — $(date)"
echo " Results dir: $BASE_DIR"
echo "============================================================"
echo ""

python3 - "$BASE_DIR" "${NAMES[@]}" << 'PYEOF'
import json, sys, os

base_dir = sys.argv[1]
names = sys.argv[2:]

# Overall summary
header = f"{'Config':<25s} {'Total':>6s} {'Correct':>7s} {'Acc':>8s} {'Errors':>6s}"
sep    = f"{'-'*25} {'-'*6} {'-'*7} {'-'*8} {'-'*6}"
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
    print(f"{name:<25s} {o['total']:6d} {o['correct']:7d} {o['accuracy']*100:7.2f}% {o['errors']:6d}")

# Per-category comparison
print()
print("Per-category accuracy:")
print()

all_cats = set()
config_stats = {}
for name in names:
    stats_path = os.path.join(base_dir, name, "stats.json")
    if not os.path.exists(stats_path):
        continue
    with open(stats_path) as f:
        s = json.load(f)
    config_stats[name] = s.get("per_category", {})
    all_cats.update(s.get("per_category", {}).keys())

if all_cats and config_stats:
    short_names = [n.split("_", 1)[1] if "_" in n else n for n in names if n in config_stats]
    col_w = max(10, max(len(sn) for sn in short_names) + 1)
    header2 = f"{'Category':<25s}" + "".join(f"{sn:>{col_w}s}" for sn in short_names)
    print(header2)
    print("-" * len(header2))

    for cat in sorted(all_cats):
        row = f"{cat:<25s}"
        for name in names:
            if name not in config_stats:
                continue
            cs = config_stats[name].get(cat)
            if cs:
                row += f"{cs['accuracy']*100:>{col_w}.1f}"
            else:
                row += f"{'—':>{col_w}s}"
        print(row)

# Per-lie-type comparison
print()
print("Per-lie-type accuracy:")
print()

all_lt = set()
lt_stats = {}
for name in names:
    stats_path = os.path.join(base_dir, name, "stats.json")
    if not os.path.exists(stats_path):
        continue
    with open(stats_path) as f:
        s = json.load(f)
    lt_stats[name] = s.get("per_lie_type", {})
    all_lt.update(s.get("per_lie_type", {}).keys())

if all_lt and lt_stats:
    short_names = [n.split("_", 1)[1] if "_" in n else n for n in names if n in lt_stats]
    col_w = max(10, max(len(sn) for sn in short_names) + 1)
    header3 = f"{'Lie Type':<35s}" + "".join(f"{sn:>{col_w}s}" for sn in short_names)
    print(header3)
    print("-" * len(header3))

    for lt in sorted(all_lt):
        row = f"{lt:<35s}"
        for name in names:
            if name not in lt_stats:
                continue
            ls = lt_stats[name].get(lt)
            if ls:
                row += f"{ls['accuracy']*100:>{col_w}.1f}"
            else:
                row += f"{'—':>{col_w}s}"
        print(row)

# Per-eval-mode comparison
print()
print("Per-eval-mode accuracy (mcq vs list):")
print()

em_stats = {}
all_em = set()
for name in names:
    stats_path = os.path.join(base_dir, name, "stats.json")
    if not os.path.exists(stats_path):
        continue
    with open(stats_path) as f:
        s = json.load(f)
    em_stats[name] = s.get("per_eval_mode", {})
    all_em.update(s.get("per_eval_mode", {}).keys())

if all_em and em_stats:
    short_names = [n.split("_", 1)[1] if "_" in n else n for n in names if n in em_stats]
    col_w = max(10, max(len(sn) for sn in short_names) + 1)
    header4 = f"{'Eval Mode':<15s}" + "".join(f"{sn:>{col_w}s}" for sn in short_names)
    print(header4)
    print("-" * len(header4))

    for em in sorted(all_em):
        row = f"{em:<15s}"
        for name in names:
            if name not in em_stats:
                continue
            es = em_stats[name].get(em)
            if es:
                row += f"{es['accuracy']*100:>{col_w}.1f}"
            else:
                row += f"{'—':>{col_w}s}"
        print(row)

PYEOF

echo ""
echo "Done. Full results in: $BASE_DIR/"
