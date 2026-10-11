# Test-only original SOTOPIA evaluator definitions. MIT. Never a product evaluator.
import abc
import logging
from typing import Any
from typing import Generic
from typing import TypeVar
import gin
from pydantic import BaseModel
from pydantic import validate_call
from actio._vendor.sotopia import LLMEvalBaseModel
from actio._vendor.sotopia import EvaluationForAgents
from actio._vendor.sotopia import PydanticOutputParser
T_eval_dim = TypeVar("T_eval_dim", bound=BaseModel)
log = logging.getLogger("evaluators")
# Test-side message seam replaces the simulator message dependency.
class Message(BaseModel):
    text: str
    def to_natural_language(self): return self.text
def supports_response_schema(**kwargs):
    raise AssertionError("transport seam must be injected by characterization")
async def agenerate(**kwargs):
    raise AssertionError("generation seam must be injected by characterization")

class Evaluator(abc.ABC):
    def __init__(self) -> None:
        pass

    @abc.abstractmethod
    def __call__(
        self, turn_number: int, messages: list[tuple[str, Message]], **kwargs: Any
    ) -> list[tuple[str, tuple[tuple[str, int | float | bool], str]]]:
        raise NotImplementedError

    @abc.abstractmethod
    async def __acall__(
        self, turn_number: int, messages: list[tuple[str, Message]], **kwargs: Any
    ) -> list[tuple[str, tuple[tuple[str, int | float | bool], str]]]:
        raise NotImplementedError


class EpisodeLLMEvaluator(Evaluator, Generic[T_eval_dim]):
    def __init__(
        self,
        model_name: str,
        response_format_class: type[EvaluationForAgents[T_eval_dim]],
    ) -> None:
        self.model_name = model_name
        self.prompt = ""
        self.response_format_class = response_format_class

    def __call__(
        self, turn_number: int, messages: list[tuple[str, Message]], **kwargs: Any
    ) -> list[tuple[str, tuple[tuple[str, int | float | bool], str]]]:
        raise NotImplementedError(
            "ReachGoalLLMEvaluator is not implemented for synchronous evaluation"
        )

    @gin.configurable
    @validate_call
    async def __acall__(
        self,
        turn_number: int,
        messages: list[tuple[str, Message]] | None,
        history: str = "",
        temperature: float | None = 0.0,
        **kwargs: Any,
    ) -> list[tuple[str, tuple[tuple[str, int | float | bool], str]]]:
        # filter did nothing
        if not history and messages:
            messages_filtered = [
                (x, y)
                for x, y in messages
                if "did nothing" not in y.to_natural_language()
            ]
            history = "\n".join(
                [
                    (
                        f"{x} {y.to_natural_language()}"
                        if x != "Environment"
                        else y.to_natural_language()
                    )
                    for x, y in messages_filtered
                ]
            )

        try:
            # Count actual participating agents (exclude Environment)
            participating_agents = set()
            if messages:
                for speaker, _ in messages:
                    if speaker != "Environment":
                        participating_agents.add(speaker)
            num_agents = len(participating_agents)

            # Build explicit agent label instruction to avoid ambiguous dynamic keys in structured output
            agent_instruction = ""
            if num_agents > 0:
                agent_instruction = (
                    "There are exactly "
                    + str(num_agents)
                    + " agents. Under the 'evaluations' field, use exactly these keys: "
                    + "["
                    + ", ".join([f'"agent_{i+1}"' for i in range(num_agents)])
                    + "] (no other keys).\n"
                )

            # Use structured output if model supports it (not just custom/structured endpoints)
            use_structured_output = self.model_name.startswith(
                "custom/structured"
            ) or supports_response_schema(model=self.model_name)

            response: EvaluationForAgents[T_eval_dim] = await agenerate(
                model_name=self.model_name,
                template="""{history}
                    Based on previous interactions, evaluate how well participants achieve their goals.
                    {agent_instruction}
                    Please follow the format:
                    {format_instructions}
                """,
                input_values=dict(history=history, agent_instruction=agent_instruction),
                output_parser=PydanticOutputParser[self.response_format_class](  # type: ignore[name-defined]
                    pydantic_object=self.response_format_class
                ),
                temperature=temperature,
                structured_output=use_structured_output,
            )
            response_list = []
            # Only process evaluations for the actual number of agents
            for i, evaluation in enumerate(
                list(response.evaluations.values())[:num_agents]
            ):
                # Map agent names to expected format (agent_1, agent_2, etc.)
                agent_key = f"agent_{i+1}"
                for dimension in evaluation.model_dump().keys():
                    response_list.append(
                        (
                            agent_key,
                            (
                                (
                                    dimension,
                                    evaluation.model_dump()[dimension][1],
                                ),
                                evaluation.model_dump()[dimension][0],
                            ),
                        )
                    )
            return response_list
        except Exception as e:
            print(e)
            log.debug(f"[red] Failed to generate environment response. {e}")
            return []
