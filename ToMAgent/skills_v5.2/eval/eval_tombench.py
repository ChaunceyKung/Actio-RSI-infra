"""
ToMBench evaluation runner for skills_v5.

## Pipeline

  Stage 1 (route prep) : micro-01 (task routing) is injected as the router's
                         system prompt. Always on.
  Stage 2 (route)      : One of 5 modes (see below) picks 0+ skills.
  Stage 3 (solve +     : Picked skills are injected as the solver's system
   reroute self-fix)     prompt. With --reroute-budget > 0, the solver FIRST
                         checks each injected skill's boundary exits; on a misfit
                         it emits `REROUTE: <skill-id> | <capability>` naming the
                         skill that does not fit. That skill is then dropped and
                         never answers: with budget left it is replaced via a
                         layer-aware re-pick (micro exit keeps the macro and re-
                         picks its expandable subset; macro exit re-runs the full
                         two-stage route); with no budget left the solver commits
                         using the remaining skills. Bounded by the budget.
                         Otherwise the solver returns a draft answer.
  Stage 4 (review)     : If --review-mode on, micro-02 + micro-03 + micro-04
                         are injected together along with the draft answer,
                         and the LLM is asked to confirm or revise. The final
                         letter is the one the reviewer outputs.

  When --review-mode is on, BOTH the draft and the final answer are recorded,
  so the lift from review can be measured without a second run. reroute_count
  and the initial vs final skill set are recorded for every item.

## Thinking mode

  All models are driven NON-THINKING: every request carries
  extra_body={"enable_thinking": False}. On providers that gate native
  reasoning on this flag (e.g. Qwen-style endpoints) the model answers
  directly, keeping the eval comparable across models.

## Routing modes (--route-mode)

  baseline      : Stage 2 picks no skill. Stages 1 and 4 still run if review
                  is on. 1 (or 2 if review on) LLM calls.
  macro_only    : LLM picks 0+ macros from 20.
  micro_only    : LLM picks 0+ non-L0 micros from the 52 (micro-05..56).
                  L0 micros (01..04) are never candidates — they have their
                  own stages.
  hierarchical  : Step 2a picks 0+ macros. Step 2b picks 0+ micros. The
                  step 2b candidate pool depends on step 2a:
                    - if step 2a picked 1+ macros: pool = UNION of their
                      expandable_micro_ids (always L0-free);
                    - if step 2a picked NONE: pool = all 52 non-L0 micros
                      (degenerates to micro_only-style selection).
  flat_all      : LLM sees all 72 candidates (20 macros + 52 non-L0 micros).

Every routing step explicitly allows the LLM to answer "none" (meaning the
question does not need any skill from the library).

## Injection mode (--inject-mode)

  Controls how ALL skill content (L0 stages 1 & 4 + the routed skills in
  stage 3) is rendered. BOTH modes are value-curated (never a raw dump): routing-
  time signals (use_when / trigger_checklist / route_signal) and maintainer
  metadata (notes / validation_seed / hard_boundary) are excluded from both,
  because over-long skill context dilutes the model's judgement.

  light : highest-ROI solve-time core — decision_variable + direct_route_rule
          (macro) + workflow + special_case.worked_example + common_failure_modes
          + shortcut_to_avoid + boundary_exit_rule.
  full  : light + value-curated discrimination/transfer — minimal_pair +
          do_not_use_when + generalization_note.

  light vs full is thus a clean ablation of whether the extra discrimination/
  transfer content raises accuracy or merely dilutes it.

## Combinations

  4 routing modes (excluding baseline) × 2 injection modes = 8 experimental
  conditions. Plus baseline = 9 runs to fully compare.

## Answer format (single- and multi-select, any number of options)

  An answer is scored as a SET of option keys, so >4 options and multi-answer
  questions are supported. Each item resolves an answer_mode — single / multi /
  auto — via: an explicit --answer-mode override, else a per-item question-type
  field (题型 / answer_type / multiple / …, bilingual), else gold cardinality,
  else 'auto' (the model decides). The solver/reviewer prompts list the option
  letters from the item's own options and ask for one letter (single), all
  correct letters comma-separated (multi), or one-or-more (auto). Scoring is
  exact key-set match; per-item Jaccard is also recorded.

## Per-item output

  Each row in results.jsonl has: idx, task, ability, lang, gold, pred,
  correct, gold_n, jaccard, picked_skills (list), reroute_count,
  initial_picked (list), latency_s, error. (With --review-mode on, draft_pred /
  draft_correct / review_changed and the reasoning fields are added.) `gold` and
  `pred` are canonical comma-joined keys (e.g. "A" or "A,C").

## API

  OpenAI-compatible client.chat.completions.create with the same env vars as
  the rest of skills_v5:
    SKILL_V5_API_KEY / OPENAI_API_KEY  (required)
    SKILL_V5_BASE_URL                  (default: https://api.openai.com/v1)
    SKILL_V5_MODEL                     (default: gpt-4o-mini)

## Datasets

  By default the runner loads data/ToMBench_<lang>.jsonl. Point it at ANY other
  MCQ jsonl dataset with --data (absolute or relative path); records are
  normalized onto the internal schema, so field-name aliases
  (story/context/passage, question/query/prompt, options/choices,
  gold/answer/label, task/category, ability, lang), dict-or-list options, and a
  gold given as a letter / numeric index / option text are all accepted. Use
  --dataset-name to label the run dir, and --gold-index-base {0,1} when gold is
  a numeric index. >4 options and multi-answer questions are supported: gold may
  be a list (["A","C"]) or a delimited/concatenated string ("A,C" / "AC"), and a
  per-item question-type field (题型 / answer_type / multiple / …) or
  --answer-mode selects the single/multi framing. Add new datasets without
  touching this file.

## Usage

  python eval_tombench.py --route-mode baseline      --lang en --limit 100
  python eval_tombench.py --route-mode macro_only    --inject-mode light --lang en --workers 8
  python eval_tombench.py --route-mode hierarchical  --inject-mode full  --lang zh --workers 8
  python eval_tombench.py --route-mode hierarchical  --data D:/datasets/my_tom_set.jsonl --workers 8
  python eval_tombench.py --route-mode flat_all      --data ./data/custom.jsonl --dataset-name custom --gold-index-base 1

Outputs land in eval/runs/<auto_run_id>/.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, asdict
from functools import lru_cache
from pathlib import Path
from typing import Any

try:
    from openai import OpenAI
except ImportError:
    print("Install: pip install openai", file=sys.stderr)
    raise

ROOT = Path(__file__).resolve().parent.parent  # skills_v5/
SKILLS_DIR = ROOT / "skills"
DATA_DIR = ROOT / "data"
EVAL_DIR = ROOT / "eval"
RUNS_DIR = EVAL_DIR / "runs"

DEFAULT_MODEL = os.environ.get("SKILL_V5_MODEL", "gpt-4o-mini")
DEFAULT_BASE_URL = os.environ.get(
    "SKILL_V5_BASE_URL", os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
)


# --------------------------------------------------------------------------
# Skill loading
# --------------------------------------------------------------------------
_SKILL_MD_CACHE: dict[str, str] = {}
_SKILL_PACK_CACHE: dict[str, dict] = {}


def load_skill_md(skill_id: str) -> str:
    if skill_id not in _SKILL_MD_CACHE:
        _SKILL_MD_CACHE[skill_id] = (SKILLS_DIR / skill_id / "SKILL.md").read_text(encoding="utf-8")
    return _SKILL_MD_CACHE[skill_id]


def load_skill_pack(skill_id: str) -> dict:
    if skill_id not in _SKILL_PACK_CACHE:
        _SKILL_PACK_CACHE[skill_id] = json.loads(
            (SKILLS_DIR / skill_id / "unit_pack.json").read_text(encoding="utf-8")
        )
    return _SKILL_PACK_CACHE[skill_id]


def _skill_title(skill_id: str) -> str:
    """Human-readable capability name for a skill id (falls back to the id)."""
    try:
        return load_skill_pack(skill_id).get("title", skill_id) or skill_id
    except Exception:
        return skill_id


def list_macros() -> list[str]:
    return sorted(d.name for d in SKILLS_DIR.iterdir() if d.is_dir() and d.name.startswith("macro-"))


def list_all_micros() -> list[str]:
    return sorted(d.name for d in SKILLS_DIR.iterdir() if d.is_dir() and d.name.startswith("micro-"))


L0_MICROS = ["micro-01", "micro-02", "micro-03", "micro-04"]
L0_ROUTE = "micro-01"                                  # injected at stage 1
L0_REVIEW = ["micro-02", "micro-03", "micro-04"]       # injected at stage 4


def list_non_l0_micros() -> list[str]:
    """All micros except L0 (meta-control). 52 candidates."""
    return [m for m in list_all_micros() if m not in set(L0_MICROS)]


# --------------------------------------------------------------------------
# Skill summary / rendering
# --------------------------------------------------------------------------
@lru_cache(maxsize=None)
def router_summary(skill_id: str) -> str:
    """Compact one-block summary used in router prompts. ~5-8 lines.
    Cached: the underlying pack is static for the whole run, and flat_all
    renders all 72 candidate summaries on every item."""
    pack = load_skill_pack(skill_id)
    parts = [f"[{skill_id}] {pack.get('title', '')}",
             f"  decision_variable: {pack.get('decision_variable', '')}"]
    if pack.get("direct_route_rule"):
        parts.append(f"  direct_route_rule: {pack['direct_route_rule']}")
    use_when = pack.get("use_when") or []
    if use_when:
        parts.append("  use_when: " + " | ".join(use_when))
    do_not = pack.get("do_not_use_when") or []
    if do_not:
        parts.append("  do_not_use_when: " + " | ".join(do_not))
    return "\n".join(parts)


_INTERNAL_ID_RE = re.compile(r"\b(?:micro|macro)-\d{2}\b")


def _scrub_internal_ids(text: str) -> str:
    """Replace any `micro-XX` / `macro-XX` mention with a generic label so
    internal naming does not leak when content is shown as a guide rather
    than as a labelled candidate."""
    return _INTERNAL_ID_RE.sub("a neighboring skill", text)


# Injection field profiles (both are VALUE-CURATED — never a raw dump, because
# over-long skill context dilutes the model's judgement):
#   light = highest-ROI solve-time core: decision_variable + direct_route_rule
#           (macro) + workflow + worked_example + common_failure_modes +
#           shortcut_to_avoid + boundary_exit_rule.
#   full  = light + value-curated discrimination/transfer: minimal_pair +
#           do_not_use_when + generalization_note.
# Routing-time signals (use_when / trigger_checklist / route_signal) and
# maintainer metadata (notes / validation_seed / hard_boundary) are omitted from
# BOTH: at solve time they add tokens without improving the answer. light vs full
# is therefore a clean ablation of whether the extra discrimination/transfer
# content helps or merely dilutes.
def _render_from_pack(skill_id: str, mode: str, strip_id: bool = False) -> str:
    """Render a skill from unit_pack.json with an explicit, value-curated field
    set. `mode` is 'light' or 'full'. If strip_id, omit the `[id]` label and the
    boundary-exit block (used when a skill is injected as a guide rather than a
    labelled candidate), and scrub any internal ids from retained text."""
    pack = load_skill_pack(skill_id)
    refs = pack.get("references") or {}
    full = (mode == "full")
    parts: list[str] = []
    if not strip_id:
        parts.append(f"### [{skill_id}] {pack.get('title', '')}")
    elif pack.get("title"):
        parts.append(f"### {pack.get('title')}")
    if pack.get("decision_variable"):
        parts.append(f"**Decision variable**: {pack['decision_variable']}")
    if pack.get("direct_route_rule"):  # macros only
        parts.append(f"**Direct route rule**: {pack['direct_route_rule']}")
    wf = pack.get("workflow") or []
    if wf:
        parts.append("**Workflow**:\n" + "\n".join(f"- {s}" for s in wf))
    sc = pack.get("special_case") or {}
    if sc.get("rule"):
        block = [f"**Special case — {sc.get('title', '').strip()}**: {sc['rule']}"]
        we = sc.get("worked_example") or {}
        if we.get("scene"):
            block.append(f"  - Scene: {we.get('scene', '')}")
            block.append(f"  - Question: {we.get('question', '')}")
            block.append(f"  - Logic: {we.get('answer_logic', '')}")
        parts.append("\n".join(block))
    if full:  # discrimination: near-miss pairs
        mp = refs.get("minimal_pair") or []
        if mp:
            lines = ["**Minimal pairs (near-miss discrimination)**:"]
            for it in mp:
                if isinstance(it, dict):
                    lines.append(f"- {it.get('case', '')} — {it.get('why_it_matches', '')}")
                else:
                    lines.append(f"- {it}")
            parts.append("\n".join(lines))
    cfm = refs.get("common_failure_modes") or []
    if cfm:
        parts.append("**Common failure modes (do NOT make these)**:\n"
                     + "\n".join(f"- {s}" for s in cfm))
    sta = refs.get("shortcut_to_avoid") or []
    if sta:
        parts.append("**Shortcuts to avoid**:\n" + "\n".join(f"- {s}" for s in sta))
    if full:
        dnu = pack.get("do_not_use_when") or []
        if dnu:
            parts.append("**Do not use when**:\n" + "\n".join(f"- {s}" for s in dnu))
    if not strip_id:
        bex = pack.get("boundary_exit_rule") or []
        if bex:
            parts.append("**Boundary exits (if one matches, this skill does NOT "
                         "fit — request a re-route)**:\n"
                         + "\n".join(f"- {s}" for s in bex))
    if full:
        gn = (refs.get("generalization_note") or "").strip()
        if gn:
            parts.append(f"**Generalization**: {gn}")
    out = "\n\n".join(parts)
    if strip_id:
        out = _scrub_internal_ids(out)
    return out


def render_skill(skill_id: str, inject_mode: str, strip_id: bool = False) -> str:
    if inject_mode in ("full", "light"):
        return _render_from_pack(skill_id, inject_mode, strip_id=strip_id)
    raise ValueError(f"unknown inject_mode={inject_mode}")


# --------------------------------------------------------------------------
# LLM client
# --------------------------------------------------------------------------
class LLMClient:
    def __init__(self, model: str, base_url: str, api_key: str,
                 timeout: int = 120, temperature: float = 0.0,
                 top_p: float = 1.0,
                 max_attempts: int = 3, retry_backoff_cap: int = 8,
                 enable_thinking: bool = False):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.temperature = temperature
        self.top_p = top_p
        self.max_attempts = max(1, int(max_attempts))
        self.retry_backoff_cap = max(0, int(retry_backoff_cap))
        # All models are driven in NON-THINKING mode by default: every request
        # carries extra_body={"enable_thinking": False}. Providers that gate a
        # model's native reasoning on this flag (e.g. Qwen-style endpoints) then
        # answer directly; this keeps the eval comparable across models.
        self.enable_thinking = bool(enable_thinking)
        self.client = OpenAI(api_key=api_key, base_url=self.base_url, timeout=timeout)

    def chat(self, system: str, user: str, max_tokens: int) -> str:
        for attempt in range(1, self.max_attempts + 1):
            try:
                resp = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "system", "content": system},
                              {"role": "user", "content": user}],
                    temperature=self.temperature,
                    top_p=self.top_p,
                    max_completion_tokens=max_tokens,
                    extra_body={"enable_thinking": self.enable_thinking},
                )
                msg = resp.choices[0].message
                content = msg.content
                if isinstance(content, list):
                    content = "\n".join(
                        (p.text if hasattr(p, "text") else p.get("text", "")) for p in content
                    )
                return (content or "").strip()
            except Exception:
                if attempt >= self.max_attempts:
                    raise
                if self.retry_backoff_cap > 0:
                    time.sleep(min(2 ** attempt, self.retry_backoff_cap))
        return ""


# --------------------------------------------------------------------------
# Prompt builders — router
# --------------------------------------------------------------------------
def format_options(options: dict) -> str:
    return "\n".join(f"{k}. {v}" for k, v in sorted(options.items()))


def _scene_block(item: dict) -> str:
    lang = item["lang"]
    story = (item.get("story") or "").strip()
    question = item.get("question") or ""
    if lang == "zh":
        return f"故事:\n{story}\n\n问题:{question}" if story else f"问题:{question}"
    return f"Story:\n{story}\n\nQuestion: {question}" if story else f"Question: {question}"


SINGLE_RULES_EN = (
    "Output ONLY one id like macro-XX, OR the literal word `none` if no skill "
    "in the list fits this scene. No explanation, no quotes."
)
SINGLE_RULES_ZH = (
    "只输出一个 id (形如 macro-XX),或者字面量 `none`(如果列表里没有匹配)。"
    "不要解释,不要引号。"
)
MULTI_RULES_EN = (
    "Output a JSON array of ids you want to use, e.g. [\"micro-12\", \"micro-23\"]. "
    "If none of the skills apply, output [\"none\"]. No explanation."
)
MULTI_RULES_ZH = (
    "输出一个 JSON 数组,内容是你想使用的 id,例如 [\"micro-12\", \"micro-23\"]。"
    "如果都不适用,输出 [\"none\"]。不要解释。"
)


def build_router_prompt(item: dict, candidates: list[str], multi: bool,
                        header: str, inject_mode: str,
                        hint: str | None = None) -> tuple[str, str]:
    """Generic router prompt. micro-01 (task routing) is injected as the
    system prompt prefix (rendered per --inject-mode), so the router sees the
    L0 routing playbook in addition to the candidate summaries.

    If `hint` is given (a re-route), a misfit note is prepended to the user
    prompt so the router re-selects toward the capability the solver said the
    scene actually needs."""
    lang = item["lang"]
    blocks = "\n\n".join(router_summary(c) for c in candidates)
    rules = (MULTI_RULES_ZH if multi else SINGLE_RULES_ZH) if lang == "zh" \
            else (MULTI_RULES_EN if multi else SINGLE_RULES_EN)
    l0_block = render_skill(L0_ROUTE, inject_mode, strip_id=True)
    misfit = ""
    if hint:
        misfit = (f"注意:之前所选 skill 经判定与本题不匹配。本题真正需要的能力是:"
                  f"{hint}。请从候选中选出匹配该能力的 skill。\n\n") if lang == "zh" else (
                  f"NOTE: the previously selected skill was judged a MISFIT for "
                  f"this scene. The scene actually needs: {hint}. Pick the "
                  f"candidate skill(s) that match that capability.\n\n")
    if lang == "zh":
        sys_p = (
            "你是一个社会认知技能路由器。先阅读下面的任务路由指南,"
            "然后从候选技能中选择最合适的。\n\n"
            "## 任务路由指南\n\n" + l0_block + "\n\n"
            "## 路由规则\n" + rules
        )
        user = f"{misfit}{_scene_block(item)}\n\n候选 {header}:\n{blocks}\n\n你的选择:"
    else:
        sys_p = (
            "You are a social-cognition skill router. First read the task-"
            "routing playbook below, then select the best candidate skill(s).\n\n"
            "## Task Routing Playbook\n\n" + l0_block + "\n\n"
            "## Routing rules\n" + rules
        )
        user = f"{misfit}{_scene_block(item)}\n\nCandidate {header}:\n{blocks}\n\nYour choice:"
    return sys_p, user


# --------------------------------------------------------------------------
# Prompt builders — solver
# --------------------------------------------------------------------------
def _answer_letters(options: dict) -> tuple[str, str]:
    """Return (letter_list, multi_example) derived from THIS item's option keys,
    e.g. ('A/B/C/D/E', 'A,C'). Falls back to A-D if options are missing."""
    keys = sorted(options.keys()) or list("ABCD")
    letters = "/".join(keys)
    ex = ",".join(keys[:2]) if len(keys) >= 2 else (keys[0] if keys else "A")
    return letters, ex


def _answer_spec(options: dict, answer_mode: str, lang: str) -> str:
    """Bilingual placeholder describing what the ANSWER must contain, with the
    letter list taken from the item's options and the single/multi/auto framing."""
    letters, ex = _answer_letters(options)
    if lang == "zh":
        if answer_mode == "multi":
            return f"<所有正确字母,取自 {letters},逗号分隔,如 {ex}>"
        if answer_mode == "auto":
            return f"<正确字母,取自 {letters};仅一个正确就给一个,有多个正确就逗号分隔多个>"
        return f"<从 {letters} 中选一个字母>"
    if answer_mode == "multi":
        return f"<all correct letters from {letters}, comma-separated, e.g. {ex}>"
    if answer_mode == "auto":
        return (f"<the correct letter(s) from {letters}: one if only one is "
                f"correct, otherwise several comma-separated>")
    return f"<one letter from {letters}>"


