from typing import AsyncGenerator

from pydantic import BaseModel

from src.agent.state import AnswerInput
from src.agent.prompts import (
    get_final_answer_system_prompt,
    build_final_answer_user_prompt,
)
from src.model.llm import llm_stream_call
from src.agent.phases.base import Phase
from src.utils.logger import get_logger
from src.utils.context import ToolContextManager

logger = get_logger(__name__)


class AnswerPhaseOptions(BaseModel):
    model: str
    context_manager: ToolContextManager

    class Config:
        arbitrary_types_allowed = True


class AnswerPhase(Phase):
    """Answer phase that synthesizes final response.

    This phase takes all completed plans and task results and generates
    a comprehensive answer to the user's query.
    """

    def __init__(
        self,
        model: str,
        options: AnswerPhaseOptions,
    ):
        self.model = model
        self.context_manager = options.context_manager

    async def run(self, input: AnswerInput) -> AsyncGenerator[str, None]:
        """Runs answer generation and returns a stream for the response.

        Args:
            input (AnswerInput): Contains query, completed plans, and task results

        Yields:
            str: Chunks of the final answer to the user's query
        """
        logger.info("Answer phase: Generating final response")

        # 1. Format task outputs from ALL plans
        task_outputs = "\n\n---\n\n".join(
            f"Task: {task.description}\nOutput: {input.taskResults.get(task.id).output if input.taskResults.get(task.id) else 'No output'}"
            for plan in input.completedPlans
            for task in plan.tasks
        )

        # 2. Collect sources from context manager
        query_id = self.context_manager.hash_query(input.query)
        pointers = self.context_manager.get_pointers_for_query(query_id)

        sources = [
            {
                "description": p.tool_description,
                "urls": p.source_urls,
            }
            for p in pointers
            if p.source_urls and len(p.source_urls) > 0
        ]

        sources_str = (
            "\n".join(
                f"{s['description']}: {', '.join(s['urls'])}"
                for s in sources
            )
            if sources
            else ""
        )

        # 3. Build the final answer prompt
        system_prompt = get_final_answer_system_prompt()
        user_prompt = build_final_answer_user_prompt(
            query=input.query,
            task_outputs=task_outputs,
            sources=sources_str,
        )

        # 4. Stream the response
        async for chunk in llm_stream_call(
            prompt=user_prompt,
            system_prompt=system_prompt,
            model=self.model,
        ):
            yield chunk

        print()
        logger.info("Answer phase: Final response generated")
