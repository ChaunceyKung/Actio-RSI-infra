"""Load ICTBench dataset into the harness-compatible format.

ICTBench (Implicit Cognitive Tracking Benchmark) tests Theory of Mind
capabilities: belief attribution, belief source tracking, implicit belief
extraction, and belief graph construction.

Supports four evaluation modes per exercise:
  - Q1 (mcq): single-choice belief attribution → standard A/B/C/D
  - Q2 (multi_select): multi-choice belief source tracing → set match
  - Q3 (verdict): 3 judgment items (是/否/无法确定) → split into 3 MCQ samples
  - Q4 (open_analysis): free-form belief graph → LLM-as-judge scoring

Each returned sample is a dict with:
  - id:       str   (e.g. "1.1.1_0_first_person_Q1")
  - story:    str   (the narrative scenario)
  - question: str
  - options:  dict  {"A": "...", ...}   (for mcq/verdict)
  - answer:   str   ("A"|"B"|"C"|"D" for mcq, "CDE" for multi_select, etc.)
  - answer_list: list[str]             (for multi_select, ground truth letters)
  - answer_points: list[str]           (for open_analysis, reference key points)
  - metadata: dict  {"task": ..., "eval_mode": "mcq"|"multi_select"|"verdict"|"open_analysis", ...}

Perspective pairs:
  Each scenario has a first_person (limited narrator) and third_person
  (omniscient) version, forming a pair that tests the same ToM reasoning
  from different narrative perspectives.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

_ICTBENCH_PATH = Path(__file__).resolve().parent / "ICTBench" / "dataset_v4.2.json"

# Map task_id prefix to cognitive dimension category
_DIMENSION_MAP = {
    "1.1": "cognitive_state_modeling",
    "1.2": "belief_source_tracking",
    "1.3": "implicit_belief_extraction",
    "1.4": "belief_update_tracking",
    "1.5": "epistemic_state_modeling",
    "1.6": "perspective_taking",
    "1.7": "knowledge_asymmetry",
    "2.1": "intention_recognition",
    "2.2": "goal_inference",
    "2.3": "plan_recognition",
    "2.4": "motive_attribution",
    "2.5": "strategic_reasoning",
    "2.6": "deception_detection",
    "3.1": "emotion_attribution",
    "3.2": "empathy_modeling",
    "3.3": "social_norm_reasoning",
    "3.4": "relationship_dynamics",
}


def _get_dimension(task_id: str) -> str:
    """Map task_id (e.g. '1.1.1') to cognitive dimension."""
    prefix = ".".join(task_id.split(".")[:2])
    return _DIMENSION_MAP.get(prefix, "unknown")


def _build_q1_sample(
    *,
    base_id: str,
    story: str,
    question_data: dict,
    metadata_base: dict,
) -> dict:
    """Build a standard MCQ sample from Q1 (single-choice)."""
    options = {}
    for label in "ABCD":
        if label in question_data:
            options[label] = question_data[label]

    answer = question_data.get("答案", "")

    return {
        "id": f"{base_id}_Q1",
        "story": story,
        "question": question_data.get("问题", ""),
        "options": options,
        "answer": answer,
        "metadata": {
            **metadata_base,
            "question_type": "Q1",
            "eval_mode": "mcq",
            "subprocess": question_data.get("考察子过程", ""),
        },
    }


def _build_q2_sample(
    *,
    base_id: str,
    story: str,
    question_data: dict,
    metadata_base: dict,
) -> dict:
    """Build a multi-select sample from Q2 (belief source tracing)."""
    options = {}
    for label in "ABCDE":
        if label in question_data:
            options[label] = question_data[label]

    answer_str = question_data.get("答案", "")
    answer_list = list(answer_str)

    return {
        "id": f"{base_id}_Q2",
        "story": story,
        "question": question_data.get("问题", ""),
        "options": options,
        "answer": answer_str,
        "answer_list": answer_list,
        "metadata": {
            **metadata_base,
            "question_type": "Q2",
            "eval_mode": "multi_select",
            "subprocess": question_data.get("考察子过程", ""),
        },
    }


def _build_q3_samples(
    *,
    base_id: str,
    story: str,
    question_data: dict,
    metadata_base: dict,
) -> list[dict]:
    """Build 3 independent verdict MCQ samples from Q3 items."""
    items = question_data.get("Q3_items", [])
    samples = []

    verdict_to_label = {"是": "A", "否": "B", "无法确定": "C"}
    verdict_options = {"A": "是", "B": "否", "C": "无法确定"}

    for idx, item in enumerate(items):
        statement = item.get("statement", "")
        verdict = item.get("verdict", "")
        answer_label = verdict_to_label.get(verdict, "")

        question = (
            f"请判断以下陈述是否成立：\n\n"
            f"「{statement}」\n\n"
            f"根据情境中的信息，该陈述："
        )

        samples.append({
            "id": f"{base_id}_Q3_{idx}",
            "story": story,
            "question": question,
            "options": dict(verdict_options),
            "answer": answer_label,
            "metadata": {
                **metadata_base,
                "question_type": "Q3",
                "eval_mode": "verdict",
                "subprocess": question_data.get("考察子过程", ""),
                "q3_item_idx": idx,
                "verdict_gt": verdict,
            },
        })

    return samples


def _build_q4_sample(
    *,
    base_id: str,
    story: str,
    question_data: dict,
    answer_key_q4: list[str],
    metadata_base: dict,
) -> dict:
    """Build an open analysis sample from Q4 (belief graph construction)."""
    return {
        "id": f"{base_id}_Q4",
        "story": story,
        "question": question_data.get("问题", ""),
        "options": {},
        "answer": "",
        "answer_points": answer_key_q4,
        "metadata": {
            **metadata_base,
            "question_type": "Q4",
            "eval_mode": "open_analysis",
            "subprocess": question_data.get("考察子过程", ""),
        },
    }


def _apply_perturbation(
    story: str,
    perturbation: dict,
) -> str:
    """Apply a perturbation variant to the story text, returning modified story."""
    # v4.2+ ships the full perturbed text directly; prefer it when present
    # since modification_detail.original_text often uses [Sn] sentence-tag
    # anchors that don't appear in the actual 情境.
    full = perturbation.get("_variant_full_text")
    if full:
        return full

    detail = perturbation.get("modification_detail", {})
    original_text = detail.get("original_text", "")
    modified_text = detail.get("modified_text", "")

    if not original_text or not modified_text:
        return story

    new_story = story.replace(original_text, modified_text)

    for edit in detail.get("cascading_edits", []):
        orig = edit.get("original", "")
        revised = edit.get("revised", "")
        if orig and revised:
            new_story = new_story.replace(orig, revised)

    return new_story


def _normalize_question_number(qn: Any) -> str:
    """Normalize diverse question_number formats to canonical form."""
    s = str(qn)
    if s in ("1", "Q1"):
        return "Q1"
    if s in ("2", "Q2"):
        return "Q2"
    if s in ("4", "Q4"):
        return "Q4"
    # Q3 variants: "Q3_item1", "Q3-item1", "Q3-1", "Q3_item2", etc.
    m = re.match(r"Q?3[-_]?(?:item)?(\d+)", s)
    if m:
        return f"Q3_{int(m.group(1)) - 1}"  # 0-indexed
    return s


def _get_perturbed_answers(perturbation: dict, original_answer_key: dict) -> dict:
    """Compute the answer key after perturbation, merging changes onto original."""
    new_key = dict(original_answer_key)
    new_key["Q3"] = list(original_answer_key.get("Q3", []))

    for ac in perturbation.get("answer_changes", []):
        qn = _normalize_question_number(ac["question_number"])
        new_answer = ac.get("new_answer", "")

        if qn == "Q1":
            new_key["Q1"] = new_answer
        elif qn == "Q2":
            new_key["Q2"] = new_answer
        elif qn == "Q4":
            pass  # Q4 open analysis — perturbation rarely changes rubric
        elif qn.startswith("Q3_"):
            idx = int(qn.split("_")[1])
            if idx < len(new_key["Q3"]):
                new_key["Q3"][idx] = {
                    **new_key["Q3"][idx],
                    "verdict": new_answer,
                }

    return new_key


def _extract_samples_from_entry(entry: dict, *, include_perturbations: bool = False) -> list[dict]:
    """Extract all harness samples from a single ICTBench dataset entry."""
    base_id = entry["id"]
    story = entry["exercise"].get("情境", "")
    answer_key = entry.get("answer_key", {})

    metadata_base = {
        "task": entry.get("task_id", ""),
        "category": _get_dimension(entry.get("task_id", "")),
        "perspective": entry.get("perspective", ""),
        "pair_id": entry.get("pair_id", ""),
        "domain": entry.get("domain", ""),
        "length_mode": entry.get("length_mode", ""),
        "sample_idx": entry.get("sample_idx", 0),
    }

    questions = entry["exercise"].get("题目", [])
    samples: list[dict] = []

    for q in questions:
        qnum = str(q.get("题号", ""))
        if qnum in ("1", "2", "3", "4"):
            qnum = f"Q{qnum}"
        if qnum == "Q1":
            samples.append(_build_q1_sample(
                base_id=base_id, story=story, question_data=q,
                metadata_base=metadata_base,
            ))
        elif qnum == "Q2":
            samples.append(_build_q2_sample(
                base_id=base_id, story=story, question_data=q,
                metadata_base=metadata_base,
            ))
        elif qnum == "Q3":
            samples.extend(_build_q3_samples(
                base_id=base_id, story=story, question_data=q,
                metadata_base=metadata_base,
            ))
        elif qnum == "Q4":
            q4_points = answer_key.get("Q4", [])
            samples.append(_build_q4_sample(
                base_id=base_id, story=story, question_data=q,
                answer_key_q4=q4_points, metadata_base=metadata_base,
            ))

    # ── Perturbation variants ──────────────────────────────────────────────
    if include_perturbations:
        perturbations = entry["exercise"].get("perturbations", [])
        for perturb in perturbations:
            variant_id = perturb.get("variant_id", "")
            perturbed_story = _apply_perturbation(story, perturb)

            if perturbed_story == story:
                continue

            perturbed_answer_key = _get_perturbed_answers(perturb, answer_key)
            perturb_meta = {
                **metadata_base,
                "is_perturbation": True,
                "perturb_variant": variant_id,
                "perturb_dimension": perturb.get("perturb_dimension", ""),
            }
            perturb_base_id = f"{base_id}_perturb_{variant_id}"

            for q in questions:
                qnum = str(q.get("题号", ""))
                if qnum in ("1", "2", "3", "4"):
                    qnum = f"Q{qnum}"
                if qnum == "Q1":
                    s = _build_q1_sample(
                        base_id=perturb_base_id, story=perturbed_story,
                        question_data=q, metadata_base=perturb_meta,
                    )
                    s["answer"] = perturbed_answer_key.get("Q1", s["answer"])
                    samples.append(s)
                elif qnum == "Q2":
                    s = _build_q2_sample(
                        base_id=perturb_base_id, story=perturbed_story,
                        question_data=q, metadata_base=perturb_meta,
                    )
                    new_q2 = perturbed_answer_key.get("Q2", s["answer"])
                    s["answer"] = new_q2
                    s["answer_list"] = list(new_q2)
                    samples.append(s)
                elif qnum == "Q3":
                    q3_samples = _build_q3_samples(
                        base_id=perturb_base_id, story=perturbed_story,
                        question_data=q, metadata_base=perturb_meta,
                    )
                    perturbed_q3 = perturbed_answer_key.get("Q3", [])
                    verdict_to_label = {"是": "A", "否": "B", "无法确定": "C"}
                    for idx, qs in enumerate(q3_samples):
                        if idx < len(perturbed_q3):
                            new_verdict = perturbed_q3[idx].get("verdict", "")
                            if new_verdict:
                                qs["answer"] = verdict_to_label.get(new_verdict, qs["answer"])
                                qs["metadata"]["verdict_gt"] = new_verdict
                    samples.extend(q3_samples)
                elif qnum == "Q4":
                    q4_points = perturbed_answer_key.get("Q4", answer_key.get("Q4", []))
                    s = _build_q4_sample(
                        base_id=perturb_base_id, story=perturbed_story,
                        question_data=q, answer_key_q4=q4_points,
                        metadata_base=perturb_meta,
                    )
                    samples.append(s)

    return samples


def load_ictbench(
    data_path: str | Path | None = None,
    *,
    perspectives: set[str] | None = None,
    task_ids: set[str] | None = None,
    question_types: set[str] | None = None,
    domains: set[str] | None = None,
    length_modes: set[str] | None = None,
    include_perturbations: bool = False,
) -> list[dict]:
    """Load ICTBench dataset and return a flat list of harness-compatible samples.

    Args:
        data_path: Path to dataset_v4.2.json. Defaults to bundled location.
        perspectives: Filter by {"first_person", "third_person"}. None = all.
        task_ids: Filter by task_id (e.g. {"1.1.1", "2.3.1"}). None = all.
        question_types: Filter by {"Q1", "Q2", "Q3", "Q4"}. None = all.
        domains: Filter by domain name. None = all.
        length_modes: Filter by {"short", "long"}. None = all.
        include_perturbations: If True, also generate perturbation variant samples.

    Returns:
        List of sample dicts compatible with HarnessRuntime.answer_one().
    """
    path = Path(data_path) if data_path else _ICTBENCH_PATH
    if not path.exists():
        raise FileNotFoundError(f"ICTBench data file not found: {path}")

    with open(path, encoding="utf-8") as f:
        dataset = json.load(f)

    entries = dataset.get("samples", [])
    all_samples: list[dict] = []

    for entry in entries:
        # Pre-filter at entry level for efficiency
        if perspectives and entry.get("perspective") not in perspectives:
            continue
        if task_ids and entry.get("task_id") not in task_ids:
            continue
        if domains and entry.get("domain") not in domains:
            continue
        if length_modes and entry.get("length_mode") not in length_modes:
            continue

        samples = _extract_samples_from_entry(entry, include_perturbations=include_perturbations)
        all_samples.extend(samples)

    # Post-filter by question_type
    if question_types:
        all_samples = [
            s for s in all_samples
            if s["metadata"].get("question_type") in question_types
        ]

    return all_samples
