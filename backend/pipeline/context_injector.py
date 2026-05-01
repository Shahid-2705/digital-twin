from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RuntimeContext:
    company: str
    role: str
    mode: str
    kb_namespaces: list[str]


class ContextInjector:
    """Injects mandatory context into every prompt before LLM execution."""

    @staticmethod
    def build_prefix(context: RuntimeContext) -> str:
        namespaces = ", ".join(context.kb_namespaces) if context.kb_namespaces else "none"
        return (
            f"[CONTEXT]\n"
            f"Company: {context.company}\n"
            f"Role: {context.role}\n"
            f"Mode: {context.mode}\n"
            f"KB namespaces: {namespaces}\n"
            f"[/CONTEXT]\n\n"
        )

    @classmethod
    def inject(cls, prompt: str, context: RuntimeContext) -> str:
        if not context.company.strip() or not context.role.strip() or not context.mode.strip():
            raise RuntimeError("Context injection failed: company, role, and mode are required.")
        prefix = cls.build_prefix(context)
        return f"{prefix}{prompt}"

    @classmethod
    def enforce_and_inject(cls, prompt: str, context: RuntimeContext) -> str:
        injected = cls.inject(prompt, context)
        if not injected.startswith("[CONTEXT]"):
            raise RuntimeError("Context injection missing. System fails by policy.")
        return injected
