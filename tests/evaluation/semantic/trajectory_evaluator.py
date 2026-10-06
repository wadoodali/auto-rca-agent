from deepeval.metrics import GEval
from deepeval.metrics.g_eval.utils import Rubric
from deepeval.test_case import LLMTestCase, SingleTurnParams

from tests.evaluation.semantic.groq_judge import GroqJudge


JUDGE_MODEL = GroqJudge(
    model="openai/gpt-oss-120b",
    temperature=0.0,
)


def evaluate_investigation_trajectory(
    test_case: LLMTestCase,
) -> GEval:
    """Evaluate the quality of an RCA agent's investigation trajectory."""

    metric = GEval(
        name="RCA Trajectory Quality",
        evaluation_params=[
            SingleTurnParams.INPUT,
            SingleTurnParams.ACTUAL_OUTPUT,
            SingleTurnParams.TOOLS_CALLED,
        ],
        criteria=(
            "Evaluate whether the agent followed an effective investigation "
            "trajectory for root-cause analysis. The agent should use relevant "
            "tools, gather sufficient evidence, make meaningful progress toward "
            "the root cause, avoid unnecessary or redundant investigation steps, "
            "and reach its conclusion only after gathering appropriate evidence."
        ),
        rubric=[
            Rubric(
                score_range=(0, 2),
                expected_outcome=(
                    "The investigation is ineffective. Tools are missing, "
                    "mostly irrelevant, or the agent reaches a conclusion "
                    "without meaningful evidence gathering."
                ),
            ),
            Rubric(
                score_range=(3, 5),
                expected_outcome=(
                    "The investigation is partially effective. Some tools and "
                    "evidence are relevant, but the trajectory contains clear "
                    "gaps, unnecessary steps, or insufficient investigation "
                    "before the conclusion."
                ),
            ),
            Rubric(
                score_range=(6, 8),
                expected_outcome=(
                    "The investigation is effective. The agent uses relevant "
                    "tools, gathers sufficient evidence, makes reasonable "
                    "progress toward the root cause, and avoids significant "
                    "redundancy."
                ),
            ),
            Rubric(
                score_range=(9, 10),
                expected_outcome=(
                    "The investigation is highly effective. Every major step "
                    "meaningfully contributes to the RCA, evidence gathering "
                    "is sufficient and focused, there is little or no "
                    "redundancy, and the final conclusion follows naturally "
                    "from the investigation."
                ),
            ),
        ],
        model=JUDGE_MODEL,
        threshold=0.7,
    )

    metric.measure(test_case)

    return metric