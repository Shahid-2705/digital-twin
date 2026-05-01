"""
Context builder — retrieves relevant docs from Qdrant and assembles context for LLM.
"""
import logging
from typing import Optional
from backend.memory.qdrant_store import QdrantMemory
from backend.config import RAG_TOP_K, RAG_SCORE_THRESHOLD

logger = logging.getLogger(__name__)


class ContextBuilder:
    def __init__(self, memory: QdrantMemory):
        self.memory = memory

    def build_context(
        self, query: str, company_id: Optional[str] = None,
        doc_type: Optional[str] = None, top_k: int = RAG_TOP_K,
        score_threshold: float = RAG_SCORE_THRESHOLD, max_chars: int = 3000,
    ) -> dict:
        results = self.memory.search(
            query=query, top_k=top_k, score_threshold=score_threshold,
            company_id=company_id, doc_type=doc_type,
        )
        if not results:
            return {"context_text": "", "sources": [], "num_sources": 0, "has_context": False}

        parts, total, sources = [], 0, []
        for i, doc in enumerate(results):
            text = doc["text"].strip()
            if total + len(text) > max_chars:
                rem = max_chars - total
                if rem > 100:
                    text = text[:rem] + "..."
                else:
                    break
            parts.append(f"[Source {i+1} | Relevance: {doc['score']:.2f}]\n{text}")
            total += len(text)
            sources.append({"id": doc["id"], "score": doc["score"],
                            "doc_type": doc.get("doc_type", "unknown"),
                            "preview": text[:120]})
        return {"context_text": "\n\n".join(parts), "sources": sources,
                "num_sources": len(sources), "has_context": True}

    def build_conversation_context(
        self, query: str, history: list[dict],
        company_id: Optional[str] = None, max_history: int = 6,
    ) -> dict:
        rag = self.build_context(query=query, company_id=company_id, max_chars=2500)
        recent = history[-max_history:] if history else []
        hist_text = "\n".join(f"{m['role'].upper()}: {m['content']}" for m in recent)
        combined = ""
        if rag["has_context"]:
            combined += f"=== RELEVANT KNOWLEDGE ===\n{rag['context_text']}\n\n"
        if hist_text:
            combined += f"=== RECENT CONVERSATION ===\n{hist_text}\n\n"
        return {"context_text": combined, "rag_sources": rag["sources"],
                "num_rag_sources": rag["num_sources"], "history_messages": len(recent),
                "has_context": bool(combined.strip())}
