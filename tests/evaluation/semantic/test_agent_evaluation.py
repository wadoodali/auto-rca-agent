from tests.evaluation.deterministic.evaluator import evaluate_incident_report
from tests.evaluation.deterministic.expected_incidents import (INCIDENT_001_EXPECTATION)
from src.agent.rca_agent import run_investigation

def test_agent_investigation_matches_expected_incident() -> None:
    """Verify that the AI investigator produces an acceptable RCA."""

    report = run_investigation(
        incident_id="INC-2026-001",
        investigation_query=(
            "Determine the most likely root cause of the checkout API "
            "incident using the available logs, Git commits, and deployments."
        ),
    )
    
    print(f"\nLikely cause: {report.likely_cause}")
    print(f"Confidence: {report.confidence}")
    print(f"Evidence: {report.evidence}")

    failures = evaluate_incident_report(report=report, expectation=INCIDENT_001_EXPECTATION)
    assert failures == []