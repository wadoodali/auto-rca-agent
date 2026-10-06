from dataclasses import dataclass

@dataclass(frozen=True)
class ExpectedIncident:
    """Structured ground truth for a known incident."""

    incident_id: str
    affected_service: str
    root_cause_category: str | None
    introducing_commit: str | None  
    expected_consequence: str
    minimum_confidence: float

INCIDENT_001_EXPECTATION = ExpectedIncident(
    incident_id="INC-2026-001",
    affected_service="checkout-api",
    root_cause_category="database_connection_leak",
    introducing_commit="a13f9c2",
    expected_consequence="database_pool_exhaustion",
    minimum_confidence=0.9,
)
INCIDENT_002_EXPECTATION = ExpectedIncident(
    incident_id="INC-2026-002",
    affected_service="order-api",
    root_cause_category="database_query_performance_regression",
    introducing_commit="f31ab82",
    expected_consequence="database_overload_and_request_latency",
    minimum_confidence=0.85,
)