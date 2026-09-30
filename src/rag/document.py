from pydantic import BaseModel, Field

class EvidenceDocument(BaseModel):
    #Represents a searchable piece of incident evidence.
    content: str = Field(
        description="Text content of the incident evidence."
    )
    source_type: str = Field(
        description="Type of evidence, such as log, commit, or deployment."
    )
    incident_id: str = Field(
        description="Identifier of the incident this evidence belongs to."
    )
    source_id: str = Field(
        description="Unique identifier for the individual evidence item."
    )