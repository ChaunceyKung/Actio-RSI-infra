"""Run agent harness evaluation using the ToMEval pipeline.

Bridge script: fully reuses ToMEval's data loading, prompt construction,
answer extraction (\boxed{}), judge, and metrics. Injects agent augmentation
(skill / RAG / memory) into the prompt before the LLM call.

Usage examples:
  # Baseline (no agent modules) on HiToM
  python eval/run_tomeval_harness.py --datasets HiToM

  # With skill routing
  python eval/run_tomeval_harness.py --datasets HiToM --skill

  # With RAG
  python eval/run_tomeval_harness.py --datasets HiToM --rag

  # With memory
  python eval/run_tomeval_harness.py --datasets HiToM --memory

  # Full agent stack
  python eval/run_tomeval_harness.py --datasets HiToM --skill --rag --memory

  # Multiple benchmarks
  python eval/run_tomeval_harness.py --datasets HiToM ToMBench EmoBench --skill --rag

  # English-only subset for bilingual datasets
  python eval/run_tomeval_harness.py --datasets ToMBench EmoBench --lang-filter en

Main evaluated model:
  Configure llm.model_name, llm.api_url, and llm.api_key in
  ToMEval/experiment_config.yaml, following ToMEval's native style.

Env vars for helper endpoint credentials (skill router / RAG tagger / memory selector):
  HELPER_API_BASE, HELPER_API_KEY
"""

from __future__ import annotations

import argparse
import copy
import json
import logging
import os
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

# ── path setup ────────────────────────────────────────────────────────────────
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_TOMEVAL_ROOT = _PROJECT_ROOT / "ToMEval"

sys.path.insert(0, str(_PROJECT_ROOT))
sys.path.insert(0, str(_TOMEVAL_ROOT))

# ── ToMEval imports ───────────────────────────────────────────────────────────
from src import runner as tomeval_runner
from src.evaluation.data import load_standardized_data, load_task_config
from src.evaluation.lang import get_sample_lang
from src.evaluation.paths import build_experiment_dir, save_config
from src.evaluation.pipeline import run_metric_stage
from src.evaluation.prompt_loaders import (
    load_task_prepare_samples,
    load_task_prompt_builder,
    load_task_system_prompt_builder,
)
from src.evaluation.prompts import build_option_bundle, build_prompt, extract_prediction_from_text, prompt_type
from src.evaluation.protocols import (
    PROTOCOLS,
    extractor_name_for,
    llm_overrides_for,
    repeats_for,
    shuffle_for,
    system_prompt_for,
)
from src.evaluation.storage import serialize_llm_response, write_prediction_file

# ── tom_harness imports ───────────────────────────────────────────────────────
from tom_harness.llm import LLMClient
from tom_harness.routing import SkillV5Router, NoOpRouter
from tom_harness.tools.rag_v2 import RAGv2Engine, CategoryClassifier
from tom_harness.orchestration import ModuleOrchestrator, run_validator_loop
from tom_harness.gate import load_gate_config
from tom_harness.validators.scalar_procedural import ScalarProceduralValidator
from tom_harness.validators.epistemic_calibration import EpistemicCalibrationValidator
from tom_harness.validators.multi_select_calibration import MultiSelectCalibrationValidator

