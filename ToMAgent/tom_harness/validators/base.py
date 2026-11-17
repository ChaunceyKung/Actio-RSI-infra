"""Validator ABC."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ValidationResult:
    valid: bool
    feedback: str = ""                          # what to feed back to LLM if !valid
    suggested_answer: str | None = None         # if validator can substitute directly
    rationale: str = ""                         # short reason (for trace/debug)


class Validator(ABC):
    """A post-LLM validator. Cheap (no LLM by default) and task-scoped."""

    # Subclasses set this. Empty set = applies to every task.
    def applies(self, *, eval_mode: str | None = None) -> bool:
        return True

    @abstractmethod
    def validate(
        self,
        *,
        question: str,
        story: str,
        options: dict[str, str],
        current_answer: str,
        reasoning: str = "",
        eval_mode: str | None = None,
    ) -> ValidationResult: ...
