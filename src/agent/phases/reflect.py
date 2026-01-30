from typing import Optional
from pydantic import BaseModel, Field

from src.agent.state import ReflectInput, ReflectionResult, Plan, TaskResult
from src.agent.prompts import (
    get_reflect_system_prompt,
    build_reflect_user_prompt,
)
from src.model.llm import llm_call_with_structured_output
from src.utils.logger import get_logger

logger = get_logger(__name__)


# ============================================================================
# Reflection Schema
# ============================================================================


class ReflectionSchema(BaseModel):
    """Schema for the reflection response from the LLM."""

    isComplete: bool = Field(
        ..., description="Whether the gathered data is sufficient to answer the query"
    )
    reasoning: str = Field(..., description="Explanation of the completion decision")
    missingInfo: list[str] = Field(default_factory=list, description="List of missing information")
    suggestedNextSteps: str = Field(default="", description="Suggested next steps if incomplete")


# ============================================================================
# Reflect Phase Options
# ============================================================================


class ReflectPhaseOptions(BaseModel):
    """Options for the reflect phase."""

    model: str
    maxIterations: Optional[int] = 3


# ============================================================================
# Reflect Phase
# ============================================================================


class ReflectPhase:
    """Reflect phase that evaluates if the task is complete.

    This phase analyzes the current plan, task results, and determines
    if enough information has been gathered to answer the query.
    """

    def __init__(
        self,
        options: ReflectPhaseOptions,
    ):
        self.model = options.model
        self.max_iterations: int = options.maxIterations or 3

    async def run(self, input: ReflectInput) -> ReflectionResult:
        """Evaluate if enough information has been gathered.

        Args:
            input (ReflectInput): Contains query, understanding, completed plans,
                                 task results, and iteration number

        Returns:
            ReflectionResult: Contains completion status, reasoning, and next steps
        """
        logger.info("Reflect phase: Evaluating task completion")

        # Force completion on max iterations
        if input.iteration >= self.max_iterations:
            return ReflectionResult(
                isComplete=True,
                reasoning=f"Reached maximum iterations ({self.max_iterations}). Proceeding with available data.",
                missingInfo=[],
                suggestedNextSteps="",
            )

        completed_work = self._format_completed_work(input.completedPlans, input.taskResults)

        system_prompt = get_reflect_system_prompt()
        user_prompt = build_reflect_user_prompt(
            query=input.query,
            intent=input.understanding.intent,
            completed_work=completed_work,
            iteration=input.iteration,
            max_iterations=self.max_iterations,
        )

        response = await llm_call_with_structured_output(
            prompt=user_prompt,
            system_prompt=system_prompt,
            model=self.model,
            output_schema=ReflectionSchema,
        )

        result = ReflectionResult(
            isComplete=response.isComplete,
            reasoning=response.reasoning,
            missingInfo=response.missingInfo,
            suggestedNextSteps=response.suggestedNextSteps,
        )

        logger.info(
            f"Reflect phase: Task complete={result.isComplete}, reasoning={result.reasoning}"
        )

        return result

    def build_planning_guidance(self, reflection: ReflectionResult) -> str:
        """Builds guidance string from reflection result for the next planning iteration.

        Args:
            reflection: The reflection result to build guidance from

        Returns:
            str: Formatted guidance for the next planning iteration
        """
        parts: list[str] = [reflection.reasoning]

        if len(reflection.missingInfo) > 0:
            parts.append(f"Missing information: {', '.join(reflection.missingInfo)}")

        if len(reflection.suggestedNextSteps) > 0:
            parts.append(f"Suggested next steps: {reflection.suggestedNextSteps}")

        return "\n".join(parts)

    def _format_completed_work(
        self,
        plans: list[Plan],
        task_results: dict[str, TaskResult],
    ) -> str:
        """Formats all completed work from prior plans for LLM context.

        Args:
            plans: List of completed plans
            task_results: Map of task IDs to their results

        Returns:
            str: Formatted string of completed work
        """
        parts: list[str] = []

        for i, plan in enumerate(plans):
            parts.append(f"--- Pass {i + 1}: {plan.summary} ---")

            for task in plan.tasks:
                result = task_results.get(task.id)
                output = result.output if result else "No output"
                status = "✓" if result else "✗"
                parts.append(f"{status} {task.description}: {output}")

        return "\n".join(parts)
