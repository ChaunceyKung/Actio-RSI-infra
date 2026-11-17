"""Epistemic Calibration Validator for ICTBench Q3 (verdict) questions.

v2 signal: "absolute statement × mixed/qualified evidence". The model often
predicts B (否) on cases where ground truth is C (无法确定) by citing a
single piece of qualifying evidence ("但其实…", "并未完全…", "不仅仅是…",
"内心充满矛盾…") and treating it as a refutation. ICTBench's rubric is
stricter: 否 requires the story to *directly contradict* the claim's
specific assertion, not merely complicate it.

The validator fires when:
  (1) the statement under test makes an absolute / total / pure claim
      (e.g. "完全恢复", "主要是 X", "已明确意识到", "确实处于"); AND
  (2) the model's reasoning cites mixed/qualifying/transitional evidence
      ("但同时", "并未完全", "尚未决定", "内心矛盾", "为了…给…看", etc.).

Under those conditions, the model is using partial counter-evidence to
refute an absolute claim — which is the textbook trigger for "无法确定".
"""

from __future__ import annotations

import re

from .base import Validator, ValidationResult


def _is_verdict_question(options: dict[str, str]) -> bool:
    return options.get("A") == "是" and options.get("B") == "否" and options.get("C") == "无法确定"


_ABSOLUTE_STATEMENT_PATTERNS = re.compile(
    r"完全(?:恢复|消除|实现|信任|理解|认同|相信|放弃|意识|改变|转移|转变)|"
    r"已(?:经)?完全|彻底(?:恢复|放下|认同|改变|消除)|"
    r"主要(?:是|驱动力|驱动身份|动机|原因|目的|因素|功能|来源|考量)|"
    r"纯粹(?:是|出于)|"
    r"准确(?:判断|理解|意识|把握|认识|概括|描述)|"
    r"明确(?:意识到|知道|认识到|认定|表明|信息|信号|意图|认同|信念|地)|"
    r"确实(?:处于|属于|是|意味着|实现|表明)|"
    r"已经(?:明确|成功|实现|达到|完成|从|彻底)|"
    r"成功(?:[^。，]{0,12}(?:传达|实现|完成|说服|劝服|改变|获得))|"
    r"百分(?:之?百|百)|绝对(?:[^。，]{0,5}(?:不|是|没有|相信))|"
    r"完全恢复到|没有任何(?:怀疑|疑虑|犹豫)|"
    r"全部(?:[^。，]{0,5}(?:来源|出于|因为|归因))|"
    r"真实(?:驱动力|目的|动机|意图|原因)|"
    r"不可(?:取消|改变|逆转|否定)|"
    r"等同于(?:直接|明确)?|"
    r"可以(?:确定|断定|据此|认定)|"
    r"据此(?:可以|判断|确定|认为|断定)|"
    r"已经从[^。]{0,30}(?:转变|转化|进入|跨越|发展)"
)

