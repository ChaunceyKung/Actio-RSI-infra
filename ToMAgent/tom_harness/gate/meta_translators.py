"""Translators from each loader's raw metadata to StandardMeta.

Additive module — does NOT modify existing loaders. Call:

    from tom_harness.gate.meta_translators import translate
    std = translate(dataset_name, sample["metadata"])

Returns a StandardMeta. Any field returning None will need LLM fallback
at preprocess time.
"""

from __future__ import annotations

from .standard_meta import StandardMeta


# ─────────────────────────── Hi-ToM ───────────────────────────
def _hitom(raw: dict) -> StandardMeta:
    order = raw.get("question_order", 0)
    deception = bool(raw.get("deception", False))
    if order == 0:
        fb_kind = "none"        # factual retrieval, no belief mismatch
    elif deception:
        fb_kind = "deception"
    else:
        fb_kind = "sally_anne"  # classic unseen-move pattern
    if order >= 3:
        diff = "high"
    elif order >= 2:
        diff = "mid"
    else:
        diff = "low"
    return StandardMeta(
        construct="belief",
        false_belief_kind=fb_kind,
        deception=deception,
        dialogue_format=False,
        answer_type="multi_choice",
        difficulty_hint=diff,
    )


# ─────────────────────────── ToMBench ───────────────────────────
def _tombench(raw: dict) -> StandardMeta:
    ability = raw.get("ability", "")
    task = raw.get("task", "")

    # construct
    if "Emotion" in ability:
        construct = "emotion"
    elif "Intention" in ability:
        construct = "intention"
    elif "Desire" in ability:
        construct = "intention"
    elif "Belief" in ability or "Knowledge" in ability:
        construct = "belief"
    elif "Non-Literal" in ability or "Pragmatic" in ability or "Implicature" in ability:
        construct = "irony"
    else:
        construct = "mixed"

    # false belief kind
    if "Second-order" in ability:
        fb_kind = "sally_anne"  # second-order built atop a Sally-Anne core
    elif "False Belief" in task or "false belief" in ability.lower():
        fb_kind = "sally_anne"
    elif "Faux pas" in ability or "Faux-pas" in task:
        fb_kind = "deception"
    else:
        fb_kind = "none"

    # deception
    deception = (
        "Faux pas" in ability
        or "Faux-pas" in task
        or "Persuasion" in task
        or "Hidden Emotions" in task
    )

    # difficulty
    if "Second-order" in ability:
        diff = "high"
    elif "Faux pas" in ability or "Persuasion" in task:
        diff = "mid"
    else:
        diff = "low"

    return StandardMeta(
        construct=construct,
        false_belief_kind=fb_kind,
        deception=deception,
        dialogue_format=False,
        answer_type="multi_choice",
        difficulty_hint=diff,
    )


# ─────────────────────────── EmoBench ───────────────────────────
def _emobench(raw: dict) -> StandardMeta:
    cat = raw.get("category", "")
    fg = raw.get("finegrained_category", "") or ""
    task = raw.get("task", "")  # EU (Understanding) vs EA (Application)

    if "false_belief" in fg:
        fb_kind = "sally_anne"
    elif "faux_pas" in fg:
        fb_kind = "deception"
    else:
        fb_kind = "none"

    deception = "faux_pas" in fg or "persona" in fg

    # EmoBench is primarily emotion, but some EU subcategories cross into belief
    if cat in {"perspective_taking", "personal_beliefs_and_experiences"}:
        construct = "mixed"     # has belief reasoning under emotion umbrella
    else:
        construct = "emotion"

    diff = "high" if task == "EA" else "mid"

    return StandardMeta(
        construct=construct,
        false_belief_kind=fb_kind,
        deception=deception,
        dialogue_format=False,
        answer_type="multi_choice",
        difficulty_hint=diff,
    )


# ─────────────────────────── ICTBench ───────────────────────────
_ICT_CATEGORY_TO_CONSTRUCT = {
    "intention_recognition":     "intention",
    "cognitive_state_modeling":  "belief",
    "belief_update_tracking":    "belief",
    "perspective_taking":        "belief",
    "emotion_attribution":       "emotion",
    "empathy_modeling":          "emotion",
    "social_norm_reasoning":     "norm",
}


