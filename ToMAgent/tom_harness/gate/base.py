"""ModuleGate — two-layer gate that decides which modules to activate per sample.

Architecture:
  Layer 1 (Rule Engine): Configurable rules that match on task_type prefix,
    question patterns, or eval_mode. Zero LLM cost. Covers most samples when
    task_type metadata is available.

  Layer 2 (LLM Classifier): For samples that don't match any rule, a single
    LLM call classifies the "reasoning demand" into one of several categories,
    which maps to a module activation decision. This layer is dataset-agnostic.

The gate sits between the Router and module injection in HarnessRuntime:
  Router (which skill?) → Gate (which modules?) → Module injection → LLM Solve
"""

from __future__ import annotations

import json
import logging
import re
import threading
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GateDecision:
    """Output of the gate: which modules to activate."""
    use_skill: bool = True
    use_rag: bool = True
    use_memory: bool = True
    rationale: str = ""
    n_llm_calls: int = 0

    def any_active(self) -> bool:
        return self.use_skill or self.use_rag or self.use_memory


# Default: all modules on (backward compatible)
GATE_ALL_ON = GateDecision(use_skill=True, use_rag=True, use_memory=True, rationale="default: all on")
GATE_ALL_OFF = GateDecision(use_skill=False, use_rag=False, use_memory=False, rationale="gate: no modules")


# Dataset-specific prefixes to strip for normalized matching
_TASK_TYPE_PREFIXES = ("tom:", "cogtom:", "ict:")

def _normalize_task_type(task_type: str) -> str:
    """Strip common dataset prefixes for uniform rule matching."""
    for prefix in _TASK_TYPE_PREFIXES:
        if task_type.startswith(prefix):
            return task_type[len(prefix):]
    return task_type


@dataclass
class GateRule:
    """A single rule in the Layer 1 rule engine.

    Match conditions (all specified conditions must match):
      - task_type_prefix: matches if task_type starts with this string
      - task_type_exact: matches if task_type equals this string exactly
      - eval_mode: matches if eval_mode equals this string
      - question_pattern: regex pattern to match against question text

    Gate output when matched:
      - gate: dict with {skill: bool, rag: bool, memory: bool}
    """
    gate: dict  # {"skill": bool, "rag": bool, "memory": bool}
    task_type_prefix: str | None = None
    task_type_exact: str | None = None
    eval_mode: str | None = None
    question_pattern: str | None = None
    name: str = ""

    _compiled_pattern: re.Pattern | None = field(default=None, init=False, repr=False)

    def __post_init__(self):
        if self.question_pattern:
            self._compiled_pattern = re.compile(self.question_pattern, re.IGNORECASE)

    def matches(
        self,
        *,
        question: str = "",
        task_type: str | None = None,
        eval_mode: str | None = None,
    ) -> bool:
        """Return True if all specified conditions match.

        task_type matching is prefix-normalized: common dataset prefixes like
        "tom:" are stripped before comparison so rules don't need to enumerate
        both "belief:accessible" and "tom:belief:accessible".
        """
        normalized = _normalize_task_type(task_type) if task_type else None

        if self.task_type_exact is not None:
            if normalized != self.task_type_exact:
                return False

        if self.task_type_prefix is not None:
            if not normalized or not normalized.startswith(self.task_type_prefix):
                return False

        if self.eval_mode is not None:
            if eval_mode != self.eval_mode:
                return False

        if self._compiled_pattern is not None:
            if not self._compiled_pattern.search(question):
                return False

        return True

    def to_decision(self) -> GateDecision:
        return GateDecision(
            use_skill=self.gate.get("skill", True),
            use_rag=self.gate.get("rag", True),
            use_memory=self.gate.get("memory", True),
            rationale=f"rule:{self.name}" if self.name else "rule:matched",
        )


# ── Reasoning demand types ──────────────────────────────────────────────────
# 20 task-type categories for fine-grained classification
# Optimized prompt based on confusion matrix analysis

