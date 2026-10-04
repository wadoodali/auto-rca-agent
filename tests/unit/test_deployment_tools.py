from src.tools.deployment_tools import get_deployment_delta

def test_get_deployment_delta_returns_deployment_evidence() -> None:
    """Verify that the deployment tool returns deployment evidence."""

    results = get_deployment_delta(incident_id="INC-2026-001", query="deployment associated with checkout API failure",)
    assert results
    assert all(
        result["source_type"] == "deployment"
        for result in results
    )
    assert all(
        result["incident_id"] == "INC-2026-001"
        for result in results
    )