"""Shared output parsers used by both the runtime and validators."""

from __future__ import annotations

import json
import re


def parse_multi_select_response(raw: str) -> list[str]:
    """Parse model output for multi-select (ICTBench Q2) into a list of letters.

    Tolerates JSON / pattern / bare-letter formats. Always returns a sorted
    de-duplicated list of letters from A-E.
    """
    text = re.sub(r"<think>[\s\S]*?</think>", "", raw or "").strip()
    if not text:
        m_think = re.search(r"<think>([\s\S]*?)</think>", raw or "")
        text = m_think.group(1).strip() if m_think else ""

    json_match = re.search(r'\{[^{}]*"answer"\s*:\s*\[([^\]]*)\][^{}]*\}', text)
    if json_match:
        try:
            obj = json.loads(json_match.group(0))
            letters = obj.get("answer", [])
            if isinstance(letters, list):
                return sorted({
                    l.strip().upper() for l in letters
                    if isinstance(l, str) and l.strip().upper() in "ABCDE"
                })
        except (json.JSONDecodeError, TypeError):
            inner = json_match.group(1)
            parts = [p.strip().strip('"').strip("'").upper() for p in inner.split(",")]
            return sorted({p for p in parts if p in "ABCDE"})

    m = re.search(
        r'(?:答案|选|answer)\s*(?:[:：为是]+)?\s*([A-E][、,\s]*(?:[A-E][、,\s]*)*)',
        text, re.IGNORECASE,
    )
    if m:
        letters = re.findall(r'[A-E]', m.group(1).upper())
        if letters:
            return sorted(set(letters))

    m2 = re.search(r'^([A-E]{2,5})\s*$', text, re.MULTILINE)
    if m2:
        return sorted(set(m2.group(1).upper()))

    for line in reversed(text.splitlines()):
        letters = re.findall(r'\b([A-E])\b', line.upper())
        if letters:
            return sorted(set(letters))

    return []