DEMAND_TYPES = [
    # NO_MODULES (4 types) - High baseline, modules hurt
    "AMBIGUOUS_STORY",
    "DISCREPANT_INTENTIONS",
    "EMOTION_REGULATION",
    "MORAL_EMOTIONS",

    # MEMORY_ONLY (8 types) - Social pragmatics and simple belief tracking
    "FALSE_BELIEF",
    "FAUX_PAS",
    "DISCREPANT_EMOTIONS",
    "HINTING",
    "KNOWLEDGE_ATTENTION",
    "PERSUASION",
    "STRANGE_STORY",
    "UNEXPECTED_OUTCOME",

    # SKILL_ONLY (1 type) - Information flow tracking
    "PERCEPTS_KNOWLEDGE",

    # RAG_ONLY (2 types) - Requires commonsense knowledge
    "FAILED_ACTIONS",
    "DISCREPANT_DESIRES",

    # ALL_MODULES (5 types) - Complex reasoning, true complementarity
    "HIDDEN_EMOTIONS",
    "KNOWLEDGE_PRETEND",
    "MULTIPLE_DESIRES",
    "PREDICTION_ACTIONS",
    "SCALAR_IMPLICATURE",
]

# Default mapping from demand type to module activation.
DEFAULT_DEMAND_TO_GATE: dict[str, dict[str, bool]] = {
    # NO_MODULES - High baseline, modules hurt
    "AMBIGUOUS_STORY":       {"skill": False, "rag": False, "memory": False},
    "DISCREPANT_INTENTIONS": {"skill": False, "rag": False, "memory": False},
    "EMOTION_REGULATION":    {"skill": False, "rag": False, "memory": False},
    "MORAL_EMOTIONS":        {"skill": False, "rag": False, "memory": False},

    # MEMORY_ONLY - Social pragmatics and simple belief tracking
    "FALSE_BELIEF":          {"skill": False, "rag": False, "memory": True},
    "FAUX_PAS":              {"skill": False, "rag": False, "memory": True},
    "DISCREPANT_EMOTIONS":   {"skill": False, "rag": False, "memory": True},
    "HINTING":               {"skill": False, "rag": False, "memory": True},
    "KNOWLEDGE_ATTENTION":   {"skill": False, "rag": False, "memory": True},
    "PERSUASION":            {"skill": False, "rag": False, "memory": True},
    "STRANGE_STORY":         {"skill": False, "rag": False, "memory": True},
    "UNEXPECTED_OUTCOME":    {"skill": False, "rag": False, "memory": True},

    # SKILL_ONLY - Information flow tracking
    "PERCEPTS_KNOWLEDGE":    {"skill": True,  "rag": False, "memory": False},

    # RAG_ONLY - Requires commonsense knowledge
    "FAILED_ACTIONS":        {"skill": False, "rag": True,  "memory": False},
    "DISCREPANT_DESIRES":    {"skill": False, "rag": True,  "memory": False},

    # ALL_MODULES - Complex reasoning, true complementarity
    "HIDDEN_EMOTIONS":       {"skill": True,  "rag": True,  "memory": True},
    "KNOWLEDGE_PRETEND":     {"skill": True,  "rag": True,  "memory": True},
    "MULTIPLE_DESIRES":      {"skill": True,  "rag": True,  "memory": True},
    "PREDICTION_ACTIONS":    {"skill": True,  "rag": True,  "memory": True},
    "SCALAR_IMPLICATURE":    {"skill": True,  "rag": True,  "memory": True},
}


