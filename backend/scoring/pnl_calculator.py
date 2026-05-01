from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PnLScore:
    best_case: float
    realistic: float
    worst_case: float
    confidence: float
    accuracy_drivers: list[str]


class PnLCalculator:
    ROLE_WEIGHTS: dict[str, float] = {
        "investor": 1.18,
        "ceo": 1.12,
        "founder": 1.08,
        "board member": 1.10,
        "advisor": 1.03,
        "operator": 1.00,
        "analyst": 1.02,
        "user": 0.95,
    }

    DOMAIN_WEIGHTS: dict[str, float] = {
        "finance": 1.20,
        "operations": 1.05,
        "product": 1.08,
        "legal": 1.15,
        "general": 0.90,
    }

    @classmethod
    def score(
        cls,
        *,
        role: str,
        verdict: str,
        rag_relevance: float,
        domain: str,
        retrieved_count: int,
    ) -> PnLScore:
        normalized_role = role.strip().lower()
        role_weight = cls.ROLE_WEIGHTS.get(normalized_role, 1.0)

        normalized_domain = domain.strip().lower()
        domain_weight = cls.DOMAIN_WEIGHTS.get(normalized_domain, 1.0)

        verdict_factor = {
            "GOOD": 1.0,
            "RISKY": 0.55,
            "BAD": 0.2,
        }.get(verdict, 0.45)

        base = max(0.0, min(1.0, rag_relevance))
        realistic = round(100 * base * role_weight * domain_weight * verdict_factor, 2)
        
        if retrieved_count == 0:
            realistic = round(realistic * 0.70, 2)

        best_case = round(realistic * 1.35, 2)
        worst_case = round(realistic * 0.52, 2)

        confidence = round(
            min(
                0.99,
                max(
                    0.2,
                    0.45
                    + (rag_relevance * 0.45)
                    + ((role_weight - 1.0) * 0.15),
                ),
            ),
            3,
        )

        drivers = [
            f"Role weight applied: {normalized_role or 'default'} x{role_weight:.2f}",
            f"Domain weight applied: {normalized_domain or 'default'} x{domain_weight:.2f}",
            f"Verdict factor: {verdict_factor:.2f} ({verdict})",
            f"RAG relevance contribution: {rag_relevance:.3f}",
            f"Retrieval count: {retrieved_count} (penalty applied: {'yes' if retrieved_count == 0 else 'no'})",
        ]

        return PnLScore(
            best_case=best_case,
            realistic=realistic,
            worst_case=worst_case,
            confidence=confidence,
            accuracy_drivers=drivers,
        )
