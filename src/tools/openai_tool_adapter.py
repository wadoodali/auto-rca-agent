import json
from typing import Any
from src.tools.tool_executor import ToolExecutionError, execute_tool_call

def run_tool_call(tool_call: Any) -> list[dict[str, Any]]:
    """Execute an OpenAI function tool call."""

    try:
        return execute_tool_call(
            tool_name=tool_call.name,
            arguments=tool_call.arguments,
        )
    except ToolExecutionError as error:
        return [{
            "error": str(error),
            "tool_name": tool_call.name,
        }]

def create_tool_result(tool_call: Any, result: list[dict[str, Any]],) -> dict[str, str]:
    """Format a tool result for the OpenAI Responses API."""

    return {
        "type": "function_call_output",
        "call_id": tool_call.call_id,
        "output": json.dumps(result, sort_keys=True),
    }
