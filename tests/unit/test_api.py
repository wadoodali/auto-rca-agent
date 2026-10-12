from fastapi.testclient import TestClient

from src.api import app as api_module
from src.llm.client import LLMProviderError
from src.rag.vector_store import RAGRetrievalError
from src.schemas.incident import IncidentReport, InvestigationResult


client = TestClient(api_module.app)


def sample_result() -> InvestigationResult:
    return InvestigationResult(
        report=IncidentReport(
            likely_cause="The connection pool was exhausted.",
            evidence=["Logs show all database connections were occupied."],
            confidence=0.98,
            suggested_remediation="Release connections reliably and redeploy.",
        ),
        retrieved_context=["Database connection pool reached capacity."],
        execution_trace=[
            {
                "tool_name": "fetch_incident_logs",
                "tool_call": '{"incident_id":"INC-2026-001","query":"pool"}',
                "result": [],
                "round": 1,
                "status": "success",
                "result_count": 1,
            }
        ],
    )


def test_list_incidents_returns_seeded_incidents() -> None:
    response = client.get("/api/incidents")

    assert response.status_code == 200
    assert response.json() == [
        {"incident_id": f"INC-2026-{number:03d}"}
        for number in range(1, 7)
    ]


def test_investigation_forwards_arguments_and_serializes_result(monkeypatch) -> None:
    expected = sample_result()
    calls: list[tuple[str, str]] = []

    def fake_run_investigation(
        incident_id: str,
        investigation_query: str,
    ) -> InvestigationResult:
        calls.append((incident_id, investigation_query))
        return expected

    monkeypatch.setattr(api_module, "run_investigation", fake_run_investigation)

    response = client.post(
        "/api/investigations",
        json={
            "incident_id": "INC-2026-001",
            "investigation_query": "Why did the database pool exhaust?",
        },
    )

    assert response.status_code == 200
    assert calls == [
        ("INC-2026-001", "Why did the database pool exhaust?")
    ]
    assert response.json() == expected.model_dump(mode="json")


def test_blank_investigation_fields_are_rejected() -> None:
    response = client.post(
        "/api/investigations",
        json={"incident_id": "  ", "investigation_query": "  "},
    )

    assert response.status_code == 422


def test_missing_investigation_fields_are_rejected() -> None:
    response = client.post("/api/investigations", json={})

    assert response.status_code == 422


def test_unsupported_incident_is_rejected_before_agent(monkeypatch) -> None:
    called = False

    def fake_run_investigation(*_: object, **__: object) -> InvestigationResult:
        nonlocal called
        called = True
        raise AssertionError("agent should not be called")

    monkeypatch.setattr(api_module, "run_investigation", fake_run_investigation)

    response = client.post(
        "/api/investigations",
        json={
            "incident_id": "INC-2027-001",
            "investigation_query": "Investigate this incident.",
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "The requested incident is not supported."
    }
    assert called is False


def test_provider_error_is_safe(monkeypatch) -> None:
    def fail_run_investigation(*_: object, **__: object) -> InvestigationResult:
        raise LLMProviderError("provider-secret-marker")

    monkeypatch.setattr(api_module, "run_investigation", fail_run_investigation)

    response = client.post(
        "/api/investigations",
        json={
            "incident_id": "INC-2026-001",
            "investigation_query": "Investigate this incident.",
        },
    )

    assert response.status_code == 502
    assert response.json() == {
        "detail": "The investigation provider is unavailable."
    }
    assert "provider-secret-marker" not in response.text


def test_rag_error_is_safe(monkeypatch) -> None:
    def fail_run_investigation(*_: object, **__: object) -> InvestigationResult:
        raise RAGRetrievalError("raw-rag-marker")

    monkeypatch.setattr(api_module, "run_investigation", fail_run_investigation)

    response = client.post(
        "/api/investigations",
        json={
            "incident_id": "INC-2026-001",
            "investigation_query": "Investigate this incident.",
        },
    )

    assert response.status_code == 502
    assert response.json() == {
        "detail": "Incident evidence could not be retrieved."
    }
    assert "raw-rag-marker" not in response.text


def test_unexpected_error_returns_generic_response(monkeypatch) -> None:
    def fail_run_investigation(*_: object, **__: object) -> InvestigationResult:
        raise RuntimeError("internal-secret-marker")

    monkeypatch.setattr(api_module, "run_investigation", fail_run_investigation)

    response = client.post(
        "/api/investigations",
        json={
            "incident_id": "INC-2026-001",
            "investigation_query": "Investigate this incident.",
        },
    )

    assert response.status_code == 500
    assert response.json() == {
        "detail": "The investigation could not be completed."
    }
    assert "internal-secret-marker" not in response.text