def build_solver_prompt(item: dict, picked: list[str], inject_mode: str,
                        with_reasoning: bool,
                        allow_reroute: bool = False) -> tuple[str, str]:
    """If with_reasoning is False, the solver is told to output ONLY a letter.
    If True, the solver must output a structured response of REASONING + ANSWER
    so a downstream reviewer can audit the chain rather than just the letter.

    If allow_reroute is True (and skills are injected), the solver is told to
    first check the selected skill's boundary exits and, on a misfit, emit a
    single `REROUTE: <capability>` line instead of answering — so the pipeline
    can re-select a better-fitting skill before committing to an answer."""
    lang = item["lang"]
    if picked:
        rendered = "\n\n---\n\n".join(render_skill(s, inject_mode) for s in picked)
        if lang == "zh":
            base = (
                "你正在使用一套社会心智 skill 库求解题目。下面是被选中的 skill:\n\n"
                + rendered + "\n\n严格按照所选 skill 的 workflow / boundary 推理。"
            )
        else:
            base = (
                "You are solving a social-cognition problem with a skill library. "
                "Selected skills:\n\n" + rendered +
                "\n\nReason strictly using the selected skill's workflow / boundary."
            )
        if allow_reroute:
            if lang == "zh":
                base += (
                    "\n\n解题前,先逐个用所选 skill 的 \"Boundary exits\" 对照本题。"
                    "若某个所选 skill 命中其某条退出条件(即它与本题不匹配),不要作答,"
                    "只输出一行:\n"
                    "REROUTE: <触发退出的 skill 标号(取自其标题方括号,如 micro-23)>"
                    " | <本题真正需要的能力,用文字描述>\n"
                    "只有当所选 skill 全部适配时,才继续解题并按下面的格式作答。"
                )
            else:
                base += (
                    "\n\nBefore solving, check EACH selected skill's \"Boundary "
                    "exits\" against this scene. If one selected skill matches an "
                    "exit condition — it does NOT fit — do NOT answer; output "
                    "exactly one line:\n"
                    "REROUTE: <the id of the misfitting skill (from its title's "
                    "square brackets, e.g. micro-23)> | <the capability this scene "
                    "actually needs, in plain words>\n"
                    "Only if ALL selected skills truly fit, proceed and answer in "
                    "the format below."
                )
    else:
        if lang == "zh":
            base = "你是一个谨慎的选择题解题器。"
        else:
            base = "You are a careful multiple-choice solver."

    answer_mode = item.get("answer_mode", "single")
    spec = _answer_spec(item["options"], answer_mode, lang)
    if with_reasoning:
        if lang == "zh":
            sys_p = base + (
                "\n\n输出格式必须严格遵守(只有两行):\n"
                "REASONING: <2-6 句话,且必须包含三点——"
                "(a) 引用或点名原文中真正决定答案的证据,并把原文证据与你的推断分开;"
                "(b) 说明依据所选 skill 某一步得出的关键推断;"
                "(c) 指出你排除掉的最强备选项及排除理由>\n"
                f"ANSWER: {spec}\n"
                "不要在这两行之外输出任何其他内容。"
            )
            user_tail = "请按格式输出 REASONING 与 ANSWER:"
        else:
            sys_p = base + (
                "\n\nOutput format MUST be exactly two lines:\n"
                "REASONING: <2-6 sentences that MUST include three things: "
                "(a) quote or name the decisive evidence actually in the text, "
                "keeping textual evidence separate from your inference; "
                "(b) state the key inference drawn from a specific step of the "
                "selected skill; "
                "(c) name the strongest competing option you ruled out and why>\n"
                f"ANSWER: {spec}\n"
                "Do not output anything else."
            )
            user_tail = "Output REASONING and ANSWER per the format:"
    else:
        if lang == "zh":
            sys_p = base + f"\n\n最后只输出一行:\nANSWER: {spec}\n不要解释。"
            user_tail = "请按格式只输出 ANSWER 行:"
        else:
            sys_p = base + f"\n\nOutput ONLY one line:\nANSWER: {spec}\nNo explanation."
            user_tail = "Output only the ANSWER line:"

    if lang == "zh":
        user = f"{_scene_block(item)}\n\n选项:\n{format_options(item['options'])}\n\n{user_tail}"
    else:
        user = f"{_scene_block(item)}\n\nOptions:\n{format_options(item['options'])}\n\n{user_tail}"
    return sys_p, user


