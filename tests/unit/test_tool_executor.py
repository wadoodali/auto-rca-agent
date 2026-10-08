from src.tools import tool_executor


def test_execute_tool_call_dispatches_to_log_tool(
    monkeypatch,
) -> None:
    """Verify that the executor dispatches a tool call correctly."""

    def fake_fetch_incident_logs(
        incident_id: str,
        query: str,
    ) -> list[dict[str, object]]:
        assert incident_id == "INC-2026-001"
        assert query == "database connection pool exhaustion"

        return [
            {
                "source_type": "log",
                "incident_id": "INC-2026-001",
                "source_id": "log-001",
                "content": "Database connection pool reached 100%.",
                "distance": 0.12,
            }
        ]

    monkeypatch.setitem(
        tool_executor.TOOL_FUNCTIONS,
        "fetch_incident_logs",
        fake_fetch_incident_logs,
    )

    arguments = (
        '{"incident_id": "INC-2026-001", '
        '"query": "database connection pool exhaustion"}'
    )

    results = tool_executor.execute_tool_call(
        tool_name="fetch_incident_logs",
        arguments=arguments,
    )

    assert results
    assert all(
        result["source_type"] == "log"
        for result in results
    )
    assert all(
        result["incident_id"] == "INC-2026-001"
        for result in results
    )