import pytest
import chromadb

from src.rag.vector_store import RAGRetrievalError, search_documents


VALID_RESULT = {
    "ids": [["log-001", "log-002"]],
    "documents": [["first", "second"]],
    "metadatas": [[
        {
            "incident_id": "INC-1",
            "source_type": "log",
            "source_id": "log-001",
        },
        {
            "incident_id": "INC-1",
            "source_type": "log",
            "source_id": "log-002",
        },
    ]],
    "distances": [[0.2, 0.1]],
}


class FakeCollection:
    def __init__(self, result: dict[str, object]) -> None:
        self.result = result
        self.query_kwargs: dict[str, object] | None = None

    def query(self, **kwargs: object) -> dict[str, object]:
        self.query_kwargs = kwargs
        return self.result


class FailingCollection:
    def query(self, **kwargs: object) -> dict[str, object]:
        raise chromadb.errors.ChromaError("query failed")


@pytest.mark.parametrize("missing_key", ["ids", "documents", "metadatas", "distances"])
def test_missing_result_key_raises_controlled_error(missing_key: str) -> None:
    result = {key: value for key, value in VALID_RESULT.items() if key != missing_key}

    with pytest.raises(RAGRetrievalError):
        search_documents(FakeCollection(result), "query", incident_id="INC-1")


@pytest.mark.parametrize(
    "result",
    [
        {**VALID_RESULT, "documents": []},
        {**VALID_RESULT, "metadatas": [[]]},
        {**VALID_RESULT, "distances": [[0.2]]},
        {**VALID_RESULT, "documents": [["first", "second"], ["extra"]]},
    ],
)
def test_malformed_result_structure_raises_controlled_error(result: dict[str, object]) -> None:
    with pytest.raises(RAGRetrievalError):
        search_documents(FakeCollection(result), "query", incident_id="INC-1")


def test_mismatched_parallel_result_lengths_raise_controlled_error() -> None:
    result = {**VALID_RESULT, "distances": [[0.2]]}

    with pytest.raises(RAGRetrievalError):
        search_documents(FakeCollection(result), "query", incident_id="INC-1")


@pytest.mark.parametrize(
    "metadata",
    [
        {"incident_id": "INC-1", "source_type": "log"},
        {"incident_id": "INC-1", "source_id": "log-001"},
        {"source_type": "log", "source_id": "log-001"},
    ],
)
def test_missing_required_metadata_raises_controlled_error(metadata: dict[str, str]) -> None:
    result = {**VALID_RESULT, "metadatas": [[metadata, metadata]]}

    with pytest.raises(RAGRetrievalError):
        search_documents(FakeCollection(result), "query", incident_id="INC-1")


def test_wrong_incident_is_rejected() -> None:
    metadata = {
        "incident_id": "INC-2",
        "source_type": "log",
        "source_id": "log-001",
    }
    result = {**VALID_RESULT, "metadatas": [[metadata, metadata]]}

    with pytest.raises(RAGRetrievalError, match="another incident"):
        search_documents(FakeCollection(result), "query", incident_id="INC-1")


def test_incident_and_source_filters_are_preserved() -> None:
    collection = FakeCollection(VALID_RESULT)

    search_documents(
        collection,
        "query",
        incident_id="INC-1",
        source_type="log",
    )

    assert collection.query_kwargs is not None
    assert collection.query_kwargs["where"] == {
        "$and": [
            {"incident_id": "INC-1"},
            {"source_type": "log"},
        ]
    }


def test_valid_empty_response_returns_empty_list() -> None:
    result = {
        "ids": [[]],
        "documents": [[]],
        "metadatas": [[]],
        "distances": [[]],
    }

    assert search_documents(FakeCollection(result), "query", incident_id="INC-1") == []


def test_chroma_query_failure_raises_controlled_error() -> None:
    with pytest.raises(RAGRetrievalError, match="vector store query failed"):
        search_documents(FailingCollection(), "query", incident_id="INC-1")


def test_invalid_distance_raises_controlled_error() -> None:
    result = {**VALID_RESULT, "distances": [["invalid", 0.1]]}

    with pytest.raises(RAGRetrievalError):
        search_documents(FakeCollection(result), "query", incident_id="INC-1")
