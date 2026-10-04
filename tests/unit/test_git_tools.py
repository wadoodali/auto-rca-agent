from src.tools.git_tools import query_git_commits

def test_query_git_commits_returns_commit_evidence() -> None:
    """Verify that the Git tool returns relevant commit evidence."""

    results = query_git_commits(incident_id="INC-2026-001", query="database connection pool leak",)
    assert results
    assert all(
        result["source_type"] == "commit"
        for result in results
    )
    assert all(
        result["incident_id"] == "INC-2026-001"
        for result in results
    )