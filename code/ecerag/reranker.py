"""Cross-encoder reranking of hybrid retrieval candidates."""
import os

os.environ.setdefault("USE_TF", "0")
os.environ.setdefault("USE_TORCH", "1")

from sentence_transformers import CrossEncoder

CROSS_ENCODER_NAME = os.environ.get("ECERAG_RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")

_cross_encoder = None


def get_cross_encoder():
    global _cross_encoder
    if _cross_encoder is None:
        _cross_encoder = CrossEncoder(CROSS_ENCODER_NAME)
    return _cross_encoder


def sigmoid(x):
    import math
    return 1.0 / (1.0 + math.exp(-x))


def rerank(query: str, candidates: list, top_n: int = 5):
    if not candidates:
        return []
    ce = get_cross_encoder()
    pairs = [(query, c["text"]) for c in candidates]
    raw_scores = ce.predict(pairs)
    scored = []
    for c, s in zip(candidates, raw_scores):
        scored.append({**c, "rerank_score": float(s), "rerank_prob": sigmoid(float(s))})
    scored.sort(key=lambda x: -x["rerank_score"])
    return scored[:top_n]
