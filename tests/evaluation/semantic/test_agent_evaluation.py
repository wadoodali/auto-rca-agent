import json

import pytest
from dotenv import load_dotenv
from deepeval.metrics import FaithfulnessMetric
from deepeval.test_case import LLMTestCase, ToolCall

from src.agent.rca_agent import run_investigation
from tests.evaluation.deterministic.evaluator import (
    evaluate_incident_report,
)
from tests.evaluation.deterministic.expected_incidents import (
    INCIDENT_001_EXPECTATION,
    INCIDENT_002_EXPECTATION,
    INCIDENT_003_EXPECTATION,
    INCIDENT_004_EXPECTATION,
    INCIDENT_005_EXPECTATION,
    INCIDENT_006_EXPECTATION,
    ExpectedIncident,
)
from tests.evaluation.semantic.groq_judge import (
    GroqJudge,
    JudgeUnavailableError,
)
from tests.evaluation.semantic.trajectory_evaluator import (
    evaluate_investigation_trajectory,
)


load_dotenv()


JUDGE_MODEL = GroqJudge(
    model="openai/gpt-oss-120b",
    temperature=0.0,
)


def build_deepeval_tool_calls(
    execution_trace: list[dict[str, object]],
) -> list[ToolCall]:
    """Convert the investigator trace into DeepEval tool calls."""

    return [
        ToolCall(
            name=str(step["tool_name"]),
            input_parameters=json.loads(str(step["tool_call"])),
            output=step["result"],
        )
        for step in execution_trace
    ]


@pytest.mark.parametrize(
    ("incident_id", "investigation_query", "expectation"),
    [
        (
            "INC-2026-001",
            (
                "Determine the most likely root cause of the checkout API "
                "incident using the available logs, Git commits, and deployments."
            ),
            INCIDENT_001_EXPECTATION,
        ),
        (
            "INC-2026-002",
            (
                "Determine the most likely root cause of the order API "
                "latency incident using the available logs, Git commits, "
                "and deployments."
            ),
            INCIDENT_002_EXPECTATION,
        ),
        (
            "INC-2026-003",
            (
                "Determine the most likely root cause of the authentication "
                "failures using the available logs, Git commits, and deployments."
            ),
            INCIDENT_003_EXPECTATION,
        ),
        (
            "INC-2026-004",
            (
                "Determine the most likely root cause of the image-service "
                "out-of-memory incident using the available logs, Git commits, "
                "and deployments. Pay attention to the timeline leading up "
                "to the failure."
            ),
            INCIDENT_004_EXPECTATION,
        ),
        (
            "INC-2026-005",
            (
                "Determine the most likely root cause of the checkout payment "
                "failures using the available logs, Git commits, and deployments."
            ),
            INCIDENT_005_EXPECTATION,
        ),
        (
            "INC-2026-006",
            (
                "Determine the most likely root cause of the cart API incident "
                "using the available logs, Git commits, and deployments. Pay "
                "particular attention to the Git history and any previously "
                "fixed validation logic."
            ),
            INCIDENT_006_EXPECTATION,
        ),
    ],
)
def test_agent_investigation_is_faithful(
    incident_id: str,
    investigation_query: str,
    expectation: ExpectedIncident,
    incident_filter: str | None,
) -> None:
    """Verify that an incident investigation is faithful and effective."""

    if incident_filter and incident_id != incident_filter:
        pytest.skip(
            f"Skipping {incident_id}; filter is {incident_filter}."
        )

    # ---------------------------------------------------------
    # 1. Run the actual AI incident investigation
    # ---------------------------------------------------------

    result = run_investigation(
        incident_id=incident_id,
        investigation_query=investigation_query,
    )

    report = result.report

    assert result.retrieved_context
    assert result.execution_trace

    tools_called = build_deepeval_tool_calls(
        result.execution_trace,
    )

    # ---------------------------------------------------------
    # 2. Deterministic evaluation
    # ---------------------------------------------------------
    #
    # This evaluation does not use an external LLM judge.
    # It checks the known expected facts for the incident.
    #
    # We run this BEFORE semantic evaluation so that a temporary
    # Groq outage/quota problem does not prevent deterministic
    # validation from happening.
    # ---------------------------------------------------------

    failures = evaluate_incident_report(
        report=report,
        expectation=expectation,
    )

    assert failures == [], (
        f"Deterministic evaluation failed for {incident_id}: "
        f"{failures}"
    )

    # ---------------------------------------------------------
    # 3. Semantic evaluations
    # ---------------------------------------------------------
    #
    # These evaluations use the external Groq judge.
    #
    # If Groq is unavailable because of rate limits or quota,
    # we skip the semantic part instead of marking the agent
    # itself as failed.
    # ---------------------------------------------------------

    try:
        # -----------------------------------------------------
        # 3a. Faithfulness evaluation
        # -----------------------------------------------------

        faithfulness_metric = FaithfulnessMetric(
            model=JUDGE_MODEL,
            threshold=0.7,
            include_reason=False,
        )

        faithfulness_test_case = LLMTestCase(
            input=investigation_query,
            actual_output=report.model_dump_json(),
            retrieval_context=result.retrieved_context,
        )

        faithfulness_metric.measure(
            faithfulness_test_case,
        )

        assert faithfulness_metric.is_successful(), (
            f"Faithfulness evaluation failed for {incident_id}."
        )

        # -----------------------------------------------------
        # 3b. Investigation trajectory evaluation
        # -----------------------------------------------------

        trajectory_test_case = LLMTestCase(
            input=investigation_query,
            actual_output=report.model_dump_json(),
            tools_called=tools_called,
        )

        trajectory_metric = evaluate_investigation_trajectory(
            trajectory_test_case,
        )

        print(
            f"\nTrajectory score: "
            f"{trajectory_metric.score:.3f}"
        )

        print(
            f"Trajectory reason: "
            f"{trajectory_metric.reason}"
        )

        assert trajectory_metric.is_successful(), (
            f"Trajectory evaluation failed for {incident_id} "
            f"with score {trajectory_metric.score:.3f}: "
            f"{trajectory_metric.reason}"
        )

    except JudgeUnavailableError as error:
        pytest.skip(
            f"Semantic judge unavailable: {error}"
        )

    # ---------------------------------------------------------
    # 4. Display useful evaluation information
    # ---------------------------------------------------------

    print(f"\nIncident: {incident_id}")
    print(f"Likely cause: {report.likely_cause}")
    print(f"Confidence: {report.confidence}")
    print(f"Evidence: {report.evidence}")
    print(f"Tools called: {len(tools_called)}")