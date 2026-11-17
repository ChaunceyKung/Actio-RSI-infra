"""Deterministic renderer for skill units.

Re-renders SKILL.md and references/examples.md from a unit's unit_pack.json,
using the exact same logic as skill_generator.render_skill_md /
render_examples_md, but without the openai dependency.

unit_pack.json is the single source of truth. Edit it, then run this to keep
SKILL.md and references/examples.md perfectly consistent.

All skill files use CRLF line endings; writes preserve that convention.

Usage:
    python render_units.py check  <skills_dir>      # diff render vs on-disk, no writes
    python render_units.py write  <macro_dir> ...   # normalize JSON + re-render SKILL.md + examples.md
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

NEWLINE = "\r\n"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_crlf(path: Path, text: str) -> None:
    """Write text with CRLF line endings, matching the repo convention."""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(normalized.replace("\n", NEWLINE).encode("utf-8"))


def normalize_json(path: Path) -> bool:
    """Re-dump a JSON file with canonical formatting (indent=2, CRLF, trailing newline).

    Returns True if the file content changed.
    """
    data = load_json(path)
    rendered = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    before = path.read_bytes()
    after = rendered.replace("\n", NEWLINE).encode("utf-8")
    if before != after:
        path.write_bytes(after)
        return True
    return False


def render_list(items: Any) -> str:
    values = items if isinstance(items, list) else [items] if items else []
    if not values:
        return "- None specified."
    return "\n".join(f"- {str(item).strip()}" for item in values if str(item).strip())


def load_micro_lookup(skills_dir: Path) -> dict[str, str]:
    """Map micro id -> human-readable 'Title: decision_variable' from each micro's unit_pack.

    Lets the Expand section render meaningful capability lines instead of opaque ids,
    so the consuming LLM can act on the hint even without a skill registry.
    """
    lookup: dict[str, str] = {}
    if not skills_dir.is_dir():
        return lookup
    for d in skills_dir.glob("micro-*"):
        pp = d / "unit_pack.json"
        if not pp.exists():
            continue
        try:
            pack = load_json(pp)
        except Exception:
            continue
        mid = str(pack.get("id", d.name)).strip()
        title = str(pack.get("title", "")).strip()
        dv = str(pack.get("decision_variable", "")).strip().rstrip(".")
        if title and dv:
            lookup[mid] = f"{title}: {dv}"
        elif title:
            lookup[mid] = title
    return lookup


def render_expand_list(ids: Any, micro_lookup: dict[str, str]) -> str:
    values = [str(x).strip() for x in (ids if isinstance(ids, list) else [ids] if ids else []) if str(x).strip()]
    if not values:
        return "- None specified."
    out = []
    for mid in values:
        desc = micro_lookup.get(mid)
        out.append(f"- {desc} ({mid})" if desc else f"- {mid}")
    return "\n".join(out)


def yaml_safe(value: Any) -> str:
    text = str(value or "").replace('"', "'").strip()
    return f'"{text}"'


def render_skill_md(pack: dict[str, Any], micro_lookup: dict[str, str] | None = None) -> str:
    micro_lookup = micro_lookup or {}
    refs = pack.get("references", {}) if isinstance(pack.get("references"), dict) else {}
    lines = [
        "---",
        f"name: {pack['id']}",
        f"level: {pack.get('level', '')}",
        f"layer: {pack.get('layer', '')}",
        f"family: {yaml_safe(pack.get('family', ''))}",
        f"description: {yaml_safe(pack.get('frontmatter_description') or pack.get('core_question') or pack.get('title'))}",
        "---",
        "",
        f"# {pack.get('title', pack['id'])}",
        "",
        "## Use When",
        render_list(pack.get("use_when")),
        "",
        "## Do Not Use When",
        render_list(pack.get("do_not_use_when")),
        "",
        "## Decision Variable",
        str(pack.get("decision_variable", "")).strip() or "None specified.",
    ]
    if pack.get("level") == "macro":
        lines.extend([
            "",
            "## Direct Route Rule",
            str(pack.get("direct_route_rule", "")).strip() or "None specified.",
            "",
            "## Expand With Micro Units",
            render_expand_list(pack.get("expandable_micro_ids"), micro_lookup),
        ])
    lines.extend([
        "",
        "## Trigger Checklist",
        render_list(pack.get("trigger_checklist")),
        "",
        "## Workflow",
        render_list(pack.get("workflow")),
    ])
    special = pack.get("special_case") if isinstance(pack.get("special_case"), dict) else {}
    if special:
        example = special.get("worked_example", {}) if isinstance(special.get("worked_example"), dict) else {}
        lines.extend([
            "",
            "## Special Case",
            f"**{special.get('title', 'Special case')}**: {special.get('rule', '')}",
        ])
        if example:
            lines.extend([
                "",
                f"Scene: {example.get('scene', '')}",
                f"Question: {example.get('question', '')}",
                f"Answer logic: {example.get('answer_logic', '')}",
            ])
    lines.extend([
        "",
        "## Boundary Exit Rule",
        render_list(pack.get("boundary_exit_rule")),
        "",
        "## References",
        "- See `references/examples.md` for route signals, hard boundaries, and minimal pairs.",
    ])
    if refs.get("route_signal"):
        lines.extend(["", "## Quick Route Signal", str(refs.get("route_signal"))])
    return "\n".join(lines).rstrip() + "\n"


def render_examples_md(pack: dict[str, Any]) -> str:
    refs = pack.get("references", {}) if isinstance(pack.get("references"), dict) else {}
    lines = [
        f"# {pack['id']} Examples and Boundaries",
        "",
        "## Decision Variable",
        str(pack.get("decision_variable", "")).strip() or "None specified.",
        "",
        "## Route Signal",
        str(refs.get("route_signal", "")).strip() or "None specified.",
        "",
        "## Hard Boundary",
        render_list(refs.get("hard_boundary")),
        "",
        "## Shortcut To Avoid",
        render_list(refs.get("shortcut_to_avoid")),
        "",
        "## Common Failure Modes",
        render_list(refs.get("common_failure_modes")),
        "",
        "## Minimal Pair",
    ]
    pairs = refs.get("minimal_pair", [])
    if isinstance(pairs, list) and pairs:
        for item in pairs:
            if isinstance(item, dict):
                lines.append(f"- Case: {item.get('case', '')} | Why: {item.get('why_it_matches', '')}")
            else:
                lines.append(f"- {item}")
    else:
        lines.append("- None specified.")
    lines.extend([
        "",
        "## Boundary Stress Test",
        render_list(refs.get("boundary_stress_test")),
        "",
        "## Generalization Note",
        str(refs.get("generalization_note", "")).strip() or "None specified.",
    ])
    return "\n".join(lines).rstrip() + "\n"


def render_dir(macro_dir: Path, write: bool) -> list[str]:
    pack = load_json(macro_dir / "unit_pack.json")
    micro_lookup = load_micro_lookup(macro_dir.parent)
    diffs = []
    targets = {
        macro_dir / "SKILL.md": render_skill_md(pack, micro_lookup),
        macro_dir / "references" / "examples.md": render_examples_md(pack),
    }
    for path, rendered in targets.items():
        current = path.read_text(encoding="utf-8") if path.exists() else ""
        if current != rendered:
            diffs.append(str(path))
            if write:
                write_crlf(path, rendered)
    return diffs


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 1
    mode = argv[0]
    if mode == "check":
        skills_dir = Path(argv[1])
        macro_dirs = sorted(d for d in skills_dir.glob("macro-*") if d.is_dir())
        any_diff = False
        for d in macro_dirs:
            diffs = render_dir(d, write=False)
            if diffs:
                any_diff = True
                print(f"DIFF {d.name}: " + ", ".join(Path(x).name for x in diffs))
            else:
                print(f"OK   {d.name}")
        return 1 if any_diff else 0
    if mode == "write":
        for arg in argv[1:]:
            d = Path(arg)
            json_changed = []
            for jf in ("unit_pack.json", "validation_items.json"):
                p = d / jf
                if p.exists() and normalize_json(p):
                    json_changed.append(jf)
            diffs = render_dir(d, write=True)
            md_changed = ", ".join(Path(x).name for x in diffs) if diffs else "no md change"
            jc = (" json:[" + ", ".join(json_changed) + "]") if json_changed else ""
            print(f"WROTE {d.name}: {md_changed}{jc}")
        return 0
    print(f"unknown mode: {mode}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
