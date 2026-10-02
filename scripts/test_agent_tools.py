from src.agent.rca_agent import (
    execute_requested_tools,
    extract_tool_calls,
    format_tool_results,
    request_investigation,
)


def main() -> None:
    """Verify the complete tool execution and formatting flow."""

    response = request_investigation(
        incident_id="INC-2026-001",
        investigation_query=(
            "Find evidence about database connection pool "
            "exhaustion and connection timeouts."
        ),
    )

    tool_calls = extract_tool_calls(response)
    tool_results = execute_requested_tools(tool_calls)
    outputs = format_tool_results(tool_results)

    print(f"Function outputs: {len(outputs)}")

    for output in outputs:
        print(f"{output['type']}: {output['call_id']}")


if __name__ == "__main__":
    main()