_CLASSIFY_SYSTEM = (
    "You are a Theory of Mind question classifier. Given a story excerpt and a question, "
    "classify into ONE of 20 categories. Focus on the PRIMARY reasoning type required.\n\n"
    "## Group 1: NO assistance needed (high baseline)\n"
    "- AMBIGUOUS_STORY: Social situations with ambiguous meaning. Often asks 'why' someone did something when multiple interpretations exist.\n"
    "- DISCREPANT_INTENTIONS: Understanding hidden intentions or motivations behind behavior.\n"
    "- EMOTION_REGULATION: How someone controls or manages their emotional reactions.\n"
    "- MORAL_EMOTIONS: Emotions tied to moral judgments (guilt, shame, pride, regret).\n\n"
    "## Group 2: Belief state tracking & social pragmatics\n"
    "- FALSE_BELIEF: What someone thinks/believes about object locations. Key: 'where will X look', 'think', 'believe' + location.\n"
    "  ⚠️ NOT PERCEPTS_KNOWLEDGE (which asks what X knows from perception)\n"
    "- FAUX_PAS: Socially awkward or inappropriate statements. Key: 'inappropriate', 'awkward', 'shouldn't have said'.\n"
    "  ⚠️ NOT KNOWLEDGE_ATTENTION (no mention of seeing/attending)\n"
    "  ⚠️ NOT PERCEPTS_KNOWLEDGE (not about perception-to-knowledge)\n"
    "- DISCREPANT_EMOTIONS: Difference between felt emotion vs displayed emotion (when visible to observer).\n"
    "  ⚠️ NOT UNEXPECTED_OUTCOME (no unexpected event causing emotion)\n"
    "- HINTING: Indirect communication, implied meaning, reading between the lines.\n"
    "  ⚠️ NOT STRANGE_STORY if not about lies/sarcasm\n"
    "- KNOWLEDGE_ATTENTION: Links between what someone attends to and what they know.\n"
    "- PERSUASION: How someone convinces or influences another person. Key: 'persuade', 'convince'.\n"
    "- STRANGE_STORY: Non-literal speech - lies, jokes, sarcasm, white lies, irony. Key: 'is it true', 'why say this'.\n"
    "  ⚠️ NOT AMBIGUOUS_STORY (more about deception/sarcasm than ambiguity)\n"
    "  ⚠️ NOT DISCREPANT_INTENTIONS (focus on speech acts, not general intentions)\n"
    "- UNEXPECTED_OUTCOME: Emotional reactions to surprising/unexpected events. Key: 'unexpected', 'surprising', emotion after event.\n"
    "  ⚠️ NOT DISCREPANT_EMOTIONS (emotion is reaction to event, not discrepancy)\n"
    "  ⚠️ NOT AMBIGUOUS_STORY (event is unexpected, not ambiguous)\n\n"
    "## Group 3: Perception & information flow\n"
    "- PERCEPTS_KNOWLEDGE: What someone knows based on what they SAW/HEARD. Key: 'what does X see', 'based on what X saw'.\n"
    "  ⚠️ NOT FALSE_BELIEF (not about beliefs, about direct perception)\n\n"
    "## Group 4: Commonsense & action prediction\n"
    "- FAILED_ACTIONS: Completing or predicting actions after a failed attempt.\n"
    "- DISCREPANT_DESIRES: Conflicting wants or preferences between characters.\n\n"
    "## Group 5: Complex multi-faceted reasoning\n"
    "- HIDDEN_EMOTIONS: Real vs hidden/displayed emotion (internal state). Key: 'really feel', 'actually feel', 'true emotion'.\n"
    "  ⚠️ NOT DISCREPANT_EMOTIONS (more about internal hiding than observable discrepancy)\n"
    "- KNOWLEDGE_PRETEND: Understanding pretend play, what someone is imitating.\n"
    "- MULTIPLE_DESIRES: Multiple conflicting desires WITHIN one character.\n"
    "- PREDICTION_ACTIONS: Predicting what someone will do based on their complex mental states.\n"
    "- SCALAR_IMPLICATURE: Quantity reasoning. Key: 'some', 'all', 'most', 'few', 'how many'.\n\n"
    "Decision rules:\n"
    "1. If question asks about 'inappropriate' → FAUX_PAS (not KNOWLEDGE_ATTENTION)\n"
    "2. If about 'where will X look/find' → FALSE_BELIEF (not PERCEPTS_KNOWLEDGE)\n"
    "3. If about emotion after unexpected event → UNEXPECTED_OUTCOME (not DISCREPANT_EMOTIONS)\n"
    "4. If about lies/sarcasm → STRANGE_STORY (not AMBIGUOUS_STORY)\n"
    "5. If about 'really feel' → HIDDEN_EMOTIONS (not DISCREPANT_EMOTIONS)\n\n"
    'Output ONLY a JSON object: {"demand": "<one of the 20 categories above>"}'
)


