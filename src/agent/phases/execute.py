from typing import Optional, override
from pydantic import BaseModel

from src.agent.state import ExecuteInput, TaskResult
from src.agent.prompts import get_execute_system_prompt, build_execute_user_prompt
from src.model.llm import llm_call
from src.agent.phases.base import Phase


class ExecutePhaseOptions(BaseModel):
    """Options for the execute phase."""

    model: str


class ExecutePhase(Phase):
    """Execute phase for "reason" tasks using the LLM.

    Called only for tasks that require analysis, comparison, or synthesis.
    Data has already been gathered and is passed in as contextData.
    """

    def __init__(
        self,
        options: ExecutePhaseOptions,
    ):
        self.model: str = options.model

    @override
    async def run(self, input: ExecuteInput) -> TaskResult:
        """Execute a reasoning task.

        Args:
            input (ExecuteInput): Contains query, task, plan, and context data

        Returns:
            TaskResult: The task ID and output from the reasoning
        """
        system_prompt = get_execute_system_prompt()
        user_prompt = build_execute_user_prompt(
            query=input.query,
            task_description=input.task.description,
            context_data=input.contextData,
        )

        response = await llm_call(
            prompt=user_prompt,
            system_prompt=system_prompt,
            model=self.model,
        )

        # Normalize response to string
        output = response.content if hasattr(response, "content") else str(response)

        return TaskResult(
            taskId=input.task.id,
            output=output,
        )
