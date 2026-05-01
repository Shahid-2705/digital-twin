"""
Qdrant vector memory store for RAG.
Supports in-memory mode (no Docker needed) and persistent mode.
"""

import uuid
import logging
from typing import Optional
from datetime import datetime, timezone

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)

from backend.config import (
    QDRANT_HOST,
    QDRANT_PORT,
    QDRANT_COLLECTION,
    QDRANT_IN_MEMORY,
    EMBEDDING_DIM,
    RAG_TOP_K,
    RAG_SCORE_THRESHOLD,
)
from backend.models.embeddings import EmbeddingEngine

logger = logging.getLogger(__name__)


class QdrantMemory:
    """Vector memory using Qdrant for document storage and retrieval."""

    def __init__(
        self,
        embedding_engine: EmbeddingEngine,
        collection_name: str = QDRANT_COLLECTION,
        in_memory: bool = QDRANT_IN_MEMORY,
    ):
        self.embedding_engine = embedding_engine
        self.collection_name = collection_name

        if in_memory:
            logger.info("Initializing Qdrant in in-memory mode")
            self.client = QdrantClient(":memory:")
        else:
            logger.info(f"Connecting to Qdrant at {QDRANT_HOST}:{QDRANT_PORT}")
            self.client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

        self._ensure_collection()

    def _ensure_collection(self):
        """Create collection if it doesn't exist."""
        collections = [c.name for c in self.client.get_collections().collections]
        if self.collection_name not in collections:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=EMBEDDING_DIM,
                    distance=Distance.COSINE,
                ),
            )
            logger.info(f"Created Qdrant collection: {self.collection_name}")
        else:
            logger.info(f"Qdrant collection exists: {self.collection_name}")

    def add_document(
        self,
        text: str,
        metadata: Optional[dict] = None,
        company_id: Optional[str] = None,
        doc_type: str = "general",
    ) -> str:
        """Add a document to vector memory. Returns the point ID."""
        point_id = str(uuid.uuid4())
        vector = self.embedding_engine.embed(text).tolist()

        payload = {
            "text": text,
            "doc_type": doc_type,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        if company_id:
            payload["company_id"] = company_id
        if metadata:
            payload.update(metadata)

        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload,
                )
            ],
        )
        logger.debug(f"Added document {point_id} to Qdrant")
        return point_id

    def add_documents_batch(
        self,
        texts: list[str],
        metadatas: Optional[list[dict]] = None,
        company_id: Optional[str] = None,
        doc_type: str = "general",
    ) -> list[str]:
        """Add multiple documents in a batch."""
        vectors = self.embedding_engine.embed(texts)
        if vectors.ndim == 1:
            vectors = vectors.reshape(1, -1)

        point_ids = []
        points = []
        for i, (text, vector) in enumerate(zip(texts, vectors)):
            pid = str(uuid.uuid4())
            point_ids.append(pid)

            payload = {
                "text": text,
                "doc_type": doc_type,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            if company_id:
                payload["company_id"] = company_id
            if metadatas and i < len(metadatas):
                payload.update(metadatas[i])

            points.append(PointStruct(id=pid, vector=vector.tolist(), payload=payload))

        self.client.upsert(collection_name=self.collection_name, points=points)
        logger.info(f"Batch added {len(points)} documents to Qdrant")
        return point_ids

    def search(
        self,
        query: str,
        top_k: int = RAG_TOP_K,
        score_threshold: float = RAG_SCORE_THRESHOLD,
        company_id: Optional[str] = None,
        doc_type: Optional[str] = None,
    ) -> list[dict]:
        """Search for similar documents. Returns list of {text, score, metadata}."""
        query_vector = self.embedding_engine.embed(query).tolist()

        conditions = []
        if company_id:
            conditions.append(
                FieldCondition(key="company_id", match=MatchValue(value=company_id))
            )
        if doc_type:
            conditions.append(
                FieldCondition(key="doc_type", match=MatchValue(value=doc_type))
            )

        search_filter = Filter(must=conditions) if conditions else None

        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=top_k,
            score_threshold=score_threshold,
            query_filter=search_filter,
        )

        return [
            {
                "id": str(hit.id),
                "text": hit.payload.get("text", ""),
                "score": round(hit.score, 4),
                "company_id": hit.payload.get("company_id"),
                "doc_type": hit.payload.get("doc_type"),
                "metadata": {
                    k: v
                    for k, v in hit.payload.items()
                    if k not in ("text", "company_id", "doc_type")
                },
            }
            for hit in results
        ]

    def delete_by_company(self, company_id: str) -> int:
        """Delete all documents for a company."""
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="company_id", match=MatchValue(value=company_id)
                    )
                ]
            ),
        )
        logger.info(f"Deleted all documents for company {company_id}")
        return 0

    def count(self, company_id: Optional[str] = None) -> int:
        """Count documents, optionally filtered by company."""
        info = self.client.get_collection(self.collection_name)
        return info.points_count

    def clear(self):
        """Delete and recreate the collection."""
        self.client.delete_collection(self.collection_name)
        self._ensure_collection()
        logger.info("Cleared all documents from Qdrant")
