"""Run the harness on ICTBench — implicit cognitive tracking benchmark.

Usage examples:
  # Run 5 samples per question type, baseline (no tools)
  python examples/run_ictbench_harness.py --limit 5

  # Run with skill routing + RAG
  python examples/run_ictbench_harness.py --limit 10 --skill --rag

  # Run only Q1 (single-choice belief attribution)
  python examples/run_ictbench_harness.py --limit 10 --question-types Q1

  # Run only first-person perspective
  python examples/run_ictbench_harness.py --limit 10 --perspectives first_person

  # Include perturbation variants for robustness testing
  python examples/run_ictbench_harness.py --limit 5 --perturbations

  # Run ALL samples
  python examples/run_ictbench_harness.py --limit 0

  # Skip Q4 (open analysis) to avoid judge model costs
  python examples/run_ictbench_harness.py --limit 10 --question-types Q1,Q2,Q3

Env vars for test model:
  TOM_API_BASE, TOM_API_KEY, TOM_MODEL, TOM_TEMPERATURE

Env vars for helper model (skill router / memory selector / RAG classifier):
  HELPER_API_BASE, HELPER_API_KEY

Env vars for judge model (Q4 open analysis LLM-as-judge scoring):
  JUDGE_API_BASE, JUDGE_API_KEY, JUDGE_MODEL

Outputs (saved to <out_dir>/):
  - results.jsonl        per-sample records
  - stats.json           per-type + per-category + overall accuracy
  - run.log              framework debug logs
"""

from __future__ import annotations

import argparse
import json
import logging
import logging.handlers
import os
import re
import sys
import threading
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from benchmark.load_ictbench import load_ictbench  # noqa: E402

from tom_harness import LLMClient, build_default_runtime  # noqa: E402
from tom_harness.parsers import parse_multi_select_response as _parse_multi_select_response  # noqa: E402
from tom_harness.routing import SkillV5Router, NoOpRouter  # noqa: E402
from tom_harness.tools.rag_v2 import RAGv2Engine, CategoryClassifier  # noqa: E402


class _FrameworkConsoleFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return not record.name.startswith("tom_harness")


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("ictbench")

_framework_logger = logging.getLogger("tom_harness")
_framework_logger.setLevel(logging.DEBUG)
_console_handler = logging.getLogger().handlers[0] if logging.getLogger().handlers else None
_console_filter = _FrameworkConsoleFilter()
if _console_handler:
    _console_handler.addFilter(_console_filter)

from dotenv import load_dotenv  # noqa: E402
load_dotenv()


# ── Prompt templates ──────────────────────────────────────────────────────

_Q2_PROMPT_TEMPLATE = (
    "仔细阅读以下情境，然后回答多选题。\n\n"
    "--- 情境 ---\n{story}\n--- 情境结束 ---\n\n"
    "问题：{question}\n\n"
    "选项：\n{options_text}\n\n"
    "请选出所有正确的选项。先简要说明理由（2-3句），然后在单独一行输出 JSON：\n"
    '{{"answer": ["C", "D", "E"]}}  — 列出所有正确选项的字母。'
)

_Q4_PROMPT_TEMPLATE = (
    "仔细阅读以下情境，然后完成分析任务。\n\n"
    "--- 情境 ---\n{story}\n--- 情境结束 ---\n\n"
    "任务：{question}\n\n"
    "请按照任务要求进行详细分析，结构化地输出你的分析结果。"
)

_Q4_JUDGE_PROMPT = (
    "你是一个严格的评分员。请评估一份关于心智理论（Theory of Mind）分析任务的回答。\n\n"
    "参考答案包含以下 {n_points} 个要点：\n{points_text}\n\n"
    "待评回答：\n{response}\n\n"
    "请逐一判断每个要点的覆盖程度：\n"
    "  0 = 未提及或完全错误\n"
    "  1 = 部分涉及但不完整或有偏差\n"
    "  2 = 充分覆盖且分析准确\n\n"
    "先对每个要点简要说明判断理由，然后在单独一行输出 JSON：\n"
    '{{"scores": [2, 1, 0, 2, 1]}}  — 列表长度应为 {n_points}。'
)


