"""ModuleGate — selective module activation for HarnessRuntime."""

from .base import ModuleGate, GateDecision, GateRule
from .config import load_gate_config
from .unified_gate import UnifiedModuleGate, load_unified_gate

__all__ = [
    "ModuleGate", "GateDecision", "GateRule", "load_gate_config",
    "UnifiedModuleGate", "load_unified_gate",
]