def build_review_prompt(item: dict, picked: list[str], draft_reasoning: str,
                        draft_letter: str, inject_mode: str
                        ) -> tuple[str, str]:
    """Stage 4 review. The reviewer sees the L0 audit playbook (micro-02/03/04),
    the capability names of the skills the solver used, and the solver's draft
    reasoning + draft answer. The draft is the DEFAULT (it was made with an
    appropriate skill), but the reviewer must actively scrutinize it — verify
    each cited cue against the text, stress-test the strongest alternative, and
    check for bias — and keep the draft only if it withstands scrutiny, changing
    it only on a specific verifiable flaw. Outputs REASONING + ANSWER."""
    lang = item["lang"]
    spec = _answer_spec(item["options"], item.get("answer_mode", "single"), lang)
    l0_block = "\n\n---\n\n".join(render_skill(m, inject_mode, strip_id=True) for m in L0_REVIEW)
    # Show the reviewer the capability NAMES, not bare ids (which it cannot interpret).
    picks_str = (", ".join(_skill_title(s) for s in picked) if picked
                 else ("(none)" if lang == "en" else "(无)"))
    if lang == "zh":
        sys_p = (
            "你的任务是审查另一个模型(下称 solver)对一道社会认知题给出的初稿(draft)"
            "推理与答案。draft 已基于合适的 skill 作答,默认它是对的——但你要带着审查的"
            "态度逐项核查,而不是盲目信任。下面提供三条审查工具:\n\n"
            + l0_block + "\n\n"
            "请逐项做实查(避免\"看起来没问题\"):\n"
            "1) 核对证据:draft 引用的每条证据,是否逐字出现在故事原文里?有没有把推断或"
            "常识当成原文事实,或用了角色根本无法获得的(全知)信息?\n"
            "2) 压测备择:点名最有迷惑性的另一个选项,并给出它为何不如 draft 所选的具体"
            "理由;若给不出这样的理由,说明该备择可能才对,需重新考虑。\n"
            "3) 偏误检查:draft 是否选了\"现实真实状态\"而非\"角色所相信的\"(现实偏差),"
            "是否被结果偏差或道德直觉带偏?\n\n"
            "判定:三项都通过(draft 经得起推敲)→沿用 draft 的答案;只有当你查出具体、"
            "可核实的问题(某条证据并不在原文、出现明显更优的备择、或某种偏误)时,才"
            "修正答案。\n\n"
            "输出格式必须严格遵守(只有两行):\n"
            "REASONING: <2-6 句话,写出你实际做过的核查:引用你核对过的关键证据、点名你"
            "压测的最强备择及结论、偏误检查结果,并说明你为何沿用或修正>\n"
            f"ANSWER: {spec}\n"
            "不要在这两行之外输出任何其他内容。"
        )
        user = (
            f"{_scene_block(item)}\n\n"
            f"选项:\n{format_options(item['options'])}\n\n"
            f"Solver 选用的辅助技能: {picks_str}\n\n"
            f"Solver 的初稿推理:\n{draft_reasoning or '(未给出)'}\n\n"
            f"Solver 的初稿答案: {draft_letter or '(未给出)'}\n\n"
            "请按格式输出你的 REASONING 与最终 ANSWER:"
        )
    else:
        sys_p = (
            "Your task is to review another model's (the solver's) DRAFT reasoning "
            "and answer to a social-cognition question. The draft was produced "
            "with an appropriate skill, so it is the default — but scrutinize it "
            "item by item; do NOT trust it blindly. Three review tools follow:\n\n"
            + l0_block + "\n\n"
            "Actually perform each check (avoid \"looks fine\"):\n"
            "1) Verify evidence: for EACH cue the draft cites, does it appear "
            "verbatim in the story? Is any inference or commonsense stated as if it "
            "were a textual fact, or does the draft use information a character "
            "could not access (omniscience)?\n"
            "2) Stress-test the alternative: name the most tempting OTHER option "
            "and give the concrete reason it is worse than the draft's choice; if "
            "you cannot give such a reason, that alternative may be correct — "
            "reconsider.\n"
            "3) Bias check: did the draft pick the real state instead of what the "
            "character believes (reality bias), or get pulled by outcome bias or a "
            "moral-intuition shortcut?\n\n"
            "Decision: if the draft passes all three (it withstands scrutiny), KEEP "
            "its answer. Change it ONLY when you find a specific, verifiable problem "
            "(a cited cue that is not in the text, a clearly better alternative, or "
            "a named bias) — then give the corrected answer.\n\n"
            "Output format MUST be exactly two lines:\n"
            "REASONING: <2-6 sentences reporting the checks you actually ran: the "
            "key evidence you verified, the strongest alternative you stress-tested "
            "and its outcome, the bias-check result; then why you kept or revised>\n"
            f"ANSWER: {spec}\n"
            "Do not output anything else."
        )
        user = (
            f"{_scene_block(item)}\n\n"
            f"Options:\n{format_options(item['options'])}\n\n"
            f"Solver's selected helper skills: {picks_str}\n\n"
            f"Solver's draft reasoning:\n{draft_reasoning or '(none)'}\n\n"
            f"Solver's draft answer: {draft_letter or '(none)'}\n\n"
            "Output REASONING and the FINAL ANSWER per the format:"
        )
    return sys_p, user


