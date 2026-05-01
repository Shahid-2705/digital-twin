import logging
import json
import urllib.request
from typing import Union

import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    import torch
    HAS_SENTENCE_TRANSFORMERS = True
except Exception:
    HAS_SENTENCE_TRANSFORMERS = False

from backend.config import EMBEDDING_MODEL, EMBEDDING_DEVICE, EMBEDDING_DIM, OLLAMA_BASE_URL

logger = logging.getLogger(__name__)


class EmbeddingEngine:
    def __init__(self, model_name=EMBEDDING_MODEL, device=EMBEDDING_DEVICE):
        self.model_name = model_name
        self._requested_device = device
        self._model = None
        self._use_ollama = True

        if HAS_SENTENCE_TRANSFORMERS:
            try:
                self._load_model()
                self._use_ollama = False
            except Exception:
                self._use_ollama = True

    @property
    def dimension(self):
        return EMBEDDING_DIM

    def _resolve_device(self):
        if self._requested_device:
            return self._requested_device
        try:
            return "cuda" if torch.cuda.is_available() else "cpu"
        except:
            return "cpu"

    def _load_model(self):
        device = self._resolve_device()
        self._model = SentenceTransformer(self.model_name, device=device)

    def _embed_ollama(self, texts):
        embeddings = []

        for text in texts:
            payload = json.dumps({
                "model": "all-minilm",
                "input": text
            }).encode("utf-8")

            for ep in ["/api/embeddings", "/api/embed"]:
                try:
                    req = urllib.request.Request(
                        f"{OLLAMA_BASE_URL.rstrip('/')}{ep}",
                        data=payload,
                        headers={"Content-Type": "application/json"},
                    )
                    with urllib.request.urlopen(req) as response:
                        res = json.loads(response.read().decode("utf-8"))

                        if "embedding" in res:
                            embeddings.append(res["embedding"])
                        elif "data" in res:
                            embeddings.append(res["data"][0]["embedding"])
                        else:
                            raise Exception()

                        break
                except:
                    continue
            else:
                embeddings.append([0.0] * EMBEDDING_DIM)

        return np.array(embeddings)

    def embed(self, text):
        if isinstance(text, str):
            text = [text]

        if not self._use_ollama:
            try:
                embeddings = self._model.encode(text)
            except:
                self._use_ollama = True
                embeddings = self._embed_ollama(text)
        else:
            embeddings = self._embed_ollama(text)

        return embeddings[0] if len(embeddings) == 1 else embeddings