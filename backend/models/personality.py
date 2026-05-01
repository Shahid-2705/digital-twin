from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PersonalityProfile:
    system_prompt: str
    pnl_eligible: bool
    accuracy_bonus: float
    font_style: str


PERSONALITY_MODES: dict[str, PersonalityProfile] = {
    "ceo_brain": PersonalityProfile(
        system_prompt=(
            "You are CEO Brain: decisive, strategic, and P&L-aware. "
            "Prioritize long-term value, risk-adjusted ROI, and execution clarity."
        ),
        pnl_eligible=True,
        accuracy_bonus=0.20,
        font_style="Inter-SemiBold",
    ),
    "advisor_mode": PersonalityProfile(
        system_prompt=(
            "You are Advisor Mode: analytical and neutral. "
            "Provide option sets, assumptions, trade-offs, and practical next actions."
        ),
        pnl_eligible=True,
        accuracy_bonus=0.15,
        font_style="IBM Plex Sans",
    ),
    "casual_self": PersonalityProfile(
        system_prompt=(
            "You are Casual Self: concise, approachable, and plain-language first. "
            "Keep answers practical while preserving factual accuracy."
        ),
        pnl_eligible=False,
        accuracy_bonus=0.05,
        font_style="Nunito",
    ),
    "reflective_self": PersonalityProfile(
        system_prompt=(
            "You are Reflective Self: thoughtful, context-sensitive, and introspective. "
            "Surface assumptions, uncertainty, and learning-oriented guidance."
        ),
        pnl_eligible=False,
        accuracy_bonus=0.10,
        font_style="Merriweather",
    ),
}


def get_personality(mode: str) -> PersonalityProfile:
    key = mode.strip().lower().replace(" ", "_")
    if key not in PERSONALITY_MODES:
        raise ValueError(
            "Unsupported personality mode. Expected one of: "
            "ceo_brain, advisor_mode, casual_self, reflective_self."
        )
    return PERSONALITY_MODES[key]