# --------------------------------------------------------------------------
# Output parsing
# --------------------------------------------------------------------------
ID_RE = re.compile(r"(macro|micro)-(\d{1,2})", re.I)
ANSWER_MARK_RE = re.compile(r"(?im)^\s*ANSWER\s*[:：]\s*(.+)$")
REASONING_LINE_RE = re.compile(r"(?ims)^\s*REASONING\s*[:：]\s*(.+?)(?=^\s*ANSWER\s*[:：]|\Z)")
REROUTE_LINE_RE = re.compile(r"(?im)^\s*REROUTE\s*[:：]\s*(.+?)\s*$")
_TOKEN_RE = re.compile(r"[A-Za-z]+|\d+")


def parse_reroute(text: str, picked: set[str] | None = None) -> tuple[str, str]:
    """Parse a solver misfit signal. Returns (rejected_skill_id, capability):
      - capability: the capability the scene actually needs, in plain words
        ('' if the solver did not signal a misfit -> no reroute);
      - rejected_skill_id: the injected skill the solver said misfits, normalized
        and validated against `picked` ('' if not identifiable, so the caller
        falls back to dropping ALL picked skills).
    If the reply also contains an ANSWER line the model hedged — prefer the
    answer and do NOT re-route (returns ('', ''))."""
    if not text:
        return ("", "")
    m = REROUTE_LINE_RE.search(text)
    if not m:
        return ("", "")
    if ANSWER_MARK_RE.search(text):
        return ("", "")
    body = m.group(1).strip()
    # Format: "REROUTE: <id> | <capability>". Split structurally on the pipe so
    # any skill id mentioned inside the capability text can never be mistaken for
    # the misfit. The id is matched ANCHORED at the head's front (it is always
    # first per the format), so an off-format reply that puts the capability —
    # possibly containing an id — before/instead of the pipe is left intact.
    parts = re.split(r"[|｜]", body, maxsplit=1)
    head, tail = parts[0], (parts[1] if len(parts) > 1 else "")
    rid = ""
    head_clean = head.lstrip(" [\t")                 # tolerate [micro-23] wrapping
    idm = ID_RE.match(head_clean)
    if idm:
        cand = f"{idm.group(1).lower()}-{int(idm.group(2)):02d}"
        if picked is None or cand in picked:
            rid = cand
        head_rest = head_clean[idm.end():]
    else:
        head_rest = head
    cap = (tail if tail.strip() else head_rest).strip(" |｜:：-[]\t").strip()
    return (rid, cap)


def _keys_in(region: str, keyset: set[str]) -> list[str]:
    """Extract option keys appearing in `region`, order-preserving, deduped.
    A run of letters where every char is a key (e.g. 'AC') is split into keys,
    so concatenated multi-answers are recovered."""
    found: list[str] = []
    for tok in _TOKEN_RE.findall(region):
        u = tok.upper()
        if u in keyset:
            found.append(u)
        elif tok.isalpha() and len(tok) > 1 and all(c.upper() in keyset for c in tok):
            found.extend(c.upper() for c in tok)
    seen: set[str] = set()
    out: list[str] = []
    for k in found:
        if k not in seen:
            seen.add(k)
            out.append(k)
    return out


def extract_answer_set(text: str, options: dict, multi: bool) -> set[str]:
    """Parse the answer as a SET of option keys, constrained to THIS item's
    option keys (supports >4 options and multi-select). Robust to chatty output:
      1) prefer the `ANSWER:` line content;
      2) else the last non-empty line (single -> last key, avoiding the
         left-most-letter trap);
      3) else the whole text;
      4) else match the region against the option TEXTS.
    For single-answer items returns a 1-element set (or empty if unparsable)."""
    if not text:
        return set()
    keyset = set(options.keys()) or set("ABCD")
    m = ANSWER_MARK_RE.search(text)
    if m:
        keys = _keys_in(m.group(1), keyset)
        if keys:
            return set(keys) if multi else {keys[0]}
    lines = [ln for ln in text.strip().splitlines() if ln.strip()]
    if lines:
        keys = _keys_in(lines[-1], keyset)
        if keys:
            return set(keys) if multi else {keys[-1]}
    keys = _keys_in(text, keyset)
    if keys:
        return set(keys) if multi else {keys[-1]}
    region = (m.group(1) if m else (lines[-1] if lines else text)).strip().lower()
    if region:
        hit = [k for k, v in options.items()
               if str(v).strip() and str(v).strip().lower() in region]
        if hit:
            return set(hit) if multi else {hit[0]}
    return set()


def extract_reasoning_and_answer(text: str, options: dict, multi: bool) -> tuple[str, set[str]]:
    """Parse a structured `REASONING: ...\\nANSWER: X` reply into (reasoning,
    answer-key-set). Falls back to the body before the ANSWER line (or the whole
    text) for the reasoning, and to extract_answer_set for the keys."""
    if not text:
        return "", set()
    pred = extract_answer_set(text, options, multi)
    am = REASONING_LINE_RE.search(text)
    if am:
        reasoning = am.group(1).strip()
    else:
        mk = ANSWER_MARK_RE.search(text)
        reasoning = text[:mk.start()].strip() if mk else text.strip()
    return reasoning, pred


def _norm_id(prefix: str, num: str) -> str:
    return f"{prefix.lower()}-{int(num):02d}"


def parse_multi_ids(text: str, valid: set[str]) -> list[str]:
    """Return the valid skill ids named in `text` (order-preserving, deduped).
    Empty if none. Ids are extracted FIRST, so a stray word 'none' in a reply
    that also names a real id (e.g. 'none of these except macro-03') no longer
    wipes the pick."""
    if not text:
        return []
    out: list[str] = []
    seen: set[str] = set()
    for m in ID_RE.finditer(text):
        pid = _norm_id(m.group(1), m.group(2))
        if pid in valid and pid not in seen:
            seen.add(pid)
            out.append(pid)
    return out


