from src.tools.tool_executor import execute_tool_call

def test_execute_tool_call_dispatches_to_log_tool() -> None:
    """Verify that the executor dispatches a tool call correctly."""

    arguments = (
        '{"incident_id": "INC-2026-001", '
        '"query": "database connection pool exhaustion"}'
    )
    results = execute_tool_call(tool_name="fetch_incident_logs", arguments=arguments,)
    assert results
    assert all(
        result["source_type"] == "log"
        for result in results
    )
    assert all(
        result["incident_id"] == "INC-2026-001"
        for result in results
    )