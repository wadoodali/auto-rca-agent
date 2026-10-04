from src.rag.retriever import retrieve_logs
from src.rag.models import RetrievalConfig

def test_retrieve_logs_returns_incident_evidence() -> None:
    """Verify that log retrieval returns evidence for the requested incident."""

    results = retrieve_logs(incident_id="INC-2026-001", query="database connection pool exhaustion",)

    assert results
    assert all(
        result.source_type == "log"
        for result in results
    )
    assert all(
    result.incident_id == "INC-2026-001"
    for result in results
)
def test_retrieve_logs_respects_max_distance() -> None:
    """Verify that evidence beyond the configured distance is excluded."""

    config = RetrievalConfig(
        n_results=5,
        max_distance=0.0,
    )

    results = retrieve_logs(
        incident_id="INC-2026-001",
        query="database connection pool exhaustion",
        config=config,
    )

    assert all(
        result.distance <= 0.0
        for result in results
    )