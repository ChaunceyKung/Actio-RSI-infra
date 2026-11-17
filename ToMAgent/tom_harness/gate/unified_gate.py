"""UnifiedModuleGate — gate that uses (nesting, StandardMeta) instead of
raw task_type. Drop-in replacement for ModuleGate.

Interface compatibility:
    gate.decide(question, story, options, eval_mode, task_type, raw_metadata) → GateDecision

It needs `dataset_name` (set at load time) to dispatch the correct
metadata translator. The runtime/loader plumbs `raw_metadata` from the
sample's metadata dict.
"""

from __future__ import annotations

import logging
import re
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .base import GateDecision, GATE_ALL_ON
from .meta_translators import translate
from .standard_meta import StandardMeta
from .unified_match import UnifiedConfig, load_unified_config, decide as unified_decide

logger = logging.getLogger(__name__)


_MENTAL_EN = re.compile(
    r"\b(?:thinks?|believes?|knows?|expects?|supposes?|imagines?|guesses?|assumes?|wonders?)\b",
    re.IGNORECASE,
)
_MENTAL_ZH = re.compile(r"(?:想|认为|相信|觉得|以为|猜|料|断定|意识到)")


def count_nesting(question: str) -> int:
    """Count mental-state verb occurrences in the question."""
    return len(_MENTAL_EN.findall(question)) + len(_MENTAL_ZH.findall(question))


@dataclass
class UnifiedModuleGate:
    """Drop-in replacement for ModuleGate that consumes unified.yaml.

    Args:
        config: parsed UnifiedConfig (from unified_match.load_unified_config)
        dataset_name: which meta_translator to dispatch (e.g. "hitom")
        mode: "on" | "off"
    """
    config: UnifiedConfig
    dataset_name: str
    mode: str = "on"

    # Stats — same shape as ModuleGate for compatibility
    _stats: dict[str, int] = field(default_factory=lambda: {
        "total": 0,
        "layer1_rule": 0,
        "default": 0,
    }, init=False, repr=False)
    _stats_lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)

    # Per-rule hit counter — exposed for analysis
    _rule_hits: dict[str, int] = field(default_factory=dict, init=False, repr=False)

    # Surface ModuleGate's `.rules` attribute for the loader's log line
    @property
    def rules(self) -> list:
        return self.config.rules

    def decide(
        self,
        *,
        question: str,
        story: str = "",
        options: dict[str, str] | None = None,
        eval_mode: str | None = None,
        task_type: str | None = None,
        raw_metadata: dict | None = None,
    ) -> GateDecision:
        with self._stats_lock:
            self._stats["total"] += 1

        if self.mode == "off":
            return GATE_ALL_ON

        if raw_metadata is None:
            logger.warning(
                "[UnifiedGate] no raw_metadata passed (dataset=%s); falling back to all-on",
                self.dataset_name,
            )
            with self._stats_lock:
                self._stats["default"] += 1
            return GATE_ALL_ON

        std = translate(self.dataset_name, raw_metadata)
        nesting = count_nesting(question)
        u = unified_decide(self.config, nesting=nesting, std=std)

        with self._stats_lock:
            self._stats["layer1_rule"] += 1
            self._rule_hits[u.matched_rule] = self._rule_hits.get(u.matched_rule, 0) + 1

        rationale = f"unified:{u.matched_rule} (nest={nesting},con={std.construct},fb={std.false_belief_kind},dec={std.deception})"
        logger.debug("[UnifiedGate] %s → S=%s R=%s M=%s",
                     rationale, u.use_skill, u.use_rag, u.use_memory)

        return GateDecision(
            use_skill=u.use_skill,
            use_rag=u.use_rag,
            use_memory=u.use_memory,
            rationale=rationale,
            n_llm_calls=0,
        )

    def get_stats(self) -> dict[str, int]:
        with self._stats_lock:
            return dict(self._stats)

    def get_rule_hits(self) -> dict[str, int]:
        with self._stats_lock:
            return dict(self._rule_hits)

    def reset_stats(self) -> None:
        with self._stats_lock:
            self._stats = {"total": 0, "layer1_rule": 0, "default": 0}
            self._rule_hits = {}


def load_unified_gate(config_path: str | Path, dataset_name: str) -> UnifiedModuleGate:
    cfg = load_unified_config(config_path)
    return UnifiedModuleGate(config=cfg, dataset_name=dataset_name, mode=cfg.mode)
