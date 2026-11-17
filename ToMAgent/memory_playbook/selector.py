"""Selector agent — picks a relevant subset of playbook bullets for a question."""
from __future__ import annotations

import re
from typing import List, Optional, Tuple

from .prompts import SELECTOR_PROMPT
from .llm import timed_llm_call
from .playbook import extract_json_from_text
from .buckets import coerce_bucket, slugify_bucket, OTHERS_BUCKET

# A bullet line starts with a `[prefix-NNNNN]` id in BOTH the full playbook
# (`[sai-00128] helpful=... buckets={...} :: ...`) and the compact summary
# index Memory feeds the selector (`[sai-00128](12/15) snippet`). Matching the
# id token keeps the "is there anything to pick?" guard format-agnostic.
_BULLET_LINE_RE = re.compile(r'^\s*\[[A-Za-z]+-\d+\]')


class Selector:
    def __init__(self, api_client, api_provider: str, model: str,
                 max_tokens: int = 1024, max_bullets: int = 8,
                 bucket_vocab: Optional[List[str]] = None):
        self.api_client = api_client
        self.api_provider = api_provider
        self.model = model
        self.max_tokens = max_tokens
        self.max_bullets = max_bullets
        self.bucket_vocab = list(bucket_vocab) if bucket_vocab else []

    def select(
        self,
        question: str,
        playbook: str,
        *,
        context: str = "",
        known_subtasks: Optional[List[str]] = None,
        target_subtask: Optional[str] = None,
        use_json_mode: bool = False,
    ) -> Tuple[str, List[str], dict]:
        """Return (predicted_subtask, selected_bullet_ids, call_info).

        Returns (Others, [], {}) when the playbook has no bullets. When a
        `bucket_vocab` is configured, `predicted_subtask` is always coerced into
        it, defaulting to the slug form of `Others` for any out-of-vocab string.
        """
        others = slugify_bucket(OTHERS_BUCKET)
        has_bullets = any(_BULLET_LINE_RE.match(l) for l in playbook.split('\n'))
        if not has_bullets:
            return others, [], {}

        subtasks_str = ", ".join(known_subtasks) if known_subtasks else "(none yet)"
        if target_subtask:
            target_str = (f"{target_subtask} — prefer bullets whose bucket for this "
                          f"subtask shows helpful >= harmful and n >= 3")
        else:
            target_str = "(unknown — pick from the list above or output 'Others')"

        prompt = SELECTOR_PROMPT.format(
            max_bullets=self.max_bullets,
            known_subtasks=subtasks_str,
            target_subtask=target_str,
            playbook=playbook,
            question=question,
            context=context or "",
        )

        response, call_info = timed_llm_call(
            self.api_client,
            self.api_provider,
            self.model,
            prompt,
            max_tokens=self.max_tokens,
            use_json_mode=use_json_mode,
        )

        predicted_subtask = others
        bullet_ids: List[str] = []

        try:
            parsed = extract_json_from_text(response)
            if parsed:
                raw_subtask = parsed.get("predicted_subtask")
                if self.bucket_vocab:
                    predicted_subtask = coerce_bucket(raw_subtask, self.bucket_vocab)
                else:
                    predicted_subtask = str(raw_subtask or others).strip() or others
                raw_ids = parsed.get("selected_bullet_ids") or []
                if isinstance(raw_ids, list):
                    bullet_ids = [str(b) for b in raw_ids if isinstance(b, (str, int))]
                bullet_ids = bullet_ids[: self.max_bullets]
        except Exception:
            pass

        return predicted_subtask, bullet_ids, call_info
