from src.rag.models import RetrievedEvidence
from src.tools import git_tools


def test_query_git_commits_returns_commit_evidence(
    monkeypatch,
) -> None:
    """Verify that the Git tool returns relevant commit evidence."""

    fake_evidence = [
        RetrievedEvidence(
            content="Database connections were not released after checkout requests.",
            source_type="commit",
            incident_id="INC-2026-001",
            source_id="a13f9c2",
            distance=0.10,
        )
    ]

    def fake_retrieve_code_changes(
        incident_id: str,
        query: str,
    ) -> list[RetrievedEvidence]:
        assert incident_id == "INC-2026-001"
        assert query == "database connection pool leak"
        return fake_evidence

    monkeypatch.setattr(
        git_tools,
        "retrieve_code_changes",
        fake_retrieve_code_changes,
    )

    results = git_tools.query_git_commits(
        incident_id="INC-2026-001",
        query="database connection pool leak",
    )

    assert results
    assert all(
        result["source_type"] == "commit"
        for result in results
    )
    assert all(
        result["incident_id"] == "INC-2026-001"
        for result in results
    )