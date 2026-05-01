from __future__ import annotations

import asyncio
import httpx
import uuid
import qdrant_client
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from backend.companies.company_manager import CompanyManager
from backend.models.brain import BrainClient, BrainMessage
from backend.models.verdict import VerdictEngine
from backend.pipeline.context_injector import ContextInjector, RuntimeContext
from backend.pipeline.rag import RAGPipeline
from backend.pipeline.router import IntentRouter
from backend.pipeline.personality import PersonalityEngine
from backend.pipeline.domain_resolver import DomainResolver
from backend.memory.qdrant_client import CompanyQdrantMemory
from backend.memory.mistake_db import MistakeDB
from backend.scoring.pnl_calculator import PnLCalculator


router = APIRouter(tags=["chat"])

company_manager = CompanyManager()
memory = CompanyQdrantMemory()
rag = RAGPipeline(memory_client=memory, top_k=5)
brain = BrainClient()
personality_engine = PersonalityEngine()
mistake_db = MistakeDB()


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    company_id: str | None = None
    mode: str = Field(default="advisor")
    role: str | None = None
    namespaces: list[str] | None = None
    top_k: int = Field(default=5, ge=1, le=20)


def _resolve_company(company_id: str | None) -> dict[str, Any]:
    if company_id:
        company = company_manager.get_company(company_id)
    else:
        company = company_manager.get_active()
    if company is None:
        raise RuntimeError("No valid company found.")
    return company


async def send_error(websocket: WebSocket, stage: str, error_type: str, message: str, recoverable: bool):
    await websocket.send_json({
        "type": "error",
        "stage": stage,
        "error_type": error_type,
        "message": message,
        "recoverable": recoverable
    })