@dataclass
class ModuleGate:
    """Two-layer gate: rules (zero cost) + LLM classifier (fallback).

    Args:
        rules: Ordered list of GateRule. First match wins.
        llm: LLMClient for Layer 2 classification. If None, Layer 2 is skipped
             and the default (all-on) is used for unmatched samples.
        demand_to_gate: Mapping from demand type to module activation.
        default_decision: What to return when nothing matches and no LLM.
        mode: "on" (gate active), "off" (always all-on), "rules_only" (skip LLM).
        story_prefix_len: How many chars of story to send to the LLM classifier.
    """
    rules: list[GateRule] = field(default_factory=list)
    llm: Any = None
    demand_to_gate: dict[str, dict[str, bool]] = field(default_factory=lambda: dict(DEFAULT_DEMAND_TO_GATE))
    default_decision: GateDecision = GATE_ALL_ON
    mode: str = "on"
    story_prefix_len: int = 500

    # Cache: demand classification per task_type (since same task_type → same demand)
    _demand_cache: dict[str, str] = field(default_factory=dict, init=False, repr=False)
    _cache_lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)

    # Statistics: track gate decision sources
    _stats: dict[str, int] = field(default_factory=lambda: {
        "total": 0,
        "layer1_pattern": 0,
        "layer1_task_type": 0,
        "layer2_llm": 0,
        "default": 0,
    }, init=False, repr=False)
    _stats_lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)

    def decide(
        self,
        *,
        question: str,
        story: str = "",
        options: dict[str, str] | None = None,
        eval_mode: str | None = None,
        task_type: str | None = None,
        raw_metadata: dict | None = None,  # ignored; consumed by UnifiedModuleGate
    ) -> GateDecision:
        """Decide which modules to activate for this sample."""

        with self._stats_lock:
            self._stats["total"] += 1

        if self.mode == "off":
            return GATE_ALL_ON

        # ── Layer 1: Rule engine ──────────────────────────────────────────
        for rule in self.rules:
            if rule.matches(question=question, task_type=task_type, eval_mode=eval_mode):
                decision = rule.to_decision()

                # Track whether this was a pattern match or task_type match
                with self._stats_lock:
                    if rule.question_pattern:
                        self._stats["layer1_pattern"] += 1
                    elif rule.task_type_exact or rule.task_type_prefix:
                        self._stats["layer1_task_type"] += 1

                logger.debug("[Gate] L1 rule matched: %s → %s", rule.name, decision)
                return decision

        # ── Layer 2: LLM demand classification ────────────────────────────
        if self.mode == "rules_only" or self.llm is None:
            with self._stats_lock:
                self._stats["default"] += 1
            return self.default_decision

        demand = self._classify_demand(question=question, story=story, task_type=task_type)
        gate_map = self.demand_to_gate.get(demand, {"skill": True, "rag": True, "memory": True})

        with self._stats_lock:
            self._stats["layer2_llm"] += 1

        decision = GateDecision(
            use_skill=gate_map.get("skill", True),
            use_rag=gate_map.get("rag", True),
            use_memory=gate_map.get("memory", True),
            rationale=f"llm_demand:{demand}",
            n_llm_calls=1,
        )
        logger.info("[Gate] L2 classified demand=%s → %s", demand, decision)
        return decision

    def _classify_demand(self, *, question: str, story: str, task_type: str | None) -> str:
        """Classify the reasoning demand using LLM. Cached per task_type."""

        cache_key = task_type or ""

        # Fast path: check cache
        if cache_key and cache_key in self._demand_cache:
            return self._demand_cache[cache_key]

        with self._cache_lock:
            # Re-check after acquiring lock
            if cache_key and cache_key in self._demand_cache:
                return self._demand_cache[cache_key]

            story_excerpt = story[:self.story_prefix_len] if story else ""
            user_prompt = (
                f"Story (excerpt):\n{story_excerpt}\n\n"
                f"Question:\n{question}"
            )

            try:
                response = self.llm.chat(
                    _CLASSIFY_SYSTEM,
                    user_prompt,
                    max_tokens=64,
                    temperature=0.0,
                )
                demand = self._parse_demand(response)
            except Exception as e:
                logger.warning("[Gate] LLM classify failed: %s", e)
                demand = "MEMORY_ONLY"  # safe fallback: most common strategy

            if cache_key:
                self._demand_cache[cache_key] = demand

            return demand

    @staticmethod
    def _parse_demand(text: str) -> str:
        """Extract demand category from LLM response."""
        # Strip think tags
        text = re.sub(r"<think>[\s\S]*?</think>", "", text).strip()

        # Try JSON parse
        try:
            d = json.loads(text)
            cat = d.get("demand", "").strip().upper()
            if cat in DEMAND_TYPES:
                return cat
        except (json.JSONDecodeError, AttributeError):
            pass

        # Try extracting from ```json``` block
        m = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if m:
            try:
                d = json.loads(m.group(1))
                cat = d.get("demand", "").strip().upper()
                if cat in DEMAND_TYPES:
                    return cat
            except (json.JSONDecodeError, AttributeError):
                pass

        # Fallback: substring match
        text_upper = text.upper()
        for dt in DEMAND_TYPES:
            if dt in text_upper:
                return dt

        return "MEMORY_ONLY"  # default fallback

    def get_stats(self) -> dict[str, int]:
        """Return gate decision statistics for analysis.

        Returns:
            Dict with keys: total, layer1_pattern, layer1_task_type, layer2_llm, default
        """
        with self._stats_lock:
            return dict(self._stats)

    def reset_stats(self) -> None:
        """Reset gate statistics counters."""
        with self._stats_lock:
            self._stats = {
                "total": 0,
                "layer1_pattern": 0,
                "layer1_task_type": 0,
                "layer2_llm": 0,
                "default": 0,
            }
