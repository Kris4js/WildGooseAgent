"""Tools API."""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.tools.registry import get_tool_registry
from src.tools.description.browser_automation import BROWSER_AUTOMATION_DESCRIPTION
from src.tools.description.web_search import WEB_SEARCH_DESCRIPTION

router = APIRouter()


class ToolInfo(BaseModel):
    name: str
    displayName: str
    description: str


class ToolDetail(BaseModel):
    name: str
    displayName: str
    description: str
    parameters: dict | None = None


class ToolGroupInfo(BaseModel):
    id: str
    name: str
    description: str
    tools: list[ToolInfo]


class ToolsResponse(BaseModel):
    groups: list[ToolGroupInfo]


def format_tool_name(name: str) -> str:
    """Format tool name: remove _tool suffix and convert to uppercase."""
    # Remove _tool suffix if present
    clean_name = name.replace("_tool", "")
    # Convert to uppercase and replace underscores with spaces
    return clean_name.upper().replace("_", " ")


def get_tool_groups() -> list[ToolGroupInfo]:
    """Get tools organized by groups."""
    registry = get_tool_registry("")

    # Define tool groups with descriptions from description files
    groups: dict[str, dict[str, Any]] = {
        "builtin": {
            "id": "builtin",
            "name": "Built-in Tools",
            "description": "Core file system and execution tools for basic operations",
            "tools": [],
        },
        "browser": {
            "id": "browser",
            "name": "Browser Automation",
            "description": BROWSER_AUTOMATION_DESCRIPTION,
            "tools": [],
        },
        "search": {
            "id": "search",
            "name": "Web Search",
            "description": WEB_SEARCH_DESCRIPTION,
            "tools": [],
        },
        "skills": {
            "id": "skills",
            "name": "Skills",
            "description": "Dynamic skills loaded from skill files",
            "tools": [],
        },
    }

    # Categorize tools into groups
    for tool in registry:
        # For non-builtin tools, use minimal description (just the tool name)
        # to avoid repetition since the group description covers it
        if tool.name.startswith("browser_"):
            tool_info = ToolInfo(
                name=tool.name,
                displayName=format_tool_name(tool.name),
                description="",  # Empty for browser tools
            )
            groups["browser"]["tools"].append(tool_info)
        elif tool.name == "web_search":
            tool_info = ToolInfo(
                name=tool.name,
                displayName=format_tool_name(tool.name),
                description="",  # Empty for web search
            )
            groups["search"]["tools"].append(tool_info)
        elif tool.name == "skill":
            tool_info = ToolInfo(
                name=tool.name,
                displayName=format_tool_name(tool.name),
                description="",  # Empty for skills
            )
            groups["skills"]["tools"].append(tool_info)
        else:
            # Builtin tools keep their individual descriptions
            tool_info = ToolInfo(
                name=tool.name,
                displayName=format_tool_name(tool.name),
                description=tool.description,
            )
            groups["builtin"]["tools"].append(tool_info)

    # Convert to list, filtering out empty groups
    return [
        ToolGroupInfo(
            id=group["id"],
            name=group["name"],
            description=group["description"],
            tools=group["tools"],
        )
        for group in groups.values()
        if len(group["tools"]) > 0
    ]


@router.get("/tools", response_model=ToolsResponse)
async def list_tools():
    """Get list of all available tools organized by groups."""
    return ToolsResponse(groups=get_tool_groups())


@router.get("/tools/{name}", response_model=ToolDetail)
async def get_tool(name: str):
    """Get tool detail by name."""
    registry = get_tool_registry("")
    for t in registry:
        if t.name == name:
            # Extract parameters schema from tool if available
            params = None
            if hasattr(t.tool, "args_schema") and t.tool.args_schema:
                params = t.tool.args_schema.model_json_schema()

            # Only return description for builtin tools
            # Non-builtin tools use group-level descriptions
            description = t.description
            if name.startswith("browser_") or name == "web_search" or name == "skill":
                description = ""

            return ToolDetail(
                name=t.name,
                displayName=format_tool_name(t.name),
                description=description,
                parameters=params,
            )

    raise HTTPException(status_code=404, detail=f"Tool '{name}' not found")
