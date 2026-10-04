from dataclasses import dataclass

@dataclass(frozen=True)
class ExpectedIncident:
    """Structured ground truth for a known incident."""

    incident_id: str
    affected_service: str
    root_cause_category: str
    introducing_commit: str
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