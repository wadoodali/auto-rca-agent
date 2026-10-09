from typing import Any

from src.rag.retriever import retrieve_logs
from src.rag.models import RetrievalConfig


class FakeCollection:
    """Fake ChromaDB collection used for offline unit tests."""

    def query(self, **kwargs: Any) -> dict[str, list[list[Any]]]:
        """Return controlled evidence without calling an embedding service."""

        return {
            "ids": [["log-001", "log-002"]],
            "documents": [[
                "Database connection pool reached 100%.",
                "Database connection pool reached 92%.",
            ]],
            "metadatas": [[
                {
                    "incident_id": "INC-2026-001",
                    "source_type": "log",
                    "source_id": "log-001",
                },
                {
                    "incident_id": "INC-2026-001",
                    "source_type": "log",
                    "source_id": "log-002",
                },
            ]],
            "distances": [[0.12, 0.35]],
        }


def test_retrieve_logs_returns_incident_evidence() -> None:
    """Verify that log retrieval returns evidence for the requested incident."""

    results = retrieve_logs(
        incident_id="INC-2026-001",
        query="database connection pool exhaustion",
        collection=FakeCollection(),
    )

    assert results
    assert all(
        result.source_type == "log"
        for result in results
    )
    assert all(
        result.incident_id == "INC-2026-001"
        for result in results
    )
    assert [result.distance for result in results] == [0.12, 0.35]


def test_retrieve_logs_with_no_distance_limit_retains_all_valid_results() -> None:
    config = RetrievalConfig(
        n_results=5,
        max_distance=None,
    )

    results = retrieve_logs(
        incident_id="INC-2026-001",
        query="database connection pool exhaustion",
        config=config,
        collection=FakeCollection(),
    )

    assert len(results) == 2


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
        collection=FakeCollection(),
    )

    assert all(
        item.distance <= 0.0
        for item in results
    )
