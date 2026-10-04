from src.tools.log_tools import fetch_incident_logs

def test_fetch_incident_logs_returns_log_evidence() -> None:
    """Verify that the log tool returns relevant log evidence."""

    results = fetch_incident_logs(incident_id="INC-2026-001", query="database connection pool exhaustion",)
    assert results
    assert all(
        result["source_type"] == "log"
        for result in results
    )
    assert all(
        result["incident_id"] == "INC-2026-001"
        for result in results
    )