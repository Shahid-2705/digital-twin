from __future__ import annotations

import asyncio
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

from backend import config
from backend.memory.qdrant_client import CompanyQdrantMemory

_company_lock = asyncio.Lock()

@dataclass(slots=True)
class Company:
    id: str
    name: str
    role: str
    kb_namespaces: list[str]


class CompanyManager:
    def __init__(
        self,
        storage_path: Path | None = None,
        memory: CompanyQdrantMemory | None = None,
    ) -> None:
        self.storage_path = storage_path or (config.DATA_DIR / "companies.json")
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.memory = memory or CompanyQdrantMemory()
        self._state = self._load()
        if not self._state["companies"]:
            self._seed_defaults()

    def _load(self) -> dict[str, Any]:
        if not self.storage_path.exists():
            return {"active_company_id": None, "companies": []}
        with self.storage_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if "active_company_id" not in data:
            data["active_company_id"] = None
        if "companies" not in data:
            data["companies"] = []
        return data

    def _save(self) -> None:
        tmp_path = self.storage_path.with_suffix(".json.tmp")
        with tmp_path.open("w", encoding="utf-8") as f:
            json.dump(self._state, f, indent=2)
        tmp_path.replace(self.storage_path)

    def _seed_defaults(self) -> None:
        defaults = [
            ("Alpha Ventures", "Investor"),
            ("BetaCore", "CEO"),
            ("Gamma Retail", "Founder"),
            ("Delta Infra", "Board Member"),
        ]
        for name, role in defaults:
            namespaces = ["profile", "knowledge", "strategy", "financials"]
            company = Company(
                id=str(uuid4()),
                name=name.strip(),
                role=role.strip(),
                kb_namespaces=namespaces,
            )
            self.memory.create_company_namespaces(company.id, company.kb_namespaces)
            self._state["companies"].append(asdict(company))
            if self._state["active_company_id"] is None:
                self._state["active_company_id"] = company.id
        self._save()

    def list_companies(self) -> list[dict[str, Any]]:
        return list(self._state["companies"])

    def get_company(self, company_id: str) -> dict[str, Any] | None:
        for company in self._state["companies"]:
            if company["id"] == company_id:
                return company
        return None

    async def add_company(
        self,
        *,
        name: str,
        role: str,
        kb_namespaces: list[str] | None = None,
    ) -> dict[str, Any]:
        namespaces = kb_namespaces or ["profile", "knowledge", "strategy", "financials"]
        company = Company(
            id=str(uuid4()),
            name=name.strip(),
            role=role.strip(),
            kb_namespaces=namespaces,
        )
        self.memory.create_company_namespaces(company.id, company.kb_namespaces)
        payload = asdict(company)
        
        async with _company_lock:
            self._state["companies"].append(payload)
            if self._state["active_company_id"] is None:
                self._state["active_company_id"] = company.id
            self._save()
            
        return payload

    async def update_company(
        self,
        company_id: str,
        *,
        name: str | None = None,
        role: str | None = None,
        kb_namespaces: list[str] | None = None,
    ) -> dict[str, Any]:
        async with _company_lock:
            company = self.get_company(company_id)
            if company is None:
                raise ValueError("Company not found.")
            if name is not None:
                company["name"] = name.strip()
            if role is not None:
                company["role"] = role.strip()
            if kb_namespaces is not None:
                company["kb_namespaces"] = kb_namespaces
                self.memory.create_company_namespaces(company_id, kb_namespaces)
            self._save()
            return company

    async def delete_company(self, company_id: str) -> bool:
        async with _company_lock:
            before = len(self._state["companies"])
            self._state["companies"] = [c for c in self._state["companies"] if c["id"] != company_id]
            after = len(self._state["companies"])
            if before == after:
                return False
            if self._state["active_company_id"] == company_id:
                self._state["active_company_id"] = self._state["companies"][0]["id"] if self._state["companies"] else None
            self._save()
            return True

    async def set_active(self, company_id: str) -> dict[str, Any]:
        async with _company_lock:
            company = self.get_company(company_id)
            if company is None:
                raise ValueError("Company not found.")
            self._state["active_company_id"] = company_id
            self._save()
            return company

    def get_active(self) -> dict[str, Any] | None:
        active_id = self._state["active_company_id"]
        if not active_id:
            return None
        return self.get_company(active_id)
