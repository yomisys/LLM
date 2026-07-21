"""
Robustness stress-test perturbations applied to a clean, reranked evidence set:

  irrelevant   - swap the weakest evidence slot for a real, unrelated-document chunk
                 that surfaces via lexical overlap but contains no answer content.
  contradictory - duplicate one genuine evidence chunk with its key number altered,
                 injecting a directly conflicting claim (paper Sec. V-C(ii)).
  counterfactual - replace a current-document chunk with its superseded/obsolete
                 counterpart from the same source family (Apple 10-K or RFC pair),
                 i.e. a plausible but outdated passage (paper Sec. V-C(iii)).
                 Returns no_op=True when the evidence set has no versioned
                 counterpart available (e.g. NIST/OWASP single-version docs).
"""
import copy
import random
import re

from .corpus import DOC_META

NUMBER_RE = re.compile(r"\d[\d,]*")


def inject_irrelevant(evidence: list, retriever, query: str, gold_chunk_ids: set, rng: random.Random):
    if not evidence:
        return evidence, False
    gold_doc_ids = {c["doc_id"] for c in evidence if c["chunk_id"] in gold_chunk_ids} or {evidence[0]["doc_id"]}
    candidates = retriever.retrieve(query, top_k=50)
    distractor = None
    for c in candidates:
        if c["chunk_id"] in gold_chunk_ids:
            continue
        if c["doc_id"] in gold_doc_ids:
            continue
        distractor = c
        break
    if distractor is None:
        return evidence, False
    new_evidence = copy.deepcopy(evidence)
    new_evidence[-1] = {**distractor, "rerank_score": evidence[-1].get("rerank_score", 0.0),
                         "rerank_prob": evidence[-1].get("rerank_prob", 0.5), "_perturbation": "irrelevant"}
    return new_evidence, True


def _alter_number(text: str, rng: random.Random):
    matches = list(NUMBER_RE.finditer(text))
    matches = [m for m in matches if len(m.group().replace(",", "")) >= 3]
    if not matches:
        return None
    m = rng.choice(matches)
    original = m.group()
    digits = original.replace(",", "")
    altered_val = int(digits) + rng.choice([-1, 1]) * max(1, int(int(digits) * 0.37))
    altered_str = f"{altered_val:,}"
    return text[:m.start()] + altered_str + text[m.end():]


def inject_contradictory(evidence: list, gold_chunk_ids: set, rng: random.Random):
    if not evidence:
        return evidence, False
    target_idx = None
    for i, e in enumerate(evidence):
        if e["chunk_id"] in gold_chunk_ids:
            altered = _alter_number(e["text"], rng)
            if altered is not None:
                target_idx = i
                break
    if target_idx is None:
        return evidence, False
    new_evidence = copy.deepcopy(evidence)
    fabricated = copy.deepcopy(new_evidence[target_idx])
    fabricated["text"] = _alter_number(evidence[target_idx]["text"], rng)
    fabricated["chunk_id"] = fabricated["chunk_id"] + "__CONTRADICTORY_SYNTH"
    fabricated["_perturbation"] = "contradictory"
    # replace the lowest-ranked slot (or append) with the fabricated contradictory duplicate
    replace_idx = len(new_evidence) - 1 if len(new_evidence) > 1 else 0
    if replace_idx == target_idx and len(new_evidence) > 1:
        replace_idx = len(new_evidence) - 2
    new_evidence[replace_idx] = fabricated
    return new_evidence, True


def inject_counterfactual(evidence: list, chunks_by_doc: dict, rng: random.Random):
    if not evidence:
        return evidence, False
    # doc_id (current) -> doc_id (obsolete counterpart it supersedes)
    supersedes_map = {k: v["supersedes"] for k, v in DOC_META.items() if v.get("supersedes")}
    for i, e in enumerate(evidence):
        obsolete_doc_id = supersedes_map.get(e["doc_id"])
        if obsolete_doc_id and obsolete_doc_id in chunks_by_doc and chunks_by_doc[obsolete_doc_id]:
            candidates = chunks_by_doc[obsolete_doc_id]
            replacement = rng.choice(candidates)
            new_evidence = copy.deepcopy(evidence)
            new_evidence[i] = {**replacement, "rerank_score": e.get("rerank_score", 0.0),
                                "rerank_prob": e.get("rerank_prob", 0.5), "_perturbation": "counterfactual"}
            return new_evidence, True
    return evidence, False
