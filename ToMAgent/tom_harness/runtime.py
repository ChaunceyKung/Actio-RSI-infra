"""HarnessRuntime — the canonical single-shot path.

This is the consolidated runtime, replacing the Plan/Execute multi-step
scheduler as the default. It implements:

    route(sample) -> skill_id
    build_prompt(sample, skill_id) -> messages
    LLM call
    for v in validators:
        result = v.validate(sample, current_answer)
        if not valid:
            apply v.suggested_answer  OR  retry LLM with v.feedback
    return final answer

Why this shape (vs Plan/Execute):
  - On qwen-plus, full Plan/Execute pipeline measured -7~9pp vs single-shot
    (see WEEKLY_REPORT_HARNESS_2026-04-29 §5 表 2a). Multi-step in a strong
    LLM regime is a net negative on this benchmark.
  - The remaining harness value (post-Plan/Execute) is exactly:
      adapter pattern + selective routing + procedural validators + retry
    All of which fit naturally in single-shot + checkpoint structure.

Plan/Execute (Scheduler/Planner/Executor) remains in the codebase for
multi-step research scenarios but is no longer the default.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any

from .llm import LLMClient
from .orchestration import ModuleOrchestrator, run_validator_loop
from .routing.base import Router
from .validators.base import Validator

logger = logging.getLogger(__name__)


SYSTEM_BASE = (
    "You are a reading comprehension assistant. Read the story and answer "
    "the multiple-choice question.\n"
)

SYSTEM_SKILL_HINT = (
    "A domain-specific reasoning skill is provided in the user message under "
    "\"## Reasoning Skill\". Follow its workflow step-by-step before choosing "
    "your answer.\n"
)

SYSTEM_RAG_HINT = (
    "Background knowledge retrieved from a commonsense knowledge base is "
    "provided under \"## Background Knowledge\". Use it as supplementary "
    "reference when it is relevant, but always prioritize evidence from the "
    "story itself.\n"
)

SYSTEM_PLAYBOOK_HINT = (
    "A strategy playbook is provided under \"## Playbook\". Apply its "
    "strategies and heuristics, and be mindful of the common mistakes it "
    "documents.\n"
)

SYSTEM_TAIL = (
    "First give a brief reason (2-3 sentences) for your choice, "
    "then output a JSON object on its own line: "
    "{\"answer\": \"<letter>\"} where <letter> is one of the option labels."
)

SYSTEM_FREE_FORM = (
    "You are a reading comprehension assistant. Read the story/conversation "
    "carefully and answer the question as instructed. Follow the output "
    "format described in the user message.\n"
)

SYSTEM_LIST = (
    "You are an expert in social reasoning. List the required items and split "
    "them with commas. Remember: Your answer should ONLY include the required "
    "items splitted by commas with nothing else."
)

# Keep backward-compat alias for any external code referencing SYSTEM_RAW
SYSTEM_RAW = SYSTEM_BASE + SYSTEM_TAIL


def _build_system_prompt(
    *,
    has_skill: bool = False,
    has_rag: bool = False,
    has_playbook: bool = False,
    free_form: bool = False,
) -> str:
    if free_form:
        parts = [SYSTEM_FREE_FORM]
        if has_skill:
            parts.append(SYSTEM_SKILL_HINT)
        if has_rag:
            parts.append(SYSTEM_RAG_HINT)
        if has_playbook:
            parts.append(SYSTEM_PLAYBOOK_HINT)
        return "".join(parts)
    parts = [SYSTEM_BASE]
    if has_skill:
        parts.append(SYSTEM_SKILL_HINT)
    if has_rag:
        parts.append(SYSTEM_RAG_HINT)
    if has_playbook:
        parts.append(SYSTEM_PLAYBOOK_HINT)
    parts.append(SYSTEM_TAIL)
    return "".join(parts)

_LETTER_RE = re.compile(r'"answer"\s*:\s*"([A-O])"')
_REASON_RE = re.compile(r'^([\s\S]*?)\s*(\{[\s\S]*"answer"[\s\S]*\})\s*$')
_BARE_LETTER_RE = re.compile(
    r'(?:答案|answer|选)\s*(?:[:：为]|is)?\s*\(?([A-O])\)?'
    r'|(?:^|\n)\s*\(?([A-O])\)?\s*[.。]?\s*$',
    re.IGNORECASE | re.MULTILINE
)
_VALID_LETTERS = set("ABCDEFGHIJKLMNO")


def _parse_response(text: str) -> tuple[str, str]:
    """Return (answer_letter, reasoning_text)."""
    raw = text or ""
    stripped = re.sub(r"<think>[\s\S]*?</think>", "", raw).strip()
    # If stripping think tags leaves nothing, fall back to think content
    if not stripped:
        m_think = re.search(r"<think>([\s\S]*?)</think>", raw)
        stripped = m_think.group(1).strip() if m_think else ""
    text = stripped
    reasoning = ""
    m = _REASON_RE.match(text)
    if m:
        reasoning = m.group(1).strip()
        json_part = m.group(2).strip()
    else:
        json_part = text

    try:
        d = json.loads(json_part)
        a = str(d.get("answer", "")).strip().upper()
        # Support multi-answer format for tasks like EmoBench EU (e.g., "A,H")
        if "," in a:
            # Multi-answer format: validate each letter
            letters = [l.strip() for l in a.split(",")]
            if all(l in _VALID_LETTERS for l in letters):
                return a, reasoning
        if a in _VALID_LETTERS:
            return a, reasoning
    except Exception:  # noqa: BLE001
        pass
    m2 = _LETTER_RE.search(text)
    if m2:
        return m2.group(1).upper(), reasoning
    # Last resort: match bare letter patterns like "答案：B", "answer is C", or trailing letter
    m3 = _BARE_LETTER_RE.search(text)
    if m3:
        letter = (m3.group(1) or m3.group(2)).upper()
        return letter, reasoning
    logger.warning("_parse_response failed to extract answer from: %s", text)
    return ("", reasoning)


def _build_user_prompt(*, story: str, question: str, options: dict[str, str],
                       skill_body: str | None = None,
                       rag_context: str | None = None,
                       playbook: str | None = None) -> str:
    sections: list[str] = []
    if skill_body:
        sections.append(f"## Reasoning Skill (apply before answering)\n{skill_body}")
    if rag_context:
        sections.append(
            "## Background Knowledge\n"
            "The following information may be relevant to the current question and is for reference only:\n"
            f"{rag_context}"
        )
    if playbook:
        sections.append(f"## Playbook\n{playbook}")
    sections.append(f"## Story\n{story}")
    sections.append(f"## Question\n{question}")
    opts = "\n".join(f"{k}. {v}" for k, v in options.items() if v)
    sections.append(f"## Options\n{opts}")
    opt_labels = "|".join(f'"{k}"' for k in options if options[k])
    sections.append(
        '## Answer\n'
        'After applying any guidance above, first state your reason in 2-3 sentences, '
        f'then output a JSON object on its own line: {{"answer": {opt_labels}}}'
    )
    return "\n\n".join(sections)


def _build_retry_prompt(*, base_user: str, prior_answer: str, validator_feedback: str) -> str:
    return (
        f"{base_user}\n\n"
        f"## Validator Feedback (from a procedural check on your prior answer)\n"
        f"Your previous answer was {prior_answer}.\n"
        f"{validator_feedback}\n\n"
        '## Reconsider\nState your reason in 2-3 sentences, then output a JSON object: {"answer": "A"|"B"|"C"|"D"}'
    )


def _build_free_form_retry_prompt(*, base_user: str, prior_answer: str, validator_feedback: str) -> str:
    return (
        f"{base_user}\n\n"
        f"## 校验反馈（对你的初稿做一次后验复核）\n"
        f"你的初稿如下：\n{prior_answer}\n\n"
        f"{validator_feedback}"
    )



@dataclass
class RuntimeResult:
    answer: str
    skill_id: str | None
    n_llm_calls: int
    thinking: str = ""
    draft_reasoning: str = ""
    rag_context: str = ""
    memory_bullets: list[str] = field(default_factory=list)
    memory_subtask: str = ""
    validator_events: list[dict] = field(default_factory=list)
    draft_answer: str = ""
    skill_ids: list[str] = field(default_factory=list)
    review_changed: bool = False


@dataclass
class HarnessRuntime:
    """Single-shot harness with optional validator-retry and L0 review."""
    llm: LLMClient
    router: "Router"
    validators: list["Validator"] = field(default_factory=list)
    rag_engine: Any = None
    playbook: str | None = None
    memory: Any = None
    max_retries: int = 1
    review_mode: str = "off"
    gate: Any = None  # Optional ModuleGate instance

    def __post_init__(self) -> None:
        # Shared, host-agnostic module pipeline (gate → skill → rag → memory).
        # answer_one is just one host over this orchestration.
        self._orch = ModuleOrchestrator(
            router=self.router,
            rag_engine=self.rag_engine,
            memory=self.memory,
            playbook=self.playbook,
            gate=self.gate,
        )

    def answer_one(
        self,
        *,
        question: str,
        story: str,
        options: dict[str, str],
        free_form: bool = False,
        system_override: str | None = None,
        eval_mode: str | None = None,
        raw_metadata: dict | None = None,
    ) -> RuntimeResult:
        # ── Module pipeline (gate → skill → rag → memory) via shared layer ─
        aug = self._orch.augment(
            question=question, story=story, options=options,
            gate_eval_mode="free_form" if free_form else "mcq",
            raw_metadata=raw_metadata,
        )
        skill_id = aug.skill_id
        skill_ids = aug.skill_ids
        skill_body = aug.skill_body
        rag_context = aug.rag_context
        playbook_text = aug.playbook_text
        memory_bullet_ids = aug.memory_bullet_ids
        memory_subtask = aug.memory_subtask

        base_user = _build_user_prompt(
            story=story, question=question, options=options,
            skill_body=skill_body, rag_context=rag_context or None,
            playbook=playbook_text,
        )

        system_prompt = system_override or _build_system_prompt(
            has_skill=bool(skill_body),
            has_rag=bool(rag_context),
            has_playbook=bool(playbook_text),
            free_form=free_form,
        )

        # ── free_form path: open generation with optional validator-retry ─
        if free_form:
            # For free_form, the question already contains the full prompt
            user_msg = question
            if skill_body:
                user_msg = f"## Reasoning Skill (apply before answering)\n{skill_body}\n\n{user_msg}"
            if rag_context:
                user_msg = f"## Background Knowledge\n{rag_context}\n\n{user_msg}"
            if playbook_text:
                user_msg = f"## Playbook\n{playbook_text}\n\n{user_msg}"
            n_calls = 1 + aug.n_aux_llm_calls
            try:
                text = self.llm.chat(system_prompt, user_msg, max_tokens=1024)
            except Exception as e:
                logger.warning("free_form LLM call failed: %s", e)
                text = ""
            raw = text or ""
            stripped = re.sub(r"<think>[\s\S]*?</think>", "", raw).strip()
            if not stripped:
                m_think = re.search(r"<think>([\s\S]*?)</think>", raw)
                stripped = m_think.group(1).strip() if m_think else ""

            answer = stripped
            draft_answer = stripped

            def _ff_retry(feedback: str, prior_answer: str):
                """Host (free_form) re-ask: open-text retry, strip think tags."""
                nonlocal n_calls
                retry_user = _build_free_form_retry_prompt(
                    base_user=user_msg, prior_answer=prior_answer,
                    validator_feedback=feedback,
                )
                n_calls += 1
                try:
                    rtext = self.llm.chat(system_prompt, retry_user, max_tokens=2048)
                except Exception as e:
                    logger.warning("free_form retry LLM call failed: %s", e)
                    return None
                new_raw = rtext or ""
                new_stripped = re.sub(r"<think>[\s\S]*?</think>", "", new_raw).strip()
                if not new_stripped:
                    m_think = re.search(r"<think>([\s\S]*?)</think>", new_raw)
                    new_stripped = m_think.group(1).strip() if m_think else ""
                return new_stripped, ""

            answer, events = run_validator_loop(
                self.validators,
                question=question, story=story, options=options, eval_mode=eval_mode,
                answer=answer, reasoning="",
                max_retries=self.max_retries, retry_fn=_ff_retry,
            )

            return RuntimeResult(
                answer=answer,
                skill_id=skill_id,
                n_llm_calls=n_calls,
                thinking="",
                draft_reasoning="",
                rag_context=rag_context or "",
                memory_bullets=memory_bullet_ids,
                memory_subtask=memory_subtask,
                validator_events=events,
                draft_answer=draft_answer,
                skill_ids=skill_ids,
                review_changed=False,
            )

        # ── 1. initial LLM call (Stage 3: solve) ─────────────────────────
        n_calls = 1 + aug.n_aux_llm_calls
        reasoning = ""
        try:
            text = self.llm.chat(system_prompt, base_user, max_tokens=4096)
        except Exception as e:
            logger.warning("initial LLM call failed: %s", e)
            text = ""
        draft_answer, reasoning = _parse_response(text)

        # ── 2. L0 review (Stage 4, optional) ─────────────────────────────
        answer = draft_answer
        review_changed = False
        if self.review_mode == "on" and hasattr(self.router, 'skills_dir'):
            from .routing.l0_review import run_review
            n_calls += 1
            reviewed = run_review(
                llm=self.llm,
                skills_dir=self.router.skills_dir,
                inject_mode=getattr(self.router, 'inject_mode', 'light'),
                story=story,
                question=question,
                options=options,
                draft_answer=draft_answer,
                draft_reasoning=reasoning,
                picked_skills=skill_ids or None,
                lang=getattr(self.router, 'lang', 'en'),
            )
            if reviewed and reviewed != draft_answer:
                review_changed = True
                answer = reviewed
                logger.info("[L0Review] changed %s -> %s", draft_answer, answer)

        # ── 3. validators ─────────────────────────────────────────────────
        def _json_retry(feedback: str, prior_answer: str):
            """Host (mcq) re-ask: JSON-protocol retry, parse the answer letter."""
            nonlocal n_calls
            retry_user = _build_retry_prompt(
                base_user=base_user, prior_answer=prior_answer,
                validator_feedback=feedback,
            )
            n_calls += 1
            try:
                rtext = self.llm.chat(system_prompt, retry_user, max_tokens=1024)
            except Exception as e:
                logger.warning("retry LLM call failed: %s", e)
                return None
            new_answer, _ = _parse_response(rtext)
            return new_answer, ""

        answer, events = run_validator_loop(
            self.validators,
            question=question, story=story, options=options, eval_mode=eval_mode,
            answer=answer, reasoning=reasoning,
            max_retries=self.max_retries, retry_fn=_json_retry,
        )

        return RuntimeResult(
            answer=answer, skill_id=skill_id, n_llm_calls=n_calls,
            thinking=reasoning,
            draft_reasoning=reasoning,
            rag_context=rag_context or "",
            memory_bullets=memory_bullet_ids,
            memory_subtask=memory_subtask,
            validator_events=events,
            draft_answer=draft_answer,
            skill_ids=skill_ids,
            review_changed=review_changed,
        )


def build_default_runtime(
    *,
    llm: LLMClient,
    router: "Router",
    rag_engine: Any = None,
    playbook: str | None = None,
    memory: Any = None,
    enable_scalar_validator: bool = True,
    enable_epistemic_validator: bool = False,
    enable_multi_select_validator: bool = False,
    review_mode: str = "off",
    gate: Any = None,
) -> HarnessRuntime:
    """Convenience factory: wires the default validator stack."""
    validators: list["Validator"] = []
    if enable_scalar_validator:
        from .validators.scalar_procedural import ScalarProceduralValidator
        validators.append(ScalarProceduralValidator())
    if enable_epistemic_validator:
        from .validators.epistemic_calibration import EpistemicCalibrationValidator
        validators.append(EpistemicCalibrationValidator())
    if enable_multi_select_validator:
        from .validators.multi_select_calibration import MultiSelectCalibrationValidator
        validators.append(MultiSelectCalibrationValidator())
    return HarnessRuntime(
        llm=llm, router=router, validators=validators,
        rag_engine=rag_engine, playbook=playbook,
        memory=memory, review_mode=review_mode,
        gate=gate,
    )
