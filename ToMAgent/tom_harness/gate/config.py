"""Load gate configuration from YAML file.

Example gate_config.yaml:

    mode: "on"                    # "on" | "off" | "rules_only"
    story_prefix_len: 500

    demand_to_gate:
      BELIEF_TRACKING:   {skill: true,  rag: true,  memory: true}
      SOCIAL_PRAGMATICS: {skill: false, rag: false, memory: true}
      INFO_FLOW_CHAIN:   {skill: true,  rag: false, memory: false}
      FACTUAL:           {skill: false, rag: false, memory: false}
      HIGH_BASELINE:     {skill: false, rag: false, memory: false}

    rules:
      - name: "tactful_inaccessible"
        match:
          task_type_prefix: "belief:inaccessible"
        gate: {skill: false, rag: false, memory: false}

      - name: "tactful_comprehension"
        match:
          task_type_prefix: "comprehension"
        gate: {skill: false, rag: false, memory: true}
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .base import GateRule, ModuleGate, GateDecision, DEFAULT_DEMAND_TO_GATE, GATE_ALL_ON


def load_gate_config(
    config_path: str | Path,
    *,
    llm: Any = None,
    dataset_name: str | None = None,
) -> ModuleGate:
    """Load a ModuleGate from a YAML config file.

    Auto-detects unified.yaml shape: if any rule has a `when:` block
    (instead of `match:`), returns a UnifiedModuleGate instead.

    Args:
        config_path: Path to a YAML file.
        llm: LLMClient for Layer 2 classification. If None, Layer 2 is skipped.
        dataset_name: Required when loading a unified.yaml so the gate can
            dispatch the right meta_translator.
    """
    import yaml

    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Gate config not found: {path}")

    with open(path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}

    # ── Auto-detect unified config (rules use `when:` instead of `match:`) ──
    rules_raw = cfg.get("rules", []) or []
    if rules_raw and any("when" in r for r in rules_raw):
        from .unified_gate import load_unified_gate
        if dataset_name is None:
            raise ValueError(
                f"{path.name} is a unified gate config but no dataset_name "
                "was provided to load_gate_config()"
            )
        return load_unified_gate(path, dataset_name=dataset_name)

    mode = cfg.get("mode", "on")
    story_prefix_len = cfg.get("story_prefix_len", 500)

    # Parse rules
    rules: list[GateRule] = []
    for rule_cfg in cfg.get("rules", []):
        match = rule_cfg.get("match", {})
        gate = rule_cfg.get("gate", {"skill": True, "rag": True, "memory": True})
        rules.append(GateRule(
            name=rule_cfg.get("name", ""),
            task_type_prefix=match.get("task_type_prefix"),
            task_type_exact=match.get("task_type_exact"),
            eval_mode=match.get("eval_mode"),
            question_pattern=match.get("question_pattern"),
            gate=gate,
        ))

    # Parse demand_to_gate mapping
    demand_to_gate = dict(DEFAULT_DEMAND_TO_GATE)
    for demand_type, gate_map in cfg.get("demand_to_gate", {}).items():
        demand_to_gate[demand_type.upper()] = {
            "skill": bool(gate_map.get("skill", True)),
            "rag": bool(gate_map.get("rag", True)),
            "memory": bool(gate_map.get("memory", True)),
        }

    return ModuleGate(
        rules=rules,
        llm=llm,
        demand_to_gate=demand_to_gate,
        default_decision=GATE_ALL_ON,
        mode=mode,
        story_prefix_len=story_prefix_len,
    )
