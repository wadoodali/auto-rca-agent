import json
from typing import Any
from src.tools.tool_registry import TOOL_FUNCTIONS


def execute_tool_call(
    tool_name: str,
    arguments: str,
) -> list[dict[str, Any]]:
    """Execute a tool requested by the LLM."""

    if tool_name not in TOOL_FUNCTIONS:
        raise ValueError(f"Unknown tool: {tool_name}")

    parsed_arguments: dict[str, Any] = json.loads(arguments)

    tool_function = TOOL_FUNCTIONS[tool_name]

    return tool_function(**parsed_arguments)