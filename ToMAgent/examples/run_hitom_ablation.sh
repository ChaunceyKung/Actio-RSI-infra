#!/usr/bin/env bash
# Hi-ToM 消融实验：8 种模块组合 (skill × rag × memory)
#
# 用法:
#   bash examples/run_hitom_ablation.sh                       # 全量数据（默认去重，600个unique questions）
#   bash examples/run_hitom_ablation.sh --limit 5             # 每个 question_order 5 条试跑
#   bash examples/run_hitom_ablation.sh --no_deduplicate      # 禁用去重（1200个样本）
#   bash examples/run_hitom_ablation.sh --prompting_type CoTP # 使用CoTP版本
#
# 已完成的组合会自动跳过（检测 stats.json），删除对应目录可重跑。

set -euo pipefail

EXTRA_ARGS="${*}"
BASE_DIR="results/hitom_ablation_$(date +%m%d)"
RUNNER="python examples/run_hitom_harness.py"
DATA_DIR="benchmark/Hi-ToM"

# 默认不限制数量
if [[ ! "$EXTRA_ARGS" =~ "--limit" ]]; then
    EXTRA_ARGS="--limit 0 $EXTRA_ARGS"
fi

mkdir -p "$BASE_DIR"

# 9 种组合（包含门控优化）
NAMES=(
    "1_baseline"
    "2_skill"
    "3_rag"
    "4_memory"
    "8_skill_rag_memory"
    "9_skill_rag_memory_gate"
)
FLAGS=(
    ""
    "--skill"
    "--rag"
    "--memory"
    "--skill --rag --memory"
    "--skill --rag --memory --gate tom_harness/gate/configs/hitom.yaml"
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
    echo "  Data:  $DATA_DIR"
    echo "  Output: $OUT_DIR"
    echo "============================================================"

    if [ -f "$OUT_DIR/stats.json" ]; then
        echo "  → Already completed, skipping. Delete $OUT_DIR/stats.json to re-run."
        continue
    fi

    mkdir -p "$OUT_DIR"
    $RUNNER --data_dir "$DATA_DIR" $EXTRA_ARGS $flag --out_dir "$OUT_DIR" 2>&1 | tee "$OUT_DIR/console.log"

    echo "  → Done."
done

# ── 汇总表 ──────────────────────────────────────────────────────────
echo ""
echo "============================================================"
echo " Hi-ToM Ablation Summary — $(date)"
echo " Data: $DATA_DIR"
echo " Results dir: $BASE_DIR"
echo "============================================================"
echo ""

python3 - "$BASE_DIR" "${NAMES[@]}" << 'PYEOF'
import json, sys, os

base_dir = sys.argv[1]
names = sys.argv[2:]

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

# per-task (question_order) 对比
print()
print("Per-task (question_order) accuracy:")
print()

all_tasks = set()
config_stats = {}
for name in names:
    stats_path = os.path.join(base_dir, name, "stats.json")
    if not os.path.exists(stats_path):
        continue
    with open(stats_path) as f:
        s = json.load(f)
    config_stats[name] = s.get("per_task", {})
    all_tasks.update(s.get("per_task", {}).keys())

if all_tasks and config_stats:
    short_names = [n.split("_", 1)[1] if "_" in n else n for n in names if n in config_stats]
    col_w = max(10, max(len(sn) for sn in short_names) + 1)
    header2 = f"{'Task':<20s}" + "".join(f"{sn:>{col_w}s}" for sn in short_names)
    print(header2)
    print("-" * len(header2))

    for task in sorted(all_tasks):
        row = f"{task:<20s}"
        for name in names:
            if name not in config_stats:
                continue
            ts = config_stats[name].get(task)
            if ts:
                row += f"{ts['accuracy']*100:>{col_w}.1f}"
            else:
                row += f"{'—':>{col_w}s}"
        print(row)

# per-deception 对比
print()
print("Per-deception accuracy:")
print()

all_deceptions = set()
config_deception_stats = {}
for name in names:
    stats_path = os.path.join(base_dir, name, "stats.json")
    if not os.path.exists(stats_path):
        continue
    with open(stats_path) as f:
        s = json.load(f)
    config_deception_stats[name] = s.get("per_deception", {})
    all_deceptions.update(s.get("per_deception", {}).keys())

if all_deceptions and config_deception_stats:
    short_names = [n.split("_", 1)[1] if "_" in n else n for n in names if n in config_deception_stats]
    col_w = max(10, max(len(sn) for sn in short_names) + 1)
    header3 = f"{'Deception':<20s}" + "".join(f"{sn:>{col_w}s}" for sn in short_names)
    print(header3)
    print("-" * len(header3))

    for deception in sorted(all_deceptions):
        row = f"{deception:<20s}"
        for name in names:
            if name not in config_deception_stats:
                continue
            ds = config_deception_stats[name].get(deception)
            if ds:
                row += f"{ds['accuracy']*100:>{col_w}.1f}"
            else:
                row += f"{'—':>{col_w}s}"
        print(row)

# per-story_length 对比
print()
print("Per-story_length accuracy:")
print()

all_story_lengths = set()
config_story_length_stats = {}
for name in names:
    stats_path = os.path.join(base_dir, name, "stats.json")
    if not os.path.exists(stats_path):
        continue
    with open(stats_path) as f:
        s = json.load(f)
    config_story_length_stats[name] = s.get("per_story_length", {})
    all_story_lengths.update(s.get("per_story_length", {}).keys())

if all_story_lengths and config_story_length_stats:
    short_names = [n.split("_", 1)[1] if "_" in n else n for n in names if n in config_story_length_stats]
    col_w = max(10, max(len(sn) for sn in short_names) + 1)
    header4 = f"{'Story Length':<20s}" + "".join(f"{sn:>{col_w}s}" for sn in short_names)
    print(header4)
    print("-" * len(header4))

    for story_length in sorted(all_story_lengths):
        row = f"{story_length:<20s}"
        for name in names:
            if name not in config_story_length_stats:
                continue
            sls = config_story_length_stats[name].get(story_length)
            if sls:
                row += f"{sls['accuracy']*100:>{col_w}.1f}"
            else:
                row += f"{'—':>{col_w}s}"
        print(row)

PYEOF

echo ""
echo "Done. Full results in: $BASE_DIR/"
