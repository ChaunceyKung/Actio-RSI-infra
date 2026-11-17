"""Standardized metadata contract for the unified gate.

Each loader's raw metadata is translated to a `StandardMeta` so that
downstream gate rules can reason in dataset-agnostic terms.

Any field may be `None`, indicating the loader did not have enough
information to fill it. Such fields trigger LLM fallback at preprocess
time (not implemented here).
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Literal, Optional

Construct = Literal["belief", "emotion", "intention", "irony", "norm", "mixed"]
FalseBeliefKind = Literal["none", "sally_anne", "deception", "hidden_change"]
AnswerType = Literal["multi_choice", "binary", "open"]
Difficulty = Literal["low", "mid", "high"]


@dataclass
class StandardMeta:
    construct: Optional[Construct] = None
    false_belief_kind: Optional[FalseBeliefKind] = None
    deception: Optional[bool] = None
    dialogue_format: Optional[bool] = None
    answer_type: Optional[AnswerType] = None
    difficulty_hint: Optional[Difficulty] = None

    def to_dict(self) -> dict:
        return asdict(self)

    def filled_fields(self) -> int:
        return sum(1 for v in asdict(self).values() if v is not None)

    def missing_fields(self) -> list[str]:
        return [k for k, v in asdict(self).items() if v is None]
