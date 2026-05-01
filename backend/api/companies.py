from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.companies.company_manager import CompanyManager


router = APIRouter(prefix="/companies", tags=["companies"])
manager = CompanyManager()


class CompanyCreateRequest(BaseModel):
    name: str = Field(min_length=1)
    role: str = Field(min_length=1)
    kb_namespaces: list[str] = Field(default_factory=list)


class CompanyUpdateRequest(BaseModel):
    name: str | None = None
    role: str | None = None
    kb_namespaces: list[str] | None = None


@router.get("")
def list_companies() -> dict[str, Any]:
    return {
        "companies": manager.list_companies(),
        "active_company_id": manager.get_active()["id"] if manager.get_active() else None,
    }


@router.get("/{company_id}")
def get_company(company_id: str) -> dict[str, Any]:
    company = manager.get_company(company_id)
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found.")
    return {"company": company}


@router.post("")
async def create_company(payload: CompanyCreateRequest) -> dict[str, Any]:
    company = await manager.add_company(
        name=payload.name,
        role=payload.role,
        kb_namespaces=payload.kb_namespaces or None,
    )
    return {"company": company}


@router.put("/{company_id}")
async def update_company(company_id: str, payload: CompanyUpdateRequest) -> dict[str, Any]:
    try:
        company = await manager.update_company(
            company_id,
            name=payload.name,
            role=payload.role,
            kb_namespaces=payload.kb_namespaces,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"company": company}


@router.delete("/{company_id}")
async def delete_company(company_id: str) -> dict[str, Any]:
    if not await manager.delete_company(company_id):
        raise HTTPException(status_code=404, detail="Company not found.")
    return {"deleted": True}


@router.get("/active/current")
def get_active_company() -> dict[str, Any]:
    active = manager.get_active()
    if active is None:
        raise HTTPException(status_code=404, detail="No active company set.")
    return {"company": active}


@router.post("/active/{company_id}")
async def set_active_company(company_id: str) -> dict[str, Any]:
    try:
        active = await manager.set_active(company_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"company": active}
