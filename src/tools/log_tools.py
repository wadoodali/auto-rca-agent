from typing import Any
from src.rag.retriever import retrieve_logs

def fetch_incident_logs(incident_id: str, query: str,) -> list[dict[str, Any]]:
    """Search incident logs semantically using the RAG pipeline."""

    evidence = retrieve_logs(incident_id=incident_id, query=query,)
    return [item.model_dump() for item in evidence]