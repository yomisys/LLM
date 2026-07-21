"""
Evidence sufficiency scoring: S(q, E) = alpha*R + beta*C + gamma*A + delta*T

R (Relevance):  mean cross-encoder relevance probability of the selected evidence.
C (Coverage):   fraction of salient query terms that appear in the evidence text.
A (Agreement):  consistency across evidence chunks; penalizes same-topic chunks
                that report conflicting numeric facts (catches contradictory injection).
T (Trust/Temporal): penalizes evidence drawn from documents flagged obsolete/superseded
                in DOC_META, and rewards more recently-dated sources.
"""
import re
from datetime import date

import numpy as np

from .corpus import DOC_META, get_embed_model

STOPWORDS = set("""
a an the is are was were be been being of to in on for with and or as at by from
what which who whom this that these those it its as into over under between about
does do did has have had can could would should will shall may might must not no
according per most current currently latest recent recently compare compared than
""".split())

NUMBER_RE = re.compile(r"\$?\d[\d,]*\.?\d*\s?%?")

REFERENCE_DATE = date(2024, 1, 1)  # experiment "as-of" date


def salient_terms(text: str):
    terms = re.findall(r"[a-zA-Z0-9]+", text.lower())
    return {t for t in terms if t not in STOPWORDS and len(t) >= 3}


def extract_numbers(text: str):
    raw = NUMBER_RE.findall(text)
    cleaned = set()
    for r in raw:
        digits = re.sub(r"[^\d.]", "", r)
        if digits and digits not in {".", ""}:
            try:
                cleaned.add(round(float(digits), 2))
            except ValueError:
                pass
    return cleaned


def relevance_signal(evidence: list) -> float:
    if not evidence:
        return 0.0
    return float(np.mean([e.get("rerank_prob", 0.5) for e in evidence]))


def coverage_signal(query: str, evidence: list) -> float:
    q_terms = salient_terms(query)
    if not q_terms:
        return 1.0
    ev_text = " ".join(e["text"] for e in evidence).lower()
    covered = sum(1 for t in q_terms if t in ev_text)
    return covered / len(q_terms)


def agreement_signal(evidence: list) -> float:
    if len(evidence) <= 1:
        return 1.0
    model = get_embed_model()
    texts = [e["text"] for e in evidence]
    embs = model.encode(texts, normalize_embeddings=True)
    numbers = [extract_numbers(t) for t in texts]

    pair_scores = []
    n = len(evidence)
    for i in range(n):
        for j in range(i + 1, n):
            text_sim = float(embs[i] @ embs[j])
            same_topic = text_sim > 0.55
            has_numbers = numbers[i] and numbers[j]
            conflicting = has_numbers and len(numbers[i] & numbers[j]) == 0
            if same_topic and conflicting:
                pair_scores.append(text_sim * 0.1)  # heavy contradiction penalty
            else:
                pair_scores.append(text_sim)
    return float(np.mean(pair_scores)) if pair_scores else 1.0


def _doc_trust(doc_id: str) -> float:
    meta = DOC_META.get(doc_id)
    if meta is None:
        return 0.7
    base = 0.35 if meta["obsolete"] else 1.0
    try:
        y, m, d = (int(x) for x in meta["version_date"].split("-"))
        age_years = (REFERENCE_DATE - date(y, m, d)).days / 365.25
    except Exception:
        age_years = 5.0
    recency = max(0.0, 1.0 - min(age_years, 20.0) / 20.0)
    return float(0.7 * base + 0.3 * recency)


def trust_temporal_signal(evidence: list) -> float:
    if not evidence:
        return 0.0
    return float(np.mean([_doc_trust(e["doc_id"]) for e in evidence]))


def compute_signals(query: str, evidence: list) -> dict:
    return {
        "R": relevance_signal(evidence),
        "C": coverage_signal(query, evidence),
        "A": agreement_signal(evidence),
        "T": trust_temporal_signal(evidence),
    }


def sufficiency_score(query: str, evidence: list, weights: dict) -> dict:
    sig = compute_signals(query, evidence)
    s = (weights["alpha"] * sig["R"] + weights["beta"] * sig["C"]
         + weights["gamma"] * sig["A"] + weights["delta"] * sig["T"])
    return {"S": float(s), **sig}


DEFAULT_WEIGHTS = {"alpha": 0.25, "beta": 0.25, "gamma": 0.25, "delta": 0.25}
