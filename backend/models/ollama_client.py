"""
Ollama LLM Client — wraps local Ollama API for llama3.1:8b-instruct-q4_K_M.
Handles streaming, retries, and structured output extraction.
"""

import json
import asyncio
import logging
from typing import AsyncGenerator, Optional

import httpx

from backend.config import (
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    OLLAMA_TIMEOUT,
    OLLAMA_NUM_CTX,
    OLLAMA_TEMPERATURE,
    OLLAMA_TOP_P,
)

logger = logging.getLogger(__name__)


class OllamaClient:
    """Async client for local Ollama inference."""

    def __init__(
        self,
        base_url: str = OLLAMA_BASE_URL,
        model: str = OLLAMA_MODEL,
        timeout: int = OLLAMA_TIMEOUT,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout, connect=10.0),
            )
        return self._client

    async def generate(
        self,
        prompt: str,
        system: str = "",
        temperature: float = OLLAMA_TEMPERATURE,
        top_p: float = OLLAMA_TOP_P,
        num_ctx: int = OLLAMA_NUM_CTX,
        max_retries: int = 2,
    ) -> str:
        """Generate a complete response from Ollama."""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": top_p,
                "num_ctx": num_ctx,
            },
        }

        last_error = None
        for attempt in range(max_retries + 1):
            try:
                client = await self._get_client()
                response = await client.post("/api/generate", json=payload)
                response.raise_for_status()
                data = response.json()
                return data.get("response", "")
            except (httpx.HTTPError, httpx.TimeoutException, json.JSONDecodeError) as e:
                last_error = e
                logger.warning(f"Ollama attempt {attempt + 1} failed: {e}")
                if attempt < max_retries:
                    await asyncio.sleep(1.0 * (attempt + 1))

        raise ConnectionError(f"Ollama failed after {max_retries + 1} attempts: {last_error}")

    async def generate_stream(
        self,
        prompt: str,
        system: str = "",
        temperature: float = OLLAMA_TEMPERATURE,
        top_p: float = OLLAMA_TOP_P,
        num_ctx: int = OLLAMA_NUM_CTX,
    ) -> AsyncGenerator[str, None]:
        """Stream tokens from Ollama."""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system,
            "stream": True,
            "options": {
                "temperature": temperature,
                "top_p": top_p,
                "num_ctx": num_ctx,
            },
        }

        client = await self._get_client()
        async with client.stream("POST", "/api/generate", json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.strip():
                    continue
                try:
                    chunk = json.loads(line)
                    token = chunk.get("response", "")
                    if token:
                        yield token
                    if chunk.get("done", False):
                        return
                except json.JSONDecodeError:
                    continue

    async def chat(
        self,
        messages: list[dict],
        temperature: float = OLLAMA_TEMPERATURE,
        top_p: float = OLLAMA_TOP_P,
        num_ctx: int = OLLAMA_NUM_CTX,
    ) -> str:
        """Chat-style completion using Ollama /api/chat endpoint."""
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": top_p,
                "num_ctx": num_ctx,
            },
        }

        client = await self._get_client()
        response = await client.post("/api/chat", json=payload)
        response.raise_for_status()
        data = response.json()
        return data.get("message", {}).get("content", "")

    async def chat_stream(
        self,
        messages: list[dict],
        temperature: float = OLLAMA_TEMPERATURE,
        top_p: float = OLLAMA_TOP_P,
        num_ctx: int = OLLAMA_NUM_CTX,
    ) -> AsyncGenerator[str, None]:
        """Stream chat tokens from Ollama."""
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature,
                "top_p": top_p,
                "num_ctx": num_ctx,
            },
        }

        client = await self._get_client()
        async with client.stream("POST", "/api/chat", json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.strip():
                    continue
                try:
                    chunk = json.loads(line)
                    token = chunk.get("message", {}).get("content", "")
                    if token:
                        yield token
                    if chunk.get("done", False):
                        return
                except json.JSONDecodeError:
                    continue

    async def health_check(self) -> dict:
        """Check Ollama server health and model availability."""
        try:
            client = await self._get_client()
            resp = await client.get("/api/tags")
            resp.raise_for_status()
            tags = resp.json()
            models = [m["name"] for m in tags.get("models", [])]
            model_loaded = any(self.model.split(":")[0] in m for m in models)
            return {
                "status": "healthy",
                "server": self.base_url,
                "model": self.model,
                "model_available": model_loaded,
                "available_models": models,
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "server": self.base_url,
                "model": self.model,
                "error": str(e),
            }

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
