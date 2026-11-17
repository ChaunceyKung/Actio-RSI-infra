"""Selector configuration: SelectorConfig dataclass, TOML loader, env-var resolution."""
from __future__ import annotations

import os
import re
import tomllib
from dataclasses import dataclass
from typing import List, Optional

from .prompts import DEFAULT_FALLBACK_TEXT

PROVIDER_DEFAULT_BASE_URL = {
    "sambanova":   "https://api.sambanova.ai/v1",
    "together":    "https://api.together.xyz/v1",
    "openai":      "https://api.openai.com/v1",
    "commonstack": "https://api.commonstack.ai/v1",
    "deepseek":    "https://api.deepseek.com",
    "qwen":        "https://dashscope.aliyuncs.com/compatible-mode/v1",
}

_VALID_PROVIDERS = set(PROVIDER_DEFAULT_BASE_URL) | {"custom"}

_ENV_REF = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")


def resolve_env_refs(value: str, *, where: str) -> str:
    """Replace every ``${VAR}`` in *value* with ``os.environ[VAR]``."""
    if not isinstance(value, str):
        return value

    missing: list[str] = []

    def _sub(m: re.Match[str]) -> str:
        var = m.group(1)
        v = os.environ.get(var, "")
        if not v:
            missing.append(var)
        return v

    out = _ENV_REF.sub(_sub, value)
    if missing:
        names = ", ".join(f"${{{n}}}" for n in missing)
        raise ValueError(f"{where} references {names} which is unset or empty")
    return out


@dataclass(frozen=True)
class SelectorConfig:
    provider: str
    api_key: str
    model: str
    base_url: Optional[str] = None
    # Headroom for reasoning helper models (e.g. deepseek): the selector's
    # reasoning tokens often eat ~700+ of the budget, and if the JSON answer
    # gets squeezed out the call returns empty -> recall silently falls back to
    # nothing. 1024 is too tight; the model still stops naturally well under
    # this cap, and per-task_type caching bounds the call count.
    max_tokens: int = 8192
    max_bullets: int = 8
    use_json_mode: bool = False
    # Closed bucket vocabulary for fixed classification. None -> ToM default
    # (see buckets.DEFAULT_PLAYBOOK_BUCKETS). Normalized by Memory at load time.
    buckets: Optional[List[str]] = None
    # Tier-3 generic guidance text. None disables tier 3. Defaults to the ToM
    # scaffold; in TOML an empty string also disables it.
    fallback_text: Optional[str] = DEFAULT_FALLBACK_TEXT
    # Legacy tier when tiers 2-3 don't apply: "empty" (no context) or "full"
    # (whole playbook).
    fallback_policy: str = "empty"
    # Master switch. False restores the old no-fallback contract: recall()
    # only ever returns tier-1 selected bullets, else an empty result.
    enable_fallback: bool = True
    # Per-tier switches (only consulted when enable_fallback is True). When a
    # tier is off it is skipped and the cascade falls through to the next; turn
    # both off (with fallback_policy="empty") to make every miss return empty.
    enable_subtask_fallback: bool = True   # tier 2: subtask-bucket bullets
    enable_generic_fallback: bool = False  # tier 3: generic fallback_text

    def resolved_base_url(self) -> str:
        if self.base_url:
            return self.base_url
        if self.provider == "custom":
            raise ValueError("base_url is required when provider='custom'")
        url = PROVIDER_DEFAULT_BASE_URL.get(self.provider)
        if not url:
            raise ValueError(
                f"Unknown provider {self.provider!r}. "
                f"Valid: {sorted(_VALID_PROVIDERS)}. "
                f"Or set base_url explicitly."
            )
        return url


def load_selector_config(path: str) -> SelectorConfig:
    """Load a ``SelectorConfig`` from a TOML file's ``[selector]`` table."""
    with open(path, "rb") as f:
        data = tomllib.load(f)

    raw = data.get("selector")
    if not raw:
        raise ValueError(f"[selector] table missing in {path}")

    provider = raw.get("provider")
    if not provider or provider not in _VALID_PROVIDERS:
        raise ValueError(
            f"[selector].provider={provider!r} is not one of {sorted(_VALID_PROVIDERS)}"
        )

    api_key_raw = raw.get("api_key")
    if not api_key_raw:
        raise ValueError("[selector].api_key is required")
    api_key = resolve_env_refs(api_key_raw, where="[selector].api_key")

    model = raw.get("model")
    if not model:
        raise ValueError("[selector].model is required")

    base_url = raw.get("base_url")
    if base_url:
        base_url = resolve_env_refs(base_url, where="[selector].base_url")

    max_tokens = raw.get("max_tokens", 8192)
    max_bullets = raw.get("max_bullets", 8)
    use_json_mode = raw.get("use_json_mode", False)

    buckets = raw.get("buckets")  # None -> ToM default, normalized by Memory

    # Absent key -> ship the ToM default; explicit empty string -> disable tier 3.
    if "fallback_text" in raw:
        ft = raw["fallback_text"]
        fallback_text = ft if ft else None
    else:
        fallback_text = DEFAULT_FALLBACK_TEXT

    fallback_policy = raw.get("fallback_policy", "empty")
    if fallback_policy not in ("empty", "full"):
        raise ValueError(
            f"[selector].fallback_policy={fallback_policy!r} must be 'empty' or 'full'"
        )
    enable_fallback = raw.get("enable_fallback", True)
    enable_subtask_fallback = raw.get("enable_subtask_fallback", True)
    enable_generic_fallback = raw.get("enable_generic_fallback", False)

    return SelectorConfig(
        provider=provider,
        api_key=api_key,
        model=model,
        base_url=base_url,
        max_tokens=max_tokens,
        max_bullets=max_bullets,
        use_json_mode=use_json_mode,
        buckets=buckets,
        fallback_text=fallback_text,
        fallback_policy=fallback_policy,
        enable_fallback=enable_fallback,
        enable_subtask_fallback=enable_subtask_fallback,
        enable_generic_fallback=enable_generic_fallback,
    )
