"""Run the harness on TactfulToM — white lie understanding benchmark.

Usage examples:
  # Run 5 samples per question type, baseline (no tools)
  python examples/run_tactful_tom_harness.py --limit 5

  # Run with skill routing + RAG + memory
  python examples/run_tactful_tom_harness.py --limit 10 --skill --rag --memory

  # Run only belief-related questions
  python examples/run_tactful_tom_harness.py --limit 10 --categories belief

  # Run only specific question types
  python examples/run_tactful_tom_harness.py --limit 10 --question-types "comprehension,justification:liar"

  # Run specific dataset subsets (0-4)
  python examples/run_tactful_tom_harness.py --limit 10 --sets 0,1

  # Run ALL samples
  python examples/run_tactful_tom_harness.py --limit 0

Env vars for test model:
  TOM_API_BASE, TOM_API_KEY, TOM_MODEL, TOM_TEMPERATURE

Env vars for helper model (selector/classifier):
  HELPER_API_BASE, HELPER_API_KEY

Outputs (saved to <out_dir>/):
  - results.jsonl        per-sample records
  - stats.json           per-type + per-category + overall accuracy
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

from benchmark.load_tactful_tom import load_tactful_tom  # noqa: E402

from tom_harness import LLMClient, build_default_runtime  # noqa: E402
from tom_harness.runtime import SYSTEM_LIST  # noqa: E402
from tom_harness.routing import SkillV5Router, NoOpRouter  # noqa: E402
from tom_harness.tools.rag_v2 import RAGv2Engine, CategoryClassifier  # noqa: E402
from tom_harness.gate import ModuleGate, load_gate_config  # noqa: E402


class _FrameworkConsoleFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return not record.name.startswith("tom_harness")


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("tactful_bench")

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
    """Apply offset/limit per question_type to balance the sample pool."""
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


def _score_list_answer(predicted_names: list[str], ground_truth: list[str]) -> bool:
    """Exact set match: precision=1 AND recall=1 (case-insensitive)."""
    pred_set = {n.strip().lower() for n in predicted_names if n.strip()}
    gt_set = {n.strip().lower() for n in ground_truth}
    return pred_set == gt_set


def _parse_list_response(raw: str, all_characters: list[str]) -> list[str]:
    """Parse model output into a list of character names.

    Strategy (aligned with original paper's comma-separated output format):
      1. Primary: comma-split the output and validate against known characters
      2. Fallback: try JSON {"answer": [...]} for backward compatibility
      3. Last resort: find known character names in the raw output
    """
    import re as _re
    # Strip think tags
    text = _re.sub(r"<think>[\s\S]*?</think>", "", raw or "").strip()
    if not text:
        m_think = _re.search(r"<think>([\s\S]*?)</think>", raw or "")
        text = m_think.group(1).strip() if m_think else ""
    if not text:
        return []

    char_lower = {n.lower().strip(): n for n in all_characters}

    # 1. Primary: comma-split (paper's expected format)
    # Try each line, preferring lines where ALL parts match known characters
    for line in text.splitlines():
        line_s = line.strip().strip(".")
        if not line_s:
            continue
        parts = [p.strip().strip("*").strip('"').strip("'").strip()
                 for p in line_s.replace(" and ", ",").split(",")]
        parts = [p for p in parts if p]
        if not parts:
            continue
        matched = [char_lower[p.lower()] for p in parts if p.lower() in char_lower]
        if matched and len(matched) == len(parts):
            return matched

    # 2. Fallback: JSON parse (for backward compatibility with older outputs)
    json_match = _re.search(r'\{[^{}]*"answer"\s*:\s*\[([^\]]*)\][^{}]*\}', text)
    if json_match:
        try:
            obj = json.loads(json_match.group(0))
            names = obj.get("answer", [])
            if isinstance(names, list):
                return [n.strip() for n in names if isinstance(n, str) and n.strip()]
        except (json.JSONDecodeError, TypeError):
            inner = json_match.group(1)
            parts = [p.strip().strip('"').strip("'") for p in inner.split(",")]
            return [p for p in parts if p]

    # 3. Substring fallback (riskier — only if above failed)
    found = []
    text_lower = text.lower()
    for name in all_characters:
        if name.lower() in text_lower:
            found.append(name)
    return found


def _build_list_prompt(story: str, question: str, all_characters: list[str],
                       information: str | None = None,
                       information_type: str | None = None) -> str:
    """Build a prompt for list-mode questions, following the original paper's design.

    Paper format: # Context → # Information/Target Question → # Question
    No reasoning requested, no JSON format, comma-separated output only.
    """
    parts = [f"# Context:\n{story}"]
    if information:
        if information_type == "target_question":
            parts.append(f"# Target Question:\n{information}")
        else:
            parts.append(f"# Information:\n{information}")
    parts.append(f"# Question:\n{question}")
    return "\n\n".join(parts)


def process_one(runtime_factory, sample, timeout_sec: float = 180.0):
    buf_handler = logging.handlers.MemoryHandler(capacity=10000, flushLevel=logging.CRITICAL + 1)
    buf_handler.setLevel(logging.DEBUG)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    buf_handler.setFormatter(fmt)
    framework_logger = logging.getLogger("tom_harness")
    framework_logger.addHandler(buf_handler)

    is_list_mode = sample["metadata"].get("eval_mode") == "list"

    t0 = time.time()
    rec = {
        "id": sample["id"],
        "task": sample["metadata"].get("task"),
        "category": sample["metadata"].get("category"),
        "lie_type": sample["metadata"].get("lie_type"),
        "eval_mode": "list" if is_list_mode else "mcq",
        "answer": sample.get("answer_list", []) if is_list_mode else sample["answer"],
        "predicted": "",
        "predicted_list": [],
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
        if is_list_mode:
            prompt = _build_list_prompt(
                sample["story"], sample["question"], sample.get("all_characters", []),
                information=sample.get("information"),
                information_type=sample.get("information_type"),
            )
            result = runtime.answer_one(
                question=prompt,
                story="",
                options={},
                free_form=True,
                system_override=SYSTEM_LIST,
            )
            raw_output = result.answer or ""
            rec["predicted"] = raw_output
            parsed = _parse_list_response(raw_output, sample.get("all_characters", []))
            rec["predicted_list"] = parsed
            rec["correct"] = _score_list_answer(parsed, sample.get("answer_list", []))
        else:
            result = runtime.answer_one(
                question=sample["question"],
                story=sample["story"],
                options=sample["options"],
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
        description="Run ToM harness on TactfulToM (white lie understanding).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    data_grp = ap.add_argument_group("data selection")
    data_grp.add_argument("--data_dir", type=str, default=None,
                          help="Path to TactfulToM final_set/ directory.")
    data_grp.add_argument("--sets", type=str, default=None,
                          help="Comma-separated set indices (0-4). Default: all.")
    data_grp.add_argument("--categories", type=str, default=None,
                          help="Comma-separated categories: comprehension,justification,fact,"
                               "belief,info_accessibility,answerability,liedetectability,lieability")
    data_grp.add_argument("--question-types", type=str, default=None,
                          help="Comma-separated exact question_type strings to include.")
    data_grp.add_argument("--limit", type=int, default=20,
                          help="Max samples PER QUESTION TYPE (default: 20, 0 = no limit).")
    data_grp.add_argument("--offset", type=int, default=0)

    exec_grp = ap.add_argument_group("execution")
    exec_grp.add_argument("--workers", type=int, default=8)
    exec_grp.add_argument("--verbose", "-v", action="store_true")

    out_grp = ap.add_argument_group("output")
    out_grp.add_argument("--out_dir", default="results/tactful_tom")

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
    set_indices = [int(x.strip()) for x in args.sets.split(",")] if args.sets else None
    cat_filter = {c.strip() for c in args.categories.split(",")} if args.categories else None
    qt_filter = {t.strip() for t in args.question_types.split(",")} if args.question_types else None

    samples = load_tactful_tom(
        data_dir=args.data_dir,
        sets=set_indices,
        categories=cat_filter,
        question_types=qt_filter,
    )
    logger.info("Loaded %d total TactfulToM samples", len(samples))

    pool = select_samples(samples, offset=args.offset, limit=args.limit)

    task_counts = defaultdict(int)
    cat_counts = defaultdict(int)
    for s in pool:
        task_counts[s["metadata"]["task"]] += 1
        cat_counts[s["metadata"]["category"]] += 1
    logger.info("Selected %d samples across %d question types (offset=%d, limit=%s per type)",
                len(pool), len(task_counts), args.offset, args.limit or "all")
    for c in sorted(cat_counts):
        logger.info("  category %-25s %4d", c, cat_counts[c])

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
            shared_gate = load_gate_config(gate_path, llm=gate_llm)
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
                is_list = s["metadata"].get("eval_mode") == "list"
                rec = {"id": s["id"], "task": s["metadata"].get("task"),
                       "category": s["metadata"].get("category"),
                       "lie_type": s["metadata"].get("lie_type"),
                       "eval_mode": "list" if is_list else "mcq",
                       "answer": s.get("answer_list", []) if is_list else s["answer"],
                       "predicted": "", "predicted_list": [],
                       "correct": False,
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
    logger.info("\n%s\nTactfulToM results  →  %s\n%s", sep, stats_path, sep)
    o = stats["overall"]
    logger.info("Overall: %d/%d = %.1f%%  (errors: %d)",
                o["correct"], o["total"], o["accuracy"] * 100, o["errors"])

    if "per_eval_mode" in stats:
        logger.info("\n%-10s %4s %7s  %4s", "Eval Mode", "N", "Acc", "Err")
        logger.info("-" * 30)
        for em in sorted(stats["per_eval_mode"]):
            es = stats["per_eval_mode"][em]
            logger.info("  %-8s %4d %6.1f%%  %4d", em, es["total"], es["accuracy"] * 100, es["errors"])

    logger.info("\n%-30s %4s %7s  %4s", "Category", "N", "Acc", "Err")
    logger.info("-" * 50)
    for c in sorted(stats["per_category"]):
        cs = stats["per_category"][c]
        logger.info("  %-28s %4d %6.1f%%  %4d", c, cs["total"], cs["accuracy"] * 100, cs["errors"])

    logger.info("\n%-45s %4s %7s  %4s", "Question Type", "N", "Acc", "Err")
    logger.info("-" * 65)
    for t in sorted(stats["per_task"]):
        ts = stats["per_task"][t]
        logger.info("  %-43s %4d %6.1f%%  %4d", t, ts["total"], ts["accuracy"] * 100, ts["errors"])

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
    errors = sum(1 for r in records if r.get("error") or (
        r.get("eval_mode") != "list" and not r.get("predicted")
    ))

    per_task = defaultdict(lambda: {"total": 0, "correct": 0, "errors": 0, "avg_elapsed": 0.0})
    per_category = defaultdict(lambda: {"total": 0, "correct": 0, "errors": 0})
    per_lie_type = defaultdict(lambda: {"total": 0, "correct": 0, "errors": 0})
    per_eval_mode = defaultdict(lambda: {"total": 0, "correct": 0, "errors": 0})
    elapsed_sum = defaultdict(float)

    for r in records:
        t = r.get("task", "unknown")
        cat = r.get("category", "unknown")
        lt = r.get("lie_type", "unknown")
        em = r.get("eval_mode", "mcq")
        is_correct = int(bool(r.get("correct")))
        is_error = int(bool(r.get("error") or (em != "list" and not r.get("predicted"))))

        per_task[t]["total"] += 1
        per_task[t]["correct"] += is_correct
        per_task[t]["errors"] += is_error
        elapsed_sum[t] += float(r.get("elapsed_sec", 0.0) or 0.0)

        per_category[cat]["total"] += 1
        per_category[cat]["correct"] += is_correct
        per_category[cat]["errors"] += is_error

        per_lie_type[lt]["total"] += 1
        per_lie_type[lt]["correct"] += is_correct
        per_lie_type[lt]["errors"] += is_error

        per_eval_mode[em]["total"] += 1
        per_eval_mode[em]["correct"] += is_correct
        per_eval_mode[em]["errors"] += is_error

    for t, d in per_task.items():
        valid_n = d["total"] - d["errors"]
        d["accuracy"] = d["correct"] / valid_n if valid_n > 0 else 0.0
        d["avg_elapsed"] = round(elapsed_sum[t] / (d["total"] or 1), 2)

    for d in list(per_category.values()) + list(per_lie_type.values()) + list(per_eval_mode.values()):
        valid_n = d["total"] - d["errors"]
        d["accuracy"] = d["correct"] / valid_n if valid_n > 0 else 0.0

    valid_total = total - errors
    return {
        "overall": {
            "total": total, "correct": correct, "errors": errors,
            "accuracy": round(correct / valid_total, 4) if valid_total else 0,
        },
        "per_category": dict(per_category),
        "per_task": dict(per_task),
        "per_lie_type": dict(per_lie_type),
        "per_eval_mode": dict(per_eval_mode),
        "benchmark": "TactfulToM",
    }


if __name__ == "__main__":
    main()
