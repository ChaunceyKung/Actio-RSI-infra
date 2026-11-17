"""Run the harness on Hi-ToM — higher-order Theory of Mind benchmark.

Usage examples:
  # Run 10 samples per question order, baseline (no tools)
  python examples/run_hitom_harness.py --limit 10

  # Run with skill routing + RAG + memory
  python examples/run_hitom_harness.py --limit 10 --skill --rag --memory

  # Run only skill
  python examples/run_hitom_harness.py --limit 10 --skill

  # Run only RAG
  python examples/run_hitom_harness.py --limit 10 --rag

  # Run only memory
  python examples/run_hitom_harness.py --limit 10 --memory

  # Run ALL samples
  python examples/run_hitom_harness.py --limit 0

Env vars for test model:
  TOM_API_BASE, TOM_API_KEY, TOM_MODEL, TOM_TEMPERATURE

Env vars for helper model (selector/classifier):
  HELPER_API_BASE, HELPER_API_KEY

Outputs (saved to <out_dir>/):
  - results.jsonl        per-sample records
  - stats.json           per-question_order + overall accuracy
"""

from __future__ import annotations

import argparse
import json
import logging
import logging.handlers
import os
import sys
import threading
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from benchmark.load_hitom import load_hitom  # noqa: E402

from tom_harness import LLMClient, build_default_runtime  # noqa: E402
from tom_harness.routing import SkillV5Router, NoOpRouter  # noqa: E402
from tom_harness.tools.rag_v2 import RAGv2Engine, CategoryClassifier  # noqa: E402
from tom_harness.gate import ModuleGate, load_gate_config  # noqa: E402


class _FrameworkConsoleFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return not record.name.startswith("tom_harness")


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("hitom_bench")

_framework_logger = logging.getLogger("tom_harness")
_framework_logger.setLevel(logging.DEBUG)
_console_handler = logging.getLogger().handlers[0] if logging.getLogger().handlers else None
_console_filter = _FrameworkConsoleFilter()
if _console_handler:
    _console_handler.addFilter(_console_filter)

from dotenv import load_dotenv  # noqa: E402
load_dotenv()


def build_harness(
    *,
    shared_rag: RAGv2Engine | None = None,
    shared_memory=None,
    shared_gate: ModuleGate | None = None,
    cache_dir: str | None = None,
    enable_skill: bool = False,
    enable_validator: bool = True,
    route_mode: str = "hierarchical",
    inject_mode: str = "light",
    review_mode: str = "off",
    lang: str = "en",
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
        temperature=temperature, max_tokens=2048, timeout=120.0, max_retries=3,
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
        review_mode=review_mode,
        gate=shared_gate,
    )


def select_samples(
    samples: list[dict],
    *,
    offset: int,
    limit: int,
) -> list[dict]:
    """Apply offset/limit per question_order to balance the sample pool."""
    buckets: dict[str, list[dict]] = defaultdict(list)
    for s in samples:
        buckets[s["metadata"].get("task", "")].append(s)

    pool: list[dict] = []
    for t in sorted(buckets):
        bucket = buckets[t]
        sliced = bucket[offset:]
        if limit > 0:
            sliced = sliced[:limit]
        pool.extend(sliced)

    return pool


