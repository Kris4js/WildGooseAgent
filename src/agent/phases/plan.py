from typing import Optional
from pydantic import BaseModel, Field

from src.agent.state import PlanInput, Task, Plan, TaskType, TaskStatus, TaskResult
from src.agent.prompts import (
    get_plan_system_prompt,
    build_plan_user_prompt,
)
from src.model.llm import llm_call_with_structured_output
from src.utils.logger import get_logger

logger = get_logger(__name__)


# ============================================================================
# Plan Schema
# ============================================================================


class TaskSchema(BaseModel):
    """Schema for a single task in the plan."""

    id: str = Field(..., description="Unique identifier for the task")
    description: str = Field(..., description="Description of what this task should accomplish")
    taskType: str = Field(..., description="Type of task: 'use_tools' or 'reason'")
    dependsOn: list[str] = Field(default_factory=list, description="List of task IDs this task depends on")


class PlanSchema(BaseModel):
    """Schema for the plan output from the LLM."""

    summary: str = Field(..., description="Summary of the plan")
    tasks: list[TaskSchema] = Field(..., description="List of tasks to execute")


class PlanPhaseOptions(BaseModel):
    """Options for the plan phase."""

    model: str


# ============================================================================
# Plan Phase
# ============================================================================


class PlanPhase:
    """Plan phase that creates task lists without selecting tools.

    This phase analyzes the query and creates a list of tasks with
    dependencies to accomplish the goal.
    """

    def __init__(
        self,
        options: PlanPhaseOptions,
    ):
        self.model = options.model

    async def run(
        self,
        input: PlanInput,
    ) -> Plan:
        """Create a plan with tasks to accomplish the query.

        Args:
            input (PlanInput): Contains query, understanding, prior plans,
                             and optional guidance

        Returns:
            Plan: A plan with tasks and their dependencies
        """
        logger.info("Plan phase: Starting planning iteration")

        # Format entities string
        entities_str = (
            ", ".join([f"{e.type}: {e.value}" for e in input.understanding.entities])
            if len(input.understanding.entities) > 0
            else "None identified"
        )

        # Format prior work summary if available
        prior_work_summary = (
            self._format_prior_work(input.priorPlans, input.priorResults)
            if input.priorPlans and len(input.priorPlans) > 0
            else None
        )

        system_prompt = get_plan_system_prompt()
        user_prompt = build_plan_user_prompt(
            query=input.query,
            intent=input.understanding.intent,
            entities=entities_str,
            prior_work_summary=prior_work_summary,
            guidance=input.guidanceFromReflection,
        )

        # Call LLM with structured output
        response = await llm_call_with_structured_output(
            prompt=user_prompt,
            system_prompt=system_prompt,
            model=self.model,
            output_schema=PlanSchema,
        )

        # Generate unique task IDs that don't conflict with prior plans
        iteration = len(input.priorPlans) + 1 if input.priorPlans else 1
        id_prefix = f"iter{iteration}_"

        # Map to Task type with taskType and dependencies
        tasks: list[Task] = []
        for t in response.tasks:
            task = Task(
                id=id_prefix + t.id,
                description=t.description,
                status=TaskStatus.PENDING,
                taskType=TaskType(t.taskType),
                dependsOn=[id_prefix + dep for dep in t.dependsOn],
                toolCalls=None,
            )
            tasks.append(task)

        # Create and return the plan
        return Plan(
            summary=response.summary,
            tasks=tasks,
        )

    def _format_prior_work(
        self,
        plans: Optional[list[Plan]],
        task_results: Optional[dict[str, TaskResult]] = None,
    ) -> str:
        """Format prior work from completed plans for context.

        Args:
            plans: List of previously completed plans
            task_results: Optional map of task IDs to their results

        Returns:
            str: Formatted summary of prior work
        """
        if not plans:
            return ""

        parts: list[str] = []

        for i, plan in enumerate(plans):
            parts.append(f"Pass {i + 1}: {plan.summary}")

            for task in plan.tasks:
                result = task_results.get(task.id) if task_results else None
                status = "✓" if result else "✗"
                parts.append(f"  {status} {task.description}")

        return "\n".join(parts)