from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv(_PROJECT_ROOT / ".env")
load_dotenv(_TOMEVAL_ROOT / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("tomeval_harness")


# ── Agent augmentation hints (selective-use, with exit conditions) ─────────

SKILL_HINT = (
    "A reasoning guide is provided below for reference. "
    "If it matches the type of question being asked, follow its approach. "
    "If it does not apply or conflicts with the story evidence, ignore it "
    "and reason directly from the text."
)

RAG_HINT = (
    "Background knowledge entries are provided below. They may or may not "
    "be relevant to this specific question. Use only the entries that directly "
    "relate to the situation described in the story. Always prioritize evidence "
    "from the story over background knowledge."
)

MEMORY_HINT = (
    "A strategy guide with common reasoning patterns is provided below. "
    "Refer to it if a listed pattern matches the current question type. "
    "Ignore any strategies that do not apply."
)


def augment_prompts(
    user_prompt: str,
    system_prompt: str,
    *,
    skill_body: str | None = None,
    rag_context: str | None = None,
    playbook_text: str | None = None,
) -> tuple[str, str]:
    """Inject agent content into ToMEval's prompt pair."""
    hints = []
    if skill_body:
        hints.append(SKILL_HINT)
    if rag_context:
        hints.append(RAG_HINT)
    if playbook_text:
        hints.append(MEMORY_HINT)
    if hints:
        system_prompt = system_prompt + "\n\n" + "\n".join(hints)

    sections = []
    if skill_body:
        sections.append(f"## Reasoning Guide\n{skill_body}")
    if rag_context:
        sections.append(f"## Background Knowledge\n{rag_context}")
    if playbook_text:
        sections.append(f"## Strategy Guide\n{playbook_text}")
    if sections:
        user_prompt = "\n\n".join(sections) + "\n\n" + user_prompt

    return user_prompt, system_prompt


# ── Agent modules setup ───────────────────────────────────────────────────────

def helper_endpoint(args, experiment_config: dict) -> tuple[str, str, str]:
    llm_config = experiment_config["llm_config"]
    return (
        args.helper_api_base or os.environ.get("HELPER_API_BASE") or llm_config.get("api_url", ""),
        args.helper_api_key or os.environ.get("HELPER_API_KEY") or llm_config.get("api_key", ""),
        llm_config["model_name"],
    )


def setup_skill_router(args, experiment_config: dict) -> SkillV5Router | None:
    if not args.skill:
        return None
    api_base, api_key, model_name = helper_endpoint(args, experiment_config)
    if not api_key:
        logger.warning("No API key for skill router — skipping")
        return None
    router_llm = LLMClient(
        api_base=api_base, api_key=api_key, model=model_name,
        temperature=0.0, max_tokens=256, timeout=60.0, max_retries=3,
    )
    logger.info("Skill router using model: %s", model_name)

    router = SkillV5Router(
        llm=router_llm,
        route_mode=args.route_mode,
        inject_mode=args.inject_mode,
        lang=args.lang,
    )
    logger.info(
        "Skill routing enabled (route_mode=%s, inject_mode=%s, lang=%s)",
        args.route_mode, args.inject_mode, args.lang,
    )
    return router


def setup_rag(args, experiment_config: dict) -> RAGv2Engine | None:
    if not args.rag:
        return None
    api_base, api_key, model_name = helper_endpoint(args, experiment_config)

    classifier = None
    if api_key:
        classifier = CategoryClassifier(
            api_base=api_base, api_key=api_key, model=model_name,
        )
    rag = RAGv2Engine(
        data_dir=args.rag_data_dir,
        index_dir=args.rag_index_dir,
        model_name=args.rag_model,
        classifier=classifier,
    )
    rag.build_index()
    if rag.size() > 0:
        logger.info("RAG enabled: %d rules indexed", rag.size())
        return rag
    logger.warning("RAG data not found — running without RAG")
    return None


def setup_memory(args, experiment_config: dict):
    if not args.memory:
        return None
    api_base, api_key, model_name = helper_endpoint(args, experiment_config)

    if not api_key:
        logger.warning("Memory requires an API key — skipping")
        return None
    if not Path(args.memory_playbook).exists():
        logger.warning("Playbook file %s not found — skipping memory", args.memory_playbook)
        return None

    from memory_playbook import Memory, SelectorConfig
    selector_cfg = SelectorConfig(
        provider="custom",
        api_key=api_key,
        model=model_name,
        base_url=api_base or None,
    )
    mem = Memory(args.memory_playbook, selector_cfg)
    logger.info("Memory enabled: playbook=%s, selector_model=%s",
                args.memory_playbook, model_name)
    return mem


def setup_gate(args, experiment_config: dict, dataset_name: str):
    """Build a per-dataset ModuleGate (unified gates dispatch on dataset_name)."""
    if not args.gate:
        return None
    gate_path = Path(args.gate)
    if not gate_path.exists():
        logger.warning("Gate config %s not found — running without gate", gate_path)
        return None
    gate_llm = None
    if args.gate_mode != "rules_only":
        api_base, api_key, model_name = helper_endpoint(args, experiment_config)
        if api_key:
            gate_llm = LLMClient(
                api_base=api_base, api_key=api_key, model=model_name,
                temperature=0.0, max_tokens=64, timeout=30.0, max_retries=2,
            )
    gate = load_gate_config(gate_path, llm=gate_llm, dataset_name=dataset_name.lower())
    gate.mode = args.gate_mode
    logger.info(
        "[%s] Gate enabled: config=%s, mode=%s, llm=%s",
        dataset_name, gate_path.name, args.gate_mode, "yes" if gate_llm else "no",
    )
    return gate


# ── Per-sample agent augmentation ─────────────────────────────────────────────

_AUG_MAX_WORKERS = 16


def _option_cache_key(option_map: dict[str, str] | None) -> tuple:
    if option_map is None:
        return ()
    return tuple(sorted(option_map.items()))


def _gate_eval_mode(prompt_type: str | None) -> str:
    """Map a ToMEval prompt_type to the coarse mode the module gate keys on."""
    return "free_form" if prompt_type == "open" else "mcq"


def get_agent_augmentation(
    sample,
    option_map: dict[str, str] | None,
    *,
    orch: ModuleOrchestrator,
    gate_eval_mode: str,
) -> tuple[str | None, str | None, str | None]:
    """Run the shared module pipeline; return (skill_body, rag_context, playbook).

    Delegates to the host-agnostic ModuleOrchestrator so eval uses the exact
    same gate→skill→rag→memory orchestration as HarnessRuntime.answer_one.
    """
    aug = orch.augment(
        question=sample["question"],
        story=sample["story"],
        options=option_map or {},
        gate_eval_mode=gate_eval_mode,
        raw_metadata=sample.get("meta"),
    )
    return aug.skill_body, aug.rag_context, aug.playbook_text


# ── Validator support ────────────────────────────────────────────────────────

def setup_validators(args) -> list:
    """Build the list of active validators from CLI flags."""
    validators = []
    if not args.no_scalar_validator:
        validators.append(ScalarProceduralValidator())
    if args.epistemic_validator:
        validators.append(EpistemicCalibrationValidator())
    if args.multi_select_validator:
        validators.append(MultiSelectCalibrationValidator())
    return validators


def _validate_and_retry(
    payload: dict,
    validators: list,
    client,
    max_retries: int,
) -> list[dict]:
    """Run the shared validator loop on one ToMEval payload.

    Uses the same `run_validator_loop` as HarnessRuntime; the only
    host-specific piece is the `retry_fn`, which re-asks via ToMEval's
    `client.generate` (boxed protocol) and extracts with ToMEval's
    extractor. The final answer is reflected back into `pred.content` so
    ToMEval's judge scores exactly what the loop settled on.

    Returns a list of validator event dicts for tracing.
    """
    content = payload["pred"].get("content")
    if content is None:
        return []

    prompt_t = payload["prompt_type"]
    if prompt_t == "open":
        return []

    extractor = payload.get("extractor", "legacy")
    predicted = extract_prediction_from_text(prompt_t, str(content), extractor)
    if predicted is None:
        return []

    current_answer = predicted if isinstance(predicted, str) else ",".join(predicted)
    options = payload.get("options") or {}
    story = payload.get("story", "")
    question = payload.get("question", "")
    eval_mode = payload.get("eval_mode")
    system_prompt = payload.get("system_prompt", "")

    def tomeval_retry(feedback: str, prior_answer: str):
        """Host (ToMEval) re-ask: boxed-protocol retry via client.generate."""
        retry_prompt = payload["prompt"] + "\n\n" + feedback
        response = client.generate(retry_prompt, system_prompt=system_prompt or None)
        new_content = response.content if response else None
        if new_content is None:
            return None  # LLM re-ask failed → abort retries for this validator
        new_pred = extract_prediction_from_text(prompt_t, str(new_content), extractor)
        if new_pred is None:
            return "", (response.reasoning or "")
        new_answer = new_pred if isinstance(new_pred, str) else ",".join(new_pred)
        return new_answer, (response.reasoning or "")

    final_answer, events = run_validator_loop(
        validators,
        question=question, story=story, options=options, eval_mode=eval_mode,
        answer=current_answer, reasoning=payload["pred"].get("reasoning", ""),
        max_retries=max_retries, retry_fn=tomeval_retry,
    )

    # Reflect the loop's final answer into the record. Covers both pure
    # substitution (no LLM call) and a successful retry: whenever the answer
    # the loop settled on differs from what pred.content currently encodes,
    # coerce content to the corrected boxed answer for the judge.
    if final_answer:
        cur = extract_prediction_from_text(prompt_t, str(payload["pred"].get("content") or ""), extractor)
        cur_str = cur if isinstance(cur, str) else (",".join(cur) if cur else "")
        if cur_str != final_answer:
            payload["pred"]["content"] = f"\\boxed{{{final_answer}}}"

    return events


# ── Prediction stage (adapted from ToMEval predict_records) ───────────────────

def agent_predict_records(
    samples,
    dataset_name: str,
    client,
    repeats: int,
    protocol: str | None,
    *,
    orch: ModuleOrchestrator | None,
    has_agent: bool,
    validators: list | None = None,
    max_retries: int = 1,
):
    """Build predictions with agent augmentation injected into ToMEval prompts."""
    records = []
    use_shuffle = shuffle_for(protocol)
    extractor = extractor_name_for(protocol)
    # The cross-repeat augmentation cache only benefits del_tom (8 repeats, no
    # shuffle → stable (sample_id, options) key). Single-repeat protocols
    # (direct/cot) never reuse it, so it is enabled only for del_tom and every
    # sample is computed fresh otherwise.
    use_aug_cache = protocol == "del_tom"

    prepare = load_task_prepare_samples(dataset_name)
    if prepare is not None:
        samples = prepare(samples)
    custom_builder = load_task_prompt_builder(dataset_name)
    builder = custom_builder or build_prompt
    custom_system = load_task_system_prompt_builder(dataset_name)

    # Cache augmentation results across repeats: keyed by (sample_id, frozen_options).
    # Only used when use_aug_cache (del_tom): repeat 0 populates it, repeats 1-7
    # reuse it. Stays empty for direct/cot.
    aug_cache: dict[tuple, tuple[str | None, str | None, str | None]] = {}

    for repeat in range(repeats):
        repeat_payloads = []
        grouped_prompts: dict[str, list[str]] = defaultdict(list)
        grouped_system: dict[str, list[str]] = defaultdict(list)
        grouped_indices: dict[str, list[int]] = defaultdict(list)

        # Phase 1: build option bundles and base prompts (no LLM calls)
        sample_bundles = []
        for sample_index, sample in enumerate(samples):
            override = (sample.get("meta") or {}).get("prompt_type_override")
            if override:
                option_map, correct_letters, wrong_letters, shuffle_seed = None, [], [], 0
                current_prompt_type = override
            else:
                option_map, correct_letters, wrong_letters, shuffle_seed = build_option_bundle(
                    dataset_name, sample["sample_id"], sample["answer"],
                    repeat, shuffle=use_shuffle,
                )
                current_prompt_type = prompt_type(sample["answer"])

            user_prompt = builder(sample, option_map, include_instruction=protocol is None)
            if protocol is None:
                system_prompt = ""
            else:
                lang = get_sample_lang(sample.get("meta"))
                if custom_system is not None:
                    system_prompt = custom_system(sample, protocol, lang, current_prompt_type)
                else:
                    system_prompt = system_prompt_for(protocol, lang, current_prompt_type)

            sample_bundles.append({
                "sample_index": sample_index,
                "sample": sample,
                "option_map": option_map,
                "correct_letters": correct_letters,
                "wrong_letters": wrong_letters,
                "shuffle_seed": shuffle_seed,
                "current_prompt_type": current_prompt_type,
                "user_prompt": user_prompt,
                "system_prompt": system_prompt,
            })

        # Phase 2: parallel agent augmentation (cross-repeat cache only for del_tom)
        if has_agent:
            if use_aug_cache:
                uncached_indices = [
                    i for i, bundle in enumerate(sample_bundles)
                    if (bundle["sample"]["sample_id"],
                        _option_cache_key(bundle["option_map"])) not in aug_cache
                ]
            else:
                # No caching: recompute every sample fresh this repeat.
                uncached_indices = list(range(len(sample_bundles)))

            augmentations: dict[int, tuple] = {}
            if uncached_indices:
                with ThreadPoolExecutor(max_workers=_AUG_MAX_WORKERS) as executor:
                    future_to_idx = {}
                    for i in uncached_indices:
                        b = sample_bundles[i]
                        future = executor.submit(
                            get_agent_augmentation,
                            b["sample"], b["option_map"],
                            orch=orch,
                            gate_eval_mode=_gate_eval_mode(b["current_prompt_type"]),
                        )
                        future_to_idx[future] = i

                    cache_hit = len(sample_bundles) - len(uncached_indices)
                    desc = f"Agent augmentation (repeat {repeat})"
                    if cache_hit:
                        desc += f" [{cache_hit} cached]"
                    for future in tqdm(as_completed(future_to_idx),
                                       total=len(future_to_idx), desc=desc):
                        idx = future_to_idx[future]
                        augmentations[idx] = future.result()

                if use_aug_cache:
                    for i in uncached_indices:
                        b = sample_bundles[i]
                        cache_key = (b["sample"]["sample_id"],
                                     _option_cache_key(b["option_map"]))
                        aug_cache[cache_key] = augmentations[i]

            for idx, bundle in enumerate(sample_bundles):
                if use_aug_cache:
                    cache_key = (bundle["sample"]["sample_id"],
                                 _option_cache_key(bundle["option_map"]))
                    skill_body, rag_context, playbook_text = aug_cache[cache_key]
                else:
                    skill_body, rag_context, playbook_text = augmentations[idx]
                bundle["user_prompt"], bundle["system_prompt"] = augment_prompts(
                    bundle["user_prompt"], bundle["system_prompt"],
                    skill_body=skill_body, rag_context=rag_context,
                    playbook_text=playbook_text,
                )

        # Phase 3: build payloads and group by prompt type
        for bundle in sample_bundles:
            sample = bundle["sample"]
            current_prompt_type = bundle["current_prompt_type"]
            user_prompt = bundle["user_prompt"]
            system_prompt = bundle["system_prompt"]

            payload = {
                "sample_id": sample["sample_id"],
                "sample_index": bundle["sample_index"],
                "repeat": repeat,
                "story": sample["story"],
                "question": sample["question"],
                "correct_answers": sample["answer"]["correct_answers"],
                "wrong_answers": sample["answer"]["wrong_answers"],
                "prompt_type": current_prompt_type,
                "prompt": user_prompt,
                "options": bundle["option_map"],
                "correct_letters": bundle["correct_letters"],
                "wrong_letters": bundle["wrong_letters"],
                "shuffle_seed": bundle["shuffle_seed"],
                "meta": sample["meta"],
                "pred": {"content": None, "reasoning": ""},
                "protocol": protocol,
                "extractor": extractor,
                "system_prompt": system_prompt,
            }
            repeat_payloads.append(payload)
            grouped_prompts[current_prompt_type].append(user_prompt)
            grouped_system[current_prompt_type].append(system_prompt)
            grouped_indices[current_prompt_type].append(bundle["sample_index"])

        # Phase 4: batch LLM calls (reuse ToMEval's client)
        responses_by_index = {}
        prompt_type_labels = {
            "open": "Open QA",
            "mcq_single": "Multiple Choice (Single)",
            "mcq_multi": "Multiple Choice (Multi)",
            "mcq_grouped": "Multiple Choice (Grouped)",
        }
        for current_prompt_type in sorted(grouped_prompts):
            prompts = grouped_prompts[current_prompt_type]
            if not prompts:
                continue
            desc = f"Generating ({prompt_type_labels.get(current_prompt_type, current_prompt_type)})"
            system_prompts = grouped_system[current_prompt_type] if protocol is not None else None
            responses = client.batch_generate(prompts, desc=desc, system_prompts=system_prompts)
            for sample_index, response in zip(grouped_indices[current_prompt_type], responses):
                responses_by_index[sample_index] = response

        for payload in repeat_payloads:
            response = responses_by_index.get(payload["sample_index"])
            payload["pred"] = serialize_llm_response(response)

        # Phase 5: per-sample validation + retry
        if validators:
            for payload in repeat_payloads:
                events = _validate_and_retry(payload, validators, client, max_retries)
                if events:
                    if payload.get("meta") is None:
                        payload["meta"] = {}
                    payload["meta"]["validator_events"] = events

        for payload in repeat_payloads:
            records.append(payload)

    return records


# ── Protocol config ───────────────────────────────────────────────────────────

def apply_protocol(experiment_config: dict, protocol: str | None) -> dict:
    cfg = copy.deepcopy(experiment_config)
    cfg["protocol"] = protocol
    if protocol is not None:
        cfg["llm_config"].update(llm_overrides_for(protocol))
        cfg["repeats"] = repeats_for(protocol, cfg.get("repeats", 1))
    return cfg


# ── Run one dataset ───────────────────────────────────────────────────────────

def run_dataset(
    dataset_name: str,
    experiment_config: dict,
    *,
    args,
    router: SkillV5Router | None,
    rag_engine: RAGv2Engine | None,
    memory,
    validators: list | None = None,
    max_retries: int = 1,
    results_path_override: str | None = None,
    lang_filter: str | None = None,
) -> dict | None:
    """Run agent-augmented prediction + ToMEval metric for one dataset."""
    task_config_path = str(_TOMEVAL_ROOT / "tasks" / dataset_name / "config.yaml")
    if not Path(task_config_path).exists():
        logger.warning("[%s] config.yaml not found, skipping", dataset_name)
        return None

    task_config = load_task_config(task_config_path)
    samples = load_standardized_data(task_config, experiment_config)
    if lang_filter:
        before_count = len(samples)
        samples = [
            sample for sample in samples
            if get_sample_lang(sample.get("meta")) == lang_filter
        ]
        logger.info(
            "[%s] Language filter %s: %d/%d samples kept",
            dataset_name, lang_filter, len(samples), before_count,
        )
    if not samples:
        logger.warning("[%s] no samples loaded, skipping", dataset_name)
        return None

    logger.info("[%s] Loaded %d samples", dataset_name, len(samples))

    results_path = results_path_override or experiment_config["results_path"]
    model_name = experiment_config["llm_config"]["model_name"]
    output_dir = build_experiment_dir(
        dataset_name, model_name, results_path, create=True,
    )
    save_config(output_dir, task_config, experiment_config)
    logger.info("[%s] Output directory: %s", dataset_name, output_dir)

    # ── shared module orchestration (gate → skill → rag → memory) ─────────
    # Build the per-dataset gate, then one ModuleOrchestrator reused for every
    # sample — the exact same orchestration HarnessRuntime.answer_one uses.
    gate = setup_gate(args, experiment_config, dataset_name)
    has_agent = router is not None or rag_engine is not None or memory is not None
    orch = ModuleOrchestrator(
        router=router if router is not None else NoOpRouter(),
        rag_engine=rag_engine, memory=memory, playbook=None, gate=gate,
    )

    # ── prediction stage ──────────────────────────────────────────────────
    client = tomeval_runner.create_content_client(experiment_config["llm_config"])
    records = agent_predict_records(
        samples, dataset_name, client,
        repeats=experiment_config["repeats"],
        protocol=experiment_config.get("protocol"),
        orch=orch, has_agent=has_agent,
        validators=validators, max_retries=max_retries,
    )
    prediction_path = write_prediction_file(output_dir, records)
    logger.info("[%s] Saved %d predictions to %s", dataset_name, len(records), prediction_path)

    # ── metric stage (reuse ToMEval's judge + metrics) ────────────────────
    metrics_path = run_metric_stage(task_config, experiment_config, output_dir)
    logger.info("[%s] Metrics saved to %s", dataset_name, metrics_path)

    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    return metrics


# ── CLI ───────────────────────────────────────────────────────────────────────

def parse_args():
    ap = argparse.ArgumentParser(
        description="Run agent harness evaluation via the ToMEval pipeline.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    ap.add_argument(
        "--experiment-config",
        default=str(_TOMEVAL_ROOT / "experiment_config.yaml"),
        help="Path to ToMEval experiment_config.yaml",
    )
    ap.add_argument(
        "--datasets", nargs="+", default=None,
        help="Override datasets from experiment_config (e.g. --datasets HiToM EmoBench)",
    )
    ap.add_argument(
        "--results-path", default=None,
        help="Override results output root directory",
    )
    ap.add_argument(
        "--datasets-root", default=None,
        help="Override ToMEval normalized dataset root directory",
    )
    ap.add_argument(
        "--max-samples", "--max_samples", dest="max_samples", type=int, default=None,
        help="Override max samples per dataset (0 = all)",
    )
    ap.add_argument(
        "--protocols", nargs="+", default=None,
        choices=[*PROTOCOLS, "all"],
        help="Run one or more ToMEval protocols. Use 'all' for direct direct_think cot del_tom. Default: experiment_config protocol.",
    )
    ap.add_argument(
        "--lang-filter", choices=["en", "zh"], default=None,
        help="Run only samples matching the normalized ToMEval sample language.",
    )

    skill_grp = ap.add_argument_group("Skill injection (v5)")
    skill_grp.add_argument("--skill", action="store_true",
                           help="Enable LLM-routed skill injection.")
    skill_grp.add_argument("--route-mode", type=str, default="hierarchical",
                           choices=["baseline", "macro_only", "micro_only",
                                    "hierarchical", "flat_all"])
    skill_grp.add_argument("--inject-mode", type=str, default="light",
                           choices=["full", "light"])
    skill_grp.add_argument("--lang", type=str, default="en",
                           choices=["en", "zh"])

    rag_grp = ap.add_argument_group("RAG retrieval")
    rag_grp.add_argument("--rag", action="store_true", help="Enable RAG retrieval.")
    rag_grp.add_argument("--rag_data_dir", type=str,
                         default=str(_PROJECT_ROOT / "tom_harness" / "tools" / "rag_v2_data"))
    rag_grp.add_argument("--rag_index_dir", type=str,
                         default=str(_PROJECT_ROOT / "tom_harness" / "tools" / "rag_v2_index"))
    rag_grp.add_argument("--rag_model", type=str,
                         default=str(_PROJECT_ROOT / "model" / "bge-m3"))

    mem_grp = ap.add_argument_group("Memory playbook")
    mem_grp.add_argument("--memory", action="store_true")
    mem_grp.add_argument("--memory_playbook", type=str,
                         default=str(_PROJECT_ROOT / "memory_playbook" / "playbook" / "final_playbook.txt"))

    gate_grp = ap.add_argument_group("Module gate")
    gate_grp.add_argument("--gate", type=str, default=None,
                          help="Path to gate config YAML. Enables selective module activation.")
    gate_grp.add_argument("--gate-mode", type=str, default="on",
                          choices=["on", "off", "rules_only"],
                          help="Gate mode: on (rules+LLM), rules_only (no LLM fallback), off.")

    val_grp = ap.add_argument_group("Validators")
    val_grp.add_argument("--no-scalar-validator", action="store_true",
                         help="Disable ScalarProceduralValidator (enabled by default)")
    val_grp.add_argument("--epistemic-validator", action="store_true",
                         help="Enable EpistemicCalibrationValidator (disabled by default)")
    val_grp.add_argument("--multi-select-validator", action="store_true",
                         help="Enable MultiSelectCalibrationValidator (disabled by default)")
    val_grp.add_argument("--max-retries", type=int, default=1,
                         help="Max validator retry attempts per sample (default: 1)")

    helper_grp = ap.add_argument_group("Helper endpoint credentials (router / tagger / selector)")
    helper_grp.add_argument("--helper_api_base", type=str, default=None)
    helper_grp.add_argument("--helper_api_key", type=str, default=None)

    return ap.parse_args()


def main():
    args = parse_args()

    # ── load experiment config ────────────────────────────────────────────
    os.chdir(str(_TOMEVAL_ROOT))
    experiment_config = tomeval_runner.load_experiment_config(args.experiment_config)
    if args.datasets_root:
        experiment_config["normalized_datasets_path"] = args.datasets_root
    if args.max_samples is not None:
        experiment_config["max_samples"] = args.max_samples

    datasets = args.datasets or experiment_config.get("datasets") or []
    if not datasets:
        logger.error("No datasets specified. Use --datasets or set in experiment_config.yaml")
        return

    if args.protocols:
        protocols = list(PROTOCOLS) if "all" in args.protocols else args.protocols
    else:
        protocols = [experiment_config.get("protocol")]
    multi_protocol = len(protocols) > 1

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.environ["RUN_TIMESTAMP"] = timestamp

    agent_flags = []
    if args.skill:
        agent_flags.append("skill")
    if args.rag:
        agent_flags.append("rag")
    if args.memory:
        agent_flags.append("memory")
    agent_label = "+".join(agent_flags) if agent_flags else "baseline"

    logger.info("=" * 70)
    logger.info("ToMEval Agent Harness")
    logger.info("=" * 70)
    logger.info("Timestamp:  %s", timestamp)
    logger.info("Config:     %s", args.experiment_config)
    logger.info("Protocols:  %s", ", ".join(p or "(none)" for p in protocols))
    logger.info("Model:      %s", experiment_config["llm_config"]["model_name"])
    logger.info("API URL:    %s", experiment_config["llm_config"].get("api_url"))
    logger.info("Data root:  %s", experiment_config["normalized_datasets_path"])
    logger.info("Datasets:   %s", ", ".join(datasets))
    logger.info("Lang filter:%s", f"  {args.lang_filter}" if args.lang_filter else "  (none)")
    logger.info("Agent:      %s", agent_label)
    logger.info("=" * 70)

    # ── setup agent modules ───────────────────────────────────────────────
    router = setup_skill_router(args, experiment_config)
    rag_engine = setup_rag(args, experiment_config)
    memory = setup_memory(args, experiment_config)
    validators = setup_validators(args)
    if validators:
        logger.info("Validators: %s  max_retries=%d",
                     ", ".join(type(v).__name__ for v in validators), args.max_retries)

    # ── save agent config ─────────────────────────────────────────────────
    agent_config = {
        "skill": args.skill,
        "rag": args.rag,
        "memory": args.memory,
        "gate": args.gate,
        "gate_mode": args.gate_mode if args.gate else None,
        "route_mode": args.route_mode if args.skill else None,
        "inject_mode": args.inject_mode if args.skill else None,
        "lang": args.lang,
        "lang_filter": args.lang_filter,
        "validators": [type(v).__name__ for v in validators],
        "max_retries": args.max_retries,
        "agent_label": agent_label,
    }

    # ── run each protocol × dataset ───────────────────────────────────────
    all_results = {}
    for protocol in protocols:
        protocol_config = apply_protocol(experiment_config, protocol)
        protocol_label = protocol or "none"
        protocol_results_path = args.results_path or protocol_config["results_path"]
        if multi_protocol:
            protocol_results_path = str(Path(protocol_results_path) / protocol_label)

        for dataset in datasets:
            result_key = f"{protocol_label}/{dataset}" if multi_protocol else dataset
            logger.info("\n%s", "=" * 60)
            logger.info("Running: %s  protocol=%s", dataset, protocol_label)
            logger.info("=" * 60)
            try:
                metrics = run_dataset(
                    dataset, protocol_config,
                    args=args,
                    router=router, rag_engine=rag_engine, memory=memory,
                    validators=validators, max_retries=args.max_retries,
                    results_path_override=protocol_results_path,
                    lang_filter=args.lang_filter,
                )
                if metrics:
                    all_results[result_key] = metrics

                    # save agent_config alongside results
                    model_name = protocol_config["llm_config"]["model_name"]
                    output_dir = build_experiment_dir(
                        dataset, model_name, protocol_results_path,
                    )
                    agent_config_path = output_dir / "agent_config.json"
                    agent_config_with_protocol = dict(agent_config)
                    agent_config_with_protocol["protocol"] = protocol
                    agent_config_path.write_text(
                        json.dumps(agent_config_with_protocol, ensure_ascii=False, indent=2),
                        encoding="utf-8",
                    )
            except Exception as e:
                logger.error("[%s/%s] Failed: %s", protocol_label, dataset, e, exc_info=True)

    # ── summary ───────────────────────────────────────────────────────────
    logger.info("\n%s", "=" * 70)
    logger.info("Summary  [%s]", agent_label)
    logger.info("=" * 70)
    for key, m in all_results.items():
        avg = m.get("avg_metrics", {})
        if not avg and m.get("all_metrics"):
            avg = m["all_metrics"][0]
        acc = avg.get("accuracy", 0)
        total = avg.get("total", 0)
        correct = avg.get("correct", 0)
        failed = avg.get("extraction_failed", 0)
        logger.info(
            "  %-32s  acc=%.4f  correct=%d/%d  extraction_failed=%d",
            key, acc, int(correct), int(total), int(failed),
        )
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
