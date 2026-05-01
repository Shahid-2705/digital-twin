from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.memory.qdrant_client import CompanyQdrantMemory


@dataclass(frozen=True, slots=True)
class RetrievedContext:
    namespace: str
    text: str
    score: float
    metadata: dict[str, Any]


class RAGPipeline:
    def __init__(self, memory_client: CompanyQdrantMemory, top_k: int = 5) -> None:
        self.memory_client = memory_client
        self.top_k = top_k

    def retrieve(
        self,
        *,
        company_id: str,
        namespaces: list[str],
        query: str,
        top_k: int | None = None,
    ) -> list[RetrievedContext]:
        limit = top_k or self.top_k
        contexts: list[RetrievedContext] = []
        for namespace in namespaces:
            hits = self.memory_client.search(
                company_id=company_id,
                namespace=namespace,
                query=query,
                top_k=limit,
            )
            for hit in hits:
                contexts.append(
                    RetrievedContext(
                        namespace=hit.namespace,
                        text=hit.text,
                        score=hit.score,
                        metadata=hit.metadata,
                    )
                )
        contexts.sort(key=lambda item: item.score, reverse=True)
        return contexts[:limit]

    @staticmethod
    def inject_into_prompt(prompt: str, contexts: list[RetrievedContext]) -> str:
        if not contexts:
            return f"{prompt}\n\n[RETRIEVED_CONTEXT]\nNo relevant context found.\n[/RETRIEVED_CONTEXT]"
        chunks = []
        for idx, item in enumerate(contexts, start=1):
            chunks.append(
                f"{idx}. (ns={item.namespace}, score={item.score:.4f}) {item.text}"
            )
        context_block = "\n".join(chunks)
        return (
            f"{prompt}\n\n"
            f"[RETRIEVED_CONTEXT]\n{context_block}\n[/RETRIEVED_CONTEXT]"
        )
