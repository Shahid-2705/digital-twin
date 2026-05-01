"""
FastAPI routes for the MistakeDB.

GET  /api/mistakes/pending         — list unreviewed mistakes
POST /api/mistakes/{id}/review     — mark a mistake reviewed, attach note
GET  /api/mistakes/export          — download all mistakes as RLHF JSONL
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from backend.memory.mistake_db import MistakeDB

router = APIRouter(prefix="/api/mistakes", tags=["mistakes"])

# Temporary export path (written on each request)
_EXPORT_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "rlhf_export.jsonl"


class ReviewRequest(BaseModel):
    note: str = ""


@router.get("/pending")
async def list_pending() -> list[dict]:
    """Return all unreviewed BAD-verdict responses."""
    return await asyncio.to_thread(MistakeDB.list_pending)


@router.post("/{mistake_id}/review")
async def review_mistake(mistake_id: str, body: ReviewRequest) -> dict:
    """Mark a mistake as reviewed with an optional note."""
    updated = await asyncio.to_thread(MistakeDB.mark_reviewed, mistake_id, body.note)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Mistake '{mistake_id}' not found.")
    return {"ok": True, "id": mistake_id, "note": body.note}


@router.get("/export")
async def export_rlhf() -> FileResponse:
    """Export all mistakes as a RLHF-ready JSONL file (triggers download)."""
    count = await asyncio.to_thread(MistakeDB.export_rlhf_jsonl, _EXPORT_PATH)
    if count == 0:
        raise HTTPException(status_code=404, detail="No mistakes to export.")
    return FileResponse(
        path=str(_EXPORT_PATH),
        media_type="application/x-ndjson",
        filename="rlhf_mistakes.jsonl",
        headers={"X-Record-Count": str(count)},
    )
