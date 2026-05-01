"""Centralized runtime configuration and constants."""

from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"
KB_DIR = DATA_DIR / "kb"
DEMO_DATA_DIR = DATA_DIR / "demo"

# Services and URLs
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
API_BASE_URL = os.getenv("API_BASE_URL", f"http://{API_HOST}:{API_PORT}")
WS_PATH = os.getenv("WS_PATH", "/ws")
WS_URL = os.getenv("WS_URL", f"ws://localhost:{API_PORT}{WS_PATH}")

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_CHAT_ENDPOINT = os.getenv("OLLAMA_CHAT_ENDPOINT", "/api/chat")
OLLAMA_GENERATE_ENDPOINT = os.getenv("OLLAMA_GENERATE_ENDPOINT", "/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b-instruct-q4_K_M")
OLLAMA_TIMEOUT_SECONDS = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "120"))
OLLAMA_TIMEOUT = int(OLLAMA_TIMEOUT_SECONDS)
OLLAMA_RETRIES = int(os.getenv("OLLAMA_RETRIES", "3"))
OLLAMA_RETRY_BACKOFF_SECONDS = float(os.getenv("OLLAMA_RETRY_BACKOFF_SECONDS", "1.25"))

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_GRPC_PORT = int(os.getenv("QDRANT_GRPC_PORT", "6334"))
QDRANT_URL = os.getenv("QDRANT_URL", f"http://{QDRANT_HOST}:{QDRANT_PORT}")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "ai_clone_memory")
QDRANT_IN_MEMORY = os.getenv("QDRANT_IN_MEMORY", "true").lower() == "true"


# Tokens and headers
API_AUTH_TOKEN = os.getenv("API_AUTH_TOKEN", "dev-token")
OLLAMA_API_TOKEN = os.getenv("OLLAMA_API_TOKEN", "")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
DEFAULT_HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_AUTH_TOKEN}",
}

# Auto-detect CUDA for embeddings
try:
    import torch
    _default_device = "cuda" if torch.cuda.is_available() else "cpu"
except ImportError:
    _default_device = "cpu"

# Model and inference tuning
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "384"))
EMBEDDING_DEVICE = os.getenv("EMBEDDING_DEVICE", _default_device)
OLLAMA_NUM_CTX = int(os.getenv("OLLAMA_NUM_CTX", "4096"))
OLLAMA_TEMPERATURE = float(os.getenv("OLLAMA_TEMPERATURE", "0.7"))
OLLAMA_TOP_P = float(os.getenv("OLLAMA_TOP_P", "0.9"))
MAX_OUTPUT_TOKENS = int(os.getenv("MAX_OUTPUT_TOKENS", "1024"))
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "3"))
RAG_SCORE_THRESHOLD = float(os.getenv("RAG_SCORE_THRESHOLD", "0.5"))

# Roles and persona routing
ROLE_ADMIN = "admin"
ROLE_OPERATOR = "operator"
ROLE_ANALYST = "analyst"
ROLE_USER = "user"
SUPPORTED_ROLES = [ROLE_ADMIN, ROLE_OPERATOR, ROLE_ANALYST, ROLE_USER]

# Domain classification for verdict policy
DOMAIN_FINANCE = "finance"
DOMAIN_LEGAL = "legal"
DOMAIN_HEALTH = "health"
DOMAIN_SECURITY = "security"
DOMAIN_OPERATIONS = "operations"
DOMAIN_PRODUCT = "product"
DOMAIN_GENERAL = "general"
SUPPORTED_DOMAINS = [
    DOMAIN_FINANCE,
    DOMAIN_LEGAL,
    DOMAIN_HEALTH,
    DOMAIN_SECURITY,
    DOMAIN_OPERATIONS,
    DOMAIN_PRODUCT,
    DOMAIN_GENERAL,
]
RISK_DOMAINS = {DOMAIN_FINANCE, DOMAIN_LEGAL, DOMAIN_HEALTH, DOMAIN_SECURITY}

# Verdict constants
VERDICT_GOOD = "GOOD"
VERDICT_RISKY = "RISKY"
VERDICT_BAD = "BAD"
VALID_VERDICTS = {VERDICT_GOOD, VERDICT_RISKY, VERDICT_BAD}
GENERIC_REASON_BLOCKLIST = {
    "needs more info",
    "insufficient information",
    "cannot determine",
    "unclear",
    "not enough context",
}
