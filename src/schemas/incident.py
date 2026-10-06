from pydantic import BaseModel, Field
from typing import Any

class IncidentReport(BaseModel):
    """Structured root-cause analysis produced by the AI investigator."""

    model_config = {"extra": "forbid"}
    likely_cause: str = Field(description="The most likely root cause of the incident.")
    evidence: list[str] = Field(description="Evidence supporting the root-cause hypothesis.")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in the root-cause analysis, from 0.0 to 1.0.")
    suggested_remediation: str = Field(description="Recommended action to mitigate or resolve the incident.")

class InvestigationResult(BaseModel):
    """Complete result of an incident investigation.

    Contains the final RCA report together with the evidence retrieved
    during the investigation and the sequence of tool calls executed
    by the agent.
    """

    report: IncidentReport
    retrieved_context: list[str] = Field(default_factory=list, description="Evidence documents retrieved during the investigation.")
    execution_trace: list[dict[str, Any]] = Field(default_factory=list, description="Ordered record of tool calls executed during the investigation.")