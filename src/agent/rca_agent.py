import json
from typing import Any
from openai import OpenAIError
from src.config import get_config
from src.llm.client import LLMProviderError, create_openai_client
from src.tools.tool_registry import TOOL_SCHEMAS
from src.tools.openai_tool_adapter import create_tool_result, run_tool_call
from src.schemas.incident import IncidentReport, InvestigationResult

def request_investigation(incident_id: str, investigation_query: str,) -> Any:
    """Request an incident investigation from the LLM."""

    client = create_openai_client()
    config = get_config()
    try:
        response = client.responses.create(
            model=config.openai_model,
            input=(
                f"Investigate incident {incident_id}. "
                f"{investigation_query}"
            ),
            tools=TOOL_SCHEMAS,
        )
    except OpenAIError as error:
        raise LLMProviderError(
            "The OpenAI provider failed while starting the investigation."
        ) from None

    return response

def extract_tool_calls(response: Any) -> list[Any]:
    """Extract function calls requested by the LLM response."""

    return [
        item
        for item in response.output
        if item.type == "function_call"
    ]

def _tool_call_signature(tool_call: Any) -> tuple[str, str]:
    """Build a stable signature for one logical tool call."""

    try:
        canonical_arguments = json.dumps(
            json.loads(tool_call.arguments),
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError):
        canonical_arguments = tool_call.arguments

    return tool_call.name, canonical_arguments


def execute_requested_tools(
    tool_calls: list[Any],
    seen_tool_calls: set[tuple[str, str]],
    investigation_id: str,
) -> list[tuple[Any, list[dict[str, Any]]]]:
    """Execute all tools requested by the LLM."""

    results = []
    for tool_call in tool_calls:
        try:
            parsed_arguments = json.loads(tool_call.arguments)
        except (TypeError, ValueError):
            parsed_arguments = None

        if (
            isinstance(parsed_arguments, dict)
            and set(parsed_arguments) == {"incident_id", "query"}
            and isinstance(parsed_arguments.get("incident_id"), str)
            and isinstance(parsed_arguments.get("query"), str)
            and parsed_arguments["incident_id"].strip()
            and parsed_arguments["query"].strip()
            and parsed_arguments["incident_id"] != investigation_id
        ):
            result = [{
                "error": (
                    "Tool call incident_id does not match "
                    "the investigation incident."
                ),
                "tool_name": tool_call.name,
            }]
            results.append((tool_call, result))
            continue

        signature = _tool_call_signature(tool_call)
        if signature in seen_tool_calls:
            result = [{
                "error": "Exact duplicate tool call was not executed.",
                "tool_name": tool_call.name,
            }]
        else:
            seen_tool_calls.add(signature)
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
    config = get_config()
    try:
        return client.responses.parse(
            model=config.openai_model,
            previous_response_id=response.id,
            input=tool_outputs,
            tools=TOOL_SCHEMAS,
            text_format=IncidentReport,
        )
    except OpenAIError as error:
        raise LLMProviderError(
            "The OpenAI provider failed while continuing the investigation."
        ) from None

def run_investigation_round(
    response: Any,
    seen_tool_calls: set[tuple[str, str]],
    investigation_id: str,
) -> tuple[Any, list[tuple[Any, list[dict[str, Any]]]]]:
    """Execute requested tools and continue the investigation."""

    tool_calls = extract_tool_calls(response)
    tool_results = execute_requested_tools(
        tool_calls,
        seen_tool_calls,
        investigation_id,
    )
    tool_outputs = format_tool_results(tool_results)

    next_response = continue_investigation(response=response, tool_outputs=tool_outputs)
    return next_response, tool_results

def has_tool_calls(response: Any) -> bool:
    """Return True when the LLM response contains function calls."""

    return any(
        item.type == "function_call"
        for item in response.output
    )

def _classify_tool_result(
    result: list[dict[str, Any]],
) -> tuple[str, int]:
    """Classify a tool result for the execution trace."""

    error_results = [item for item in result if "error" in item]
    if error_results:
        status = (
            "duplicate"
            if any(
                item.get("error") == "Exact duplicate tool call was not executed."
                for item in error_results
            )
            else "error"
        )
        return status, 0

    if not result:
        return "empty", 0

    return "success", len(result)


def build_execution_trace(
    tool_results: list[tuple[Any, list[dict[str, Any]]]],
    round_numbers: list[int] | None = None,
) -> list[dict[str, Any]]:
    """Convert internal tool results into an evaluation-friendly trace."""

    if round_numbers is None:
        round_numbers = [1] * len(tool_results)

    return [
        {
            "tool_name": tool_call.name,
            "tool_call": tool_call.arguments,
            "result": result,
            "round": round_number,
            "status": status,
            "result_count": result_count,
        }
        for (tool_call, result), round_number in zip(
            tool_results,
            round_numbers,
        )
        for status, result_count in [_classify_tool_result(result)]
    ]

def build_retrieved_context(tool_results: list[tuple[Any, list[dict[str, Any]]]]) -> list[str]:
    """Extract retrieved evidence from executed tool results."""

    return [
        str(evidence)
        for _, results in tool_results
        for evidence in results
    ]

MAX_INVESTIGATION_ROUNDS = 5
def run_investigation(incident_id: str, investigation_query: str) -> InvestigationResult:
    """Run the investigation until the LLM returns a structured report."""

    response = request_investigation(incident_id=incident_id, investigation_query=investigation_query)
    execution_trace: list[tuple[Any, list[dict[str, Any]]]] = []
    execution_trace_rounds: list[int] = []
    seen_tool_calls: set[tuple[str, str]] = set()


    for round_number in range(1, MAX_INVESTIGATION_ROUNDS + 1):
        if not has_tool_calls(response):
            if response.output_parsed is None:
                raise RuntimeError("The investigation completed without a structured incident report.")

            return InvestigationResult(
                report=response.output_parsed,
                retrieved_context=build_retrieved_context(execution_trace),
                execution_trace=build_execution_trace(
                    execution_trace,
                    execution_trace_rounds,
                )
            )
        
        response, tool_results = run_investigation_round(
            response,
            seen_tool_calls,
            incident_id,
        )
        execution_trace.extend(tool_results)
        execution_trace_rounds.extend([round_number] * len(tool_results))

    raise RuntimeError("Investigation exceeded the maximum number of rounds.")
