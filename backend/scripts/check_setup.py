import sys
import os
import urllib.request
import urllib.error
from pathlib import Path

# Fix path so we can import config
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend import config

def print_result(success, message, fix=None):
    if success:
        print(f"[\u2713] {message}")
    else:
        print(f"[\u2717] {message}")
        if fix:
            print(f"    -> FIX: {fix}")

def check_python_version():
    version = sys.version_info
    success = version.major == 3 and version.minor >= 11
    message = f"Python version is {version.major}.{version.minor}.{version.micro} (requires >= 3.11)"
    fix = "Install Python 3.11 or newer from python.org."
    print_result(success, message, fix)
    return success

def check_cuda():
    try:
        import torch
        available = torch.cuda.is_available()
        message = "CUDA is available via PyTorch" if available else "CUDA is NOT available in PyTorch"
        fix = "Install PyTorch with CUDA support: pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121"
        print_result(available, message, fix)
        return available
    except ImportError:
        print_result(False, "PyTorch is not installed", "Run 'pip install torch'")
        return False

def check_ollama():
    url = f"{config.OLLAMA_BASE_URL}/api/tags"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as response:
            success = response.status == 200
            print_result(success, f"Ollama reachable at {config.OLLAMA_BASE_URL}", "Ensure Ollama is running and accessible.")
            return success
    except Exception as e:
        print_result(False, f"Ollama NOT reachable at {config.OLLAMA_BASE_URL} ({e})", "Start Ollama or check OLLAMA_BASE_URL in .env.")
        return False

def check_qdrant():
    url = config.QDRANT_URL
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as response:
            success = response.status == 200
            print_result(success, f"Qdrant reachable at {config.QDRANT_URL}", "Ensure Qdrant is running (e.g. via docker compose up).")
            return success
    except Exception as e:
        print_result(False, f"Qdrant NOT reachable at {config.QDRANT_URL} ({e})", "Start Qdrant or check QDRANT_URL in .env.")
        return False

def check_env_file():
    env_path = PROJECT_ROOT / ".env"
    success = env_path.exists()
    print_result(success, ".env file exists", "Copy .env.example to .env and configure your values: cp .env.example .env")
    return success

def main():
    print("--- AI Clone Setup Check ---")
    results = [
        check_python_version(),
        check_cuda(),
        check_ollama(),
        check_qdrant(),
        check_env_file()
    ]
    print("----------------------------")
    if all(results):
        print("All checks passed! You are ready to go.")
    else:
        print("Some checks failed. Please review the output above and apply the fixes.")

if __name__ == "__main__":
    main()
