from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

# ======================================================================
## Phase Types
# ======================================================================


class Phase(Enum):
    UNDERSTAND = "understand"
    PLAN = "plan"
    EXECUTE = "execute"
    REFLECT = "reflect"
    ANSWER = "answer"
    COMPLETE = "complete"


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskType(Enum):
    USE_TOOLS = "use_tools"
    REASON = "reason"


# ======================================================================
## Entity Types
# ======================================================================


class EntityType(Enum):
    ACTION = "action"
    SKILL_NAME = "skill_name"
    TOOL_NAME = "tool_name"


@dataclass
class Entity:
    type: EntityType
    value: str


# ======================================================================
## Understanding Phase Types
# ======================================================================


@dataclass
class UnderstandInput:
    query: str
    conversation_history: Optional[Any] = None  # TODO Build a history middleware


@dataclass
class Understanding:
    intent: str
    entities: list[Entity] = field(default_factory=list)


@dataclass
class ToolCall:
    tool: str
    args: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolCallStatus(ToolCall):
    """工具调用状态对象

    Attributes:
        tool (str): 工具名称

        args (dict[str, Any]): 工具参数

        status (TaskStatus): 工具调用状态

        ```python
        class TaskStatus(Enum):
            PENDING = "pending"
            IN_PROGRESS = "in_progress"
            COMPLETED = "completed"
            FAILED = "failed"
        ```
    """

    status: TaskStatus = TaskStatus.PENDING


# ======================================================================
## Plan Phase Types
# ======================================================================


@dataclass
class Task:
    id: str
    description: str
    status: TaskStatus
    taskType: Optional[TaskType] = None
    toolCalls: Optional[list[ToolCallStatus]] = None
    dependsOn: Optional[list[str]] = None


@dataclass
class Plan:
    summary: str
    tasks: list[Task] = field(default_factory=list)


@dataclass
class PlanInput:
    query: str
    understanding: Understanding
    priorPlans: Optional[list[Plan]] = None
    priorResults: Optional[dict[str, TaskResult]] = None
    guidanceFromReflection: Optional[str] = None


# ======================================================================
## Execute Phase Types
# ======================================================================


@dataclass
class TaskResult:
    taskId: str
    output: Optional[str] = None


@dataclass
class ExecuteInput:
    query: str
    task: Task
    plan: Plan
    contextData: str = ""


# ======================================================================
## Summary of a tool call result which keep in context
# ======================================================================


@dataclass
class ToolSummary:
    id: str
    toolName: str
    args: dict[str, Any] = field(default_factory=dict)


# ======================================================================
## Agent State
# ======================================================================


@dataclass
class AgentState:
    query: str
    currentPhase: Phase
    understanding: Optional[Understanding] = None
    plan: Optional[Plan] = None
    taskResults: dict[str, TaskResult] = field(default_factory=dict)
    currentTaskId: Optional[str] = None


def create_initial_state(query: str) -> AgentState:
    return AgentState(
        query=query,
        currentPhase=Phase.UNDERSTAND,
        taskResults={},
    )


# ======================================================================
## Reflection Phase Types
# ======================================================================


@dataclass
class ReflectInput:
    query: str
    understanding: Understanding
    completedPlans: list[Plan]
    taskResults: dict[str, TaskResult]
    iteration: int


@dataclass
class ReflectionResult:
    isComplete: bool
    reasoning: str
    missingInfo: list[str] = field(default_factory=list)
    suggestedNextSteps: str = ""


# ======================================================================
## Answer Phase Types
# ======================================================================


@dataclass
class AnswerInput:
    query: str
    completedPlans: list[Plan]
    taskResults: dict[str, TaskResult] = field(default_factory=dict)
