import pytest

from src.agent.tool_executor import ToolExecutor, ToolExecutionError


class TestToolExecutor:
    @pytest.fixture
    def tool_executor(self, mock_tool_executor_options) -> ToolExecutor:
        return ToolExecutor(options=mock_tool_executor_options)
