from backend.config import (
    DOMAIN_FINANCE,
    DOMAIN_LEGAL,
    DOMAIN_HEALTH,
    DOMAIN_SECURITY,
    DOMAIN_OPERATIONS,
    DOMAIN_PRODUCT,
    DOMAIN_GENERAL,
)

class DomainResolver:
    # Domain risk hierarchy (lower index = higher risk)
    RISK_HIERARCHY = [
        DOMAIN_FINANCE,
        DOMAIN_LEGAL,
        DOMAIN_HEALTH,
        DOMAIN_SECURITY,
        DOMAIN_OPERATIONS,
        DOMAIN_PRODUCT,
        DOMAIN_GENERAL,
    ]

    @classmethod
    def resolve(cls, namespaces: list[str], intent: str) -> str:
        candidates = set()
        
        # 1. Map RAG namespaces to domains
        for ns in namespaces:
            ns_lower = ns.lower()
            if "financials" in ns_lower:
                candidates.add(DOMAIN_FINANCE)
            elif "strategy" in ns_lower:
                candidates.add(DOMAIN_OPERATIONS)
            elif "knowledge" in ns_lower or "profile" in ns_lower:
                candidates.add(DOMAIN_GENERAL)
            
            # Custom namespaces containing keywords
            if "legal" in ns_lower:
                candidates.add(DOMAIN_LEGAL)
            if "risk" in ns_lower or "security" in ns_lower:
                candidates.add(DOMAIN_SECURITY)
            if "health" in ns_lower:
                candidates.add(DOMAIN_HEALTH)
            if "product" in ns_lower:
                candidates.add(DOMAIN_PRODUCT)

        # 2. Map IntentRouter intents to a domain hint
        intent_lower = intent.lower()
        if intent_lower == "data":
            if any("financials" in ns.lower() for ns in namespaces):
                candidates.add(DOMAIN_FINANCE)
            else:
                candidates.add(DOMAIN_OPERATIONS)
        elif intent_lower == "suggestion":
            top_ns = namespaces[0].lower() if namespaces else ""
            if "product" in top_ns:
                candidates.add(DOMAIN_PRODUCT)
            elif "strategy" in top_ns:
                candidates.add(DOMAIN_OPERATIONS)
            else:
                candidates.add(DOMAIN_OPERATIONS)

        if not candidates:
            candidates.add(DOMAIN_GENERAL)

        # 3. Return the highest-risk domain found
        for domain in cls.RISK_HIERARCHY:
            if domain in candidates:
                return domain
                
        return DOMAIN_GENERAL
