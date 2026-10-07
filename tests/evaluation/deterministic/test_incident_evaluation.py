from tests.evaluation.deterministic.evaluator import evaluate_incident_report
from tests.evaluation.deterministic.expected_incidents import (INCIDENT_001_EXPECTATION, INCIDENT_002_EXPECTATION, INCIDENT_003_EXPECTATION)
from src.schemas.incident import IncidentReport

def test_valid_incident_report_passes_deterministic_evaluation() -> None:
    """Verify that a valid incident report passes deterministic evaluation."""

    report = IncidentReport(
        likely_cause=(
            "Commit a13f9c2 introduced a database connection leak "
            "by acquiring connections without releasing them."
        ),
        evidence=[
            "Database connection pool reached 100% utilization.",
            "The deployment included commit a13f9c2.",
            "Multiple checkout requests returned HTTP 500 errors.",
            "The service was recovered after rollback.",
        ],
        confidence=0.97,
        suggested_remediation=(
            "Restore guaranteed database connection cleanup."
        ),
    )

    failures = evaluate_incident_report(report=report, expectation=INCIDENT_001_EXPECTATION)
    assert failures == []

def test_incident_report_rejects_low_confidence() -> None:
    """Verify that a low-confidence report fails evaluation."""

    report = IncidentReport(
        likely_cause=(
            "Commit a13f9c2 introduced a database connection leak "
            "by acquiring connections without releasing them."
        ),
        evidence=[
            "Database connection pool reached 100% utilization.",
            "The deployment included commit a13f9c2.",
            "Multiple checkout requests returned HTTP 500 errors.",
            "The service was recovered after rollback.",
        ],
        confidence=0.5,
        suggested_remediation=(
            "Restore guaranteed database connection cleanup."
        ),
    )

    failures = evaluate_incident_report(report=report, expectation=INCIDENT_001_EXPECTATION)
    assert failures
    assert any(
        "confidence" in failure.lower()
        for failure in failures
    )

def test_incident_report_passes_confidence_and_commit_checks() -> None:
    """Verify that sufficient confidence and the expected commit pass."""

    report = IncidentReport(
        likely_cause=(
            "Commit a13f9c2 introduced the database connection leak."
        ),
        evidence=["Supporting evidence."],
        confidence=0.95,
        suggested_remediation="Apply the appropriate remediation.",
    )

    failures = evaluate_incident_report(report=report, expectation=INCIDENT_001_EXPECTATION)
    assert failures == []

def test_incident_report_rejects_wrong_commit() -> None:
    """Verify that an incorrect introducing commit fails evaluation."""

    report = IncidentReport(
        likely_cause=(
            "Commit b72d4e1 introduced the database connection leak."
        ),
        evidence=["Supporting evidence."],
        confidence=0.95,
        suggested_remediation="Apply the appropriate remediation.",
    )

    failures = evaluate_incident_report(report=report, expectation=INCIDENT_001_EXPECTATION)
    assert failures
    assert any(
        "introducing commit" in failure.lower()
        for failure in failures
    )

def test_incident_002_report_passes_deterministic_evaluation() -> None:
    """Verify that a correct RCA for incident 002 passes evaluation."""

    report = IncidentReport(
        likely_cause=(
            "Commit f31ab82 introduced a database query performance "
            "regression that caused increased database load and request latency."
        ),
        evidence=[
            "The order history query was changed by commit f31ab82.",
            "Database query duration increased during the incident.",
            "Database CPU utilization reached 91%.",
            "Request timeouts occurred during the latency spike.",
            "Latency returned to baseline after rollback.",
        ],
        confidence=0.90,
        suggested_remediation=(
            "Optimize the order history query and verify its database "
            "performance before redeployment."
        ),
    )

    failures = evaluate_incident_report(
        report=report,
        expectation=INCIDENT_002_EXPECTATION,
    )
    assert failures == []

def test_incident_003_report_passes_deterministic_evaluation() -> None:
    """Verify that an SSL certificate incident passes deterministic evaluation."""

    report = IncidentReport(
        likely_cause=(
            "The auth-service certificate expired at midnight, "
            "causing TLS validation failures and authentication failures."
        ),
        evidence=[
            "The certificate expired at 2026-10-01T00:00:00Z.",
            "TLS handshake failures began immediately afterward.",
        ],
        confidence=0.95,
        suggested_remediation="Renew the expired internal SSL certificate.",
    )

    failures = evaluate_incident_report(
        report=report,
        expectation=INCIDENT_003_EXPECTATION,
    )

    assert failures == []