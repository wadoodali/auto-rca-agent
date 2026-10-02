from src.tools.executor import execute_tool_call


def main() -> None:
    """Verify that the tool executor can dispatch a tool call."""

    arguments = (
        '{"incident_id": "INC-2026-001", '
        '"query": "database connection pool exhaustion"}'
    )

    results = execute_tool_call(
        tool_name="fetch_incident_logs",
        arguments=arguments,
    )

    print(f"Retrieved {len(results)} logs")

    for result in results:
        print(result)


if __name__ == "__main__":
    main()