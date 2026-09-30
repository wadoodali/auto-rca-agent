from pydantic import BaseModel
from pydantic import BaseModel, Field

class RetrievedEvidence(BaseModel):
    """Represents evidence returned by semantic retrieval."""
    content: str
    source_type: str
    source_id: str
    distance: float

class RetrievalConfig(BaseModel):
    """Configuration for semantic evidence retrieval."""

    n_results: int = Field(default=5, ge=1, description="Maximum number of evidence documents to retrieve.",)
    max_distance: float | None = Field(default=None, ge=0.0, description="Maximum allowed vector distance for retrieved evidence.",)