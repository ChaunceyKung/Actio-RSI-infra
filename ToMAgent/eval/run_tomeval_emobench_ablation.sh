#!/usr/bin/env bash
# EmoBench agent ablation: 5 module combinations via ToMEval pipeline
#
# Usage:
#   bash eval/run_tomeval_emobench_ablation.sh
#   bash eval/run_tomeval_emobench_ablation.sh --max_samples 50

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

DATASET="EmoBench"
EXTRA_ARGS="${*}"
BASE_DIR="$ROOT_DIR/ToMEval/results/${DATASET}_ablation_$(date +%m%d)"
RUNNER="python eval/run_tomeval_harness.py --datasets ${DATASET}"

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
    echo "  Dataset: $DATASET"
    echo "  Flags: ${flag:-(none)}"
    echo "  Output: $OUT_DIR"
    echo "============================================================"

    if find "$OUT_DIR" -name metrics.json -print -quit 2>/dev/null | grep -q .; then
        echo "  → Already completed, skipping. Delete metrics.json under $OUT_DIR to re-run."
        continue
    fi

    mkdir -p "$OUT_DIR"
    $RUNNER $flag --results-path "$OUT_DIR" $EXTRA_ARGS 2>&1 | tee "$OUT_DIR/console.log"

    echo "  → Done."
done

echo ""
echo "============================================================"
echo " ${DATASET} Agent Ablation Summary — $(date)"
echo " Results dir: $BASE_DIR"
echo "============================================================"
echo ""

python3 - "$BASE_DIR" "$DATASET" "${NAMES[@]}" << 'PYEOF'
import json, sys, os, glob
from collections import defaultdict
from pathlib import Path

base_dir = Path(sys.argv[1])
dataset = sys.argv[2]
names = sys.argv[3:]
protocol_order = ["direct", "direct_think", "cot", "del_tom", "config"]
protocol_set = set(protocol_order)
labels = {
    "1_baseline": "baseline",
    "2_skill": "skill",
    "3_rag": "rag",
    "4_memory": "memory",
    "5_skill_rag_memory": "skill+rag+memory",
}
rows = defaultdict(dict)


def infer_protocol(metrics_path, rel):
    parts = rel.split(os.sep)
    if parts and parts[0] in protocol_set:
        return parts[0]
    config_path = Path(metrics_path).with_name("config.json")
    if config_path.exists():
        with open(config_path) as f:
            cfg = json.load(f)
        return cfg.get("experiment_config", {}).get("protocol") or "config"
    return "config"


for name in names:
    pattern = str(base_dir / name / "**" / "metrics.json")
    found = sorted(glob.glob(pattern, recursive=True))
    for path in found:
        with open(path) as f:
            m = json.load(f)
        avg = m.get("avg_metrics") or (m.get("all_metrics", [{}])[0] if m.get("all_metrics") else {})
        total = int(avg.get("total", 0))
        correct = int(avg.get("correct", 0))
        acc = float(avg.get("accuracy", 0))
        rel = os.path.relpath(path, base_dir / name)
        protocol = infer_protocol(path, rel)
        rows[protocol][labels[name]] = {
            "accuracy": acc,
            "correct": correct,
            "total": total,
            "metrics_path": rel,
        }

if not rows:
    print("No metrics.json found.")
    raise SystemExit

ordered_protocols = sorted(
    rows,
    key=lambda p: (protocol_order.index(p) if p in protocol_order else len(protocol_order), p),
)
columns = [labels[name] for name in names]
header = f"{'Protocol':<14s}" + "".join(f" {col:>22s}" for col in columns)
sep = f"{'-'*14}" + "".join(f" {'-'*22}" for _ in columns)
lines = [header, sep]

for protocol in ordered_protocols:
    line = f"{protocol:<14s}"
    for col in columns:
        item = rows[protocol].get(col)
        value = "-" if item is None else f"{item['accuracy']*100:.2f}% ({item['correct']}/{item['total']})"
        line += f" {value:>22s}"
    lines.append(line)

print("\n".join(lines))

summary = {
    "dataset": dataset,
    "columns": columns,
    "protocols": {protocol: rows[protocol] for protocol in ordered_protocols},
}
(base_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

md_lines = [
    f"# {dataset} Agent Ablation Summary",
    "",
    "| Protocol | " + " | ".join(columns) + " |",
    "|" + "---|" * (len(columns) + 1),
]
for protocol in ordered_protocols:
    cells = []
    for col in columns:
        item = rows[protocol].get(col)
        cells.append("-" if item is None else f"{item['accuracy']*100:.2f}% ({item['correct']}/{item['total']})")
    md_lines.append("| " + protocol + " | " + " | ".join(cells) + " |")
md_lines.append("")
(base_dir / "summary.md").write_text("\n".join(md_lines), encoding="utf-8")
print(f"\nSaved summary: {base_dir / 'summary.md'}")
print(f"Saved summary: {base_dir / 'summary.json'}")

PYEOF

echo ""
echo "Done. Full results in: $BASE_DIR/"
