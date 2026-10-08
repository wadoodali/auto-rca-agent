from src.rag.models import RetrievedEvidence
from src.tools import log_tools


def test_fetch_incident_logs_returns_log_evidence(
    monkeypatch,
) -> None:
    """Verify that the log tool returns relevant log evidence."""

    fake_evidence = [
        RetrievedEvidence(
            content="Database connection pool reached 100%.",
            source_type="log",
            incident_id="INC-2026-001",
            source_id="log-001",
            distance=0.12,
        )
    ]

    def fake_retrieve_logs(
        incident_id: str,
        query: str,
    ) -> list[RetrievedEvidence]:
        assert incident_id == "INC-2026-001"
        assert query == "database connection pool exhaustion"
        return fake_evidence

    monkeypatch.setattr(
        log_tools,
        "retrieve_logs",
        fake_retrieve_logs,
    )

    results = log_tools.fetch_incident_logs(
        incident_id="INC-2026-001",
        query="database connection pool exhaustion",
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