@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        while True:
            try:
                raw = await websocket.receive_json()
            except WebSocketDisconnect:
                return

            pipeline_stages = []

            # Stage: input
            stage = "input"
            pipeline_stages.append(stage)
            try:
                def do_input():
                    req = ChatRequest.model_validate(raw)
                    company = _resolve_company(req.company_id)
                    role = req.role or company["role"]
                    namespaces = req.namespaces or company.get("kb_namespaces", [])
                    return req, company, role, namespaces

                req, company, role, namespaces = await asyncio.wait_for(asyncio.to_thread(do_input), timeout=30.0)

                await websocket.send_json({
                    "type": "stage",
                    "stage": "input",
                    "ok": True,
                    "payload": {"message": req.message},
                })
            except asyncio.TimeoutError:
                await send_error(websocket, stage, "TimeoutError", "Model timeout — retry", True)
                continue
            except Exception as e:
                await send_error(websocket, stage, type(e).__name__, f"Unexpected error at stage {stage}", False)
                await websocket.send_json({"type": "final", "ok": False, "error": f"Unexpected error at stage {stage}", "stage_failed": stage})
                return

            # Stage: rag
            stage = "rag"
            pipeline_stages.append(stage)
            route_intent = "general"
            route_confidence = 0.0
            retrieved = []
            prompt_with_rag = req.message
            try:
                def do_rag():
                    route = IntentRouter.classify_intent(req.message)
                    ret = rag.retrieve(
                        company_id=company["id"],
                        namespaces=namespaces,
                        query=req.message,
                        top_k=req.top_k,
                    )
                    return route, ret

                route, retrieved_tmp = await asyncio.wait_for(asyncio.to_thread(do_rag), timeout=30.0)
                route_intent = route.intent
                route_confidence = route.confidence
                retrieved = retrieved_tmp
                prompt_with_rag = rag.inject_into_prompt(req.message, retrieved)

                await websocket.send_json({
                    "type": "stage",
                    "stage": "rag",
                    "ok": True,
                    "payload": {
                        "intent": route_intent,
                        "intent_confidence": route_confidence,
                        "retrieved_count": len(retrieved),
                        "retrieved": [
                            {
                                "namespace": item.namespace,
                                "score": item.score,
                                "text": item.text,
                                "metadata": item.metadata,
                            }
                            for item in retrieved
                        ],
                    },
                })
            except asyncio.TimeoutError:
                await send_error(websocket, stage, "TimeoutError", "Model timeout — retry", True)
            except httpx.TimeoutException:
                await send_error(websocket, stage, "TimeoutException", "Model timeout — retry", True)
            except Exception as e:
                if isinstance(e, qdrant_client.http.exceptions.UnexpectedResponse) or "qdrant" in str(type(e)).lower():
                    await send_error(websocket, stage, type(e).__name__, "Memory retrieval failed", False)
                    await websocket.send_json({"type": "final", "ok": False, "error": "Memory retrieval failed", "stage_failed": stage})
                    return
                else:
                    await send_error(websocket, stage, type(e).__name__, f"Unexpected error at stage {stage}", False)
                    await websocket.send_json({"type": "final", "ok": False, "error": f"Unexpected error at stage {stage}", "stage_failed": stage})
                    return

            # Stage: context_inject
            stage = "context_inject"
            pipeline_stages.append(stage)
            final_prompt = prompt_with_rag
            try:
                def do_context():
                    rc = RuntimeContext(
                        company=company["name"],
                        role=role,
                        mode=req.mode,
                        kb_namespaces=namespaces,
                    )
                    fp = ContextInjector.enforce_and_inject(prompt_with_rag, rc)
                    return rc, fp
                
                runtime_context, final_prompt_tmp = await asyncio.wait_for(asyncio.to_thread(do_context), timeout=30.0)
                final_prompt = final_prompt_tmp

                await websocket.send_json({
                    "type": "stage",
                    "stage": "context_inject",
                    "ok": True,
                    "payload": {
                        "company": runtime_context.company,
                        "role": runtime_context.role,
                        "mode": runtime_context.mode,
                        "kb_namespaces": runtime_context.kb_namespaces,
                    },
                })
            except asyncio.TimeoutError:
                await send_error(websocket, stage, "TimeoutError", "Model timeout — retry", True)
            except RuntimeError as e:
                await send_error(websocket, stage, "RuntimeError", f"Context build failed: {e}", False)
                await websocket.send_json({"type": "final", "ok": False, "error": f"Context build failed: {e}", "stage_failed": stage})
                return
            except Exception as e:
                await send_error(websocket, stage, type(e).__name__, f"Unexpected error at stage {stage}", False)
                await websocket.send_json({"type": "final", "ok": False, "error": f"Unexpected error at stage {stage}", "stage_failed": stage})
                return

            # Stage: llm_stream
            stage = "llm_stream"
            pipeline_stages.append(stage)
            llm_response = ""
            try:
                system_prompt = personality_engine.get_system_prompt(req.mode)
                
                async def stream_with_timeout():
                    res = ""
                    stream = brain.stream_chat([
                        BrainMessage(role="system", content=system_prompt),
                        BrainMessage(role="user", content=final_prompt),
                    ])
                    async for token in stream:
                        res += token
                        await websocket.send_json({
                            "type": "stage",
                            "stage": "llm_stream",
                            "ok": True,
                            "payload": {"token": token},
                        })
                    return res
                
                llm_response = await asyncio.wait_for(stream_with_timeout(), timeout=30.0)
            except asyncio.TimeoutError:
                await send_error(websocket, stage, "TimeoutError", "Model timeout — retry", True)
            except httpx.TimeoutException:
                await send_error(websocket, stage, "TimeoutException", "Model timeout — retry", True)
            except Exception as e:
                await send_error(websocket, stage, type(e).__name__, f"Unexpected error at stage {stage}", False)
                await websocket.send_json({"type": "final", "ok": False, "error": f"Unexpected error at stage {stage}", "stage_failed": stage})
                return

            # Stage: verdict
            stage = "verdict"
            pipeline_stages.append(stage)
            resolved_domain = "general"
            verdict = None
            try:
                def do_verdict():
                    rag_score = max((item.score for item in retrieved), default=0.35) if retrieved else 0.35
                    score_proxy = min(1.0, rag_score)
                    r_namespaces = [item.namespace for item in retrieved] if retrieved else namespaces
                    dom = DomainResolver.resolve(r_namespaces, route_intent)
                    v = VerdictEngine.evaluate(
                        score=score_proxy,
                        reason=(
                            f"Intent={route_intent} with confidence {route_confidence:.2f}, "
                            f"retrieved {len(retrieved)} context chunks and generated focused response."
                        ),
                        domain=dom,
                    )
                    return dom, v
                
                resolved_domain, verdict = await asyncio.wait_for(asyncio.to_thread(do_verdict), timeout=30.0)
            except asyncio.TimeoutError:
                await send_error(websocket, stage, "TimeoutError", "Model timeout — retry", True)
                class DummyVerdict:
                    label = "RISKY"
                    reason = "Verdict timeout"
                verdict = DummyVerdict()
            except Exception as e:
                await send_error(websocket, stage, type(e).__name__, f"Unexpected error at stage {stage}", False)
                await websocket.send_json({"type": "final", "ok": False, "error": f"Unexpected error at stage {stage}", "stage_failed": stage})
                return

            # Stage: pnl
            stage = "pnl"
            pipeline_stages.append(stage)
            pnl = None
            try:
                def do_pnl():
                    rag_score = max((item.score for item in retrieved), default=0.35) if retrieved else 0.35
                    return PnLCalculator.score(
                        role=role,
                        verdict=verdict.label,
                        rag_relevance=rag_score,
                        domain=resolved_domain,
                        retrieved_count=len(retrieved),
                    )
                pnl = await asyncio.wait_for(asyncio.to_thread(do_pnl), timeout=30.0)
            except asyncio.TimeoutError:
                await send_error(websocket, stage, "TimeoutError", "Model timeout — retry", True)
                from backend.scoring.pnl_calculator import PnLScore
                pnl = PnLScore(best_case=0, realistic=0, worst_case=0, confidence=0, accuracy_drivers=[])
            except Exception as e:
                await send_error(websocket, stage, type(e).__name__, f"Unexpected error at stage {stage}", False)
                await websocket.send_json({"type": "final", "ok": False, "error": f"Unexpected error at stage {stage}", "stage_failed": stage})
                return

            # Record BAD verdicts as RLHF negative signal (non-blocking)
            rag_score_val = max((item.score for item in retrieved), default=0.35) if retrieved else 0.35
            if verdict is not None and verdict.label == "BAD":
                asyncio.ensure_future(
                    asyncio.to_thread(
                        mistake_db.record,
                        company["id"],
                        role,
                        req.mode,
                        resolved_domain,
                        req.message,
                        llm_response,
                        verdict.label,
                        verdict.reason,
                        rag_score_val,
                    )
                )

            # Final success
            try:
                namespace_used = namespaces[0] if namespaces else "default"
                await websocket.send_json({
                    "type": "final",
                    "ok": True,
                    "payload": {
                        "message_id": str(uuid.uuid4()),
                        "content": llm_response,
                        "verdict": {"verdict": verdict.label, "reason": verdict.reason} if verdict else None,
                        "pnl": {
                            "best_case": pnl.best_case,
                            "realistic": pnl.realistic,
                            "worst_case": pnl.worst_case,
                            "confidence": pnl.confidence,
                            "accuracy_drivers": pnl.accuracy_drivers,
                        } if pnl else None,
                        "pipeline_stages": pipeline_stages,
                        "namespace_used": namespace_used,
                        "rag_score": rag_score_val,
                        "role": role,
                        "mode": req.mode
                    },
                })
            except Exception as e:
                await send_error(websocket, "final", type(e).__name__, f"Unexpected error at stage final", False)
                await websocket.send_json({"type": "final", "ok": False, "error": f"Unexpected error at stage final", "stage_failed": "final"})
                return

    except WebSocketDisconnect:
        return