def parse_single_id(text: str, valid: set[str]) -> str:
    """Returns the first valid picked id or '' if none."""
    ids = parse_multi_ids(text, valid)
    return ids[0] if ids else ""


def _jaccard(a: set[str], b: set[str]) -> float:
    """|a ∩ b| / |a ∪ b|; 1.0 when both empty. Diagnostic for multi-answer."""
    if not a and not b:
        return 1.0
    u = a | b
    return len(a & b) / len(u) if u else 1.0


# --------------------------------------------------------------------------
# Routing strategies
# --------------------------------------------------------------------------
@dataclass
class TokenBudget:
    router: int = 128
    solver: int = 2048
    reviewer: int = 2048


def route_macro_only(item: dict, client: LLMClient, inject_mode: str,
                     tb: TokenBudget) -> list[str]:
    macros = list_macros()
    sys_p, user = build_router_prompt(item, macros, multi=True, header="macros", inject_mode=inject_mode)
    out = client.chat(sys_p, user, max_tokens=tb.router)
    return parse_multi_ids(out, set(macros))


def route_micro_only(item: dict, client: LLMClient, inject_mode: str,
                     tb: TokenBudget) -> list[str]:
    """Candidates are the 52 non-L0 micros."""
    micros = list_non_l0_micros()
    sys_p, user = build_router_prompt(item, micros, multi=True, header="micros", inject_mode=inject_mode)
    out = client.chat(sys_p, user, max_tokens=tb.router)
    return parse_multi_ids(out, set(micros))


def route_hierarchical(item: dict, client: LLMClient, inject_mode: str,
                       tb: TokenBudget, hint: str | None = None,
                       exclude: set[str] | None = None) -> list[str]:
    """Step 1: pick 0+ macros from 20 (minus `exclude`).
    Step 2: pick 0+ micros from a candidate pool that depends on step 1.
      - If step 1 picked 1+ macros: pool = UNION of their expandable_micro_ids
        (defensively filtered to exclude L0 and `exclude`).
      - If step 1 picked NONE: pool = all 52 non-L0 micros minus `exclude`
        (degenerates to micro_only-style selection so the LLM still gets a
        chance to pick diagnostic micros even when no scene-prototype macro fits).

    `hint`/`exclude` are empty on the first routing pass — behaviour is then
    identical to before. On a reroute they carry the solver's misfit capability
    and the rejected skills, so the re-pick re-runs this SAME two-stage flow
    (macro-gated micro) instead of collapsing to a flat pick."""
    exclude = exclude or set()
    l0 = set(L0_MICROS)
    macros = [m for m in list_macros() if m not in exclude]
    macro_picks: list[str] = []
    if macros:
        sys_p, user = build_router_prompt(item, macros, multi=True, header="macros",
                                          inject_mode=inject_mode, hint=hint)
        out = client.chat(sys_p, user, max_tokens=tb.router)
        macro_picks = parse_multi_ids(out, set(macros))
    if macro_picks:
        expandable: list[str] = []
        seen: set[str] = set()
        for m in macro_picks:
            for mid in (load_skill_pack(m).get("expandable_micro_ids") or []):
                if mid not in seen and mid not in l0 and mid not in exclude:
                    seen.add(mid)
                    expandable.append(mid)
        if not expandable:
            return list(macro_picks)
        step2_pool = expandable
        step2_header = "micros to expand the selected macro(s)"
    else:
        # No macro fit: fall back to letting the LLM pick from all non-L0 micros.
        step2_pool = [m for m in list_non_l0_micros() if m not in exclude]
        step2_header = "micros (no macro was selected — pick directly from non-L0 micros)"
    if not step2_pool:
        return list(macro_picks)

    sys_p2, user2 = build_router_prompt(
        item, step2_pool, multi=True,
        header=step2_header,
        inject_mode=inject_mode, hint=hint,
    )
    out2 = client.chat(sys_p2, user2, max_tokens=tb.router)
    micro_picks = parse_multi_ids(out2, set(step2_pool))
    return list(macro_picks) + micro_picks


def route_flat_all(item: dict, client: LLMClient, inject_mode: str,
                   tb: TokenBudget) -> list[str]:
    """Candidates are 20 macros + 52 non-L0 micros = 72."""
    all_ids = list_macros() + list_non_l0_micros()
    sys_p, user = build_router_prompt(item, all_ids, multi=True, header="skills (macros and micros)", inject_mode=inject_mode)
    out = client.chat(sys_p, user, max_tokens=tb.router)
    return parse_multi_ids(out, set(all_ids))


ROUTERS = {
    "macro_only": route_macro_only,
    "micro_only": route_micro_only,
    "hierarchical": route_hierarchical,
    "flat_all": route_flat_all,
}


def reroute_pick(item: dict, client: LLMClient, inject_mode: str, tb: TokenBudget,
                 route_mode: str, hint: str, exclude: set[str],
                 rejected_id: str = "", current_picked: list[str] | None = None) -> list[str]:
    """Re-select skill(s) after the solver flagged a misfit, FAITHFUL to
    route_mode and to WHICH layer exited.

    hierarchical (layer-aware):
      - micro exit with a scene macro still in play -> KEEP the macro(s) and
        re-pick the micro layer from those macros' expandable subset (minus
        `exclude`). The rejected micro is gone; good micros can be re-selected.
      - macro exit / no macro to keep / unidentified -> re-run the full
        two-stage flow (route_hierarchical) with hint + exclude.
    macro_only / micro_only / flat_all: re-pick over that mode's own pool minus
    the rejected skills.

    Returns the new picks (may be empty -> solve with no skill)."""
    current_picked = current_picked or []
    if route_mode == "hierarchical":
        kept_macros = [s for s in current_picked
                       if s.startswith("macro-") and s not in exclude]
        if rejected_id.startswith("micro-") and kept_macros:
            l0 = set(L0_MICROS)
            pool: list[str] = []
            seen: set[str] = set()
            for m in kept_macros:
                for mid in (load_skill_pack(m).get("expandable_micro_ids") or []):
                    if mid not in seen and mid not in l0 and mid not in exclude:
                        seen.add(mid)
                        pool.append(mid)
            if not pool:
                return list(kept_macros)
            sys_p, user = build_router_prompt(
                item, pool, multi=True,
                header="micros to expand the selected macro(s)",
                inject_mode=inject_mode, hint=hint)
            micro_picks = parse_multi_ids(
                client.chat(sys_p, user, max_tokens=tb.router), set(pool))
            return list(kept_macros) + micro_picks
        return route_hierarchical(item, client, inject_mode, tb,
                                  hint=hint, exclude=set(exclude))
    if route_mode == "macro_only":
        pool = [m for m in list_macros() if m not in exclude]
        header = "macros"
    elif route_mode == "micro_only":
        pool = [m for m in list_non_l0_micros() if m not in exclude]
        header = "micros"
    else:  # flat_all: a single flat pool is this mode's normal behaviour
        pool = [s for s in (list_macros() + list_non_l0_micros()) if s not in exclude]
        header = "skills (macros and micros)"
    if not pool:
        return []
    sys_p, user = build_router_prompt(item, pool, multi=True, header=header,
                                      inject_mode=inject_mode, hint=hint)
    out = client.chat(sys_p, user, max_tokens=tb.router)
    return parse_multi_ids(out, set(pool))


# --------------------------------------------------------------------------
# Runner
# --------------------------------------------------------------------------
@dataclass
class ItemResult:
    idx: int
    task: str
    ability: str
    lang: str
    gold: str                     # canonical gold key(s), comma-joined ("A" / "A,C")
    draft_pred: str               # answer after stage 3 (no review), comma-joined
    pred: str                     # final answer (= draft_pred if review off)
    correct: bool                 # final correctness (exact key-set match)
    draft_correct: bool           # correctness of the draft
    review_changed: bool          # whether review changed the answer
    gold_n: int = 1               # number of gold keys (1=single, >1=multi)
    jaccard: float = 1.0          # set overlap of final pred vs gold (multi diag)
    picked_skills: list[str] = field(default_factory=list)
    reroute_count: int = 0        # how many skill self-corrections fired
    initial_picked: list[str] = field(default_factory=list)  # picks before reroute
    draft_reasoning: str = ""     # only populated when review_mode=on
    review_reasoning: str = ""    # only populated when review_mode=on
    latency_s: float = 0.0
    error: str = ""


# --------------------------------------------------------------------------
# Dataset loading (generic — ToMBench by default, OR any MCQ jsonl via --data)
# --------------------------------------------------------------------------
STORY_ALIASES = ("story", "context", "passage", "scenario", "background", "text")
QUESTION_ALIASES = ("question", "query", "prompt", "ques", "q")
OPTION_ALIASES = ("options", "choices", "candidates", "answers")
GOLD_ALIASES = ("gold", "answer", "answers", "label", "labels", "gold_answer",
                "target", "correct")
TASK_ALIASES = ("task", "category", "subset")
ABILITY_ALIASES = ("ability", "skill", "subtask", "dimension")
LANG_ALIASES = ("lang", "language")
# question-type field: detect single- vs multi-select. Bilingual names + values.
# NOTE: bare "type" is intentionally NOT here (it is a TASK alias).
TYPE_ALIASES = ("题型", "答案类型", "answer_type", "question_type", "qtype",
                "answer_mode", "multi", "multiple", "is_multiple",
                "multi_select", "multiselect", "answer_count", "num_answers")
