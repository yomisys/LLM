"""Hybrid retrieval: BM25 (lexical) + dense embeddings, min-max normalized and combined."""
import re

import numpy as np
from rank_bm25 import BM25Okapi

from .corpus import get_embed_model

TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str):
    return TOKEN_RE.findall(text.lower())


class HybridRetriever:
    def __init__(self, chunks, embeddings, dense_weight: float = 0.5):
        self.chunks = chunks
        self.embeddings = embeddings  # normalized, shape (N, D)
        self.dense_weight = dense_weight
        self.bm25 = BM25Okapi([tokenize(c["text"]) for c in chunks])

    @staticmethod
    def _minmax(scores: np.ndarray) -> np.ndarray:
        lo, hi = scores.min(), scores.max()
        if hi - lo < 1e-9:
            return np.zeros_like(scores)
        return (scores - lo) / (hi - lo)

    def retrieve(self, query: str, top_k: int = 20, exclude_chunk_ids=None):
        exclude = set(exclude_chunk_ids or [])
        bm25_scores = np.asarray(self.bm25.get_scores(tokenize(query)), dtype=np.float32)

        model = get_embed_model()
        q_emb = model.encode([query], normalize_embeddings=True)[0]
        dense_scores = self.embeddings @ q_emb  # cosine sim (already normalized)

        bm25_n = self._minmax(bm25_scores)
        dense_n = self._minmax(dense_scores)
        hybrid = (1 - self.dense_weight) * bm25_n + self.dense_weight * dense_n

        order = np.argsort(-hybrid)
        results = []
        for idx in order:
            chunk = self.chunks[idx]
            if chunk["chunk_id"] in exclude:
                continue
            results.append({
                **chunk,
                "bm25_score": float(bm25_scores[idx]),
                "dense_score": float(dense_scores[idx]),
                "hybrid_score": float(hybrid[idx]),
            })
            if len(results) >= top_k:
                break
        return results
