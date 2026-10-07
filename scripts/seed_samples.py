from pathlib import Path

from src.rag.ingestion import load_incident_documents
from src.rag.vector_store import add_documents, create_vector_store


SAMPLES_DIRECTORY = Path("samples")


def main() -> None:
    """Seed all incident samples into the ChromaDB vector store."""

    collection = create_vector_store()

    incident_directories = sorted(
        SAMPLES_DIRECTORY.glob("incident_*")
    )

    for incident_directory in incident_directories:
        incident_number = incident_directory.name.split("_")[-1]
        incident_id = f"INC-2026-{int(incident_number):03d}"

        documents = load_incident_documents(
            incident_directory=incident_directory,
            incident_id=incident_id,
        )

        add_documents(collection, documents)

        print(
            f"Seeded {incident_id}: {len(documents)} documents"
        )


if __name__ == "__main__":
    main()