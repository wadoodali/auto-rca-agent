import json
from typing import Any
from src.tools.tool_registry import TOOL_FUNCTIONS


class ToolExecutionError(RuntimeError):
    """Raised when a requested tool cannot be executed safely."""


def execute_tool_call(
    tool_name: str,
    arguments: str,
) -> list[dict[str, Any]]:
    """Execute a tool requested by the LLM."""

    if tool_name not in TOOL_FUNCTIONS:
        raise ToolExecutionError(f"Unknown tool: {tool_name}")

    try:
        parsed_arguments: dict[str, Any] = json.loads(arguments)
        if not isinstance(parsed_arguments, dict):
            raise ValueError("Tool arguments must be a JSON object.")

        expected_arguments = {"incident_id", "query"}
        actual_arguments = set(parsed_arguments)
        if actual_arguments != expected_arguments:
            raise ValueError(
                "Tool arguments must contain exactly 'incident_id' and 'query'."
            )

        if not all(
            isinstance(parsed_arguments[name], str)
            and parsed_arguments[name].strip()
            for name in expected_arguments
        ):
            raise ValueError(
                "Tool arguments 'incident_id' and 'query' must be non-empty strings."
            )

        tool_function = TOOL_FUNCTIONS[tool_name]
        return tool_function(**parsed_arguments)
    except ToolExecutionError:
        raise
    except Exception as error:
        raise ToolExecutionError(
            f"Tool '{tool_name}' could not be executed."
        ) from error
