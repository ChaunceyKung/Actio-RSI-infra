"""Load EmoBench dataset into the harness-compatible format.

EmoBench evaluates emotional intelligence through two tasks:
  - EU (Emotional Understanding): 400 samples (200 en, 200 zh)
    - Dual-question format: emotion identification + cause identification
    - Strict scoring: both answers must be correct
  - EA (Emotional Application): 400 samples (200 en, 200 zh)
    - Single multiple-choice format

Each returned sample is a dict with:
  - id:       str   (e.g. "EU_en_001")
  - story:    str   (the scenario)
  - question: str
  - options:  dict  {"A": "...", "B": "...", ...}
  - answer:   str   ("A" for EA, "A|H" for EU with emotion|cause)
  - metadata: dict  {"task": "EU"|"EA", "category": ..., ...}
"""

from __future__ import annotations

import json
import string
from pathlib import Path

_EMOBENCH_DIR = Path(__file__).resolve().parent / "EmoBench" / "data"


def load_emobench(
    data_dir: Path | str | None = None,
    *,
    tasks: set[str] | None = None,
    languages: set[str] | None = None,
    categories: set[str] | None = None,
) -> list[dict]:
    """Load EmoBench dataset and return harness-compatible samples.

    Args:
        data_dir: Path to EmoBench data directory (default: benchmark/EmoBench/data/)
        tasks: Set of tasks to load {"EU", "EA"} (None = both)
        languages: Set of languages {"en", "zh"} (None = both)
        categories: Set of categories to filter by (None = all)

    Returns:
        List of sample dicts compatible with HarnessRuntime.answer_one()
    """
    if data_dir is None:
        data_dir = _EMOBENCH_DIR
    else:
        data_dir = Path(data_dir)

    # Default to loading all tasks
    if tasks is None:
        tasks = {"EU", "EA"}
    else:
        tasks = {t.upper() for t in tasks}

    # Default to loading all languages
    if languages is None:
        languages = {"en", "zh"}
    else:
        languages = {lang.lower() for lang in languages}

    samples = []

    # Load EU (Emotional Understanding) samples
    if "EU" in tasks:
        eu_file = data_dir / "EU.jsonl"
        if eu_file.exists():
            with open(eu_file, "r", encoding="utf-8") as f:
                for line in f:
                    raw = json.loads(line.strip())
                    if raw["language"] not in languages:
                        continue

                    category = raw["coarse_category"]
                    if categories is not None and category not in categories:
                        continue

                    sample = _build_eu_sample(raw)
                    samples.append(sample)

    # Load EA (Emotional Application) samples
    if "EA" in tasks:
        ea_file = data_dir / "EA.jsonl"
        if ea_file.exists():
            with open(ea_file, "r", encoding="utf-8") as f:
                for line in f:
                    raw = json.loads(line.strip())
                    if raw["language"] not in languages:
                        continue

                    category = raw["category"]
                    if categories is not None and category not in categories:
                        continue

                    sample = _build_ea_sample(raw)
                    samples.append(sample)

    return samples


def _build_eu_sample(raw: dict) -> dict:
    """Build an EU (Emotional Understanding) sample with dual-question format.

    EU uses standard options dict with emotion choices (A-F) and cause choices (G-J).
    The question instructs the model to provide two answers in "X,Y" format.
    Runtime now supports this multi-answer format in JSON parsing.
    """
    qid = raw["qid"]
    lang = raw["language"]
    scenario = raw["scenario"]
    subject = raw["subject"]

    emotion_choices = raw["emotion_choices"]
    cause_choices = raw["cause_choices"]
    emotion_label = raw["emotion_label"]
    cause_label = raw["cause_label"]

    letters = string.ascii_uppercase

    # Build standard options dict: A-F for emotions, G-J for causes
    options = {}
    emotion_letter = ""
    for i, choice in enumerate(emotion_choices):
        letter = letters[i]
        options[letter] = choice
        if choice == emotion_label:
            emotion_letter = letter

    cause_letter = ""
    offset = len(emotion_choices)
    for i, choice in enumerate(cause_choices):
        letter = letters[offset + i]
        options[letter] = choice
        if choice == cause_label:
            cause_letter = letter

    # Question instructs model to provide dual answer
    question = (
        f"This question has TWO parts:\n\n"
        f"Question 1: What emotion is {subject} feeling?\n"
        f"Question 2: What caused this emotion?\n\n"
        f"Answer BOTH questions. First give a brief reason (2-3 sentences), "
        f'then output a JSON object: {{"answer": "X,Y"}} where X is the emotion letter '
        f"and Y is the cause letter (e.g., A,G)."
    )

    # Answer format: "emotion_letter|cause_letter" for ground truth storage
    # But model will output "emotion_letter,cause_letter" in JSON
    answer = f"{emotion_letter}|{cause_letter}"

    sample_id = f"EU_{lang}_{qid.zfill(3)}"

    return {
        "id": sample_id,
        "story": scenario,
        "question": question,
        "options": options,
        "answer": answer,
        "metadata": {
            "task": "EU",
            "category": raw["coarse_category"],
            "finegrained_category": raw["finegrained_category"],
            "lang": lang,
            "qid": qid,
            "emotion_answer": emotion_letter,
            "cause_answer": cause_letter,
            "num_emotion_options": len(emotion_choices),
            "num_cause_options": len(cause_choices),
        },
    }


def _build_ea_sample(raw: dict) -> dict:
    """Build an EA (Emotional Application) sample with standard MCQ format."""
    qid = raw["qid"]
    lang = raw["language"]
    scenario = raw["scenario"]
    subject = raw["subject"]

    choices = raw["choices"]
    label = raw["label"]

    # Build options dict: A-D
    options = {}
    letters = string.ascii_uppercase
    answer_letter = ""

    for i, choice in enumerate(choices):
        letter = letters[i]
        options[letter] = choice
        if choice == label:
            answer_letter = letter

    # Question is implicit from the scenario and subject
    question = f"What should {subject} do?"

    sample_id = f"EA_{lang}_{qid.zfill(3)}"

    return {
        "id": sample_id,
        "story": scenario,
        "question": question,
        "options": options,
        "answer": answer_letter,
        "metadata": {
            "task": "EA",
            "category": raw["category"],
            "question_type": raw["question type"],
            "lang": lang,
            "qid": qid,
        },
    }
