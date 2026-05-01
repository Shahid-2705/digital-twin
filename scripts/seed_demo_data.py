from __future__ import annotations

import json
from pathlib import Path

from backend import config
from backend.companies.company_manager import CompanyManager
from backend.memory.qdrant_client import CompanyQdrantMemory


SEED_COMPANIES = [
    ("Alpha Ventures", "Investor"),
    ("BetaCore", "CEO"),
    ("Gamma Retail", "Founder"),
    ("Delta Infra", "Board Member"),
]

KB_ENTRIES = {
    "profile": [
        "Company profile includes leadership, mission, and risk posture.",
        "Preferred decision style is evidence-backed and execution-aware.",
    ],
    "knowledge": [
        "Customer acquisition cost is rising in Q2 across all channels.",
        "Retail conversion improved after simplifying checkout flow.",
    ],
    "strategy": [
        "Priority strategy is margin expansion with selective market growth.",
        "Board requires risk register updates for major initiatives.",
    ],
    "financials": [
        "Baseline gross margin target for FY is 38 percent.",
        "Capex approvals above threshold require board sign-off.",
    ],
}

MISTAKES_DB = [
    {"id": "M-001", "mistake": "Over-hiring ahead of demand confirmation", "impact": "cash burn"},
    {"id": "M-002", "mistake": "Ignoring vendor concentration risk", "impact": "operational outage"},
    {"id": "M-003", "mistake": "Launching without pricing experiments", "impact": "margin compression"},
]


def ensure_company(manager: CompanyManager, name: str, role: str) -> dict:
    companies = manager.list_companies()
    for company in companies:
        if company["name"].strip().lower() == name.strip().lower():
            return company
    return manager.add_company(name=name, role=role)


def seed_kb(memory: CompanyQdrantMemory, company: dict) -> None:
    namespaces = company.get("kb_namespaces", ["profile", "knowledge", "strategy", "financials"])
    memory.create_company_namespaces(company["id"], namespaces)
    for namespace in namespaces:
        entries = KB_ENTRIES.get(namespace, [])
        for text in entries:
            memory.upsert_document(
                company_id=company["id"],
                namespace=namespace,
                text=text,
                metadata={"seeded": True, "company_name": company["name"]},
            )


def seed_mistakes_db() -> None:
    path = Path(config.DATA_DIR) / "demo" / "mistakes_db.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(MISTAKES_DB, file, indent=2)


def main() -> None:
    memory = CompanyQdrantMemory()
    manager = CompanyManager(memory=memory)
    created = []
    for name, role in SEED_COMPANIES:
        company = ensure_company(manager, name, role)
        seed_kb(memory, company)
        created.append(company["name"])
    seed_mistakes_db()
    if manager.get_active() is None and manager.list_companies():
        manager.set_active(manager.list_companies()[0]["id"])
    print("Seed complete:", ", ".join(created))


if __name__ == "__main__":
    main()