def process_one(runtime_factory, sample, timeout_sec: float = 180.0):
    buf_handler = logging.handlers.MemoryHandler(capacity=10000, flushLevel=logging.CRITICAL + 1)
    buf_handler.setLevel(logging.DEBUG)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    buf_handler.setFormatter(fmt)
    framework_logger = logging.getLogger("tom_harness")
    framework_logger.addHandler(buf_handler)

    t0 = time.time()
    rec = {
        "id": sample["id"],
        "task": sample["metadata"].get("task"),
        "question_order": sample["metadata"].get("question_order"),
        "deception": sample["metadata"].get("deception"),
        "story_length": sample["metadata"].get("story_length"),
        "answer": sample["answer"],
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
        result = runtime.answer_one(
            question=sample["question"],
            story=sample["story"],
            options=sample["options"],
            raw_metadata=sample["metadata"],
        )
        rec["predicted"] = result.answer
        rec["correct"] = (result.answer == sample["answer"])
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
    except Exception as e:
        rec["error"] = f"{type(e).__name__}: {e}"
    rec["elapsed_sec"] = round(time.time() - t0, 2)

    log_lines = []
    for log_record in buf_handler.buffer:
        log_lines.append(fmt.format(log_record))
    framework_logger.removeHandler(buf_handler)
    buf_handler.close()

    return rec, log_lines


def main():
    ap = argparse.ArgumentParser(
        description="Run ToM harness on Hi-ToM (higher-order belief reasoning).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    data_grp = ap.add_argument_group("data selection")
    data_grp.add_argument("--data_dir", type=str, default=None,
                          help="Path to Hi-ToM data directory.")
    data_grp.add_argument("--limit", type=int, default=20,
                          help="Max samples PER QUESTION ORDER (default: 20, 0 = no limit).")
    data_grp.add_argument("--offset", type=int, default=0)
    data_grp.add_argument("--no_deduplicate", action="store_false", dest="deduplicate",
                          help="Disable deduplication of VP/CoTP pairs (default: deduplicate enabled).")
    data_grp.add_argument("--prompting_type", type=str, default="VP", choices=["VP", "CoTP"],
                          help="Preferred prompting type when deduplicating (default: VP).")

    exec_grp = ap.add_argument_group("execution")
    exec_grp.add_argument("--workers", type=int, default=8)
    exec_grp.add_argument("--verbose", "-v", action="store_true")

    out_grp = ap.add_argument_group("output")
    out_grp.add_argument("--out_dir", default="results/hitom")

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

    helper_grp = ap.add_argument_group("Helper endpoint credentials (selector / classifier)")
    helper_grp.add_argument("--helper_api_base", type=str, default=None)
    helper_grp.add_argument("--helper_api_key", type=str, default=None)

    skill_grp = ap.add_argument_group("Skill injection (v5)")
    skill_grp.add_argument("--skill", action="store_true",
                           help="Enable LLM-routed skill injection (v5: 76 skills).")
    skill_grp.add_argument("--route-mode", type=str, default="hierarchical",
                           choices=["baseline", "macro_only", "micro_only", "hierarchical", "flat_all"])
    skill_grp.add_argument("--inject-mode", type=str, default="light",
                           choices=["full", "light"])
    skill_grp.add_argument("--review-mode", type=str, default="off",
                           choices=["on", "off"])
    skill_grp.add_argument("--lang", type=str, default="en",
                           choices=["en", "zh"])

    gate_grp = ap.add_argument_group("Module gate")
    gate_grp.add_argument("--gate", type=str, default=None,
                          help="Path to gate config YAML. Enables selective module activation.")
    gate_grp.add_argument("--gate-mode", type=str, default="on",
                          choices=["on", "off", "rules_only"],
                          help="Gate mode: on (rules+LLM), rules_only (no LLM fallback), off.")

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
    samples = load_hitom(
        data_dir=args.data_dir,
        deduplicate=args.deduplicate,
        prefer_prompting_type=args.prompting_type,
    )
    logger.info("Loaded %d total Hi-ToM samples", len(samples))

    pool = select_samples(samples, offset=args.offset, limit=args.limit)

    task_counts = defaultdict(int)
    for s in pool:
        task_counts[s["metadata"]["task"]] += 1
    logger.info("Selected %d samples across %d question orders (offset=%d, limit=%s per order)",
                len(pool), len(task_counts), args.offset, args.limit or "all")
    for t in sorted(task_counts):
        logger.info("  %-20s %4d", t, task_counts[t])

    if not pool:
        logger.info("Nothing to run.")
        return

    # ── Helper endpoint credentials ────────────────────────────────────────────────────────
    helper_api_base = args.helper_api_base or os.environ.get("HELPER_API_BASE", "")
    helper_api_key = args.helper_api_key or os.environ.get("HELPER_API_KEY", "")
    main_model_name = os.environ.get("TOM_MODEL", "qwen3-32b")

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

    # ── Gate setup ─────────────────────────────────────────────────────────
    shared_gate: ModuleGate | None = None
    if args.gate:
        gate_path = Path(args.gate)
        if not gate_path.exists():
            logger.warning("Gate config %s not found — running without gate", gate_path)
        else:
            gate_llm = None
            if args.gate_mode != "rules_only" and helper_api_key:
                gate_llm = LLMClient(
                    api_base=helper_api_base, api_key=helper_api_key, model=main_model_name,
                    temperature=0.0, max_tokens=64, timeout=30.0, max_retries=2,
                )
            shared_gate = load_gate_config(gate_path, llm=gate_llm, dataset_name="hitom")
            shared_gate.mode = args.gate_mode
            logger.info("Gate enabled: config=%s, mode=%s, %d rules, llm=%s",
                        gate_path.name, args.gate_mode, len(shared_gate.rules),
                        "yes" if gate_llm else "no")

    # ── Run ─────────────────────────────────────────────────────────────────
    llm_cache_dir = str(out_dir / "llm_cache")
    runtime_factory = lambda: build_harness(  # noqa: E731
        shared_rag=shared_rag,
        shared_memory=shared_memory,
        shared_gate=shared_gate,
        cache_dir=llm_cache_dir,
        enable_skill=args.skill,
        route_mode=args.route_mode,
        inject_mode=args.inject_mode,
        review_mode=args.review_mode,
        lang=args.lang,
        router_llm=shared_router_llm,
    )
    t_start = time.time()
    completed = 0
    with ThreadPoolExecutor(max_workers=args.workers) as exe:
        futs = {exe.submit(process_one, runtime_factory, s): s for s in pool}
        for fut in as_completed(futs):
            s = futs[fut]
            try:
                rec, log_lines = fut.result(timeout=360)
            except Exception as e:
                rec = {"id": s["id"], "task": s["metadata"].get("task"),
                       "question_order": s["metadata"].get("question_order"),
                       "deception": s["metadata"].get("deception"),
                       "story_length": s["metadata"].get("story_length"),
                       "answer": s["answer"],
                       "predicted": "", "correct": False,
                       "error": f"outer: {e}", "skill_id": None, "n_llm_calls": 0,
                       "elapsed_sec": 0.0}
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

    _print_and_save_stats(results_path, stats_path, pool)


def _print_and_save_stats(results_path: Path, stats_path: Path, pool: list) -> None:
    all_records = _load_all(results_path)
    if not all_records:
        logger.info("No results to summarize.")
        return
    stats = _compute_stats(all_records)
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

    sep = "=" * 70
    logger.info("\n%s\nHi-ToM results  →  %s\n%s", sep, stats_path, sep)
    o = stats["overall"]
    logger.info("Overall: %d/%d = %.1f%%  (errors: %d)",
                o["correct"], o["total"], o["accuracy"] * 100, o["errors"])

    logger.info("\n%-20s %4s %7s  %4s", "Question Order", "N", "Acc", "Err")
    logger.info("-" * 40)
    for t in sorted(stats["per_task"]):
        ts = stats["per_task"][t]
        logger.info("  %-18s %4d %6.1f%%  %4d", t, ts["total"], ts["accuracy"] * 100, ts["errors"])

    if "per_deception" in stats:
        logger.info("\n%-20s %4s %7s  %4s", "Deception", "N", "Acc", "Err")
        logger.info("-" * 40)
        for d in sorted(stats["per_deception"]):
            ds = stats["per_deception"][d]
            logger.info("  %-18s %4d %6.1f%%  %4d", d, ds["total"], ds["accuracy"] * 100, ds["errors"])

    if "per_story_length" in stats:
        logger.info("\n%-20s %4s %7s  %4s", "Story Length", "N", "Acc", "Err")
        logger.info("-" * 40)
        for sl in sorted(stats["per_story_length"]):
            sls = stats["per_story_length"][sl]
            logger.info("  %-18s %4d %6.1f%%  %4d", sl, sls["total"], sls["accuracy"] * 100, sls["errors"])

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


def _load_all(path: Path):
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


def _compute_stats(records):
    total = len(records)
    correct = sum(1 for r in records if r.get("correct"))
    errors = sum(1 for r in records if r.get("error") or not r.get("predicted"))

    per_task = defaultdict(lambda: {"total": 0, "correct": 0, "errors": 0, "avg_elapsed": 0.0})
    per_deception = defaultdict(lambda: {"total": 0, "correct": 0, "errors": 0})
    per_story_length = defaultdict(lambda: {"total": 0, "correct": 0, "errors": 0})
    elapsed_sum = defaultdict(float)

    routed_count = 0
    review_changed_count = 0
    review_helped = 0
    review_hurt = 0

    for r in records:
        t = r.get("task", "unknown")
        deception = str(r.get("deception", "unknown"))
        story_len = str(r.get("story_length", "unknown"))
        is_correct = int(bool(r.get("correct")))
        is_error = int(bool(r.get("error") or not r.get("predicted")))

        per_task[t]["total"] += 1
        per_task[t]["correct"] += is_correct
        per_task[t]["errors"] += is_error
        elapsed_sum[t] += float(r.get("elapsed_sec", 0.0) or 0.0)

        per_deception[deception]["total"] += 1
        per_deception[deception]["correct"] += is_correct
        per_deception[deception]["errors"] += is_error

        per_story_length[story_len]["total"] += 1
        per_story_length[story_len]["correct"] += is_correct
        per_story_length[story_len]["errors"] += is_error

        if r.get("skill_ids"):
            routed_count += 1
        if r.get("review_changed"):
            review_changed_count += 1
            draft_correct = (r.get("draft_predicted") == r.get("answer"))
            final_correct = r.get("correct")
            if final_correct and not draft_correct:
                review_helped += 1
            elif draft_correct and not final_correct:
                review_hurt += 1

    for t, d in per_task.items():
        valid_n = d["total"] - d["errors"]
        d["accuracy"] = d["correct"] / valid_n if valid_n > 0 else 0.0
        d["avg_elapsed"] = round(elapsed_sum[t] / (d["total"] or 1), 2)

    for d in list(per_deception.values()) + list(per_story_length.values()):
        valid_n = d["total"] - d["errors"]
        d["accuracy"] = d["correct"] / valid_n if valid_n > 0 else 0.0

    valid_total = total - errors
    return {
        "overall": {
            "total": total, "correct": correct, "errors": errors,
            "accuracy": round(correct / valid_total, 4) if valid_total else 0,
        },
        "routing": {
            "routed": routed_count,
            "no_skill": total - routed_count,
        },
        "review": {
            "changed": review_changed_count,
            "helped": review_helped,
            "hurt": review_hurt,
        },
        "per_task": dict(per_task),
        "per_deception": dict(per_deception),
        "per_story_length": dict(per_story_length),
        "benchmark": "Hi-ToM",
    }


if __name__ == "__main__":
    main()
