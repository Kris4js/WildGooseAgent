from typing import Optional, Any, AsyncGenerator, Callable
from pydantic import BaseModel
from typing import Protocol

from src.agent.state import (
    Phase,
    Plan,
    Understanding,
    TaskResult,
    ReflectionResult,
    UnderstandInput,
    PlanInput,
    ReflectInput,
    AnswerInput,
)
from src.agent.task_executor import TaskExecutor, TaskExecutorCallbacks, TaskExecutorOptions
from src.agent.phases import (
    UnderstandPhase,
    PlanPhase,
    PlanPhaseOptions,
    ExecutePhase,
    ExecutePhaseOptions,
    ReflectPhase,
    ReflectPhaseOptions,
    AnswerPhase,
    AnswerPhaseOptions,
)
from src.agent.tool_executor import ToolExecutor, ToolExecutorOptions
from src.utils.logger import get_logger
from src.utils.context import ToolContextManager

logger = get_logger(__name__)
from src.utils.message_history import MessageHistory
from src.tools import get_tools


# ============================================================================
# Constants
# ============================================================================

DEFAULT_MAX_ITERATIONS = 5


# ============================================================================
# Callbacks Interface
# ============================================================================


class AgentCallbacks(TaskExecutorCallbacks, Protocol):
    """Callbacks for observing agent execution.

    Extends TaskExecutorCallbacks with agent-specific callbacks for phase
    transitions and iteration monitoring.
    """

    # Phase transitions
    onPhaseStart: Optional[Callable[[Phase], None]] = None
    onPhaseComplete: Optional[Callable[[Phase], None]] = None

    # Understanding
    onUnderstandingComplete: Optional[Callable[[Understanding], None]] = None

    # Planning
    onPlanCreated: Optional[Callable[[Plan, int], None]] = None

    # Reflection
    onReflectionComplete: Optional[Callable[[ReflectionResult, int], None]] = None
    onIterationStart: Optional[Callable[[int], None]] = None

    # Answer
    onAnswerStart: Optional[Callable[[], None]] = None
    onAnswerStream: Optional[Callable[[AsyncGenerator[str, None]], None]] = None


# ============================================================================
# Agent Options
# ============================================================================


class ModelConfig(BaseModel):
    """Model configuration for different model sizes."""

    small: str = "google/gemini-2.5-flash-lite-preview-09-2025"
    large: str = "google/gemini-3-flash-preview"


class AgentOptions(BaseModel):
    """Configuration options for the Agent."""

    model: ModelConfig
    callbacks: Optional[Any] = None
    maxIterations: Optional[int] = DEFAULT_MAX_ITERATIONS


# ============================================================================
# Agent Implementation
# ============================================================================


