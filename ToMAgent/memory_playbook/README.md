# memory — Portable recall from a trained ACE playbook

A self-contained package that wraps a trained playbook and a selector LLM to
retrieve relevant "bullets" (strategy entries) for a given question.

## Requirements

- Python 3.12+
- `openai` (the only external dependency)

## Quick start

```python
from memory_playbook import Memory, SelectorConfig

# Programmatic
memory = Memory(
    playbook_path="playbook/final_playbook.txt",
    selector=SelectorConfig(
        provider="deepseek",
        api_key="sk-...",
        model="deepseek-chat",
    ),
)

# Or from a TOML config file
memory = Memory.from_toml(
    playbook_path="playbook/final_playbook.txt",
    config_path="memory/config.example.toml",
)

# Recall relevant bullets
result = memory.recall("Where does Sally think the marble is?")

result.bullets             # list[Bullet] — populated only on the "normal" tier
result.bullet_ids          # list[str]
result.predicted_subtask   # str — coerced into the bucket vocabulary
result.fallback_level      # "normal" | "subtask" | "generic" | "full" | "empty"
result.as_text()           # context to feed the generator ("" when "empty")
bool(result)               # True when as_text() is non-empty
```

## Fixed classification

The selector is shown a **closed bucket vocabulary** and always returns a
`predicted_subtask` coerced into it (anything out-of-vocab folds into `Others`).
The default is the Theory-of-Mind set — `Emotion, Desire, Intention, Knowledge,
Belief, Non-Literal Communication` — overridable via `SelectorConfig.buckets`
(or the `buckets` TOML key) for other domains.

## Three-level fallback

When the selector picks no usable bullets, `recall()` degrades gracefully and
records which tier produced the context in `result.fallback_level`:

1. **normal** — the selector's chosen bullets (filtered playbook). `bullets` /
   `bullet_ids` are populated.
2. **subtask** — all bullets observed in the predicted subtask bucket.
3. **generic** — the configured `fallback_text` (generic reasoning guidance).
4. **full** / **empty** — the legacy `fallback_policy`.

Tiers 2 and 3 can be toggled independently via `enable_subtask_fallback`
(default `true`) and `enable_generic_fallback` (default `false`). A disabled tier
is skipped and the cascade falls through to the next; with both off (and
`fallback_policy = "empty"`) every selector miss returns empty.

Set `enable_fallback = false` to restore the old **no-fallback contract**:
`recall()` then only ever returns tier-1 bullets, else an empty result.

> The bundled `playbook/final_playbook.txt` predates fixed classification and
> uses older dynamic bucket slugs, so the tier-2 subtask fallback matches best
> once the playbook is re-trained with the fixed vocab. The defaults remain ToM.

## Configuration

The TOML file needs a `[selector]` table:

```toml
[selector]
provider      = "openai"          # openai | deepseek | together | sambanova | commonstack | qwen | custom
api_key       = "${OPENAI_API_KEY}"  # supports ${ENV_VAR} substitution
model         = "gpt-4o-mini"
# base_url    = "https://..."     # required only when provider = "custom"
max_tokens    = 8192
max_bullets   = 8
use_json_mode = false

# buckets                 = ["Emotion", "Desire", ...]  # omit for the ToM default
# enable_fallback         = true   # false -> no-fallback contract
# enable_subtask_fallback = true   # tier 2 toggle
# enable_generic_fallback = false  # tier 3 toggle (default off)
# fallback_text           = "Before answering: ..."  # omit for ToM scaffold; "" disables tier 3
# fallback_policy         = "empty"                   # legacy tier: "empty" | "full"
```

## Portability

Copy the entire `memory_playbook/` folder into another project. As long as `openai` is
installed, it will work with no other dependencies from this repo.
