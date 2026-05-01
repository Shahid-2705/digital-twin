#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$ROOT_DIR/.venv"
MODEL_NAME="llama3.1:8b-instruct-q4_K_M"

if [ ! -d "$VENV_DIR" ]; then
  echo "Error: virtual environment not found. Run scripts/setup.sh first."
  exit 1
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

if ! command -v ollama >/dev/null 2>&1; then
  echo "Error: ollama is not installed or not in PATH."
  exit 1
fi

if ! pgrep -x "ollama" >/dev/null 2>&1; then
  nohup ollama serve >"$ROOT_DIR/logs/ollama.log" 2>&1 &
  sleep 3
fi

if ! ollama list | rg -F "$MODEL_NAME" >/dev/null 2>&1; then
  ollama pull "$MODEL_NAME"
fi

exec uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
