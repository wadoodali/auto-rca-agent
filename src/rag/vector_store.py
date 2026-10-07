import os
import chromadb
from src.rag.document import EvidenceDocument
from dotenv import load_dotenv
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

load_dotenv()
def create_embedding_function() -> OpenAIEmbeddingFunction:
    """Create the OpenAI embedding function used by ChromaDB."""

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable is not set.")
    return OpenAIEmbeddingFunction(model_name="text-embedding-3-small", api_key=api_key,)

def create_vector_store() -> chromadb.Collection:
    """Create the ChromaDB collection used for incident evidence."""

    client = chromadb.PersistentClient(path="data/chroma")
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

    results = collection.query(**query_kwargs)
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    return [
        {
            "content": document,
            "source_type": metadata["source_type"],
            "source_id": metadata["source_id"],
            "distance": distance,
        }
        for document, metadata, distance in zip(documents, metadatas, distances,)
    ]