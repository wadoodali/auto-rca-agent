from src.schemas.incident import IncidentReport
from tests.evaluation.deterministic.expected_incidents import ExpectedIncident

def evaluate_incident_report(report: IncidentReport, expectation: ExpectedIncident) -> list[str]:
    """Evaluate deterministic properties of an incident report."""

    failures: list[str] = []

    if report.confidence < expectation.minimum_confidence:
        failures.append(
            f"Confidence {report.confidence} is below "
            f"minimum {expectation.minimum_confidence}"
        )

    if (
        expectation.introducing_commit is not None
        and expectation.introducing_commit not in report.likely_cause
    ):
        failures.append(
            "Expected introducing commit "
            f"{expectation.introducing_commit} was not identified "
            "in the likely cause."
        )

    return failures