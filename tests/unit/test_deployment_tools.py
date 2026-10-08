from src.rag.models import RetrievedEvidence
from src.tools import deployment_tools


def test_get_deployment_delta_returns_deployment_evidence(
    monkeypatch,
) -> None:
    """Verify that the deployment tool returns deployment evidence."""

    fake_evidence = [
        RetrievedEvidence(
            content="checkout-api version 2026.09.15.3 was deployed successfully.",
            source_type="deployment",
            incident_id="INC-2026-001",
            source_id="deploy-2026-09-15-003",
            distance=0.11,
        )
    ]

    def fake_retrieve_deployments(
        incident_id: str,
        query: str,
    ) -> list[RetrievedEvidence]:
        assert incident_id == "INC-2026-001"
        assert query == "deployment associated with checkout API failure"
        return fake_evidence

    monkeypatch.setattr(
        deployment_tools,
        "retrieve_deployments",
        fake_retrieve_deployments,
    )

    results = deployment_tools.get_deployment_delta(
        incident_id="INC-2026-001",
        query="deployment associated with checkout API failure",
    )

    assert results
    assert all(
        result["source_type"] == "deployment"
        for result in results
    )
    assert all(
        result["incident_id"] == "INC-2026-001"
        for result in results
    )