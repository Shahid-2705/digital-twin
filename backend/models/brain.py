from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import AsyncGenerator

import httpx

from backend import config


@dataclass(slots=True)
class BrainMessage:
    role: str
    content: str


class BrainClient:
    """Async Ollama brain with retry and streaming support."""

    def __init__(
        self,
        base_url: str = config.OLLAMA_BASE_URL,
        model: str = config.OLLAMA_MODEL,
        timeout_seconds: float = config.OLLAMA_TIMEOUT_SECONDS,
        retries: int = config.OLLAMA_RETRIES,
        retry_backoff_seconds: float = config.OLLAMA_RETRY_BACKOFF_SECONDS,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.retries = retries
        self.retry_backoff_seconds = retry_backoff_seconds
        self.chat_url = f"{self.base_url}{config.OLLAMA_CHAT_ENDPOINT}"

    async def chat(
        self,
        messages: list[BrainMessage] | list[dict[str, str]],
        stream: bool = False,
    ) -> str | AsyncGenerator[str, None]:
        if stream:
            return self.stream_chat(messages)
        return await self._request_chat(messages)

    async def _request_chat(self, messages: list[BrainMessage] | list[dict[str, str]]) -> str:
        payload = {"model": self.model, "messages": self._normalize(messages), "stream": False}
        attempt = 0
        last_error: Exception | None = None

        while attempt <= self.retries:
            try:
                async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                    response = await client.post(self.chat_url, json=payload)
                    response.raise_for_status()
                    data = response.json()
                    return (data.get("message") or {}).get("content", "").strip()
            except (httpx.HTTPError, ValueError) as exc:
                last_error = exc
                attempt += 1
                if attempt > self.retries:
                    break
                await asyncio.sleep(self.retry_backoff_seconds * attempt)

        raise RuntimeError(f"Ollama chat failed after {self.retries + 1} attempts: {last_error}") from last_error

    async def stream_chat(
        self,
        messages: list[BrainMessage] | list[dict[str, str]],
    ) -> AsyncGenerator[str, None]:
        payload = {"model": self.model, "messages": self._normalize(messages), "stream": True}
        attempt = 0
        last_error: Exception | None = None

        while attempt <= self.retries:
            try:
                async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                    async with client.stream("POST", self.chat_url, json=payload) as response:
                        response.raise_for_status()
                        async for line in response.aiter_lines():
                            if not line:
                                continue
                            if line.startswith("{"):
                                chunk = httpx.Response(200, content=line.encode("utf-8")).json()
                                content = (chunk.get("message") or {}).get("content")
                                if content:
                                    yield content
                                if chunk.get("done", False):
                                    return
                        return
            except (httpx.HTTPError, ValueError) as exc:
                last_error = exc
                attempt += 1
                if attempt > self.retries:
                    break
                await asyncio.sleep(self.retry_backoff_seconds * attempt)

        raise RuntimeError(f"Ollama stream failed after {self.retries + 1} attempts: {last_error}") from last_error

    async def websocket_chunks(
        self,
        messages: list[BrainMessage] | list[dict[str, str]],
    ) -> AsyncGenerator[dict[str, str | bool], None]:
        """WebSocket-ready stream packets."""
        async for token in self.stream_chat(messages):
            yield {"type": "token", "content": token, "done": False}
        yield {"type": "done", "content": "", "done": True}

    @staticmethod
    def _normalize(messages: list[BrainMessage] | list[dict[str, str]]) -> list[dict[str, str]]:
        normalized: list[dict[str, str]] = []
        for item in messages:
            if isinstance(item, BrainMessage):
                normalized.append({"role": item.role, "content": item.content})
            else:
                normalized.append(
                    {
                        "role": str(item.get("role", "user")),
                        "content": str(item.get("content", "")),
                    }
                )
        return normalized