# ── Build harness ─────────────────────────────────────────────────────────

def build_harness(
    *,
    shared_rag: RAGv2Engine | None = None,
    shared_memory=None,
    cache_dir: str | None = None,
    enable_skill: bool = False,
    enable_validator: bool = True,
    enable_epistemic_validator: bool = True,
    # NOTE: multi-select audit (forced-removal v2) lost -11 pts on Q2 vs baseline:
    # the model defends ~5 confident picks, so an audit either no-ops or swaps the
    # picks at random (-9 net on 19 fired cases). Disabled until a non-prompt-level
    # signal is available. See results/ictbench_v2_validators_0609/ for the run.
    enable_multi_select_validator: bool = False,
    route_mode: str = "hierarchical",
    inject_mode: str = "light",
    review_mode: str = "off",
    lang: str = "zh",
    router_llm: LLMClient | None = None,
):
    api_base = os.environ.get("TOM_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    api_key = os.environ.get("TOM_API_KEY")
    model = os.environ.get("TOM_MODEL", "qwen3-32b")
    temperature = float(os.environ.get("TOM_TEMPERATURE", "0.0"))
    if not api_key:
        raise SystemExit("ERROR: set the TOM_API_KEY env var")

    llm = LLMClient(
        api_base=api_base, api_key=api_key, model=model,
        temperature=temperature, max_tokens=4096, timeout=120.0, max_retries=3,
    )
    if cache_dir:
        llm.set_cache_dir(cache_dir)

    if enable_skill:
        router = SkillV5Router(
            llm=router_llm or llm,
            route_mode=route_mode,
            inject_mode=inject_mode,
            lang=lang,
        )
    else:
        router = NoOpRouter()

    return build_default_runtime(
        llm=llm,
        router=router,
        rag_engine=shared_rag if (shared_rag is not None and shared_rag.size() > 0) else None,
        memory=shared_memory,
        enable_scalar_validator=enable_validator,
        enable_epistemic_validator=enable_epistemic_validator,
        enable_multi_select_validator=enable_multi_select_validator,
        review_mode=review_mode,
    )


# ── Sample selection ──────────────────────────────────────────────────────

def select_samples(
    samples: list[dict],
    *,
    offset: int,
    limit: int,
) -> list[dict]:
    """Apply offset/limit per (task_id, question_type) to balance the pool."""
    buckets: dict[str, list[dict]] = defaultdict(list)
    for s in samples:
        key = f"{s['metadata'].get('task', '')}_{s['metadata'].get('question_type', '')}"
        buckets[key].append(s)

    pool: list[dict] = []
    for k in sorted(buckets):
        bucket = buckets[k]
        sliced = bucket[offset:]
        if limit > 0:
            sliced = sliced[:limit]
        pool.extend(sliced)

    return pool


# ── Scoring helpers ───────────────────────────────────────────────────────

def _score_multi_select(predicted: list[str], ground_truth: list[str]) -> dict:
    """Score multi-select: exact set match + F1."""
    pred_set = set(predicted)
    gt_set = set(ground_truth)

    exact = pred_set == gt_set

    if not pred_set and not gt_set:
        precision = recall = f1 = 1.0
    elif not pred_set:
        precision = recall = f1 = 0.0
    elif not gt_set:
        precision = recall = f1 = 0.0
    else:
        tp = len(pred_set & gt_set)
        precision = tp / len(pred_set)
        recall = tp / len(gt_set)
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "exact": exact,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
    }


