"""Load corpus chunks and provide shared access to embeddings."""
import json
import os
from pathlib import Path

os.environ.setdefault("USE_TF", "0")
os.environ.setdefault("USE_TORCH", "1")

import numpy as np
from sentence_transformers import SentenceTransformer

ROOT = Path(__file__).resolve().parent.parent.parent
CHUNKS_PATH = ROOT / "data" / "corpus" / "chunks.jsonl"
EMB_CACHE = ROOT / "data" / "corpus" / "embeddings.npy"

EMBED_MODEL_NAME = "all-MiniLM-L6-v2"

_embed_model = None


def get_embed_model():
    global _embed_model
    if _embed_model is None:
        _embed_model = SentenceTransformer(EMBED_MODEL_NAME)
    return _embed_model


def load_chunks():
    chunks = []
    with open(CHUNKS_PATH, encoding="utf-8") as f:
        for line in f:
            chunks.append(json.loads(line))
    return chunks


def load_or_build_embeddings(chunks):
    if EMB_CACHE.exists():
        emb = np.load(EMB_CACHE)
        if emb.shape[0] == len(chunks):
            return emb
    model = get_embed_model()
    texts = [c["text"] for c in chunks]
    emb = model.encode(texts, batch_size=32, show_progress_bar=True, normalize_embeddings=True)
    emb = np.asarray(emb, dtype=np.float32)
    np.save(EMB_CACHE, emb)
    return emb


# doc-level trust/recency metadata used by the sufficiency scorer's T signal
DOC_META = {
    "apple_10k_fy2023": {"version_date": "2023-11-03", "obsolete": False, "supersedes": "apple_10k_fy2022"},
    "apple_10k_fy2022": {"version_date": "2022-10-28", "obsolete": True, "supersedes": None},
    "nist_ai_rmf": {"version_date": "2023-01-26", "obsolete": False, "supersedes": None},
    "owasp_top10_2021": {"version_date": "2021-09-24", "obsolete": False, "supersedes": None},
    "rfc9110_http_semantics": {"version_date": "2022-06-01", "obsolete": False, "supersedes": "rfc2616_http11"},
    "rfc2616_http11": {"version_date": "1999-06-01", "obsolete": True, "supersedes": None},
}
