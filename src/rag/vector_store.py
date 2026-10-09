from numbers import Real

import chromadb
from src.rag.document import EvidenceDocument
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from src.config import get_config, require_openai_api_key


class RAGRetrievalError(RuntimeError):
    """Raised when the vector store cannot return valid evidence."""


def create_embedding_function() -> OpenAIEmbeddingFunction:
    """Create the OpenAI embedding function used by ChromaDB."""

    config = get_config()
    api_key = require_openai_api_key(config)
    return OpenAIEmbeddingFunction(
        model_name=config.openai_embedding_model,
        api_key=api_key,
    )

def create_vector_store() -> chromadb.Collection:
    """Create the ChromaDB collection used for incident evidence."""

    client = chromadb.PersistentClient(path=get_config().chroma_path)
    return client.get_or_create_collection(name="incident_evidence", embedding_function=create_embedding_function(),)

def add_documents(collection: chromadb.Collection, documents: list[EvidenceDocument],) -> None:
    """Add evidence documents to the ChromaDB collection."""

    collection.upsert(
        ids=[
            f"{document.incident_id}:{document.source_type}:{index}"
            for index, document in enumerate(documents)
        ],
        documents=[
            document.content
            for document in documents
        ],
        metadatas=[
            {
                "incident_id": document.incident_id,
                "source_type": document.source_type,
                "source_id": document.source_id,
            }
            for document in documents
        ],
    )

def search_documents(collection: chromadb.Collection, query: str, n_results: int = 5, incident_id: str | None = None, source_type: str | None = None,) -> list[dict[str, str | float]]:
    """Search the evidence collection using semantic similarity."""

    query_kwargs: dict[str, object] = {"query_texts": [query], "n_results": n_results, "include": ["documents", "metadatas", "distances"],}

    where: dict[str, str] = {}
    if incident_id is not None:
        where["incident_id"] = incident_id
    if source_type is not None:
        where["source_type"] = source_type
    if len(where) == 1:
        query_kwargs["where"] = where
    elif len(where) > 1:
        query_kwargs["where"] = {"$and": [{key: value}for key, value in where.items()]}

    try:
        results = collection.query(**query_kwargs)
    except chromadb.errors.ChromaError as error:
        raise RAGRetrievalError(
            "The vector store query failed."
        ) from error

    required_keys = {"ids", "documents", "metadatas", "distances"}
    if not isinstance(results, dict) or not required_keys.issubset(results):
        raise RAGRetrievalError("The vector store returned an invalid response.")

    columns: dict[str, list[object]] = {}
    for key in required_keys:
        value = results[key]
        if (
            not isinstance(value, list)
            or len(value) != 1
            or not isinstance(value[0], list)
        ):
            raise RAGRetrievalError("The vector store returned an invalid response.")
        columns[key] = value[0]

    if len({len(values) for values in columns.values()}) != 1:
        raise RAGRetrievalError("The vector store returned mismatched results.")

    evidence: list[dict[str, str | float]] = []
    for document, metadata, distance in zip(
        columns["documents"],
        columns["metadatas"],
        columns["distances"],
    ):
        if not isinstance(document, str) or not isinstance(metadata, dict):
            raise RAGRetrievalError("The vector store returned invalid evidence.")

        required_metadata = {"incident_id", "source_type", "source_id"}
        if (
            not required_metadata.issubset(metadata)
            or not all(isinstance(metadata[key], str) for key in required_metadata)
        ):
            raise RAGRetrievalError("The vector store returned invalid metadata.")

        if incident_id is not None and metadata["incident_id"] != incident_id:
            raise RAGRetrievalError("The vector store returned another incident.")
        if source_type is not None and metadata["source_type"] != source_type:
            raise RAGRetrievalError("The vector store returned another source type.")
        if not isinstance(distance, Real) or isinstance(distance, bool):
            raise RAGRetrievalError("The vector store returned an invalid distance.")

        evidence.append({
            "content": document,
            "incident_id": metadata["incident_id"],
            "source_type": metadata["source_type"],
            "source_id": metadata["source_id"],
            "distance": float(distance),
        })

    return evidence