def _score_open_analysis(
    response: str,
    answer_points: list[str],
    judge_llm: LLMClient | None,
) -> dict:
    """Score Q4 open analysis using LLM-as-judge."""
    if not judge_llm or not answer_points:
        return {"total_score": 0, "max_score": 0, "ratio": 0.0, "per_point": [], "error": "no_judge"}

    n = len(answer_points)
    points_text = "\n".join(f"[{i+1}] {pt}" for i, pt in enumerate(answer_points))

    prompt = _Q4_JUDGE_PROMPT.format(
        n_points=n,
        points_text=points_text,
        response=response,
    )

    try:
        system = "你是一个严格的评分员，请客观评估回答对参考要点的覆盖程度。"
        raw = judge_llm.chat(system, prompt, max_tokens=2048)
    except Exception as e:
        return {"total_score": 0, "max_score": n * 2, "ratio": 0.0, "per_point": [],
                "error": f"judge_call_failed: {e}"}

    text = re.sub(r"<think>[\s\S]*?</think>", "", raw or "").strip()
    if not text:
        m_think = re.search(r"<think>([\s\S]*?)</think>", raw or "")
        text = m_think.group(1).strip() if m_think else ""

    # Parse scores JSON
    m = re.search(r'\{[^{}]*"scores"\s*:\s*\[([^\]]*)\][^{}]*\}', text)
    scores = []
    if m:
        try:
            obj = json.loads(m.group(0))
            scores = obj.get("scores", [])
        except (json.JSONDecodeError, TypeError):
            parts = m.group(1).split(",")
            for p in parts:
                try:
                    scores.append(int(p.strip()))
                except ValueError:
                    scores.append(0)

    # Validate and clamp
    scores = [max(0, min(2, int(s))) for s in scores[:n]]
    while len(scores) < n:
        scores.append(0)

    total = sum(scores)
    max_score = n * 2

    return {
        "total_score": total,
        "max_score": max_score,
        "ratio": round(total / max_score, 4) if max_score > 0 else 0.0,
        "per_point": scores,
    }


# ── Process one sample ────────────────────────────────────────────────────

def process_one(
    runtime_factory,
    sample: dict,
    judge_llm: LLMClient | None = None,
    timeout_sec: float = 180.0,
) -> tuple[dict, list[str]]:
    buf_handler = logging.handlers.MemoryHandler(capacity=10000, flushLevel=logging.CRITICAL + 1)
    buf_handler.setLevel(logging.DEBUG)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    buf_handler.setFormatter(fmt)
    framework_logger = logging.getLogger("tom_harness")
    framework_logger.addHandler(buf_handler)

    eval_mode = sample["metadata"].get("eval_mode", "mcq")

    t0 = time.time()
    rec = {
        "id": sample["id"],
        "task": sample["metadata"].get("task"),
        "category": sample["metadata"].get("category"),
        "question_type": sample["metadata"].get("question_type"),
        "perspective": sample["metadata"].get("perspective"),
        "domain": sample["metadata"].get("domain"),
        "eval_mode": eval_mode,
        "is_perturbation": sample["metadata"].get("is_perturbation", False),
        "perturb_variant": sample["metadata"].get("perturb_variant", ""),
        "answer": sample.get("answer", ""),
        "predicted": "",
        "correct": False,
        "skill_id": None,
        "skill_ids": [],
        "draft_predicted": "",
        "review_changed": False,
        "n_llm_calls": 0,
        "elapsed_sec": 0.0,
        "error": None,
    }

    try:
        runtime = runtime_factory()

        if eval_mode == "mcq" or eval_mode == "verdict":
            result = runtime.answer_one(
                question=sample["question"],
                story=sample["story"],
                options=sample["options"],
                eval_mode=eval_mode,
            )
            rec["predicted"] = result.answer
            rec["correct"] = (result.answer == sample["answer"])

        elif eval_mode == "multi_select":
            options_text = "\n".join(
                f"{k}. {v}" for k, v in sorted(sample["options"].items())
            )
            prompt = _Q2_PROMPT_TEMPLATE.format(
                story=sample["story"],
                question=sample["question"],
                options_text=options_text,
            )
            result = runtime.answer_one(
                question=prompt,
                story="",
                options={},
                free_form=True,
                eval_mode=eval_mode,
            )
            raw_output = result.answer or ""
            rec["predicted"] = raw_output
            parsed = _parse_multi_select_response(raw_output)
            rec["predicted_list"] = parsed
            rec["answer_list"] = sample.get("answer_list", [])
            score = _score_multi_select(parsed, sample.get("answer_list", []))
            rec["correct"] = score["exact"]
            rec["multi_select_score"] = score

        elif eval_mode == "open_analysis":
            prompt = _Q4_PROMPT_TEMPLATE.format(
                story=sample["story"],
                question=sample["question"],
            )
            result = runtime.answer_one(
                question=prompt,
                story="",
                options={},
                free_form=True,
                eval_mode=eval_mode,
            )
            raw_output = result.answer or ""
            rec["predicted"] = raw_output
            score = _score_open_analysis(
                raw_output,
                sample.get("answer_points", []),
                judge_llm,
            )
            rec["open_analysis_score"] = score
            rec["correct"] = score.get("ratio", 0) >= 0.6

        else:
            rec["error"] = f"unknown eval_mode: {eval_mode}"
            result = None

        if result:
            rec["skill_id"] = result.skill_id
            rec["skill_ids"] = result.skill_ids
            rec["draft_predicted"] = result.draft_answer
            rec["review_changed"] = result.review_changed
            rec["n_llm_calls"] = result.n_llm_calls
            if result.thinking:
                rec["thinking"] = result.thinking
            if result.rag_context:
                rec["rag_context"] = result.rag_context
            if result.memory_bullets:
                rec["memory_bullets"] = result.memory_bullets
                rec["memory_subtask"] = result.memory_subtask
            if result.validator_events:
                rec["validator_events"] = result.validator_events

    except Exception as e:
        rec["error"] = f"{type(e).__name__}: {e}"

    rec["elapsed_sec"] = round(time.time() - t0, 2)

    log_lines = []
    for log_record in buf_handler.buffer:
        log_lines.append(fmt.format(log_record))
    framework_logger.removeHandler(buf_handler)
    buf_handler.close()

    return rec, log_lines


