from tests.evaluation.deterministic.evaluator import evaluate_incident_report
from tests.evaluation.deterministic.expected_incidents import (INCIDENT_001_EXPECTATION)
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


def test_incident_report_passes_confidence_check() -> None:
    """Verify that sufficient confidence passes deterministic evaluation."""

    report = IncidentReport(
        likely_cause="Some valid root-cause explanation.",
        evidence=["Supporting evidence."],
        confidence=0.95,
        suggested_remediation="Apply the appropriate remediation.",
    )

    failures = evaluate_incident_report(report=report, expectation=INCIDENT_001_EXPECTATION)
    assert failures == []