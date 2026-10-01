from typing import Any
from src.rag.retriever import retrieve_deployments

def get_deployment_delta(incident_id: str, query: str,) -> list[dict[str, Any]]:
    """Search deployment evidence semantically using the RAG pipeline."""

    evidence = retrieve_deployments(incident_id=incident_id, query=query,)
    return [item.model_dump() for item in evidence]