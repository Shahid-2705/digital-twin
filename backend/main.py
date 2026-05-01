from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from qdrant_client import QdrantClient

from backend import config
from backend.api.chat import router as chat_router
from backend.api.companies import router as companies_router
from backend.api.mistakes import router as mistakes_router
# 🔴 AUTH DISABLED FOR NOW
# from backend.auth import router as auth_router, verify_jwt


@asynccontextmanager
async def lifespan(_: FastAPI):
    # 🔹 Qdrant health check
    qdrant = QdrantClient(
        host=config.QDRANT_HOST,
        port=config.QDRANT_PORT
    )
    try:
        qdrant.get_collections()
        print("✅ Qdrant connected")
    except Exception as e:
        print(f"❌ Qdrant connection failed: {e}")

    # 🔹 Ollama health check
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            await client.get(f"{config.OLLAMA_BASE_URL}/api/tags")
        print("✅ Ollama reachable")
    except Exception as e:
        print(f"⚠️ Ollama not reachable: {e}")

    yield


# ✅ NO GLOBAL AUTH HERE
app = FastAPI(
    title="AI Clone API",
    version="1.0.0",
    lifespan=lifespan
)


# 🔹 API ROUTES
# app.include_router(auth_router)  # 🔴 disabled for now
app.include_router(companies_router, prefix="/api")
app.include_router(chat_router)
app.include_router(mistakes_router)


# 🔹 FRONTEND STATIC SERVING
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
COMPONENTS_DIR = FRONTEND_DIR / "components"

app.mount("/components", StaticFiles(directory=str(COMPONENTS_DIR)), name="components")


@app.get("/app.js")
def app_js() -> FileResponse:
    return FileResponse(
        FRONTEND_DIR / "app.js",
        media_type="application/javascript"
    )


@app.get("/styles.css")
def styles_css() -> FileResponse:
    return FileResponse(
        FRONTEND_DIR / "styles.css",
        media_type="text/css"
    )


@app.get("/")
def index() -> FileResponse:
    return FileResponse(
        FRONTEND_DIR / "index.html",
        media_type="text/html"
    )


# 🔹 HEALTH CHECK
@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}