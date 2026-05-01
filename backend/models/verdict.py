from __future__ import annotations

from dataclasses import dataclass

from backend import config


@dataclass(frozen=True, slots=True)
class Verdict:
    label: str
    reason: str


class VerdictEngine:
    """Strict verdict engine with domain-aware risk floor."""

    @staticmethod
    def evaluate(
        *,
        score: float,
        reason: str,
        domain: str,
    ) -> Verdict:
        cleaned_reason = VerdictEngine._validate_reason(reason)
        normalized_domain = domain.strip().lower() if domain else config.DOMAIN_GENERAL

        if score >= 0.75:
            label = config.VERDICT_GOOD
        elif score >= 0.45:
            label = config.VERDICT_RISKY
        else:
            label = config.VERDICT_BAD

        if normalized_domain in config.RISK_DOMAINS and label == config.VERDICT_GOOD:
            label = config.VERDICT_RISKY

        if label not in config.VALID_VERDICTS:
            raise ValueError("Invalid verdict label computed.")

        return Verdict(label=label, reason=cleaned_reason)

    @staticmethod
    def _validate_reason(reason: str) -> str:
        cleaned = " ".join(reason.strip().split())
        if not cleaned:
            raise ValueError("Verdict reason is required and cannot be empty.")
        if len(cleaned) < 12:
            raise ValueError("Verdict reason must be specific and non-generic.")
        if cleaned.lower() in config.GENERIC_REASON_BLOCKLIST:
            raise ValueError("Generic verdict reason is not allowed.")
        return cleaned
