from typing import Any
from src.rag.retriever import retrieve_code_changes

def query_git_commits(incident_id: str, query: str,) -> list[dict[str, Any]]:
    """Search Git commit evidence semantically using the RAG pipeline."""

    evidence = retrieve_code_changes(incident_id=incident_id, query=query,)
    return [item.model_dump() for item in evidence]