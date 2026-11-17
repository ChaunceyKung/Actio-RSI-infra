"""Multi-Select Calibration Validator for ICTBench Q2 (multi-select).

Triggers when the model selects >= N options on a multi_select task and
asks it to (1) cite story evidence for each selected option and (2) rule
out the five ICTBench distractor categories. Addresses the high
over-selection rate observed in baseline runs (avg +1.11 extra items;
~74% of Q2 errors are pure over-selection).

Operates on the free_form output path: `current_answer` is the raw text
returned by the LLM, which the validator parses itself.
"""

from __future__ import annotations

from .base import Validator, ValidationResult


class MultiSelectCalibrationValidator(Validator):
    """Post-hoc audit for ICTBench multi-select selections.

    The validator parses the raw answer text into a set of letters. If the
    model selected fewer than ``min_audit_threshold`` items, the answer is
    accepted as-is (over-selection is the dominant failure mode; aggressive
    audit on small selections risks destabilising correct ones). Otherwise
    a retry is requested with structured per-item audit instructions.
    """

    def __init__(self, min_audit_threshold: int = 3):
        self.min_audit_threshold = min_audit_threshold

    def applies(self, *, eval_mode: str | None = None) -> bool:
        return eval_mode == "multi_select"

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
        if eval_mode != "multi_select":
            return ValidationResult(valid=True, rationale="not a multi_select task")

        from ..parsers import parse_multi_select_response
        selected = parse_multi_select_response(current_answer)

        if len(selected) < self.min_audit_threshold:
            return ValidationResult(
                valid=True,
                rationale=f"selected {len(selected)} < threshold {self.min_audit_threshold}",
            )

        return ValidationResult(
            valid=False,
            feedback=(
                f"你刚才选择了 {len(selected)} 项：{','.join(selected)}。"
                "经验上，模型在这类题上倾向于 **过选**（多选 1-2 项）。"
                "ICTBench 的干扰项通常按以下五类陷阱构造：\n"
                "  (a) 混淆主体：把 X 的状态/行为误归给 Y；\n"
                "  (b) 反向归因：把「证据 → 结论」改写成「证据 → 相反结论」；\n"
                "  (c) 过度推断：在原文未给出的程度/范围上做扩展；\n"
                "  (d) 表层归因：用人物的公开说法代替其真实信念/意图；\n"
                "  (e) 无中生有：引入故事中根本未出现的元素。\n\n"
                "请执行下列 *偏向于删除* 的审查流程：\n"
                f"  1. 在你选中的 {len(selected)} 项中，**先指出哪一项证据最薄弱、"
                "最有可能落入 (a)-(e) 中某一类陷阱**——你必须挑出一项作为「删除候选」，"
                "不能说全部同样有力。\n"
                "  2. 对这一「删除候选」项做严格检验：能否从故事中引用一句 **直接陈述**"
                "（而非间接推断、不是常识补全）支持它？若做不到、或它落入某一类陷阱 → 移除。\n"
                "  3. 对剩余每一项重复同样的检验。当出现疑问时，**默认移除**。\n"
                "  4. 最后再扫一眼未选项：若其中有一项有 *无法被忽略的直接证据*，再补入。\n\n"
                "判断准则：**宁可少选一个有疑虑的项，也不要保留一个证据薄弱的项。**\n\n"
                "审查完成后，请在最后一行重新输出 JSON：\n"
                "{\"answer\": [\"X\", \"Y\", ...]}"
            ),
            rationale=f"selected {len(selected)} >= {self.min_audit_threshold}, triggering removal-biased audit",
        )
