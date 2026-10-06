import json

import pytest
from dotenv import load_dotenv
from deepeval.metrics import (
    FaithfulnessMetric,
    TaskCompletionMetric,
)
from deepeval.test_case import LLMTestCase, ToolCall

from src.agent.rca_agent import run_investigation
from tests.evaluation.deterministic.evaluator import (
    evaluate_incident_report,
)
from tests.evaluation.deterministic.expected_incidents import (
    INCIDENT_001_EXPECTATION,
    INCIDENT_002_EXPECTATION,
    ExpectedIncident,
)
from tests.evaluation.semantic.groq_judge import GroqJudge
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
    ],
)
def test_agent_investigation_is_faithful(
    incident_id: str,
    investigation_query: str,
    expectation: ExpectedIncident,
) -> None:
    """Verify that an incident investigation is faithful and effective."""

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
    # 1. Faithfulness evaluation
    # ---------------------------------------------------------

    faithfulness_metric = FaithfulnessMetric(
        model=JUDGE_MODEL,
        threshold=0.7,
    )

    faithfulness_test_case = LLMTestCase(
        input=investigation_query,
        actual_output=report.model_dump_json(),
        retrieval_context=result.retrieved_context,
    )

    faithfulness_metric.measure(faithfulness_test_case)

    assert faithfulness_metric.is_successful(), (
        f"Faithfulness evaluation failed for {incident_id}."
    )

    # ---------------------------------------------------------
    # 2. Task completion evaluation
    # ---------------------------------------------------------

    task_completion_metric = TaskCompletionMetric(
        task=investigation_query,
        model=JUDGE_MODEL,
        threshold=0.7,
    )

    task_completion_test_case = LLMTestCase(
        input=investigation_query,
        actual_output=report.model_dump_json(),
        tools_called=tools_called,
    )

    task_completion_metric.measure(task_completion_test_case)

    assert task_completion_metric.is_successful(), (
        f"Task completion evaluation failed for {incident_id}."
    )

    # ---------------------------------------------------------
    # 3. Investigation trajectory evaluation
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # 4. Deterministic evaluation
    # ---------------------------------------------------------

    failures = evaluate_incident_report(
        report=report,
        expectation=expectation,
    )

    assert failures == []

    # ---------------------------------------------------------
    # 5. Display useful evaluation information
    # ---------------------------------------------------------

    print(f"\nIncident: {incident_id}")
    print(f"Likely cause: {report.likely_cause}")
    print(f"Confidence: {report.confidence}")
    print(f"Evidence: {report.evidence}")
    print(f"Tools called: {len(tools_called)}")