# ── Statistics computation ────────────────────────────────────────────────

def _compute_stats(records: list[dict]) -> dict:
    total = len(records)
    correct = sum(1 for r in records if r.get("correct"))
    errors = sum(1 for r in records if r.get("error"))

    def _make_bucket():
        return {"total": 0, "correct": 0, "errors": 0}

    per_question_type = defaultdict(_make_bucket)
    per_category = defaultdict(_make_bucket)
    per_perspective = defaultdict(_make_bucket)
    per_domain = defaultdict(_make_bucket)
    per_eval_mode = defaultdict(_make_bucket)
    per_perturbation = defaultdict(_make_bucket)
    elapsed_sum = defaultdict(float)

    # Q2 F1 accumulator
    q2_f1_sum = 0.0
    q2_count = 0

    # Q4 score accumulator
    q4_score_sum = 0.0
    q4_count = 0

    for r in records:
        qt = r.get("question_type", "unknown")
        cat = r.get("category", "unknown")
        persp = r.get("perspective", "unknown")
        domain = r.get("domain", "unknown")
        em = r.get("eval_mode", "unknown")
        is_correct = int(bool(r.get("correct")))
        is_error = int(bool(r.get("error")))
        is_perturb = "perturbation" if r.get("is_perturbation") else "original"

        for bucket, key in [
            (per_question_type, qt),
            (per_category, cat),
            (per_perspective, persp),
            (per_domain, domain),
            (per_eval_mode, em),
            (per_perturbation, is_perturb),
        ]:
            bucket[key]["total"] += 1
            bucket[key]["correct"] += is_correct
            bucket[key]["errors"] += is_error

        elapsed_sum[qt] += float(r.get("elapsed_sec", 0) or 0)

        if em == "multi_select":
            ms = r.get("multi_select_score", {})
            q2_f1_sum += ms.get("f1", 0)
            q2_count += 1

        if em == "open_analysis":
            oa = r.get("open_analysis_score", {})
            q4_score_sum += oa.get("ratio", 0)
            q4_count += 1

    # Compute accuracy for each bucket
    for d in (
        list(per_question_type.values()) + list(per_category.values())
        + list(per_perspective.values()) + list(per_domain.values())
        + list(per_eval_mode.values()) + list(per_perturbation.values())
    ):
        valid_n = d["total"] - d["errors"]
        d["accuracy"] = round(d["correct"] / valid_n, 4) if valid_n > 0 else 0.0

    for qt, d in per_question_type.items():
        d["avg_elapsed"] = round(elapsed_sum.get(qt, 0) / (d["total"] or 1), 2)

    valid_total = total - errors
    stats = {
        "overall": {
            "total": total,
            "correct": correct,
            "errors": errors,
            "accuracy": round(correct / valid_total, 4) if valid_total else 0,
        },
        "per_question_type": dict(per_question_type),
        "per_category": dict(per_category),
        "per_perspective": dict(per_perspective),
        "per_eval_mode": dict(per_eval_mode),
        "per_perturbation": dict(per_perturbation),
        "per_domain": dict(per_domain),
        "benchmark": "ICTBench",
    }

    if q2_count > 0:
        stats["q2_avg_f1"] = round(q2_f1_sum / q2_count, 4)
    if q4_count > 0:
        stats["q4_avg_score_ratio"] = round(q4_score_sum / q4_count, 4)

    return stats