class Agent:
    """Agent - Planning with just-in-time tool selection, parallel task execution,
    and iterative reflection loop.

    Architecture:
    1. Understand: Extract intent and entities from query (once)
    2. Plan: Create task list with taskType and dependencies
    3. Execute: Run tasks with just-in-time tool selection
    4. Reflect: Evaluate if we have enough data or need another iteration
    5. Answer: Synthesize final answer from all task results

    The Plan → Execute → Reflect loop repeats until reflection determines
    we have sufficient data or max iterations is reached.
    """

    def __init__(self, options: AgentOptions):
        self.modelConfig = options.model
        self.callbacks = options.callbacks or {}
        self.maxIterations = options.maxIterations or DEFAULT_MAX_ITERATIONS
        self.contextManager = ToolContextManager(".dexter/context", self.modelConfig.large)

        # Initialize phases
        self.understandPhase = UnderstandPhase(model=self.modelConfig.small)
        self.planPhase = PlanPhase(options=PlanPhaseOptions(model=self.modelConfig.large))
        self.executePhase = ExecutePhase(
            options=ExecutePhaseOptions(model=self.modelConfig.large)
        )
        self.reflectPhase = ReflectPhase(
            options=ReflectPhaseOptions(
                model=self.modelConfig.large, maxIterations=self.maxIterations
            )
        )
        self.answerPhase = AnswerPhase(
            model=self.modelConfig.large,
            options=AnswerPhaseOptions(
                model=self.modelConfig.large,
                context_manager=self.contextManager,
            ),
        )

        # Initialize executors
        toolExecutor = ToolExecutor(
            options=ToolExecutorOptions(
                tools=get_tools(model=self.modelConfig.small),
                context_manager=self.contextManager,
                model=self.modelConfig.small,
            )
        )

        self.taskExecutor = TaskExecutor(
            options=TaskExecutorOptions(
                tool_executor=toolExecutor,
                execute_phase=self.executePhase,
                context_manager=self.contextManager,
            )
        )

    def _call(self, name: str, *args, **kwargs) -> None:
        """Safely call a callback method if it exists."""
        callback = getattr(self.callbacks, name, None)
        if callback:
            callback(*args, **kwargs)

    async def _call_async(self, name: str, *args, **kwargs) -> None:
        """Safely call an async callback method if it exists."""
        callback = getattr(self.callbacks, name, None)
        if callback:
            await callback(*args, **kwargs)

    async def run(
        self, query: str, messageHistory: Optional[MessageHistory] = None
    ) -> str:
        """Main entry point - runs the agent with iterative reflection.

        Args:
            query: The user's query to process
            messageHistory: Optional conversation history

        Returns:
            str: The final answer (note: actual streaming happens via callbacks)
        """
        taskResults: dict[str, TaskResult] = {}
        completedPlans: list[Plan] = []

        # ========================================================================
        # Phase 1: Understand (only once)
        # ========================================================================
        self._call("onPhaseStart", "understand")

        logger.info("[Understand]Agent: Starting Understanding Phase")

        understanding = await self.understandPhase.run(
            input=UnderstandInput(query=query, conversation_history=messageHistory)
        )

        self._call("onUnderstandingComplete", understanding)
        self._call("onPhaseComplete", "understand")

        # ========================================================================
        # Iterative Plan → Execute → Reflect Loop
        # ========================================================================
        iteration = 1
        guidanceFromReflection: Optional[str] = None

        while iteration <= self.maxIterations:
            self._call("onIterationStart", iteration)

            # ======================================================================
            # Phase 2: Plan
            # ======================================================================
            self._call("onPhaseStart", "plan")

            logger.info(f"[Plan]Agent: Starting Planning Phase - Iteration {iteration}")

            plan = await self.planPhase.run(
                input=PlanInput(
                    query=query,
                    understanding=understanding,
                    priorPlans=completedPlans if len(completedPlans) > 0 else None,
                    priorResults=taskResults if len(taskResults) > 0 else None,
                    guidanceFromReflection=guidanceFromReflection,
                )
            )

            self._call("onPlanCreated", plan, iteration)
            self._call("onPhaseComplete", "plan")

            # ======================================================================
            # Phase 3: Execute
            # ======================================================================
            self._call("onPhaseStart", "execute")

            logger.info(f"[Execute]Agent: Starting Execution Phase - Iteration {iteration}")

            iterationResults = await self.taskExecutor.execute_tasks(
                plan=plan,
                query=query,
                understanding=understanding,
                query_id=f"query-{iteration}",
                task_executor_callbacks=self.callbacks,
            )

            # Merge results
            taskResults.update(iterationResults)

            self._call("onPhaseComplete", "execute")

            # Track completed plan
            completedPlans.append(plan)

            # ======================================================================
            # Phase 4: Reflect - Should we continue?
            # ======================================================================
            self._call("onPhaseStart", "reflect")

            logger.info(f"[Reflect]Agent: Starting Reflection Phase - Iteration {iteration}")

            reflection = await self.reflectPhase.run(
                input=ReflectInput(
                    query=query,
                    understanding=understanding,
                    completedPlans=completedPlans,
                    taskResults=taskResults,
                    iteration=iteration,
                )
            )

            self._call("onReflectionComplete", reflection, iteration)
            self._call("onPhaseComplete", "reflect")

            # Check if we're done
            if reflection.isComplete:
                break

            # Prepare guidance for next iteration
            guidanceFromReflection = self.reflectPhase.build_planning_guidance(
                reflection=reflection
            )

            iteration += 1

        # ========================================================================
        # Phase 5: Generate Final Answer
        # ========================================================================
        self._call("onPhaseStart", "answer")
        self._call("onAnswerStart")

        logger.info("[Answer]Agent: Starting Answer Phase")

        stream = self.answerPhase.run(
            input=AnswerInput(query=query, completedPlans=completedPlans, taskResults=taskResults)
        )

        await self._call_async("onAnswerStream", stream)
        self._call("onPhaseComplete", "answer")

        return ""
