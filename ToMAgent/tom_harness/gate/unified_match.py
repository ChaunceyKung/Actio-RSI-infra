"""Minimal evaluator for unified.yaml.

Consumes (nesting, StandardMeta) and returns a GateDecision plus extra
enrichments (skill_allow / memory_focus / scaffold). This is an additive
runtime adapter — does NOT replace the existing GateRule engine, which
the main runtime still uses.

Usage:
    from tom_harness.gate.unified_match import load_unified_config, decide
    cfg = load_unified_config("tom_harness/gate/configs/unified.yaml")
    decision = decide(cfg, nesting=3, std_meta=std)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .standard_meta import StandardMeta


# ─────────────────────────── Comparison helpers ───────────────────────────
_OP_RE = re.compile(r"^(>=|<=|==|>|<)?\s*(-?\d+)$")


def _match_int(spec, value: int) -> bool:
    """Match int spec: literal int, or string like '>=3', '<=1', '==2'."""
    if isinstance(spec, int):
        return value == spec
    if isinstance(spec, str):
        m = _OP_RE.match(spec.strip())
        if not m:
            return False
        op, rhs = m.group(1) or "==", int(m.group(2))
        return {
            "==": value == rhs,
            ">=": value >= rhs,
            "<=": value <= rhs,
            ">":  value >  rhs,
            "<":  value <  rhs,
        }[op]
    return False


def _match_scalar_or_list(spec, value) -> bool:
    """Scalar → equality; list → membership."""
    if isinstance(spec, list):
        return value in spec
    return spec == value


# ─────────────────────────── Rule + Config dataclasses ───────────────────────────
@dataclass
class UnifiedRule:
    name: str
    when: dict
    gate: dict
    skill_allow: list[str] = field(default_factory=list)
    skill_exclude: list[str] = field(default_factory=list)
    memory_focus: list[str] = field(default_factory=list)
    memory_focus_add: list[str] = field(default_factory=list)
    scaffold: str | None = None

    def matches(self, *, nesting: int, std: StandardMeta) -> bool:
        for key, spec in self.when.items():
            if key == "nesting":
                if not _match_int(spec, nesting):
                    return False
            elif key in ("construct", "false_belief_kind", "difficulty_hint", "answer_type"):
                val = getattr(std, key, None)
                if val is None or not _match_scalar_or_list(spec, val):
                    return False
            elif key in ("deception", "dialogue_format"):
                val = getattr(std, key, None)
                if val is None or val != spec:
                    return False
            else:
                # Unknown match key → silently fail safe
                return False
        return True


@dataclass
class UnifiedDecision:
    use_skill: bool
    use_rag: bool
    use_memory: bool
    matched_rule: str
    skill_allow: list[str] = field(default_factory=list)
    skill_exclude: list[str] = field(default_factory=list)
    memory_focus: list[str] = field(default_factory=list)
    memory_focus_add: list[str] = field(default_factory=list)
    scaffold: str | None = None


@dataclass
class UnifiedConfig:
    mode: str
    rules: list[UnifiedRule]
    default_gate: dict


def load_unified_config(path: str | Path) -> UnifiedConfig:
    import yaml
    with open(path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    rules = []
    for r in cfg.get("rules", []):
        rules.append(UnifiedRule(
            name=r.get("name", ""),
            when=r.get("when", {}) or {},
            gate=r.get("gate", {"skill": True, "rag": True, "memory": True}),
            skill_allow=list(r.get("skill_allow", []) or []),
            skill_exclude=list(r.get("skill_exclude", []) or []),
            memory_focus=list(r.get("memory_focus", []) or []),
            memory_focus_add=list(r.get("memory_focus_add", []) or []),
            scaffold=r.get("scaffold"),
        ))
    return UnifiedConfig(
        mode=cfg.get("mode", "on"),
        rules=rules,
        default_gate=cfg.get("default_gate", {"skill": True, "rag": True, "memory": True}),
    )


def decide(cfg: UnifiedConfig, *, nesting: int, std: StandardMeta) -> UnifiedDecision:
    if cfg.mode == "off":
        return UnifiedDecision(True, True, True, matched_rule="<mode_off>")

    for rule in cfg.rules:
        if rule.matches(nesting=nesting, std=std):
            g = rule.gate
            return UnifiedDecision(
                use_skill=bool(g.get("skill", True)),
                use_rag=bool(g.get("rag", True)),
                use_memory=bool(g.get("memory", True)),
                matched_rule=rule.name,
                skill_allow=list(rule.skill_allow),
                skill_exclude=list(rule.skill_exclude),
                memory_focus=list(rule.memory_focus),
                memory_focus_add=list(rule.memory_focus_add),
                scaffold=rule.scaffold,
            )

    g = cfg.default_gate
    return UnifiedDecision(
        use_skill=bool(g.get("skill", True)),
        use_rag=bool(g.get("rag", True)),
        use_memory=bool(g.get("memory", True)),
        matched_rule="<default>",
    )