# ── Output ────────────────────────────────────────────────────────────────

def _print_and_save_stats(results_path: Path, stats_path: Path) -> None:
    all_records = _load_all(results_path)
    if not all_records:
        logger.info("No results to summarize.")
        return
    stats = _compute_stats(all_records)
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

    sep = "=" * 70
    logger.info("\n%s\nICTBench results  →  %s\n%s", sep, stats_path, sep)

    o = stats["overall"]
    logger.info("Overall: %d/%d = %.1f%%  (errors: %d)",
                o["correct"], o["total"], o["accuracy"] * 100, o["errors"])

    if "q2_avg_f1" in stats:
        logger.info("Q2 average F1: %.3f", stats["q2_avg_f1"])
    if "q4_avg_score_ratio" in stats:
        logger.info("Q4 average score ratio: %.3f", stats["q4_avg_score_ratio"])

    logger.info("\n%-15s %4s %7s  %4s", "Question Type", "N", "Acc", "Err")
    logger.info("-" * 35)
    for qt in sorted(stats["per_question_type"]):
        qs = stats["per_question_type"][qt]
        logger.info("  %-13s %4d %6.1f%%  %4d", qt, qs["total"], qs["accuracy"] * 100, qs["errors"])

    logger.info("\n%-15s %4s %7s  %4s", "Perspective", "N", "Acc", "Err")
    logger.info("-" * 35)
    for p in sorted(stats["per_perspective"]):
        ps = stats["per_perspective"][p]
        logger.info("  %-13s %4d %6.1f%%  %4d", p, ps["total"], ps["accuracy"] * 100, ps["errors"])

    if stats["per_perturbation"].get("perturbation"):
        logger.info("\n%-15s %4s %7s  %4s", "Perturbation", "N", "Acc", "Err")
        logger.info("-" * 35)
        for k in sorted(stats["per_perturbation"]):
            ks = stats["per_perturbation"][k]
            logger.info("  %-13s %4d %6.1f%%  %4d", k, ks["total"], ks["accuracy"] * 100, ks["errors"])

    logger.info("\n%-35s %4s %7s  %4s", "Category", "N", "Acc", "Err")
    logger.info("-" * 55)
    for c in sorted(stats["per_category"]):
        cs = stats["per_category"][c]
        logger.info("  %-33s %4d %6.1f%%  %4d", c, cs["total"], cs["accuracy"] * 100, cs["errors"])

    logger.info("\nResults saved to: %s", results_path)
    logger.info("Stats   saved to: %s", stats_path)
    logger.info("Log     saved to: %s", results_path.parent / "run.log")


def _live_accuracy(path: Path) -> float:
    n = c = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
                n += 1
                c += int(bool(r.get("correct")))
            except Exception:
                pass
    return c / n if n else 0.0


