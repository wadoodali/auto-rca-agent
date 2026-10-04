from src.schemas.incident import IncidentReport
import pytest

def test_incident_report_accepts_valid_data() -> None:
    """Verify that a valid incident report passes validation."""

    report = IncidentReport(
        likely_cause="Database connection pool exhaustion.",
        evidence=[
            "Pool utilization reached 100%.",
            "Connections were not released after requests.",
        ],
        confidence=0.95,
        suggested_remediation="Restore guaranteed connection cleanup.",
    )

    assert report.likely_cause == "Database connection pool exhaustion."
    assert len(report.evidence) == 2
    assert report.confidence == 0.95

def test_incident_report_rejects_invalid_confidence() -> None:
    """Verify that confidence outside 0.0 to 1.0 is rejected."""

    with pytest.raises(ValueError):
        IncidentReport(
            likely_cause="Database connection pool exhaustion.",
            evidence=["Pool utilization reached 100%."],
            confidence=1.5,
            suggested_remediation="Restore connection cleanup.",
        )

def test_incident_report_rejects_unexpected_fields() -> None:
    """Verify that unexpected fields are rejected."""

    with pytest.raises(ValueError):
        IncidentReport(
            likely_cause="Database connection pool exhaustion.",
            evidence=["Pool utilization reached 100%."],
            confidence=0.95,
            suggested_remediation="Restore connection cleanup.",
            unexpected_field="This should not be allowed.",
        )