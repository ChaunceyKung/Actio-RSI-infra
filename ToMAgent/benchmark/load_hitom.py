"""Load Hi-ToM dataset into the harness-compatible format.

Hi-ToM is a machine Theory of Mind benchmark featuring higher-order
belief reasoning with object tracking, deception, and variable-length
stories.

Each returned sample is a dict with:
  - id:       str   (e.g. "hitom_0042")
  - story:    str   (the narrative)
  - question: str
  - options:  dict  {"A": "...", "B": "...", ..., "O": "..."}
  - answer:   str   ("A" | "B" | ... | "O")
  - metadata: dict  {"task": "order_<N>", "prompting_type": ..., ...}
"""

from __future__ import annotations

import json
import re
from pathlib import Path

_HITOM_DIR = Path(__file__).resolve().parent / "Hi-ToM"

_OPT_RE = re.compile(r"([A-O])\.\s*")

_VP_STORY_PREFIX = "Read the following story and answer the multiple-choice question. Please provide answer without explanations.\n"


def _normalize_story(story: str, prompting_type: str) -> str:
    """Remove prompting prefix from VP stories to get base story content.

    Args:
        story: The story text from a sample.
        prompting_type: The prompting type ("VP" or "CoTP").

    Returns:
        Normalized story with VP prefix removed if applicable.
    """
    normalized = story
    # Remove VP prefix
    if prompting_type == "VP" and normalized.startswith(_VP_STORY_PREFIX):
        normalized = normalized[len(_VP_STORY_PREFIX):]
    # Remove CoTP trailing delimiter
    if prompting_type == "CoTP" and normalized.endswith("\n***"):
        normalized = normalized[:-4]
    # Strip trailing whitespace for consistent comparison
    normalized = normalized.rstrip()
    return normalized


def _parse_choices(choices_str: str) -> dict[str, str]:
    """Parse "A. foo, B. bar, ..." into {"A": "foo", "B": "bar", ...}."""
    parts = _OPT_RE.split(choices_str)
    options: dict[str, str] = {}
    i = 1
    while i + 1 < len(parts):
        letter = parts[i].strip()
        text = parts[i + 1].strip().rstrip(",").strip()
        options[letter] = text
        i += 2
    return options


def _find_answer_letter(answer_text: str, options: dict[str, str]) -> str:
    """Find which option letter matches the answer text."""
    answer_norm = answer_text.strip().lower()
    for letter, text in options.items():
        if text.strip().lower() == answer_norm:
            return letter
    return ""


def load_hitom(
    data_dir: Path | str | None = None,
    *,
    question_orders: set[int] | None = None,
    deduplicate: bool = True,
    prefer_prompting_type: str = "VP",
) -> list[dict]:
    """Load Hi-ToM dataset and return a flat list of harness-compatible samples.

    Args:
        data_dir: Path to Hi-ToM directory. Defaults to bundled location.
        question_orders: Filter by question_order (0-4). None = all.
        deduplicate: Remove VP/CoTP duplicates, keeping one variant per question.
        prefer_prompting_type: Preferred variant when deduplicating ("VP" or "CoTP").

    Returns:
        List of sample dicts compatible with HarnessRuntime.answer_one().
    """
    root = Path(data_dir) if data_dir else _HITOM_DIR
    data_path = root / "Hi-ToM_data.json"
    if not data_path.exists():
        raise FileNotFoundError(f"Hi-ToM data file not found: {data_path}")

    with open(data_path, encoding="utf-8") as f:
        raw = json.load(f)

    items = raw.get("data", raw) if isinstance(raw, dict) else raw

    samples: list[dict] = []
    for item in items:
        qo = item.get("question_order", -1)
        if question_orders is not None and qo not in question_orders:
            continue

        options = _parse_choices(item.get("choices", ""))
        if not options:
            continue

        answer_letter = _find_answer_letter(item.get("answer", ""), options)
        sample_id = item.get("sample_id", len(samples))

        samples.append({
            "id": f"hitom_{sample_id:04d}",
            "story": item.get("story", ""),
            "question": item.get("question", ""),
            "options": options,
            "answer": answer_letter,
            "metadata": {
                "task": f"order_{qo}",
                "question_order": qo,
                "prompting_type": item.get("prompting_type", ""),
                "deception": item.get("deception", False),
                "story_length": item.get("story_length", 0),
            },
        })

    # Deduplicate VP/CoTP pairs if requested
    if deduplicate:
        from collections import defaultdict

        # Group by (normalized_story, question, question_order)
        groups: dict[tuple[str, str, int], list[dict]] = defaultdict(list)
        for sample in samples:
            normalized = _normalize_story(
                sample["story"],
                sample["metadata"].get("prompting_type", "")
            )
            key = (normalized, sample["question"], sample["metadata"]["question_order"])
            groups[key].append(sample)

        # Select one sample per group, preferring the specified prompting type
        deduplicated: list[dict] = []
        for group_samples in groups.values():
            # Try to find preferred type
            preferred = next(
                (s for s in group_samples if s["metadata"].get("prompting_type") == prefer_prompting_type),
                None
            )
            # Fall back to any sample if preferred not found
            selected = preferred if preferred else group_samples[0]
            deduplicated.append(selected)

        samples = deduplicated

    return samples