def _load_all(path: Path) -> list[dict]:
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                pass
    return out


# ── Main ──────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(
        description="Run ToM harness on ICTBench (implicit cognitive tracking).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    data_grp = ap.add_argument_group("data selection")
    data_grp.add_argument("--data_path", type=str, default=None,
                          help="Path to ICTBench dataset_v4.2.json.")
    data_grp.add_argument("--perspectives", type=str, default=None,
                          help="Comma-separated: first_person,third_person")
    data_grp.add_argument("--task-ids", type=str, default=None,
                          help="Comma-separated task IDs (e.g. 1.1.1,2.3.1).")
    data_grp.add_argument("--question-types", type=str, default=None,
                          help="Comma-separated: Q1,Q2,Q3,Q4")
    data_grp.add_argument("--domains", type=str, default=None,
                          help="Comma-separated domain names.")
    data_grp.add_argument("--length-modes", type=str, default=None,
                          help="Comma-separated: short,long")
    data_grp.add_argument("--perturbations", action="store_true",
                          help="Include perturbation variant samples.")
    data_grp.add_argument("--limit", type=int, default=20,
                          help="Max samples per (task_id, question_type) bucket. 0 = no limit.")
    data_grp.add_argument("--offset", type=int, default=0)

    exec_grp = ap.add_argument_group("execution")
    exec_grp.add_argument("--workers", type=int, default=8)
    exec_grp.add_argument("--verbose", "-v", action="store_true")

    out_grp = ap.add_argument_group("output")
    out_grp.add_argument("--out_dir", default="results/ictbench")

    rag_grp = ap.add_argument_group("RAG retrieval")
    rag_grp.add_argument("--rag", action="store_true", help="Enable RAG retrieval.")
    rag_grp.add_argument("--rag_data_dir", type=str, default="tom_harness/tools/rag_v2_data")
    rag_grp.add_argument("--rag_index_dir", type=str, default="tom_harness/tools/rag_v2_index")
    rag_grp.add_argument("--rag_model", type=str, default="model/bge-m3")
    rag_grp.add_argument("--rag_category_filter", action="store_true", default=True)
    rag_grp.add_argument("--no_rag_category_filter", action="store_false", dest="rag_category_filter")

    mem_grp = ap.add_argument_group("Memory playbook (selector-based)")
    mem_grp.add_argument("--memory", action="store_true")
    mem_grp.add_argument("--memory_playbook", type=str,
                         default="memory_playbook/playbook/final_playbook.txt")

    helper_grp = ap.add_argument_group("Helper endpoint credentials (skill router / memory selector / RAG classifier)")
    helper_grp.add_argument("--helper_api_base", type=str, default=None)
    helper_grp.add_argument("--helper_api_key", type=str, default=None)

    judge_grp = ap.add_argument_group("Judge model (Q4 open analysis LLM-as-judge)")
    judge_grp.add_argument("--judge_api_base", type=str, default=None)
    judge_grp.add_argument("--judge_api_key", type=str, default=None)
    judge_grp.add_argument("--judge_model", type=str, default=None)

    skill_grp = ap.add_argument_group("Skill injection (v5)")
    skill_grp.add_argument("--skill", action="store_true",
                           help="Enable LLM-routed skill injection (v5).")
    skill_grp.add_argument("--route-mode", type=str, default="hierarchical",
                           choices=["baseline", "macro_only", "micro_only", "hierarchical", "flat_all"])
    skill_grp.add_argument("--inject-mode", type=str, default="light",
                           choices=["full", "light"])
    skill_grp.add_argument("--review-mode", type=str, default="off",
                           choices=["on", "off"])
    skill_grp.add_argument("--lang", type=str, default="zh",
                           choices=["en", "zh"])

    val_grp = ap.add_argument_group("Validators")
    val_grp.add_argument("--no-epistemic-validator", action="store_true",
                         help="Disable the Q3 epistemic-calibration validator.")
    val_grp.add_argument("--multi-select-validator", action="store_true",
                         help="Enable the Q2 multi-select audit validator (disabled by default; v2 design regressed Q2 -11pts).")

    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    results_path = out_dir / "results.jsonl"
    stats_path = out_dir / "stats.json"
    log_path = out_dir / "run.log"

    if args.verbose and _console_handler:
        _console_handler.removeFilter(_console_filter)

    _log_file_lock = threading.Lock()
    log_path.write_text("", encoding="utf-8")

    if results_path.exists():
        results_path.unlink()

    # ── Load data ──────────────────────────────────────────────────────────
    perspectives = {p.strip() for p in args.perspectives.split(",")} if args.perspectives else None
    task_id_filter = {t.strip() for t in args.task_ids.split(",")} if args.task_ids else None
    qt_filter = {t.strip() for t in args.question_types.split(",")} if args.question_types else None
    domain_filter = {d.strip() for d in args.domains.split(",")} if args.domains else None
    length_filter = {l.strip() for l in args.length_modes.split(",")} if args.length_modes else None

    samples = load_ictbench(
        data_path=args.data_path,
        perspectives=perspectives,
        task_ids=task_id_filter,
        question_types=qt_filter,
        domains=domain_filter,
        length_modes=length_filter,
        include_perturbations=args.perturbations,
    )
    logger.info("Loaded %d total ICTBench samples", len(samples))

    pool = select_samples(samples, offset=args.offset, limit=args.limit)

    qt_counts = defaultdict(int)
    cat_counts = defaultdict(int)
    for s in pool:
        qt_counts[s["metadata"]["question_type"]] += 1
        cat_counts[s["metadata"]["category"]] += 1
    logger.info("Selected %d samples (offset=%d, limit=%s per bucket)",
                len(pool), args.offset, args.limit or "all")
    for qt in sorted(qt_counts):
        logger.info("  question_type %-5s %4d", qt, qt_counts[qt])

    if not pool:
        logger.info("Nothing to run.")
        return

    # ── Helper endpoint credentials ────────────────────────────────────────────────────────
    helper_api_base = args.helper_api_base or os.environ.get("HELPER_API_BASE", "")
    helper_api_key = args.helper_api_key or os.environ.get("HELPER_API_KEY", "")
    main_model_name = os.environ.get("TOM_MODEL", "qwen3-32b")

    # ── Judge model (independent from helper) ──────────────────────────────
    judge_api_base = args.judge_api_base or os.environ.get("JUDGE_API_BASE", "")
    judge_api_key = args.judge_api_key or os.environ.get("JUDGE_API_KEY", "")
    judge_model = args.judge_model or os.environ.get("JUDGE_MODEL", "")

    # ── Judge LLM for Q4 ──────────────────────────────────────────────────
    judge_llm: LLMClient | None = None
    has_q4 = any(s["metadata"].get("eval_mode") == "open_analysis" for s in pool)
    if has_q4 and judge_api_key and judge_model:
        judge_llm = LLMClient(
            api_base=judge_api_base, api_key=judge_api_key, model=judge_model,
            temperature=0.0, max_tokens=2048, timeout=120.0, max_retries=3,
        )
        logger.info("Q4 judge model: %s", judge_model)
    elif has_q4:
        logger.warning("Q4 samples present but no JUDGE_API_KEY/JUDGE_MODEL — "
                        "Q4 will score 0. Set JUDGE_* env vars or --judge_* args "
                        "for LLM-as-judge scoring.")

    # ── RAG setup ──────────────────────────────────────────────────────────
    shared_rag: RAGv2Engine | None = None
    if args.rag:
        classifier = None
        if helper_api_key:
            classifier = CategoryClassifier(
                api_base=helper_api_base, api_key=helper_api_key, model=main_model_name,
            )
        shared_rag = RAGv2Engine(
            data_dir=args.rag_data_dir,
            index_dir=args.rag_index_dir,
            model_name=args.rag_model,
            use_category_filter=args.rag_category_filter,
            classifier=classifier,
        )
        shared_rag.build_index()
        if shared_rag.size() > 0:
            logger.info("RAG enabled: %d rules indexed", shared_rag.size())
        else:
            logger.info("RAG data not found — running without RAG")
            shared_rag = None

    # ── Memory setup ───────────────────────────────────────────────────────
    shared_memory = None
    if args.memory:
        if not helper_api_key:
            logger.warning("Memory requires HELPER_API_KEY — skipping")
        elif not Path(args.memory_playbook).exists():
            logger.warning("Playbook file %s not found — skipping memory", args.memory_playbook)
        else:
            from memory_playbook import Memory, SelectorConfig
            selector_cfg = SelectorConfig(
                provider="custom",
                api_key=helper_api_key,
                model=main_model_name,
                base_url=helper_api_base or None,
            )
            shared_memory = Memory(args.memory_playbook, selector_cfg)
            logger.info("Memory enabled: playbook=%s, selector_model=%s",
                        args.memory_playbook, main_model_name)

    # ── Router LLM ─────────────────────────────────────────────────────────
    shared_router_llm: LLMClient | None = None
    if args.skill and helper_api_key:
        shared_router_llm = LLMClient(
            api_base=helper_api_base, api_key=helper_api_key, model=main_model_name,
            temperature=0.0, max_tokens=256, timeout=60.0, max_retries=3,
        )
        logger.info("Router using helper endpoint with main model: %s", main_model_name)

    if args.skill:
        router_model_name = main_model_name
        logger.info("Skill injection enabled (v5: route_mode=%s, inject_mode=%s, review=%s, lang=%s, router_model=%s)",
                    args.route_mode, args.inject_mode, args.review_mode, args.lang, router_model_name)

    # ── Run ─────────────────────────────────────────────────────────────────
    llm_cache_dir = str(out_dir / "llm_cache")
    runtime_factory = lambda: build_harness(  # noqa: E731
        shared_rag=shared_rag,
        shared_memory=shared_memory,
        cache_dir=llm_cache_dir,
        enable_skill=args.skill,
        enable_epistemic_validator=not args.no_epistemic_validator,
        enable_multi_select_validator=args.multi_select_validator,
        route_mode=args.route_mode,
        inject_mode=args.inject_mode,
        review_mode=args.review_mode,
        lang=args.lang,
        router_llm=shared_router_llm,
    )

    t_start = time.time()
    completed = 0
    with ThreadPoolExecutor(max_workers=args.workers) as exe:
        futs = {exe.submit(process_one, runtime_factory, s, judge_llm): s for s in pool}
        for fut in as_completed(futs):
            s = futs[fut]
            try:
                rec, log_lines = fut.result(timeout=360)
            except Exception as e:
                rec = {
                    "id": s["id"],
                    "task": s["metadata"].get("task"),
                    "category": s["metadata"].get("category"),
                    "question_type": s["metadata"].get("question_type"),
                    "perspective": s["metadata"].get("perspective"),
                    "domain": s["metadata"].get("domain"),
                    "eval_mode": s["metadata"].get("eval_mode"),
                    "is_perturbation": s["metadata"].get("is_perturbation", False),
                    "answer": s.get("answer", ""),
                    "predicted": "",
                    "correct": False,
                    "error": f"outer: {e}",
                    "skill_id": None,
                    "n_llm_calls": 0,
                    "elapsed_sec": 0.0,
                }
                log_lines = []
            with open(results_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            if log_lines:
                with _log_file_lock:
                    with open(log_path, "a", encoding="utf-8") as f:
                        f.write("\n".join(log_lines) + "\n")
            completed += 1
            if completed % 20 == 0:
                acc_so_far = _live_accuracy(results_path)
                elapsed = (time.time() - t_start) / 60
                logger.info("progress=%d/%d elapsed=%.1fmin running_acc=%.3f",
                            completed, len(pool), elapsed, acc_so_far)

    _print_and_save_stats(results_path, stats_path)


if __name__ == "__main__":
    main()