_MIXED_EVIDENCE_PATTERNS = re.compile(
    r"不仅(?:仅)?(?:是|包含|有)|不只是|"
    r"既[^。]{0,30}又|"
    r"但(?:同时|又|其实|也(?:有|存在|包含)|仍(?:然|有|存在)|并未|并不)|"
    r"并未(?:完全|彻底|消除|放弃|实现|认同|发生|改变|提及|形成|表明|说过)|"
    r"尚未(?:决定|确定|明确|完成|放弃)|"
    r"(?:内心|心理|情绪|状态)[^。，]{0,8}(?:矛盾|挣扎|犹豫|复杂|纠结|混乱)|"
    r"处于[^。]{0,15}(?:之间|状态|过程|阶段)|"
    r"也(?:可能|或许|不一定|有可能)|"
    r"为了[^。]{0,15}(?:给|让)[^。]{0,10}看|出于[^。]{0,10}考虑|"
    r"复杂的(?:情绪|心理|状态|感受)|"
    r"另有(?:目的|考虑|动机|原因)|"
    r"并非(?:完全|出于|因为|意味着|而是|为了|的)|"
    r"也存在|还有|更有可能|"
    r"不足以(?:断定|确定|认定|表明|证明|支持|说明|让)|"
    r"仅(?:仅|凭)(?:一次|一项|此|从|看到|描述)|"
    r"只是(?:背景|一种|表面|出于|为了|因为)|"
    r"更多(?:是|出于|来源于|代表)[^。]{0,30}(?:而非|而不是)|"
    r"更符合[^。]{0,20}(?:而非|而不是)|"
    r"无法(?:断定|确认|确证|认定|判断)|"
    r"不能(?:认定|断定|确认|说明|断言)|"
    r"并不(?:完全|意味着|代表|等同|足以)|"
    r"这(?:仅|只)(?:是|表明|代表)|"
    r"结合[^。]{0,30}(?:并未|不足|无法|难以|没有)|"
    r"代表他[^。]{0,30}(?:但|并未)|"
    r"意味着[^。]{0,15}(?:但|并未|并不)|"
    r"并未提供证据|未提及|文中并未"
)


def _has_absolute_claim(statement: str) -> int:
    return len(_ABSOLUTE_STATEMENT_PATTERNS.findall(statement))


def _has_mixed_evidence(reasoning: str) -> int:
    return len(_MIXED_EVIDENCE_PATTERNS.findall(reasoning))


def _extract_statement(question: str) -> str:
    """Pull the statement out of the Q3 prompt format ('「…」')."""
    m = re.search(r"「([^」]+)」", question)
    return m.group(1) if m else question


class EpistemicCalibrationValidator(Validator):
    """Catch A/B verdicts on absolute claims rebutted by mixed evidence.

    Only fires on verdict-type questions (options A=是, B=否, C=无法确定).
    """

    def __init__(self, mixed_threshold: int = 1, absolute_threshold: int = 1):
        self.mixed_threshold = mixed_threshold
        self.absolute_threshold = absolute_threshold

    def validate(
        self,
        *,
        question: str,
        story: str,
        options: dict[str, str],
        current_answer: str,
        reasoning: str = "",
        eval_mode: str | None = None,
    ) -> ValidationResult:
        if not _is_verdict_question(options):
            return ValidationResult(valid=True, rationale="not a verdict question")

        if current_answer == "C":
            return ValidationResult(valid=True, rationale="already chose C")

        if not reasoning:
            return ValidationResult(valid=True, rationale="no reasoning to analyze")

        statement = _extract_statement(question)
        abs_n = _has_absolute_claim(statement)
        mix_n = _has_mixed_evidence(reasoning)

        if abs_n >= self.absolute_threshold and mix_n >= self.mixed_threshold:
            return ValidationResult(
                valid=False,
                feedback=(
                    "请重新审视：该陈述包含「完全/明确/主要是/已实现」这类绝对表述，"
                    "而你在推理中却引用了「但同时/并未完全/不仅仅是/内心矛盾/为了给…看」等"
                    "混合或带保留的证据。在 ICTBench 的判定规则下：\n"
                    "  · 选择 A(是)：故事直接、无保留地支持该陈述的完整主张；\n"
                    "  · 选择 B(否)：故事直接 *否定* 或 *与该陈述相反* 的具体事实；\n"
                    "  · 选择 C(无法确定)：故事仅提供部分、混合或带条件的证据，"
                    "不足以对该陈述的绝对断言（如「完全」「主要是」「明确」）做出严格判定。\n\n"
                    "你引用的证据是在 *弱化或限定* 该陈述，而不是直接给出相反的事实。"
                    "请重新选择，并优先考虑 C（无法确定）。"
                ),
                rationale=f"absolute_claim={abs_n} mixed_evidence={mix_n}",
            )

        return ValidationResult(
            valid=True,
            rationale=f"signals weak: absolute={abs_n} mixed={mix_n}",
        )
