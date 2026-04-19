from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import torch
from transformers import AutoModel, AutoTokenizer


def mean_pool(last_hidden_state: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
    mask = attention_mask.unsqueeze(-1).expand(last_hidden_state.size()).float()
    summed = torch.sum(last_hidden_state * mask, dim=1)
    counts = torch.clamp(mask.sum(dim=1), min=1e-9)
    return summed / counts


class TransformerEmbedder:
    def __init__(
        self,
        model_name: str,
        device: str | None = None,
        max_length: int = 512,
    ) -> None:
        self.model_name = model_name
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.max_length = max_length
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.model.to(self.device)
        self.model.eval()

    def _prepare_texts(self, texts: list[str]) -> list[str]:
        if self.model_name.startswith("intfloat/e5"):
            return [f"query: {text}" for text in texts]
        return texts

    @torch.inference_mode()
    def encode(self, texts: list[str], batch_size: int = 32) -> np.ndarray:
        prepared = self._prepare_texts([str(text) for text in texts])
        batches = []
        for start in range(0, len(prepared), batch_size):
            chunk = prepared[start : start + batch_size]
            encoded = self.tokenizer(
                chunk,
                padding=True,
                truncation=True,
                max_length=self.max_length,
                return_tensors="pt",
            )
            encoded = {key: value.to(self.device) for key, value in encoded.items()}
            outputs = self.model(**encoded)
            pooled = mean_pool(outputs.last_hidden_state, encoded["attention_mask"])
            pooled = torch.nn.functional.normalize(pooled, p=2, dim=1)
            batches.append(pooled.cpu().numpy())
        return np.concatenate(batches, axis=0)


def cache_key(model_name: str, context_mode: str, row_count: int) -> str:
    digest = hashlib.sha1(f"{model_name}|{context_mode}|{row_count}".encode("utf-8")).hexdigest()
    return digest[:12]


def save_embeddings(path: str | Path, embeddings: np.ndarray) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    np.save(target, embeddings)
