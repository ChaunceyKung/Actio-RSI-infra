"""Fixed playbook bucket vocabulary.

A closed vocabulary of subtask labels chosen up-front. The Selector echoes back
one of these labels as `predicted_subtask` for each question; every emitted
string is run through `coerce_bucket` so anything out-of-vocabulary falls into
`OTHERS_BUCKET`.

The on-disk slug (used as the bucket key inside `buckets={...}` on a bullet
line) cannot contain whitespace, ',' or ':' — see `playbook._format_buckets`
and the regex in `parse_playbook_line`. We therefore canonicalize every bucket
to its slug form internally and keep the human-readable label only for prompt
display.

`DEFAULT_PLAYBOOK_BUCKETS` ships the Theory-of-Mind vocabulary; pass your own
list via `SelectorConfig.buckets` to use this plugin in another domain.
"""

from __future__ import annotations

import re
from typing import Iterable, List, Optional

DEFAULT_PLAYBOOK_BUCKETS: List[str] = [
    "Emotion",
    "Desire",
    "Intention",
    "Knowledge",
    "Belief",
    "Non-Literal Communication",
]

OTHERS_BUCKET = "Others"


def slugify_bucket(name: str) -> str:
    """Return the on-disk form of a bucket name.

    Whitespace and punctuation are collapsed to underscores. Letters stay in
    their original case so `Belief` and `belief` remain distinct on disk; the
    coercion layer is what folds case-insensitive matches together.
    """
    s = re.sub(r"[\s\-,:]+", "_", (name or "").strip())
    s = re.sub(r"[^A-Za-z0-9_]+", "", s)
    return s.strip("_")


def normalize_vocab(buckets: Optional[Iterable[str]]) -> List[str]:
    """De-dup, preserve order, ensure `OTHERS_BUCKET` is present at the tail.

    The returned list contains slug-form names suitable for both prompt display
    and on-disk storage. Empty / None input yields the project default.
    """
    raw = list(buckets) if buckets else list(DEFAULT_PLAYBOOK_BUCKETS)
    seen: set[str] = set()
    out: List[str] = []
    for name in raw:
        slug = slugify_bucket(name)
        if not slug:
            continue
        if slug.lower() in seen:
            continue
        seen.add(slug.lower())
        out.append(slug)
    others = slugify_bucket(OTHERS_BUCKET)
    if others.lower() not in seen:
        out.append(others)
    return out


def coerce_bucket(name: Optional[str], vocab: List[str]) -> str:
    """Map any model-emitted string to a bucket inside `vocab`.

    Order: exact slug match → case-insensitive slug match → fall back to
    the slug form of `OTHERS_BUCKET`. `vocab` is expected to be the output
    of `normalize_vocab` (slug form, with `Others` present).
    """
    others = slugify_bucket(OTHERS_BUCKET)
    if not name:
        return others
    candidate = slugify_bucket(name)
    if not candidate:
        return others
    if candidate in vocab:
        return candidate
    lower_map = {v.lower(): v for v in vocab}
    hit = lower_map.get(candidate.lower())
    if hit is not None:
        return hit
    return others
