"""
Three systems compared in the experiment:

  BaselineRAG - hybrid retrieve -> rerank -> generate unconditionally.
  ECERAG      - hybrid retrieve -> rerank -> score S(q,E) -> Answer / Clarify / Abstain.
  ECERAG+CR   - ECERAG, plus one corrective retrieval pass for queries in the
                Clarify band (query rewrite -> re-retrieve -> re-rerank -> rescore).
"""
from .generator import generate_answer, rewrite_query
from .reranker import rerank
from .sufficiency import sufficiency_score

TOP_K_RETRIEVE = 20
TOP_N_RERANK = 5


def retrieve_and_rerank(retriever, query, top_k=TOP_K_RETRIEVE, top_n=TOP_N_RERANK, exclude_chunk_ids=None):
    candidates = retriever.retrieve(query, top_k=top_k, exclude_chunk_ids=exclude_chunk_ids)
    return rerank(query, candidates, top_n=top_n)


def run_baseline(query, evidence):
    answer = generate_answer(query, evidence)
    return {"system": "baseline", "decision": "answer", "answer": answer, "evidence": evidence}


def run_ecerag(query, evidence, weights, tau_a, tau_c, shadow_generate=True):
    scores = sufficiency_score(query, evidence, weights)
    S = scores["S"]
    shadow_answer = generate_answer(query, evidence) if shadow_generate else None
    if S >= tau_a:
        answer = shadow_answer if shadow_answer is not None else generate_answer(query, evidence)
        decision = "answer"
    elif S >= tau_c:
        answer = None
        decision = "clarify"
    else:
        answer = None
        decision = "abstain"
    return {"system": "ecerag", "decision": decision, "answer": answer,
            "evidence": evidence, "scores": scores, "shadow_answer": shadow_answer}


def run_ecerag_cr_from_ecerag(ecerag_result, query, weights, tau_a, tau_c, retriever, exclude_chunk_ids=None):
    """Reuses the retrieval/scoring/shadow-generation already done for plain ECERAG
    (same evidence, same deterministic decoding => same answer) so we only pay for a
    fresh LLM call when the corrective-retrieval pass actually fires."""
    evidence = ecerag_result["evidence"]
    scores = ecerag_result["scores"]
    S = scores["S"]
    if S >= tau_a:
        answer = ecerag_result.get("shadow_answer") or generate_answer(query, evidence)
        return {"system": "ecerag_cr", "decision": "answer", "answer": answer,
                "evidence": evidence, "scores": scores, "corrective_pass": False}
    if S < tau_c:
        return {"system": "ecerag_cr", "decision": "abstain", "answer": None,
                "evidence": evidence, "scores": scores, "corrective_pass": False}

    # Clarify band: one corrective retrieval pass
    rewritten = rewrite_query(query, evidence)
    new_evidence = retrieve_and_rerank(retriever, rewritten, exclude_chunk_ids=exclude_chunk_ids)
    new_scores = sufficiency_score(query, new_evidence, weights)
    if new_scores["S"] >= tau_a:
        answer = generate_answer(query, new_evidence)
        return {"system": "ecerag_cr", "decision": "answer", "answer": answer,
                "evidence": new_evidence, "scores": new_scores, "corrective_pass": True,
                "rewritten_query": rewritten}
    return {"system": "ecerag_cr", "decision": "abstain", "answer": None,
            "evidence": new_evidence, "scores": new_scores, "corrective_pass": True,
            "rewritten_query": rewritten}
