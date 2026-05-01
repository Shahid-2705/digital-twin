from __future__ import annotations

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams


COLLECTION_NAME = "demo_knowledge"
VECTOR_SIZE = 384


def build_vector(seed: int, size: int = VECTOR_SIZE) -> list[float]:
    return [((seed + i) % 100) / 100 for i in range(size)]


def main() -> None:
    client = QdrantClient(host="localhost", port=6333)

    existing = {c.name for c in client.get_collections().collections}
    if COLLECTION_NAME not in existing:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )

    points = [
        PointStruct(
            id=1,
            vector=build_vector(1),
            payload={"text": "AI Clone supports FastAPI backend services."},
        ),
        PointStruct(
            id=2,
            vector=build_vector(2),
            payload={"text": "Qdrant stores embeddings for semantic retrieval."},
        ),
        PointStruct(
            id=3,
            vector=build_vector(3),
            payload={"text": "Ollama powers local LLM inference with llama3.1."},
        ),
    ]
    client.upsert(collection_name=COLLECTION_NAME, points=points)
    print("Demo data seeded into Qdrant collection:", COLLECTION_NAME)


if __name__ == "__main__":
    main()
