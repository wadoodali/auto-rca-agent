from typing import Any
from src.llm.client import create_openai_client
from src.tools.tool_registry import TOOL_SCHEMAS
from src.tools.openai_tool_adapter import create_tool_result, run_tool_call
from src.schemas.incident import IncidentReport

def request_investigation(incident_id: str, investigation_query: str,) -> Any:
    """Request an incident investigation from the LLM."""

    client = create_openai_client()
    response = client.responses.create(
        model="gpt-5.6-luna",
        input=(
            f"Investigate incident {incident_id}. "
            f"{investigation_query}"
        ),
        tools=TOOL_SCHEMAS,
    )

    return response

def extract_tool_calls(response: Any) -> list[Any]:
    """Extract function calls requested by the LLM response."""

    return [
        item
        for item in response.output
        if item.type == "function_call"
    ]

def execute_requested_tools(tool_calls: list[Any],) -> list[tuple[Any, list[dict[str, Any]]]]:
    """Execute all tools requested by the LLM."""

    results = []
    for tool_call in tool_calls:
        result = run_tool_call(tool_call)
        results.append((tool_call, result))

    return results

def format_tool_results(tool_results: list[tuple[Any, list[dict[str, Any]]]],) -> list[dict[str, str]]:
    """Convert executed tool results into Responses API inputs."""

    return [
        create_tool_result(
            tool_call=tool_call,
            result=result,
        )
        for tool_call, result in tool_results
    ]

def continue_investigation(response: Any, tool_outputs: list[dict[str, str]],) -> Any:
    """Send tool results back to the LLM for further investigation."""

    client = create_openai_client()
    return client.responses.parse(
        model="gpt-5.6-luna",
        previous_response_id=response.id,
        input=tool_outputs,
        tools=TOOL_SCHEMAS,
        text_format=IncidentReport,
    )

def run_investigation_round(response: Any,) -> Any:
    """Execute requested tools and continue the investigation."""

    tool_calls = extract_tool_calls(response)
    tool_results = execute_requested_tools(tool_calls)
    tool_outputs = format_tool_results(tool_results)

    return continue_investigation(response=response, tool_outputs=tool_outputs,)

def has_tool_calls(response: Any) -> bool:
    """Return True when the LLM response contains function calls."""

    return any(
        item.type == "function_call"
        for item in response.output
    )

MAX_INVESTIGATION_ROUNDS = 5
def run_investigation(incident_id: str, investigation_query: str,) -> IncidentReport:
    """Run the investigation until the LLM returns a structured report."""

    response = request_investigation(incident_id=incident_id, investigation_query=investigation_query,)

    for _ in range(MAX_INVESTIGATION_ROUNDS):
        if not has_tool_calls(response):
            if response.output_parsed is None:
                raise RuntimeError(
                    "The investigation completed without a structured incident report."
                )

            return response.output_parsed

        response = run_investigation_round(response)

    raise RuntimeError("Investigation exceeded the maximum number of rounds.")