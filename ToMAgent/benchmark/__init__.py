"""Benchmark data loaders."""

from .load_tombench import load_tombench
from .load_hitom import load_hitom
from .load_social_iqa import load_social_iqa

__all__ = ["load_tombench", "load_hitom", "load_social_iqa"]
