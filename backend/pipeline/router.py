from __future__ import annotations

from dataclasses import dataclass


INTENT_CONVERSATION = "Conversation"
INTENT_DATA = "Data"
INTENT_SUGGESTION = "Suggestion"
VALID_INTENTS = {INTENT_CONVERSATION, INTENT_DATA, INTENT_SUGGESTION}


@dataclass(frozen=True, slots=True)
class RouteDecision:
    intent: str
    confidence: float


class IntentRouter:
    # 1. Assign weights to keywords
    keyword_weights = {
        INTENT_SUGGESTION: {
            "should i": 3.0,
            "recommend": 3.0,
            "what should": 3.0,
            "advise": 3.0,
            "suggest": 1.0,
            "advice": 1.0,
            "improve": 1.0,
            "strategy": 1.0,
            "plan": 1.0,
            "next step": 1.0,
        },
        INTENT_DATA: {
            "revenue": 2.5,
            "kpi": 2.5,
            "metric": 2.5,
            "analyze": 2.5,
            "data": 1.0,
            "report": 1.0,
            "dashboard": 1.0,
            "cost": 1.0,
            "growth": 1.0,
            "numbers": 1.0,
        },
        INTENT_CONVERSATION: {
            "hi": 1.0,
            "hello": 1.0,
            "thanks": 1.0,
            "thank you": 1.0,
            "how are you": 1.0,
            "who are you": 1.0,
            "chat": 1.0,
        }
    }

    # 2. Phrase detection (2-word sequences)
    phrase_boosts = {
        INTENT_SUGGESTION: ["next step"],
        INTENT_DATA: ["growth rate", "cost analysis"],
    }

    @classmethod
    def classify_intent(cls, user_text: str) -> RouteDecision:
        text = user_text.strip().lower()
        if not text:
            return RouteDecision(intent=INTENT_CONVERSATION, confidence=0.55)

        suggestion_score = cls._score(text, cls.keyword_weights[INTENT_SUGGESTION])
        data_score = cls._score(text, cls.keyword_weights[INTENT_DATA])
        conversation_score = cls._score(text, cls.keyword_weights[INTENT_CONVERSATION])

        # 2. Phrase detection boost (1.5x multiplier)
        if any(phrase in text for phrase in cls.phrase_boosts[INTENT_SUGGESTION]):
            suggestion_score *= 1.5
        if any(phrase in text for phrase in cls.phrase_boosts[INTENT_DATA]):
            data_score *= 1.5

        # 3. Detect question words
        if text.startswith(("what", "how", "why", "when", "where")):
            suggestion_score += 0.5

        # Legacy extra token coverage
        if any(token in text for token in ["?", "recommendation"]) and suggestion_score == 0:
            suggestion_score += 1.0
        if any(token in text for token in ["table", "csv", "dataset", "trend"]) and data_score == 0:
            data_score += 1.0

        score_map = {
            INTENT_SUGGESTION: suggestion_score,
            INTENT_DATA: data_score,
            INTENT_CONVERSATION: conversation_score,
        }

        # 4. Resolve ties: Priority Suggestion > Data > Conversation
        priority = {INTENT_SUGGESTION: 3, INTENT_DATA: 2, INTENT_CONVERSATION: 1}
        best_intent = max(score_map.keys(), key=lambda k: (score_map[k], priority[k]))
        max_score = score_map[best_intent]

        if max_score == 0:
            return RouteDecision(intent=INTENT_CONVERSATION, confidence=0.5)

        confidence = min(0.99, 0.55 + (max_score * 0.12))
        return RouteDecision(intent=best_intent, confidence=confidence)

    @staticmethod
    def _score(text: str, weights: dict[str, float]) -> float:
        return sum(weight for keyword, weight in weights.items() if keyword in text)


# --- Unit Test Cases (Expected Outcomes) ---
# 1. "should i invest in this?"
#    Suggestion: "should i" (3.0) -> 3.0. Conf: min(0.99, 0.55 + 3.0*0.12) = 0.91 -> Suggestion (0.91)
#
# 2. "recommend a plan for q4"
#    Suggestion: "recommend" (3.0), "plan" (1.0) -> 4.0. Conf: 0.55 + 4.0*0.12 = 0.99 -> Suggestion (0.99)
#
# 3. "analyze our cost metrics"
#    Data: "analyze" (2.5), "cost" (1.0), "metric" (2.5) -> 6.0. Conf: 0.99 -> Data (0.99)
#
# 4. "what is the growth rate?"
#    Data: "growth" (1.0) * 1.5 phrase boost = 1.5. 
#    Suggestion: starts with "what" (+0.5) = 0.5. 
#    Data wins (1.5 > 0.5). Conf: 0.55 + 1.5*0.12 = 0.73 -> Data (0.73)
#
# 5. "what is the next step for the dashboard"
#    Suggestion: "next step" (1.0) * 1.5 phrase boost = 1.5 + "what" (+0.5) = 2.0. 
#    Data: "dashboard" (1.0) -> 1.0. 
#    Suggestion wins (2.0 > 1.0). Conf: 0.55 + 2.0*0.12 = 0.79 -> Suggestion (0.79)
#
# 6. "hi how are you"
#    Conversation: "hi" (1.0), "how are you" (1.0) -> 2.0. Conf: 0.55 + 2.0*0.12 = 0.79 -> Conversation (0.79)
#
# 7. "cost analysis report"
#    Data: ("cost" 1.0 + "report" 1.0) * phrase "cost analysis" 1.5x -> 2.0 * 1.5 = 3.0. 
#    Conf: 0.55 + 3.0*0.12 = 0.91 -> Data (0.91)
#
# 8. "give me the data and kpi"
#    Data: "data" (1.0), "kpi" (2.5) -> 3.5. Conf: 0.55 + 3.5*0.12 = 0.97 -> Data (0.97)
#
# 9. "can you advise on this data?"
#    Suggestion: "advise" (3.0) -> 3.0. Data: "data" (1.0) -> 1.0. 
#    Suggestion wins (3.0 > 1.0). Conf: 0.55 + 3.0*0.12 = 0.91 -> Suggestion (0.91)
#
# 10. "what should we improve?"
#     Suggestion: "what should" (3.0), "improve" (1.0), starts with "what" (+0.5) -> 4.5. 
#     Conf: 0.99 -> Suggestion (0.99)
#
# Tie-breaker Example: "plan for data"
# Suggestion: "plan" (1.0), Data: "data" (1.0). Tie! Priority dictates Suggestion wins.
