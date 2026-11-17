"""Host-agnostic module orchestration for the agent harness.

This module factors the harness's *integration logic* out of
``HarnessRuntime.answer_one`` so it can be reused by more than one
"host" (answering substrate):

  - host A: ``HarnessRuntime.answer_one`` — JSON answer protocol, calls
    its own ``LLMClient``, parses with ``_parse_response`` (used by
    ``examples/`` scripts).
  - host B: ``eval/run_tomeval_harness.py`` — ToMEval's ``\\boxed{}``
    protocol, option shuffling, batched ``ContentClient`` calls, and
    ToMEval's judge/metrics.

The orchestration here is the actual harness IP — *which* modules fire
(gate → skill → rag → memory) and *how* the validator-retry loop is
sequenced. It deliberately knows nothing about prompt formatting, the
LLM transport, or answer parsing; those are substrate and stay with the
host. The validator loop reaches back into the host for a re-ask through
the ``retry_fn`` callback.

Two exports:

  - ``ModuleOrchestrator.augment`` runs the pre-LLM module pipeline and
    returns a structured ``Augmentation`` (no prompt, no main LLM call).
  - ``run_validator_loop`` runs the post-LLM validator orchestration,
    delegating any LLM re-ask to ``retry_fn``.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable

logger = logging.getLogger(__name__)


@dataclass
class Augmentation:
    """Structured pre-LLM module outputs.

    Produced by :meth:`ModuleOrchestrator.augment`. The host injects these
    into its own prompt (in its own wording) and owns the answering LLM
    call.
    """

    skill_id: str | None = None
    skill_ids: list[str] = field(default_factory=list)
    skill_body: str | None = None
    rag_context: str | None = None
    playbook_text: str | None = None
    memory_bullet_ids: list[str] = field(default_factory=list)
    memory_subtask: str = ""
    gate_decision: Any = None
    n_aux_llm_calls: int = 0  # router (and any aux) LLM calls already spent


class ModuleOrchestrator:
    """Runs gate → skill → rag → memory and returns an :class:`Augmentation`.

    Host-agnostic: builds no prompt and makes no main answering LLM call.
    Mirrors the module pipeline that previously lived inline in
    ``HarnessRuntime.answer_one``.
    """

    def __init__(
        self,
        *,
        router: Any,
        rag_engine: Any = None,
        memory: Any = None,
        playbook: str | None = None,
        gate: Any = None,
    ) -> None:
        self.router = router
        self.rag_engine = rag_engine
        self.memory = memory
        self.playbook = playbook
        self.gate = gate

    def augment(
        self,
        *,
        question: str,
        story: str,
        options: dict[str, str],
        gate_eval_mode: str | None = None,
        raw_metadata: dict | None = None,
    ) -> Augmentation:
        """Run the module pipeline for a single sample.

        ``gate_eval_mode`` is the coarse mode the gate keys on
        ("mcq"/"free_form"); it is host-supplied and is distinct from the
        fine-grained validator ``eval_mode``.
        """
        decision = self.router.route(
            question=question, story=story, options=options,
        )
        skill_id = decision.skill_id
        skill_ids = decision.skill_ids

        # ── Module Gate: decide which modules to activate ─────────────────
        gate_decision = None
        if self.gate is not None:
            gate_decision = self.gate.decide(
                question=question, story=story, options=options,
                eval_mode=gate_eval_mode,
                raw_metadata=raw_metadata,
            )
            logger.info(
                "[Gate] skill=%s rag=%s memory=%s (%s)",
                gate_decision.use_skill, gate_decision.use_rag,
                gate_decision.use_memory, gate_decision.rationale,
            )

        # ── resolve skill body (multi-skill aware) ────────────────────────
        skill_body = None
        if gate_decision is None or gate_decision.use_skill:
            if skill_ids and hasattr(self.router, 'get_skill_bodies'):
                skill_body = self.router.get_skill_bodies(skill_ids)
            elif skill_id and hasattr(self.router, 'get_skill_body'):
                skill_body = self.router.get_skill_body(skill_id)
            if skill_id and skill_body is None:
                logger.warning("router picked skill_id=%s but skill body is None", skill_id)

        rag_context = None
        if (gate_decision is None or gate_decision.use_rag) and self.rag_engine is not None:
            try:
                rag_context = self.rag_engine.retrieve(
                    query=question, story=story, options=options,
                )
            except Exception as e:
                logger.warning("RAG retrieve failed: %s", e)

        playbook_text = self.playbook
        memory_bullet_ids: list[str] = []
        memory_subtask = ""
        if (gate_decision is None or gate_decision.use_memory) and self.memory is not None:
            try:
                recall_result = self.memory.recall(
                    question, context=story,
                )
                selected = recall_result.as_text()
                if selected:
                    playbook_text = selected
                    memory_bullet_ids = recall_result.bullet_ids
                    memory_subtask = recall_result.predicted_subtask
                    logger.info(
                        "[Memory] recall -> subtask=%s, %d bullets selected",
                        recall_result.predicted_subtask, len(recall_result.bullets),
                    )
                else:
                    logger.debug("[Memory] recall returned no relevant bullets")
            except Exception as e:
                logger.warning("Memory recall failed: %s", e)

        return Augmentation(
            skill_id=skill_id,
            skill_ids=skill_ids,
            skill_body=skill_body,
            rag_context=rag_context,
            playbook_text=playbook_text,
            memory_bullet_ids=memory_bullet_ids,
            memory_subtask=memory_subtask,
            gate_decision=gate_decision,
            n_aux_llm_calls=decision.n_llm_calls,
        )


# Signature of the host-provided re-ask callback. Given the validator's
# feedback and the prior answer, it re-asks the host's LLM (in whatever
# prompt format / transport the host owns) and returns the new
# (answer, reasoning). Returning ``None`` signals the LLM call failed and
# the retry loop for this validator should abort (mirrors the inline
# break-on-exception in the original answer_one).
RetryFn = Callable[[str, str], "tuple[str, str] | None"]


def run_validator_loop(
    validators: list,
    *,
    question: str,
    story: str,
    options: dict[str, str],
    eval_mode: str | None,
    answer: str,
    reasoning: str,
    max_retries: int,
    retry_fn: RetryFn,
) -> "tuple[str, list[dict]]":
    """Run the validator-retry orchestration. Returns (final_answer, events).

    Host-agnostic: a validator that produces ``suggested_answer`` is
    applied by direct substitution (no LLM); a validator that produces
    ``feedback`` triggers an LLM re-ask through ``retry_fn`` — which is
    the only seam back into the host's substrate.

    ``reasoning`` is the model's reasoning from the initial answer; it is
    passed to the *first* ``validate`` only. Re-validation after a retry
    uses an empty reasoning, matching the original inline behavior.
    """
    events: list[dict] = []
    for v in validators:
        if not v.applies(eval_mode=eval_mode):
            continue
        result = v.validate(
            question=question, story=story, options=options,
            current_answer=answer,
            reasoning=reasoning, eval_mode=eval_mode,
        )
        events.append({
            "validator": v.__class__.__name__,
            "valid": result.valid,
            "rationale": result.rationale,
            "had_suggestion": bool(result.suggested_answer),
        })

        if result.valid:
            continue

        if result.suggested_answer:
            logger.info(
                "[%s] substituting %s -> %s (%s)",
                v.__class__.__name__, answer, result.suggested_answer, result.rationale,
            )
            answer = result.suggested_answer
            continue

        for retry_idx in range(max_retries):
            out = retry_fn(result.feedback, answer)
            if out is None:
                # host's LLM re-ask failed → abort retries for this validator
                break
            new_answer, _new_reasoning = out
            if new_answer:
                answer = new_answer
            result = v.validate(
                question=question, story=story, options=options,
                current_answer=answer,
                eval_mode=eval_mode,
            )
            events.append({
                "validator": v.__class__.__name__,
                "valid": result.valid,
                "rationale": result.rationale,
                "retry": retry_idx + 1,
            })
            if result.valid:
                break

    return answer, events