@router.post("/chat")
async def post_chat(req: ChatRequest) -> dict[str, Any]:
    pipeline_stages = []
    
    stage = "input"
    pipeline_stages.append(stage)
    company = _resolve_company(req.company_id)
    role = req.role or company["role"]
    namespaces = req.namespaces or company.get("kb_namespaces", [])

    stage = "rag"
    pipeline_stages.append(stage)
    route = IntentRouter.classify_intent(req.message)
    retrieved = rag.retrieve(
        company_id=company["id"],
        namespaces=namespaces,
        query=req.message,
        top_k=req.top_k,
    )
    prompt_with_rag = rag.inject_into_prompt(req.message, retrieved)

    stage = "context_inject"
    pipeline_stages.append(stage)
    runtime_context = RuntimeContext(
        company=company["name"],
        role=role,
        mode=req.mode,
        kb_namespaces=namespaces,
    )
    final_prompt = ContextInjector.enforce_and_inject(prompt_with_rag, runtime_context)
    
    stage = "llm_stream"
    pipeline_stages.append(stage)
    system_prompt = personality_engine.get_system_prompt(req.mode)

    llm_response = await brain.chat(
        [
            BrainMessage(role="system", content=system_prompt),
            BrainMessage(role="user", content=final_prompt),
        ]
    )

    rag_relevance = max((item.score for item in retrieved), default=0.35) if retrieved else 0.35
    score_proxy = min(1.0, rag_relevance)

    retrieved_namespaces = [item.namespace for item in retrieved] if retrieved else namespaces
    resolved_domain = DomainResolver.resolve(retrieved_namespaces, route.intent)

    stage = "verdict"
    pipeline_stages.append(stage)
    verdict = VerdictEngine.evaluate(
        score=score_proxy,
        reason=(
            f"Intent={route.intent} with confidence {route.confidence:.2f}, "
            f"retrieved {len(retrieved)} context chunks and generated focused response."
        ),
        domain=resolved_domain,
    )

    stage = "pnl"
    pipeline_stages.append(stage)
    pnl = PnLCalculator.score(
        role=role,
        verdict=verdict.label,
        rag_relevance=rag_relevance,
        domain=resolved_domain,
        retrieved_count=len(retrieved),
    )
    
    namespace_used = namespaces[0] if namespaces else "default"

    return {
        "message_id": str(uuid.uuid4()),
        "content": llm_response,
        "verdict": {"verdict": verdict.label, "reason": verdict.reason},
        "pnl": {
            "best_case": pnl.best_case,
            "realistic": pnl.realistic,
            "worst_case": pnl.worst_case,
            "confidence": pnl.confidence,
            "accuracy_drivers": pnl.accuracy_drivers,
        },
        "pipeline_stages": pipeline_stages,
        "namespace_used": namespace_used,
        "rag_score": rag_relevance,
        "role": role,
        "mode": req.mode
    }
