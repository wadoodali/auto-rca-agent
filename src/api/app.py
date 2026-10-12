import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator

from src.agent.rca_agent import run_investigation
from src.llm.client import LLMProviderError
from src.rag.vector_store import RAGRetrievalError
from src.schemas.incident import InvestigationResult


logger = logging.getLogger(__name__)


class InvestigationRequest(BaseModel):
    """Input required to start an incident investigation."""

    incident_id: str
    investigation_query: str

    @field_validator("incident_id", "investigation_query")
    @classmethod
    def reject_blank_values(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be empty or whitespace-only")
        return value


class IncidentSummary(BaseModel):
    """Incident identifier exposed by the sample-incident API."""

    incident_id: str


def _sample_incident_ids() -> list[str]:
    samples_directory = Path(__file__).resolve().parents[2] / "samples"
    incident_ids: list[str] = []
    for directory in sorted(samples_directory.glob("incident_*")):
        suffix = directory.name.removeprefix("incident_")
        if suffix.isdigit():
            incident_ids.append(f"INC-2026-{int(suffix):03d}")
    return incident_ids


SUPPORTED_INCIDENT_IDS = _sample_incident_ids()

app = FastAPI(
    title="AI Incident Investigator API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/api/incidents", response_model=list[IncidentSummary])
def list_incidents() -> list[IncidentSummary]:
    """List incidents available in the seeded sample data."""

    return [
        IncidentSummary(incident_id=incident_id)
        for incident_id in SUPPORTED_INCIDENT_IDS
    ]


@app.post(
    "/api/investigations",
    response_model=InvestigationResult,
)
def create_investigation(request: InvestigationRequest) -> InvestigationResult:
    """Run an investigation for one supported sample incident."""

    if request.incident_id not in SUPPORTED_INCIDENT_IDS:
        raise HTTPException(
            status_code=404,
            detail="The requested incident is not supported.",
        )

    try:
        return run_investigation(
            incident_id=request.incident_id,
            investigation_query=request.investigation_query,
        )
    except LLMProviderError:
        raise HTTPException(
            status_code=502,
            detail="The investigation provider is unavailable.",
        ) from None
    except RAGRetrievalError:
        raise HTTPException(
            status_code=502,
            detail="Incident evidence could not be retrieved.",
        ) from None
    except Exception:
        logger.exception("Unexpected investigation failure.")
        raise HTTPException(
            status_code=500,
            detail="The investigation could not be completed.",
        ) from None
