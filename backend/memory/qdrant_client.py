from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, FieldCondition, Filter, MatchValue, PointStruct, VectorParams
from backend.models.embeddings import EmbeddingEngine

from backend import config


@dataclass(frozen=True, slots=True)
class SearchHit:
    id: str
    text: str
    score: float
    namespace: str
    metadata: dict[str, Any]


class CompanyQdrantMemory:
    """Qdrant wrapper with per-company namespaces and embeddings via EmbeddingEngine."""

    def __init__(
        self,
        host: str = config.QDRANT_HOST,
        port: int = config.QDRANT_PORT,
    ) -> None:
        self.client = QdrantClient(host=host, port=port)
        self.embedding_engine = EmbeddingEngine()
        self.embedding_model_name = self.embedding_engine.model_name
        self.embedding_dim = self.embedding_engine.dimension

    @staticmethod
    def _normalize(value: str) -> str:
        return value.strip().lower().replace(" ", "_").replace("-", "_")

    def _namespace(self, company_id: str, namespace: str) -> str:
        return f"{self._normalize(company_id)}__{self._normalize(namespace)}"

    def _ensure_collection(self, collection_name: str) -> None:
        existing = {c.name for c in self.client.get_collections().collections}
        if collection_name in existing:
            return
        self.client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=self.embedding_dim, distance=Distance.COSINE),
        )

    def _embed(self, text: str) -> list[float]:
        vector = self.embedding_engine.embed(text)
        return vector.tolist()

    def create_company_namespaces(self, company_id: str, namespaces: list[str]) -> list[str]:
        created: list[str] = []
        for namespace in namespaces:
            collection_name = self._namespace(company_id, namespace)
            self._ensure_collection(collection_name)
            created.append(collection_name)
        return created

    def upsert_document(
        self,
        *,
        company_id: str,
        namespace: str,
        text: str,
        metadata: dict[str, Any] | None = None,
        doc_id: str | None = None,
    ) -> str:
        collection_name = self._namespace(company_id, namespace)
        self._ensure_collection(collection_name)
        point_id = doc_id or str(uuid4())
        payload = {
            "text": text,
            "company_id": company_id,
            "namespace": namespace,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        if metadata:
            payload.update(metadata)
        self.client.upsert(
            collection_name=collection_name,
            points=[PointStruct(id=point_id, vector=self._embed(text), payload=payload)],
        )
        return point_id

    def upsert_documents(
        self,
        *,
        company_id: str,
        namespace: str,
        texts: list[str],
        metadatas: list[dict[str, Any]] | None = None,
        doc_ids: list[str] | None = None,
    ) -> list[str]:
        collection_name = self._namespace(company_id, namespace)
        self._ensure_collection(collection_name)
        
        point_ids = doc_ids or [str(uuid4()) for _ in texts]
        vectors = self.embedding_engine.embed_batch(texts)
        
        points = []
        for i, text in enumerate(texts):
            payload = {
                "text": text,
                "company_id": company_id,
                "namespace": namespace,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            if metadatas and i < len(metadatas) and metadatas[i]:
                payload.update(metadatas[i])
            points.append(PointStruct(id=point_ids[i], vector=vectors[i], payload=payload))
            
        self.client.upsert(
            collection_name=collection_name,
            points=points,
        )
        return point_ids

    def search(
        self,
        *,
        company_id: str,
        namespace: str,
        query: str,
        top_k: int = 5,
    ) -> list[SearchHit]:
        collection_name = self._namespace(company_id, namespace)
        self._ensure_collection(collection_name)
        results = self.client.search(
            collection_name=collection_name,
            query_vector=self._embed(query),
            limit=top_k,
            query_filter=Filter(
                must=[FieldCondition(key="company_id", match=MatchValue(value=company_id))]
            ),
        )
        return [
            SearchHit(
                id=str(hit.id),
                text=str(hit.payload.get("text", "")),
                score=float(hit.score),
                namespace=str(hit.payload.get("namespace", namespace)),
                metadata={k: v for k, v in hit.payload.items() if k != "text"},
            )
            for hit in results
        ]

    def get_profile(self, company_id: str) -> dict[str, Any]:
        prefix = f"{self._normalize(company_id)}__"
        collections = [c.name for c in self.client.get_collections().collections if c.name.startswith(prefix)]
        namespaces = [name.split("__", 1)[1] for name in collections]
        return {
            "company_id": company_id,
            "embedding_model": self.embedding_model_name,
            "embedding_device": self.embedding_engine.device,
            "namespaces": namespaces,
            "collections": collections,
            "namespace_count": len(namespaces),
        }