def _ictbench(raw: dict) -> StandardMeta:
    cat = raw.get("category", "")
    construct = _ICT_CATEGORY_TO_CONSTRUCT.get(cat, "mixed")

    # ICTBench scenarios are built around incidents (often lies / hidden motives)
    # but only a subset are deception-driven. Use category as a heuristic.
    deception = cat in {"intention_recognition", "belief_update_tracking"}

    fb_kind = "deception" if deception else "none"

    return StandardMeta(
        construct=construct,
        false_belief_kind=fb_kind,
        deception=deception,
        dialogue_format=False,
        answer_type="multi_choice",
        difficulty_hint="mid",
    )


# ─────────────────────────── CogToM ───────────────────────────
_COGTOM_CAT_TO_CONSTRUCT = {
    "Belief":       "belief",
    "Knowledge":    "belief",
    "Percept":      "belief",
    "Emotion":      "emotion",
    "Desire":       "intention",
    "Intention":    "intention",
    "Non-literal":  "irony",
    "Comprehensive": "mixed",
}


def _cogtom(raw: dict) -> StandardMeta:
    cat = raw.get("category", "")
    sub = raw.get("subcategory", "") or ""
    construct = _COGTOM_CAT_TO_CONSTRUCT.get(cat, "mixed")

    if "False Belief" in sub:
        fb_kind = "sally_anne"
    elif "2nd-Order" in sub or "Second-Order" in sub:
        fb_kind = "sally_anne"
    elif "Pretend" in sub or "Flattery" in sub:
        fb_kind = "deception"
    else:
        fb_kind = "none"

    deception = "Pretend" in sub or "Flattery" in sub or "Deception" in sub

    if "2nd-Order" in sub:
        diff = "high"
    elif "False Belief" in sub:
        diff = "mid"
    else:
        diff = "low"

    return StandardMeta(
        construct=construct,
        false_belief_kind=fb_kind,
        deception=deception,
        dialogue_format=False,
        answer_type="multi_choice",
        difficulty_hint=diff,
    )


# ─────────────────────────── Tactful-ToM ───────────────────────────
def _tactful_tom(raw: dict) -> StandardMeta:
    cat = raw.get("category", "")
    task = raw.get("task", "")
    lie_type = raw.get("lie_type", "")

    # Whole corpus is about lies; non-belief categories also depend on lie context
    if cat == "belief":
        construct = "belief"
    elif cat in {"answerability", "info_accessibility"}:
        construct = "belief"
    elif cat == "liedetectability":
        construct = "intention"
    elif cat == "lieability":
        construct = "intention"
    elif cat == "fact":
        construct = "mixed"     # factual recall
    elif cat == "comprehension":
        construct = "mixed"
    else:
        construct = "intention"

    fb_kind = "deception"        # always lie-driven
    deception = True
    answer_type = "binary" if "binary" in task else "multi_choice"

    return StandardMeta(
        construct=construct,
        false_belief_kind=fb_kind,
        deception=deception,
        dialogue_format=True,    # corpus is dialogue
        answer_type=answer_type,
        difficulty_hint="mid",
    )


# ─────────────────────────── Social-IQA ───────────────────────────
_SOCIALIQA_CAT_TO_CONSTRUCT = {
    "wants":        "intention",
    "needs":        "intention",
    "motivations":  "intention",
    "reactions":    "emotion",
    "effects":      "mixed",
    "descriptions": "mixed",
    "other":        "mixed",
}


def _social_iqa(raw: dict) -> StandardMeta:
    cat = raw.get("category", "")
    return StandardMeta(
        construct=_SOCIALIQA_CAT_TO_CONSTRUCT.get(cat, "mixed"),
        false_belief_kind="none",
        deception=False,
        dialogue_format=False,
        answer_type="multi_choice",
        difficulty_hint="low",
    )


# ─────────────────────────── Dispatcher ───────────────────────────
_TRANSLATORS = {
    "hitom":       _hitom,
    "tombench":    _tombench,
    "emobench":    _emobench,
    "ictbench":    _ictbench,
    "cogtom":      _cogtom,
    "tactful_tom": _tactful_tom,
    "social_iqa":  _social_iqa,
}


def translate(dataset_name: str, raw_meta: dict) -> StandardMeta:
    fn = _TRANSLATORS.get(dataset_name)
    if fn is None:
        return StandardMeta()  # all None → LLM fallback territory
    return fn(raw_meta)


def supported_datasets() -> list[str]:
    return sorted(_TRANSLATORS.keys())
