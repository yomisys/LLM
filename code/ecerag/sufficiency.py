"""
Evidence sufficiency scoring: S(q, E) = alpha*R + beta*C + gamma*A + delta*T

R (Relevance):  mean cross-encoder relevance probability of the selected evidence.
C (Coverage):   fraction of salient query terms that appear in the evidence text.
A (Agreement):  consistency across evidence chunks; penalizes same-topic chunks
                that report conflicting numeric facts (catches contradictory injection).
T (Trust/Temporal): penalizes evidence drawn from documents flagged obsolete/superseded
                in DOC_META, and rewards more recently-dated sources.

Extensions (used by run_full.py / analyze.py):
G (Grounding):  NLI entailment probability of the drafted answer given the evidence.
                R/C/A/T score the evidence only; G scores the generator's *use* of it,
                which is the failure mode the pilot found dominant (paper Sec. VII-B).
X (Conflict):   1.0 if two passages from the same document disagree on a figure
                while otherwise near-identical -- a document cannot contradict itself,
                so this is used as a hard veto on answering rather than a soft weight.

Weights are either the paper's linear form {"alpha", "beta", "gamma", "delta"} or a
fitted logistic model {"mode": "logistic", "features": [...], "coef": [...], "intercept": b}.
"""
import math
import os
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

NEAR_DUPLICATE_SIM = 0.9
NLI_MODEL_NAME = os.environ.get("ECERAG_NLI_MODEL", "cross-encoder/nli-deberta-v3-base")
CITATION_RE = re.compile(r"\[[^\]]*\]")


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


def _pairwise(evidence: list):
    """Yield (text_sim, numbers_i, numbers_j, same_doc) for every evidence pair."""
    model = get_embed_model()
    texts = [e["text"] for e in evidence]
    embs = model.encode(texts, normalize_embeddings=True)
    numbers = [extract_numbers(t) for t in texts]
    n = len(evidence)
    for i in range(n):
        for j in range(i + 1, n):
            yield float(embs[i] @ embs[j]), numbers[i], numbers[j], evidence[i]["doc_id"] == evidence[j]["doc_id"]


def _is_conflict(text_sim, nums_i, nums_j, same_doc) -> bool:
    if not (nums_i and nums_j):
        return False
    # Topic-level disagreement: same-topic passages with no figures in common.
    if text_sim > 0.55 and not (nums_i & nums_j):
        return True
    # Near-duplicate disagreement: the same passage restated with a different figure.
    # The original check above can never see this case (the two copies share every
    # other number), which is why contradictory injection left S unchanged in the pilot.
    return same_doc and text_sim > NEAR_DUPLICATE_SIM and nums_i != nums_j


def agreement_signal(evidence: list) -> float:
    if len(evidence) <= 1:
        return 1.0
    pair_scores = []
    for text_sim, ni, nj, same_doc in _pairwise(evidence):
        if _is_conflict(text_sim, ni, nj, same_doc):
            pair_scores.append(text_sim * 0.1)  # heavy contradiction penalty
        else:
            pair_scores.append(text_sim)
    return float(np.mean(pair_scores)) if pair_scores else 1.0


def conflict_pairs(evidence: list):
    """Index pairs (i, j) of same-document near-duplicate passages that disagree on a figure."""
    pairs = []
    pair_idx = [(i, j) for i in range(len(evidence)) for j in range(i + 1, len(evidence))]
    for (i, j), (text_sim, ni, nj, same_doc) in zip(pair_idx, _pairwise(evidence)):
        if same_doc and text_sim > NEAR_DUPLICATE_SIM and ni and nj and ni != nj:
            pairs.append((i, j))
    return pairs


def conflict_flag(evidence: list) -> float:
    """1.0 if two same-document passages are near-duplicates that disagree on a figure."""
    return 1.0 if conflict_pairs(evidence) else 0.0


def quarantine_conflicts(evidence: list) -> list:
    """Drop BOTH passages of every conflicting pair. Neither copy can be trusted over the
    other (same source, same rank), so the answer must come from the remaining evidence."""
    bad = {k for pair in conflict_pairs(evidence) for k in pair}
    return [e for k, e in enumerate(evidence) if k not in bad]


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


_nli = None


def _get_nli():
    global _nli
    if _nli is None:
        from sentence_transformers import CrossEncoder
        _nli = CrossEncoder(NLI_MODEL_NAME)
    return _nli


def grounding_signal(query: str, answer: str, evidence: list, extra_premises=()) -> float:
    """Max NLI entailment probability of the answer over evidence passages (plus any
    deterministic calculator output the generator was shown). A self-declined answer
    gets 0: the generator itself judged the evidence insufficient."""
    if not answer or "NOT_SUPPORTED" in answer or not evidence:
        return 0.0
    hyp = CITATION_RE.sub("", answer).strip()
    if len(hyp.split()) < 6:  # bare values ("$29,915 million.") aren't propositions
        hyp = f"{query} {hyp}"
    premises = [e["text"] for e in evidence] + [p for p in extra_premises if p]
    nli = _get_nli()
    logits = np.asarray(nli.predict([(p, hyp) for p in premises]), dtype=np.float64)
    probs = np.exp(logits - logits.max(axis=1, keepdims=True))
    probs /= probs.sum(axis=1, keepdims=True)
    labels = {v.lower(): k for k, v in nli.model.config.id2label.items()}
    return float(probs[:, labels["entailment"]].max())


def compute_signals(query: str, evidence: list) -> dict:
    return {
        "R": relevance_signal(evidence),
        "C": coverage_signal(query, evidence),
        "A": agreement_signal(evidence),
        "T": trust_temporal_signal(evidence),
    }


LINEAR_KEYS = {"R": "alpha", "C": "beta", "A": "gamma", "T": "delta"}


def combine(signals: dict, weights: dict) -> float:
    if weights.get("mode") == "logistic":
        z = weights["intercept"] + sum(c * signals[f] for f, c in zip(weights["features"], weights["coef"]))
        return 1.0 / (1.0 + math.exp(-z))
    return float(sum(weights[k] * signals[f] for f, k in LINEAR_KEYS.items()))


def sufficiency_score(query: str, evidence: list, weights: dict) -> dict:
    sig = compute_signals(query, evidence)
    return {"S": combine(sig, weights), **sig}


DEFAULT_WEIGHTS = {"alpha": 0.25, "beta": 0.25, "gamma": 0.25, "delta": 0.25}