GOLD_SPLIT_RE = re.compile(r"[,\s;/、，]+")


def _first_alias(rec: dict, names: tuple[str, ...], default: Any = None) -> Any:
    for n in names:
        v = rec.get(n)
        if v not in (None, ""):
            return v
    return default


def _normalize_options(raw: Any) -> dict[str, str]:
    """Return an {A: text, B: text, ...} dict from either a dict or a list."""
    if isinstance(raw, dict):
        return {str(k).strip(): v for k, v in raw.items()}
    if isinstance(raw, (list, tuple)):
        return {chr(65 + i): v for i, v in enumerate(raw)}
    return {}


def _normalize_gold_one(raw: Any, options: dict[str, str], index_base: int) -> str:
    """Map ONE gold value (letter / numeric index / option text) to an option key."""
    if raw is None:
        return ""
    s = str(raw).strip()
    if s in options:                                 # already an option key
        return s
    if len(s) == 1 and s.upper() in options:         # lower-case letter
        return s.upper()
    if re.fullmatch(r"\d+", s):                       # numeric index
        keys = sorted(options.keys())
        i = int(s) - index_base
        if 0 <= i < len(keys):
            return keys[i]
    for k, v in options.items():                     # exact option text
        if str(v).strip() == s:
            return k
    return s                                         # unmatched -> counts wrong


def _normalize_gold_set(raw: Any, options: dict[str, str], index_base: int) -> list[str]:
    """Map a (possibly multi-answer) gold onto a sorted list of option keys.
    Handles a list (["A","C"] / [0,2]), a delimited string ("A,C" / "A、C"),
    concatenated letters ("AC"), a single letter/index, or the option text
    (incl. text containing spaces, which is matched whole, never split)."""
    if raw is None:
        return []
    if isinstance(raw, (list, tuple, set)):
        keys: list[str] = []
        for e in raw:
            k = _normalize_gold_one(e, options, index_base)
            if k and k not in keys:
                keys.append(k)
        return sorted(keys)
    s = str(raw).strip()
    if not s:
        return []
    whole = _normalize_gold_one(s, options, index_base)   # try whole (covers text w/ spaces)
    if whole in options:
        return [whole]
    if s.isalpha() and len(s) > 1 and all(ch.upper() in options for ch in s):
        return sorted({ch.upper() for ch in s})           # concatenated letters "AC"
    parts = [p for p in GOLD_SPLIT_RE.split(s) if p]
    if len(parts) > 1:                                     # delimited list "A,C"
        keys = []
        for p in parts:
            k = _normalize_gold_one(p, options, index_base)
            if k in options and k not in keys:
                keys.append(k)
        if keys:
            return sorted(keys)
    return [whole] if whole else []                       # unmatched -> flagged by loader


def _resolve_answer_mode(rec: dict, gold_keys: list[str], cli_mode: str) -> str:
    """Decide single vs multi for a question. Priority: explicit --answer-mode
    override > per-item type field (bilingual) > gold cardinality > 'auto' (let
    the model decide). Returns 'single' | 'multi' | 'auto'."""
    if cli_mode in ("single", "multi"):
        return cli_mode
    v = _first_alias(rec, TYPE_ALIASES, None)
    if v is not None:
        if isinstance(v, bool):
            return "multi" if v else "single"
        sv = str(v).strip().lower()
        if sv.isdigit():
            return "multi" if int(sv) > 1 else "single"
        if ("多" in sv) or ("multi" in sv):
            return "multi"
        if ("单" in sv) or ("single" in sv) or (sv == "one"):
            return "single"
        if sv in ("true", "yes", "是", "y", "t"):
            return "multi"
        if sv in ("false", "no", "否", "n", "f"):
            return "single"
    if gold_keys:
        return "multi" if len(gold_keys) > 1 else "single"
    return "auto"


def normalize_record(rec: dict, idx: int, default_lang: str, index_base: int,
                     cli_answer_mode: str = "auto") -> dict:
    """Map a raw dataset record onto the canonical internal item schema the
    runner relies on: _id, lang, story, question, options(dict), gold_keys
    (list of keys), gold (canonical comma-joined string), answer_mode, task,
    ability. Field-name aliases are accepted so a new dataset rarely needs
    reshaping; gold may be a letter / index / option text / a multi-answer
    list or delimited string; options may be a dict or a list."""
    options = _normalize_options(_first_alias(rec, OPTION_ALIASES, {}))
    gold_keys = _normalize_gold_set(_first_alias(rec, GOLD_ALIASES), options, index_base)
    return {
        "_id": idx,
        "lang": _first_alias(rec, LANG_ALIASES, default_lang),
        "story": (_first_alias(rec, STORY_ALIASES, "") or ""),
        "question": (_first_alias(rec, QUESTION_ALIASES, "") or ""),
        "options": options,
        "gold_keys": gold_keys,
        "gold": ",".join(gold_keys),
        "answer_mode": _resolve_answer_mode(rec, gold_keys, cli_answer_mode),
        "task": (_first_alias(rec, TASK_ALIASES, "default") or "default"),
        "ability": (_first_alias(rec, ABILITY_ALIASES, "") or ""),
    }


def resolve_dataset(args: argparse.Namespace) -> tuple[Path, str]:
    """Return (data_path, dataset_name). --data PATH (absolute or relative)
    selects any jsonl dataset; otherwise the default ToMBench file for --lang
    is used. dataset_name (sanitized) labels the run dir and config."""
    if args.data:
        path = Path(args.data).expanduser()
        if not path.is_absolute():
            path = (Path.cwd() / path).resolve()
        name = args.dataset_name or path.stem
    else:
        path = DATA_DIR / f"ToMBench_{args.lang}.jsonl"
        name = args.dataset_name or f"ToMBench_{args.lang}"
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("_") or "dataset"
    return path, name


def load_items(path: Path, limit: int | None, default_lang: str,
               index_base: int = 0, cli_answer_mode: str = "auto") -> tuple[list[dict], int]:
    """Load + normalize a jsonl dataset. Returns (items, n_unmappable_gold)."""
    items: list[dict] = []
    bad_gold = 0
    with open(path, "r", encoding="utf-8-sig") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            item = normalize_record(json.loads(line), i, default_lang,
                                    index_base, cli_answer_mode)
            keys = item["gold_keys"]
            if not keys or any(k not in item["options"] for k in keys):
                bad_gold += 1
            items.append(item)
            if limit and len(items) >= limit:
                break
    return items, bad_gold


