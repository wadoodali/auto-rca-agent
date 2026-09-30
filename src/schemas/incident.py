from pydantic import BaseModel, Field

class IncidentReport(BaseModel):
    """Structured root-cause analysis produced by the AI investigator."""

    model_config = {"extra": "forbid"}
    likely_cause: str = Field(
        description="The most likely root cause of the incident."
    )
    evidence: list[str] = Field(
        description="Evidence supporting the root-cause hypothesis."
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence in the root-cause analysis, from 0.0 to 1.0."
    )
    suggested_remediation: str = Field(
        description="Recommended action to mitigate or resolve the incident."
    )