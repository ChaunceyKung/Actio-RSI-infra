"""Load Social-IQA validation set into harness-compatible format.

  Each returned sample is a dict with:
    - id:       str   (e.g. "social_iqa_0001")
    - story:    str   (context)
    - question: str   (question text)
    - options:  dict  {"A": "...", "B": "...", "C": "..."}
    - answer:   str   ("A" | "B" | "C")
    - metadata: dict  {"task": "Social-IQA", "category": "wants"|"reactions"|..., "index": int}
  """

from __future__ import annotations

import csv
import re
from pathlib import Path

_SOCIAL_IQA_DIR = Path(__file__).resolve().parent / "social-IQA"

# Category classification patterns (order matters - match from top to bottom)
_CATEGORY_PATTERNS = [
    (r"what\s+will\s+\w+\s+want\s+to\s+do", "wants"),
    (r"what\s+does\s+\w+\s+want\s+to\s+do", "wants"),
    (r"what\s+will\s+\w+\s+want", "wants"),
    (r"how\s+would\s+\w+\s+feel", "reactions"),
    (r"how\s+will\s+\w+\s+feel", "reactions"),
    (r"how\s+did\s+\w+\s+feel", "reactions"),
    (r"how\s+does\s+\w+\s+feel", "reactions"),
    (r"how\s+would\s+you\s+describe", "descriptions"),
    (r"what\s+would\s+\w+\s+think\s+of", "descriptions"),
    (r"why\s+did\s+\w+", "motivations"),
    (r"what\s+does\s+\w+\s+need\s+to\s+do", "needs"),
    (r"what\s+will\s+happen\s+to", "effects"),
    (r"what\s+would\s+happen\s+to", "effects"),
    (r"where\s+will\s+\w+", "effects"),
]

def _classify_question(question: str) -> str:
    """Classify question into one of 7 categories using regex patterns."""
    q_lower = question.lower().strip()
    for pattern, category in _CATEGORY_PATTERNS:
        if re.search(pattern, q_lower):
            return category
    return "other"


def load_social_iqa(
    data_dir: Path | str | None = None,
    *,
    categories: set[str] | None = None,
) -> list[dict]:
    """Load Social-IQA validation set.
    
    Args:
        data_dir: Path to social-IQA/ directory (default: bundled location)
        categories: Filter by category (wants, reactions, etc.). None = all.
    
    Returns:
        List of harness-compatible sample dicts.
    """
    root = Path(data_dir) if data_dir else _SOCIAL_IQA_DIR
    csv_path = root / "validation.csv"

    if not csv_path.exists():
        raise FileNotFoundError(f"Social-IQA validation.csv not found: {csv_path}")

    samples: list[dict] = []

    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader, 1):
            context = row.get("context", "").strip()
            question = row.get("question", "").strip()
            answer_a = row.get("answerA", "").strip()
            answer_b = row.get("answerB", "").strip()
            answer_c = row.get("answerC", "").strip()
            label_str = row.get("label", "").strip()

            # Convert label (1/2/3) to answer letter (A/B/C)
            label_map = {"1": "A", "2": "B", "3": "C"}
            answer = label_map.get(label_str, "")

            # Classify question into category
            category = _classify_question(question)

            # Filter by category if specified
            if categories is not None and category not in categories:
                continue

            sample = {
                "id": f"social_iqa_{idx:04d}",
                "story": context,
                "question": question,
                "options": {
                    "A": answer_a,
                    "B": answer_b,
                    "C": answer_c,
                },
                "answer": answer,
                "metadata": {
                    "task": "Social-IQA",
                    "category": category,
                    "index": idx,
                },
            }
            samples.append(sample)

    return samples
