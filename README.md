# AI Clone

Dark terminal-style AI workspace with company-aware RAG, live WebSocket streaming, verdicts, and P&L scoring.

## Run

```bash
bash scripts/setup.sh
bash scripts/start.sh
```

Then open [http://localhost:8000](http://localhost:8000).

## Setup Steps

1. `scripts/setup.sh` creates `.venv`.
2. Installs Python dependencies from `requirements.txt`.
3. Ensures Ollama is running and pulls `llama3.1:8b-instruct-q4_K_M`.
4. Starts Qdrant in Docker on ports `6333/6334`.
5. Seeds companies, KB namespaces, KB entries, and mistakes DB.
6. `scripts/start.sh` activates venv, ensures Ollama is up, and starts FastAPI.

## RTX 5060 + 8GB VRAM Note

- This stack keeps embeddings on CPU (`all-MiniLM-L6-v2`) to reserve VRAM for generation.
- `llama3.1:8b-instruct-q4_K_M` is quantized for lower VRAM pressure and stable local inference.
- On an RTX 5060 8GB class GPU, this gives a practical balance of quality, latency, and thermals for daily iterative chat/RAG usage.

## Why 8B Model

- Better instruction-following and coherence than tiny models.
- Still lightweight enough to run locally with quantization.
- Strong enough for business context synthesis, verdict generation, and role-aware response shaping without remote APIs.

## Project Highlights

- WebSocket endpoint: `/ws/chat`
- Company CRUD endpoint: `/api/companies`
- Frontend: pure HTML/CSS/JS (3-panel terminal UI)
- Pipeline stages: Input -> RAG -> Context Inject -> LLM Stream -> Verdict -> P&L
"# digital-twin" 
