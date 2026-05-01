#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$ROOT_DIR/.venv"
MODEL_NAME="llama3.1:8b-instruct-q4_K_M"
QDRANT_CONTAINER="ai-clone-qdrant"

mkdir -p "$ROOT_DIR/data/demo" "$ROOT_DIR/data/qdrant" "$ROOT_DIR/logs"

if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip
pip install -r "$ROOT_DIR/requirements.txt"

if ! command -v ollama >/dev/null 2>&1; then
  echo "Error: ollama is not installed or not in PATH."
  exit 1
fi

if ! pgrep -x "ollama" >/dev/null 2>&1; then
  nohup ollama serve >"$ROOT_DIR/logs/ollama.log" 2>&1 &
  sleep 3
fi

ollama pull "$MODEL_NAME"

if ! command -v docker >/dev/null 2>&1; then
  echo "Error: docker is not installed or not in PATH."
  exit 1
fi

if ! docker ps --format '{{.Names}}' | rg -x "$QDRANT_CONTAINER" >/dev/null 2>&1; then
  if docker ps -a --format '{{.Names}}' | rg -x "$QDRANT_CONTAINER" >/dev/null 2>&1; then
    docker start "$QDRANT_CONTAINER"
  else
    docker run -d \
      --name "$QDRANT_CONTAINER" \
      -p 6333:6333 \
      -p 6334:6334 \
      -v "$ROOT_DIR/data/qdrant:/qdrant/storage" \
      qdrant/qdrant:latest
  fi
fi

sleep 3
python "$ROOT_DIR/scripts/seed_demo_data.py"

echo "Setup completed successfully."
