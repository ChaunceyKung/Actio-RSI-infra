"""Memory — portable recall from a trained ACE playbook."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import openai

from .buckets import OTHERS_BUCKET, normalize_vocab, slugify_bucket
from .config import SelectorConfig, load_selector_config
from .playbook import (
    extract_bullets_for_subtask,
    filter_playbook_to_bullets,
    parse_playbook_line,
)
from .selector import Selector

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Bullet:
    id: str
    content: str
    section: Optional[str]
    helpful: int
    harmful: int
    buckets: dict
    raw_line: str


@dataclass
class RecallResult:
    """Outcome of a `recall()`.

    `fallback_level` records which tier produced the context:
      - "normal":  selector picked bullets; `bullets`/`bullet_ids` are populated.
      - "subtask": all bullets observed in the predicted subtask bucket.
      - "generic": the configured generic guidance text.
      - "full":    the whole playbook (legacy fallback_policy="full").
      - "empty":   nothing relevant; `as_text()` is "".

    Only the "normal" tier populates `bullets`/`bullet_ids`; the fallback tiers
    carry their context in `as_text()`, not as Bullet objects.
    """
    bullets: list[Bullet]
    bullet_ids: list[str]
    predicted_subtask: str
    fallback_level: str
    _text: str = field(default="", repr=False)

    def as_text(self) -> str:
        return self._text

    def __bool__(self) -> bool:
        return bool(self._text)


class Memory:
    """Load a trained playbook and recall relevant bullets via a selector LLM.

    Optimization:
      - The selector prompt is built from a compact **summary index** instead of
        the full playbook text, shrinking the prompt from ~185KB to ~10-15KB so
        the selector LLM stays fast.

    The selector LLM is called fresh on every ``recall()`` (no cross-sample
    caching).

    On top of the selector, `recall()` applies a three-level fallback cascade
    (normal -> subtask-bucket -> generic text -> legacy policy).

    Usage::

        memory = Memory("playbook/final_playbook.txt",
                         SelectorConfig(provider="openai",
                                        api_key="sk-...",
                                        model="gpt-4o-mini"))
        result = memory.recall("Where does Sally think the marble is?",
                               task_type="Belief")
        result.bullets     # list[Bullet], may be []
        result.as_text()   # filtered playbook text or fallback text, "" when empty
    """

    def __init__(self, playbook_path: str, selector: SelectorConfig):
        self.playbook = Path(playbook_path).read_text(encoding="utf-8")
        self._bullet_index = self._build_index(self.playbook)

        # Fixed classification: a closed bucket vocabulary shown to the selector
        # and used to coerce its predicted_subtask.
        self.bucket_vocab = normalize_vocab(selector.buckets)
        self.known_subtasks = self.bucket_vocab

        self.fallback_text = selector.fallback_text
        self.fallback_policy = selector.fallback_policy
        self.enable_fallback = selector.enable_fallback
        self.enable_subtask_fallback = selector.enable_subtask_fallback
        self.enable_generic_fallback = selector.enable_generic_fallback

        # Compact bucket-grouped index fed to the selector instead of the full
        # ~185KB playbook (keeps the selector prompt small and fast). Fallback
        # tiers still scan the full playbook, so pruned bullets remain reachable.
        self._summary_index = self._build_summary_index(self._bullet_index)

        client = openai.OpenAI(
            api_key=selector.api_key,
            base_url=selector.resolved_base_url(),
        )
        self._selector = Selector(
            client, selector.provider, selector.model,
            max_tokens=selector.max_tokens,
            max_bullets=selector.max_bullets,
            bucket_vocab=self.bucket_vocab,
        )
        self._use_json_mode = selector.use_json_mode

    @classmethod
    def from_toml(cls, playbook_path: str, config_path: str) -> Memory:
        return cls(playbook_path, load_selector_config(config_path))

    def recall(
        self,
        question: str,
        *,
        context: str = "",
        task_type: str | None = None,
        max_bullets: Optional[int] = None,
    ) -> RecallResult:
        """Recall context for a question via the selector + three-level fallback.

        The selector LLM is called fresh on every call. When *task_type* is
        provided it is passed to the selector as a target-subtask hint; it is
        not used for caching.

        Tiers (when `enable_fallback` is True, the default):
          1. normal  — selector's chosen bullets, filtered.
          2. subtask — all bullets in the predicted subtask bucket
                       (skipped when `enable_subtask_fallback` is False).
          3. generic — the configured `fallback_text`
                       (skipped when `enable_generic_fallback` is False).
          4. full/empty — legacy `fallback_policy`.

        A disabled tier is skipped and the cascade falls through to the next
        one. With `enable_fallback` False, only tier 1 applies; otherwise an
        empty result is returned (the old no-fallback contract).
        """
        if max_bullets is not None:
            self._selector.max_bullets = max_bullets

        short_context = context[:200] if context else ""
        predicted, ids, _ = self._selector.select(
            question,
            self._summary_index,
            context=short_context,
            known_subtasks=self.known_subtasks,
            target_subtask=task_type,
            use_json_mode=self._use_json_mode,
        )
        logger.info(
            "[Memory] recall(task_type=%s) -> subtask=%s, %d ids",
            task_type, predicted, len(ids),
        )
        others = slugify_bucket(OTHERS_BUCKET)

        # Tier 1: selector returned usable bullets.
        if ids:
            filtered = filter_playbook_to_bullets(self.playbook, ids)
            if filtered:
                bullets = [self._bullet_index[bid] for bid in ids
                           if bid in self._bullet_index]
                return RecallResult(
                    bullets=bullets,
                    bullet_ids=[b.id for b in bullets],
                    predicted_subtask=predicted,
                    fallback_level="normal",
                    _text=filtered,
                )

        # No-fallback contract: stop here when fallback is disabled.
        if not self.enable_fallback:
            return RecallResult([], [], predicted, "empty", "")

        # Tier 2: bullets observed in the predicted subtask bucket.
        if self.enable_subtask_fallback and predicted and predicted != others:
            subtask_text = extract_bullets_for_subtask(
                self.playbook, predicted, max_bullets=20
            )
            if subtask_text and not subtask_text.startswith("("):
                return RecallResult([], [], predicted, "subtask", subtask_text)

        # Tier 3: generic guidance text.
        if self.enable_generic_fallback and self.fallback_text:
            return RecallResult([], [], predicted, "generic", self.fallback_text)

        # Tier 4: legacy policy.
        if self.fallback_policy == "full":
            return RecallResult([], [], predicted, "full", self.playbook)
        return RecallResult([], [], predicted, "empty", "")

    @staticmethod
    def _build_summary_index(bullet_index: dict[str, Bullet]) -> str:
        """Build a compact bucket-grouped index for the selector prompt.

        One ``## <subtask>`` section per bucket the bullets are tagged with;
        each line is ``[bullet_id](helpful/total) snippet`` using the bullet's
        **aggregate** helpful/harmful counts.

        Grouping is by bucket-key *presence*, not by per-bucket hit counts, so
        the index stays meaningful even for playbooks that keep all of their
        accounting under one bucket (e.g. ``Others``) and use the semantic
        buckets purely as tags. Keeps the prompt small (~10-15KB vs the ~185KB
        full playbook) so the selector LLM stays fast.
        """
        from collections import defaultdict
        bucket_bullets: dict[str, list[tuple[str, int, int, str]]] = defaultdict(list)
        for bid, b in bullet_index.items():
            if b.helpful <= b.harmful:
                continue
            total = b.helpful + b.harmful
            snippet = b.content[:60].replace("\n", " ")
            for bk in b.buckets:
                bucket_bullets[bk].append((bid, b.helpful, total, snippet))

        lines: list[str] = []
        for bk in sorted(bucket_bullets):
            entries = bucket_bullets[bk]
            entries.sort(key=lambda x: -x[1])
            bullet_strs = [f"[{bid}]({h}/{n}) {snip}" for bid, h, n, snip in entries[:10]]
            lines.append(f"## {bk}")
            lines.extend(bullet_strs)
            lines.append("")
        return "\n".join(lines)

    @staticmethod
    def _build_index(playbook_text: str) -> dict[str, Bullet]:
        index: dict[str, Bullet] = {}
        current_section: Optional[str] = None

        for line in playbook_text.split('\n'):
            stripped = line.strip()
            if stripped.startswith('##'):
                current_section = stripped.lstrip('#').strip()
                continue
            parsed = parse_playbook_line(line)
            if parsed:
                index[parsed['id']] = Bullet(
                    id=parsed['id'],
                    content=parsed['content'],
                    section=current_section,
                    helpful=parsed['helpful'],
                    harmful=parsed['harmful'],
                    buckets=parsed['buckets'],
                    raw_line=parsed['raw_line'],
                )

        return index
