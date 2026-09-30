from src.rag.models import RetrievedEvidence
from src.rag.vector_store import create_vector_store, search_documents
from src.rag.models import RetrievedEvidence, RetrievalConfig

DEFAULT_RETRIEVAL_CONFIG = RetrievalConfig(n_results=5, max_distance=None,)

def retrieve_evidence(
    query: str,
    incident_id: str,
    config: RetrievalConfig | None = None,
    source_type: str | None = None,
) -> list[RetrievedEvidence]:
    """Retrieve relevant evidence for a specific incident."""

    if config is None:
        config = DEFAULT_RETRIEVAL_CONFIG

    collection = create_vector_store()
    results = search_documents(
        collection=collection,
        query=query,
        n_results=config.n_results,
        incident_id=incident_id,
        source_type=source_type,
    )
    evidence = [
        RetrievedEvidence(**result)
        for result in results
    ]

    if config.max_distance is not None:
        evidence = [
            item
            for item in evidence
            if item.distance <= config.max_distance
        ]
    evidence.sort(key=lambda item: item.distance)
    return evidence

def retrieve_code_changes(
    incident_id: str,
    query: str,
    config: RetrievalConfig | None = None,
) -> list[RetrievedEvidence]:
    """Retrieve commit evidence relevant to an incident."""

    return retrieve_evidence(
        query=query,
        incident_id=incident_id,
        config=config,
        source_type="commit",
    )

def retrieve_deployments(
    incident_id: str,
    query: str,
    config: RetrievalConfig | None = None,
) -> list[RetrievedEvidence]:
    """Retrieve deployment evidence relevant to an incident."""

    return retrieve_evidence(
        query=query,
        incident_id=incident_id,
        config=config,
        source_type="deployment",
    )

def retrieve_logs(
    incident_id: str,
    query: str,
    config: RetrievalConfig | None = None,
) -> list[RetrievedEvidence]:
    """Retrieve log evidence relevant to an incident."""

    return retrieve_evidence(
        query=query,
        incident_id=incident_id,
        config=config,
        source_type="log",
    )

def retrieve_all_evidence(
    incident_id: str,
    query: str,
    config: RetrievalConfig | None = None,
) -> list[RetrievedEvidence]:
    """Retrieve relevant evidence across all incident source types."""

    return retrieve_evidence(
        query=query,
        incident_id=incident_id,
        config=config,
    )