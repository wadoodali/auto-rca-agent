from dataclasses import dataclass


@dataclass(frozen=True)
class ExpectedIncident:
    """Structured ground truth for a known incident."""

    incident_id: str
    affected_service: str
    root_cause_category: str
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


INCIDENT_003_EXPECTATION = ExpectedIncident(
    incident_id="INC-2026-003",
    affected_service="auth-service",
    root_cause_category="ssl_certificate_expiry",
    introducing_commit=None,
    expected_consequence="authentication_failures",
    minimum_confidence=0.90,
)


INCIDENT_004_EXPECTATION = ExpectedIncident(
    incident_id="INC-2026-004",
    affected_service="image-service",
    root_cause_category="memory_leak",
    introducing_commit="b72c91e",
    expected_consequence="gradual_memory_growth_and_oom",
    minimum_confidence=0.90,
)


INCIDENT_005_EXPECTATION = ExpectedIncident(
    incident_id="INC-2026-005",
    affected_service="checkout-api",
    root_cause_category="third_party_payment_provider_outage",
    introducing_commit=None,
    expected_consequence="credit_card_transaction_failures",
    minimum_confidence=0.90,
)


INCIDENT_006_EXPECTATION = ExpectedIncident(
    incident_id="INC-2026-006",
    affected_service="cart-api",
    root_cause_category="accidental_reintroduction_of_fixed_bug",
    introducing_commit="e51a9d4",
    expected_consequence="invalid_cart_states_and_checkout_failures",
    minimum_confidence=0.90,
)