def load_done_ids(path: Path) -> set[int]:
    if not path.exists():
        return set()
    done = set()
    with open(path, "r", encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                done.add(json.loads(line).get("idx"))
            except json.JSONDecodeError:
                continue
    return done


def solve_item(item: dict, route_mode: str, inject_mode: str,
               review_mode: str, client: LLMClient,
               tb: TokenBudget, reroute_budget: int = 1) -> ItemResult:
    t0 = time.time()
    picked: list[str] = []
    initial_picked: list[str] = []
    reroute_count = 0
    options = item.get("options") or {}
    gold_set = set(item.get("gold_keys") or [])
    multi = item.get("answer_mode", "single") in ("multi", "auto")
    draft_set: set[str] = set()
    final_set: set[str] = set()
    draft_reasoning = ""
    review_reasoning = ""
    review_on = (review_mode == "on")

    def _canon(s: set[str]) -> str:
        return ",".join(sorted(s))
    try:
        # Stage 2: route (skip for baseline)
        if route_mode == "baseline":
            picked = []
        else:
            picked = ROUTERS[route_mode](item, client, inject_mode, tb)
        initial_picked = list(picked)
        # Stage 3: solve -> draft, with a bounded skill self-correction loop.
        # The solver checks EACH injected skill's boundary exits and, on a
        # misfit, emits `REROUTE: <skill-id> | <capability>` instead of
        # answering. The flagged skill must never produce the final answer:
        #   - capability given + budget left -> drop the flagged skill and
        #     re-pick a replacement (layer-aware: a micro exit keeps the macro
        #     and re-picks within its expandable subset; a macro exit re-runs the
        #     full two-stage route);
        #   - capability but no budget, OR a bare id with no capability to guide
        #     a re-pick -> drop the flagged skill and commit using the remaining
        #     skills (one forced re-solve, no router call);
        #   - capability but no identifiable skill (and budget) -> drop ALL picked
        #     skills and re-pick from scratch.
        # If neither a capability nor an id is parsed, there is no misfit signal
        # and we use the answer. Re-picks are bounded by reroute_budget.
        reroute_on = (reroute_budget > 0 and route_mode != "baseline")
        excluded: set[str] = set()
        draft_out = ""
        final_commit = False  # once set, force a plain answer with the current set
        while True:
            detect = reroute_on and bool(picked) and not final_commit
            sys_p, user = build_solver_prompt(item, picked, inject_mode,
                                              with_reasoning=review_on,
                                              allow_reroute=detect)
            draft_out = client.chat(sys_p, user, max_tokens=tb.solver)
            rid, cap = parse_reroute(draft_out, set(picked)) if detect else ("", "")
            if not (cap or rid):              # no misfit signal -> use this answer
                break
            # solver flagged a misfit -> the rejected skill must not answer.
            if cap and reroute_count < reroute_budget:
                # capability gives a hint -> drop the misfit and re-pick a replacement
                reroute_count += 1
                if rid:                       # drop only the flagged skill
                    excluded.add(rid)
                    picked = [s for s in picked if s != rid]
                else:                         # capability but no id -> drop all, full re-pick
                    excluded |= set(picked)
                    picked = []
                picked = reroute_pick(item, client, inject_mode, tb, route_mode,
                                      cap, excluded, rid, picked)
                continue
            # no budget, OR a bare id with no capability to guide a re-pick:
            # drop the identified misfit and commit using the remaining skills.
            if rid:
                excluded.add(rid)
                picked = [s for s in picked if s != rid]
            final_commit = True
            continue
        if review_on:
            draft_reasoning, draft_set = extract_reasoning_and_answer(draft_out, options, multi)
        else:
            draft_set = extract_answer_set(draft_out, options, multi)
        # Stage 4: review (optional)
        if review_on:
            rs, ru = build_review_prompt(
                item, picked, draft_reasoning, _canon(draft_set), inject_mode,
            )
            rev_out = client.chat(rs, ru, max_tokens=tb.reviewer)
            review_reasoning, rev_set = extract_reasoning_and_answer(rev_out, options, multi)
            final_set = rev_set or draft_set
        else:
            final_set = draft_set
        return ItemResult(
            idx=item["_id"], task=item["task"], ability=item.get("ability", ""),
            lang=item["lang"], gold=item["gold"],
            draft_pred=_canon(draft_set), pred=_canon(final_set),
            correct=(bool(final_set) and final_set == gold_set),
            draft_correct=(bool(draft_set) and draft_set == gold_set),
            review_changed=(review_on and draft_set != final_set),
            gold_n=len(gold_set), jaccard=_jaccard(final_set, gold_set),
            picked_skills=picked,
            reroute_count=reroute_count, initial_picked=initial_picked,
            draft_reasoning=draft_reasoning, review_reasoning=review_reasoning,
            latency_s=time.time() - t0,
        )
    except Exception as exc:
        return ItemResult(
            idx=item["_id"], task=item["task"], ability=item.get("ability", ""),
            lang=item["lang"], gold=item["gold"],
            draft_pred=_canon(draft_set), pred=_canon(final_set),
            correct=False, draft_correct=(bool(draft_set) and draft_set == gold_set),
            review_changed=False,
            gold_n=len(gold_set), jaccard=_jaccard(final_set, gold_set),
            picked_skills=picked,
            reroute_count=reroute_count, initial_picked=initial_picked,
            draft_reasoning=draft_reasoning, review_reasoning=review_reasoning,
            latency_s=time.time() - t0, error=f"{type(exc).__name__}: {exc}",
        )


def run(args: argparse.Namespace) -> None:
    api_key = (
        os.environ.get("SKILL_V5_API_KEY") or os.environ.get("OPENAI_API_KEY") or args.api_key
    )
    if not api_key:
        sys.exit("Missing API key. Set SKILL_V5_API_KEY or OPENAI_API_KEY.")
    client = LLMClient(
        model=args.model, base_url=args.base_url, api_key=api_key,
        timeout=args.timeout, temperature=args.temperature, top_p=args.top_p,
        max_attempts=args.max_attempts, retry_backoff_cap=args.retry_backoff_cap,
        enable_thinking=args.enable_thinking,
    )
    tb = TokenBudget(
        router=args.router_max_tokens,
        solver=args.solver_max_tokens,
        reviewer=args.reviewer_max_tokens,
    )

    data_path, dataset_name = resolve_dataset(args)
    if not data_path.exists():
        sys.exit(f"Dataset not found: {data_path}")
    items, bad_gold = load_items(data_path, args.limit, args.lang,
                                 args.gold_index_base, args.answer_mode)
    n_multi = sum(1 for it in items if it.get("answer_mode") == "multi")
    print(f"Loaded {len(items)} items from {data_path} (dataset='{dataset_name}'; "
          f"multi-answer items: {n_multi})")
    if bad_gold:
        print(f"  WARNING: {bad_gold} item(s) have a gold value that matches no "
              f"option key — check the dataset schema or --gold-index-base.",
              file=sys.stderr)

    if args.route_mode == "baseline":
        run_id = args.run_id or (
            f"baseline_{dataset_name}_review-{args.review_mode}_"
            f"{args.model.replace('/', '_')}_{int(time.time())}"
        )
    else:
        run_id = args.run_id or (
            f"{args.route_mode}_{args.inject_mode}_review-{args.review_mode}_"
            f"{dataset_name}_{args.model.replace('/', '_')}_{int(time.time())}"
        )
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    results_path = run_dir / "results.jsonl"
    done_ids = load_done_ids(results_path) if args.resume else set()
    if done_ids:
        print(f"Resuming: {len(done_ids)} items already done, skipping.")
    items_todo = [it for it in items if it["_id"] not in done_ids]

    # Initial counters reflect prior run if resuming
    file_lock = threading.Lock()
    n_done = len(done_ids)
    n_correct = 0
    if results_path.exists() and args.resume:
        for line in results_path.read_text(encoding="utf-8-sig").splitlines():
            try:
                if json.loads(line).get("correct"):
                    n_correct += 1
            except json.JSONDecodeError:
                pass

    config = {
        "run_id": run_id,
        "dataset": dataset_name,
        "data_path": str(data_path),
        "route_mode": args.route_mode,
        "inject_mode": args.inject_mode if args.route_mode != "baseline" else "n/a",
        "review_mode": args.review_mode,
        "lang": args.lang,
        "gold_index_base": args.gold_index_base,
        "answer_mode": args.answer_mode,
        "model": args.model,
        "limit": args.limit,
        "workers": args.workers,
        "temperature": args.temperature,
        "top_p": args.top_p,
        "timeout": args.timeout,
        "max_attempts": args.max_attempts,
        "retry_backoff_cap": args.retry_backoff_cap,
        "router_max_tokens": args.router_max_tokens,
        "solver_max_tokens": args.solver_max_tokens,
        "reviewer_max_tokens": args.reviewer_max_tokens,
        "reroute_budget": args.reroute_budget if args.route_mode != "baseline" else 0,
        "enable_thinking": args.enable_thinking,
    }
    (run_dir / "config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    def write_result(r: ItemResult):
        nonlocal n_done, n_correct
        row = asdict(r)
        if args.review_mode != "on":
            # Drop review-only / draft-vs-final columns when review is off, so the
            # file matches the simpler schema (reroute columns are kept — they are
            # orthogonal to review):
            #   idx, task, ability, lang, gold, pred, correct, picked_skills,
            #   reroute_count, initial_picked, latency_s, error
            for k in ("draft_pred", "draft_correct", "review_changed",
                      "draft_reasoning", "review_reasoning"):
                row.pop(k, None)
            ordered_keys = ["idx", "task", "ability", "lang", "gold",
                            "pred", "correct", "gold_n", "jaccard",
                            "picked_skills", "reroute_count", "initial_picked",
                            "latency_s", "error"]
            row = {k: row[k] for k in ordered_keys if k in row}
        with file_lock:
            with open(results_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
            n_done += 1
            if r.correct:
                n_correct += 1
            if n_done % 25 == 0 or n_done == len(items):
                acc = n_correct / max(1, n_done)
                print(f"[{n_done}/{len(items)}] acc={acc:.3f}")

    print(f"Running route={args.route_mode} inject={args.inject_mode} "
          f"model={args.model} workers={args.workers}")
    print(f"Output: {results_path}")
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = [
            ex.submit(solve_item, it, args.route_mode, args.inject_mode,
                      args.review_mode, client, tb, args.reroute_budget)
            for it in items_todo
        ]
        for fut in as_completed(futures):
            try:
                write_result(fut.result())
            except Exception as exc:
                print(f"  worker error: {exc}", file=sys.stderr)

    summarize(run_dir)


def summarize(run_dir: Path) -> None:
    results_path = run_dir / "results.jsonl"
    if not results_path.exists():
        return
    rows = []
    bad_rows = []
    for line_no, line in enumerate(results_path.read_text(encoding="utf-8-sig").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            bad_rows.append((line_no, exc))
    if not rows:
        print("No rows to summarize.")
        return
    if bad_rows:
        print(f"Skipped {len(bad_rows)} malformed result row(s) while summarizing.")

    by_task: dict[str, list[bool]] = {}
    by_ability: dict[str, list[bool]] = {}
    by_first_pick: dict[str, list[bool]] = {}
    by_n_picked: dict[int, list[bool]] = {}
    pick_freq: dict[str, int] = {}
    n_none = 0
    n_err = 0
    by_reroute: dict[int, list[bool]] = {}
    by_answer_kind: dict[str, list[bool]] = {}     # "single" / "multi"
    has_draft_metrics = any("draft_correct" in r for r in rows)
    has_reroute_metrics = any("reroute_count" in r for r in rows)
    has_multi_metrics = any(int(r.get("gold_n") or 1) > 1 for r in rows)
    draft_correct = 0
    draft_total = 0
    review_changed = 0
    review_flips_correct = 0       # draft wrong, final right
    review_flips_wrong = 0         # draft right, final wrong
    n_rerouted = 0                 # items where >=1 reroute fired
    reroute_changed_pick = 0       # items where reroute changed the skill set
    jaccard_sum = 0.0
    jaccard_n = 0
    for r in rows:
        by_task.setdefault(r["task"], []).append(r["correct"])
        if r.get("ability"):
            by_ability.setdefault(r["ability"], []).append(r["correct"])
        picks = r.get("picked_skills") or []
        first = picks[0] if picks else "<none>"
        by_first_pick.setdefault(first, []).append(r["correct"])
        by_n_picked.setdefault(len(picks), []).append(r["correct"])
        for p in picks:
            pick_freq[p] = pick_freq.get(p, 0) + 1
        if not picks:
            n_none += 1
        if r.get("error"):
            n_err += 1
        if "reroute_count" in r:
            rc = int(r.get("reroute_count") or 0)
            by_reroute.setdefault(rc, []).append(r["correct"])
            if rc > 0:
                n_rerouted += 1
                if (r.get("initial_picked") or []) != picks:
                    reroute_changed_pick += 1
        if "gold_n" in r:
            kind = "multi" if int(r.get("gold_n") or 1) > 1 else "single"
            by_answer_kind.setdefault(kind, []).append(r["correct"])
        if "jaccard" in r:
            jaccard_sum += float(r.get("jaccard") or 0.0)
            jaccard_n += 1
        if "draft_correct" in r:
            draft_total += 1
            if r.get("draft_correct"):
                draft_correct += 1
        if r.get("review_changed"):
            review_changed += 1
            if not r.get("draft_correct") and r.get("correct"):
                review_flips_correct += 1
            elif r.get("draft_correct") and not r.get("correct"):
                review_flips_wrong += 1

    overall_correct = sum(1 for r in rows if r["correct"])
    summary = {
        "n": len(rows),
        "overall_acc": overall_correct / len(rows),
        "review_changed": review_changed,
        "review_flips_correct": review_flips_correct,   # draft wrong -> final right
        "review_flips_wrong": review_flips_wrong,       # draft right -> final wrong
        "errors": n_err,
        "malformed_rows": len(bad_rows),
        "n_routed_to_none": n_none,
        "by_task": {k: {"n": len(v), "acc": sum(v) / len(v)} for k, v in sorted(by_task.items())},
        "by_ability": {k: {"n": len(v), "acc": sum(v) / len(v)} for k, v in sorted(by_ability.items())},
        "by_first_pick": {k: {"n": len(v), "acc": sum(v) / len(v)} for k, v in sorted(by_first_pick.items())},
        "by_n_picked": {str(k): {"n": len(v), "acc": sum(v) / len(v)} for k, v in sorted(by_n_picked.items())},
        "pick_frequency": dict(sorted(pick_freq.items(), key=lambda kv: -kv[1])),
    }
    if has_reroute_metrics:
        summary["n_rerouted"] = n_rerouted                  # items with >=1 reroute
        summary["reroute_changed_pick"] = reroute_changed_pick
        summary["acc_by_reroute_count"] = {
            str(k): {"n": len(v), "acc": sum(v) / len(v)} for k, v in sorted(by_reroute.items())
        }
    if jaccard_n:
        summary["mean_jaccard"] = jaccard_sum / jaccard_n
    if has_multi_metrics:
        summary["acc_by_answer_kind"] = {
            k: {"n": len(v), "acc": sum(v) / len(v)} for k, v in sorted(by_answer_kind.items())
        }
    if has_draft_metrics:
        summary["draft_acc"] = draft_correct / max(1, draft_total)
    out = run_dir / "summary.json"
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nWrote {out}")
    overall_parts = [
        f"n={summary['n']}",
        f"final_acc={summary['overall_acc']:.4f}",
    ]
    if has_draft_metrics:
        overall_parts.append(f"draft_acc={summary['draft_acc']:.4f}")
    overall_parts.extend([
        f"review_changed={review_changed}",
        f"flips(wrong->right)={review_flips_correct}",
        f"flips(right->wrong)={review_flips_wrong}",
        f"errors={summary['errors']}",
        f"routed_to_none={summary['n_routed_to_none']}",
    ])
    if has_reroute_metrics:
        overall_parts.append(f"rerouted={n_rerouted}")
    if has_multi_metrics:
        mk = summary.get("acc_by_answer_kind", {})
        if "multi" in mk:
            overall_parts.append(
                f"multi_acc={mk['multi']['acc']:.4f}(n={mk['multi']['n']})")
        overall_parts.append(f"mean_jaccard={summary.get('mean_jaccard', 1.0):.4f}")
    print("Overall: " + " ".join(overall_parts))
    print("\nBy task:")
    for k, v in summary["by_task"].items():
        print(f"  {k:40s} n={v['n']:4d}  acc={v['acc']:.3f}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--route-mode",
        choices=["baseline", "macro_only", "micro_only", "hierarchical", "flat_all"],
        default="hierarchical",
    )
    p.add_argument("--inject-mode", choices=["full", "light"], default="light")
    p.add_argument("--review-mode", choices=["on", "off"], default="on",
                   help="If 'on', run an L0 review stage after the draft "
                        "answer; both draft and final letters are recorded.")
    p.add_argument("--data", default="",
                   help="Path (absolute or relative) to a jsonl dataset to "
                        "evaluate, one MCQ record per line. Overrides the "
                        "default ToMBench file. Common field aliases "
                        "(story/context, question/query, options/choices, "
                        "gold/answer/label, task/category, ability, lang) and "
                        "dict-or-list options are accepted.")
    p.add_argument("--dataset-name", default="",
                   help="Label for the run dir and config.json "
                        "(default: the dataset file stem).")
    p.add_argument("--gold-index-base", type=int, default=0, choices=[0, 1],
                   help="When a record's gold is a numeric index, treat it as "
                        "0- or 1-based. Ignored when gold is a letter or the "
                        "option text.")
    p.add_argument("--answer-mode", choices=["auto", "single", "multi"], default="auto",
                   help="Single- vs multi-select framing. auto (default): use a "
                        "per-item question-type field (题型/answer_type/multi/…) "
                        "if present, else infer from gold cardinality, else let "
                        "the model decide. single/multi force one framing for the "
                        "whole dataset. Answers are always scored by exact "
                        "option-key set match; Jaccard is also recorded.")
    p.add_argument("--lang", choices=["en", "zh"], default="en",
                   help="Default language for records without a lang field; "
                        "also selects the default ToMBench_<lang>.jsonl file "
                        "when --data is omitted.")
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--base-url", default=DEFAULT_BASE_URL)
    p.add_argument("--api-key", default="")
    p.add_argument("--limit", type=int, default=0, help="0 = all 2860")
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--temperature", type=float, default=0.0)
    p.add_argument("--top-p", type=float, default=1.0)
    p.add_argument("--enable-thinking", action="store_true",
                   help="Pass extra_body={'enable_thinking': true} to the chat API.")
    p.add_argument("--timeout", type=int, default=120,
                   help="Per-request timeout in seconds (passed to the OpenAI client).")
    p.add_argument("--max-attempts", type=int, default=3,
                   help="Maximum LLM attempts per call (1 = no retry).")
    p.add_argument("--retry-backoff-cap", type=int, default=8,
                   help="Cap (seconds) for exponential backoff between retries. "
                        "Set 0 to retry without sleeping.")
    p.add_argument("--router-max-tokens", type=int, default=128,
                   help="max_completion_tokens for each router call.")
    p.add_argument("--solver-max-tokens", type=int, default=2048,
                   help="max_completion_tokens for the solver. Default 2048 "
                        "leaves headroom for the reasoning block when "
                        "--review-mode on; you can lower it to ~256 for "
                        "letter-only solving with --review-mode off.")
    p.add_argument("--reviewer-max-tokens", type=int, default=2048,
                   help="max_completion_tokens for the L0 reviewer (which "
                        "also outputs reasoning + letter).")
    p.add_argument("--reroute-budget", type=int, default=1,
                   help="Max skill self-corrections per item. After a skill is "
                        "injected, the solver checks its boundary exits; on a "
                        "misfit it emits REROUTE and the router re-selects "
                        "(excluding the rejected skill). 0 = disable. Default 1. "
                        "Ignored for --route-mode baseline.")
    p.add_argument("--run-id", default="")
    p.add_argument("--resume", action="store_true")
    p.add_argument("--summarize-only", action="store_true",
                   help="Re-summarize an existing run dir given by --run-id.")
    args = p.parse_args()
    if args.limit == 0:
        args.limit = None

    if args.summarize_only:
        if not args.run_id:
            sys.exit("--summarize-only requires --run-id")
        summarize(RUNS_DIR / args.run_id)
        return
    run(args)


if __name__ == "__main__":
    main()
