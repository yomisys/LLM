"""
Evaluation metrics. All grading here is fully automated/code-based (no LLM judge,
no external API) so the pipeline is reproducible offline:

  answer correctness   - recall of gold "key facts" (numbers + salient keywords/phrases
                         extracted from the gold answer) inside the generated text.
  faithfulness proxy   - recall of the *generated answer's* number/entity tokens inside
                         the concatenated retrieved-evidence text (claim grounding check).
  context relevance    - fraction of retrieved evidence chunks that are in the
                         question's gold evidence set (strict chunk-id match).
  coverage             - fraction of queries the system actually answers.
  selective risk       - error rate among answered queries (wrong answer, or an
                         answer given to an unanswerable question).
  abstention P/R       - precision/recall of declining (abstain/clarify/self-declined)
                         specifically on unanswerable queries.
  risk-coverage AUC    - operating-characteristic curve of the sufficiency score S
                         swept as a selective-prediction threshold (trapezoidal AUC).
"""
import re

import numpy as np

NUMBER_UNIT_RE = re.compile(r"\$?(\d[\d,]*\.?\d*)\s*(billion|bn|million|mn|thousand)?\b", re.IGNORECASE)
# SEC filing-type references ("10-K", "8-K", "10-Q", "S-1") read as numbers otherwise
FILING_REF_RE = re.compile(r"\b\d{1,2}-[A-Z]{1,2}\b")
WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9\-]{2,}")
STOPWORDS = set("""
the a an of to in on for with and or as at by from what which who this that these
those per approximately about roughly than versus compared fiscal year years million
billion figure filing filed report reported source both according does not
""".split())

NOT_SUPPORTED_MARK = "NOT_SUPPORTED"

# scale to a common "millions" base so "$383.3 billion" and "$383,285 million"
# are recognized as the same figure instead of failing as a unit mismatch
UNIT_SCALE_TO_MILLIONS = {"billion": 1000.0, "bn": 1000.0, "million": 1.0, "mn": 1.0, "thousand": 0.001}


def _numbers(text: str):
    """Extract numbers, normalizing billion/million/thousand mentions to a common
    scale. Bare numbers with no unit word (percentages, section numbers, plain
    counts) are kept as-is. Filing-type references ("10-K") are stripped first
    so they aren't misread as the number 10."""
    text = FILING_REF_RE.sub(" ", text or "")
    out = set()
    for m in NUMBER_UNIT_RE.finditer(text):
        digits = m.group(1).replace(",", "")
        if not digits or digits == ".":
            continue
        try:
            val = float(digits)
        except ValueError:
            continue
        scale = UNIT_SCALE_TO_MILLIONS.get((m.group(2) or "").lower(), 1.0)
        out.add(round(val * scale, 1))
    return out


def _numbers_overlap(a: set, b: set, rel_tol: float = 0.01) -> int:
    """Count values in a with an approximate match in b (absorbs rounding noise
    like 383,285 vs 383.3-billion-rounded-to-383,300; does not absorb genuinely
    different values)."""
    hits = 0
    for x in a:
        if any(x == y or abs(x - y) <= rel_tol * max(abs(x), abs(y), 1.0) for y in b):
            hits += 1
    return hits


def _keywords(text: str):
    words = WORD_RE.findall(text or "")
    return {w.lower() for w in words if w.lower() not in STOPWORDS and len(w) >= 4}


def headline_number(gold_answer: str):
    """The first figure stated in the gold answer -- the value the question asks for."""
    text = FILING_REF_RE.sub(" ", gold_answer or "")
    for m in NUMBER_UNIT_RE.finditer(text):
        digits = m.group(1).replace(",", "")
        try:
            return round(float(digits) * UNIT_SCALE_TO_MILLIONS.get((m.group(2) or "").lower(), 1.0), 1)
        except ValueError:
            continue
    return None


def key_facts(gold_answer: str):
    return _numbers(gold_answer), _keywords(gold_answer)


def is_declined(record: dict) -> bool:
    if record["decision"] in ("abstain", "clarify"):
        return True
    ans = record.get("answer") or ""
    return NOT_SUPPORTED_MARK in ans


def answer_correct(gold_answer: str, generated_text: str) -> bool:
    """Numbers are the load-bearing fact in almost every gold answer in this
    benchmark, so they are graded on their own recall rather than being diluted
    by incidental keywords from explanatory/parenthetical phrasing in the gold
    answer text (e.g. "...(per the FY2023 10-K, the more recently filed
    document)"). Keywords only decide borderline/no-number cases."""
    if not generated_text:
        return False
    gold_nums, gold_kw = key_facts(gold_answer)
    gen_nums = _numbers(generated_text)
    gen_text_lower = generated_text.lower()

    def kw_recall(keywords):
        if not keywords:
            return 1.0
        hits = sum(1 for k in keywords if k in gen_text_lower)
        return hits / len(keywords)

    if gold_nums:
        num_recall = _numbers_overlap(gold_nums, gen_nums) / len(gold_nums)
        if num_recall >= 0.8:
            return True
        if num_recall >= 0.5 and _numbers_overlap({headline_number(gold_answer)}, gen_nums):
            # gold answers often append context figures after the asked-for value
            # ("$29,915 million, about 8% of total net sales"); an answer stating the
            # headline value plus at least half the figures is correct
            return True
        # partial numeric credit only counts alongside decent keyword support
        return num_recall >= 0.5 and kw_recall(gold_kw) >= 0.5

    if not gold_kw:
        return True
    return kw_recall(gold_kw) >= 0.5


def faithfulness_score(generated_text: str, evidence: list):
    if not generated_text or NOT_SUPPORTED_MARK in generated_text:
        return None
    ev_text = " ".join(e["text"] for e in evidence).lower()
    ev_numbers = _numbers(ev_text)
    gen_nums = _numbers(generated_text)
    gen_kw = _keywords(generated_text)
    claims, supported = 0, 0
    for n in gen_nums:
        claims += 1
        if _numbers_overlap({n}, ev_numbers):
            supported += 1
    for k in gen_kw:
        claims += 1
        if k in ev_text:
            supported += 1
    if claims == 0:
        return 1.0
    return supported / claims


def context_relevance(evidence: list, gold_chunk_ids: list):
    if not gold_chunk_ids:
        return None
    if not evidence:
        return 0.0
    gold_set = set(gold_chunk_ids)
    hits = sum(1 for e in evidence if e["chunk_id"] in gold_set)
    return hits / len(evidence)


def answer_in_context(evidence: list, gold_answer: str, gold_chunk_ids: list):
    """Retrieval recall that tolerates overlapping chunks: True if any gold chunk was
    retrieved, or if the evidence contains every gold figure. Strict chunk-id matching
    (context_relevance) scored 0.09-0.10 in the pilot because the 40-word chunk overlap
    makes informationally equivalent passages carry different ids."""
    if not gold_chunk_ids or not gold_answer:
        return None
    if any(e["chunk_id"] in set(gold_chunk_ids) for e in evidence):
        return True
    gold_nums = _numbers(gold_answer)
    if not gold_nums:
        return False
    ev_nums = _numbers(" ".join(e["text"] for e in evidence))
    return _numbers_overlap(gold_nums, ev_nums) == len(gold_nums)


def grade_record(record: dict, question: dict) -> dict:
    rec = dict(record)
    declined = is_declined(record)
    rec["declined"] = declined
    rec["question_answerable"] = question["answerable"]
    rec["S"] = (record.get("scores") or {}).get("S")
    rec["context_relevance"] = context_relevance(record.get("evidence", []), question.get("gold_evidence_chunk_ids", []))

    if declined:
        rec["correct"] = None
        rec["faithfulness"] = None
        rec["error"] = False  # declining is never counted as a hallucination error
    else:
        answer_text = record.get("answer") or ""
        if question["answerable"]:
            correct = answer_correct(question["gold_answer"], answer_text)
            rec["correct"] = correct
            rec["error"] = not correct
        else:
            rec["correct"] = False  # there is no correct direct answer
            rec["error"] = True     # answering an unanswerable question is always an error
        rec["faithfulness"] = faithfulness_score(answer_text, record.get("evidence", []))

    # "would this system have been correct had it answered?" -- used only for the
    # risk-coverage curve sweep, graded from the shadow (always-generate) answer
    # when available so the curve isn't confounded by the actual Answer/Clarify/Abstain decision.
    shadow = record.get("shadow_answer")
    if shadow is not None:
        if question["answerable"]:
            rec["correct_if_answered"] = answer_correct(question["gold_answer"], shadow)
        else:
            rec["correct_if_answered"] = False
    else:
        rec["correct_if_answered"] = rec["correct"] if rec["correct"] is not None else False
    return rec


def aggregate_metrics(graded_records: list) -> dict:
    n = len(graded_records)
    if n == 0:
        return {}
    answered = [r for r in graded_records if not r["declined"]]
    coverage = len(answered) / n
    errors = sum(1 for r in answered if r["error"])
    selective_risk = errors / len(answered) if answered else 0.0

    faith_vals = [r["faithfulness"] for r in answered if r["faithfulness"] is not None]
    faithfulness_mean = float(np.mean(faith_vals)) if faith_vals else None

    ctx_vals = [r["context_relevance"] for r in graded_records if r["context_relevance"] is not None]
    context_relevance_mean = float(np.mean(ctx_vals)) if ctx_vals else None

    def _answerable(r):
        return r["question_answerable"] if "question_answerable" in r else r["answerable"]

    unanswerable = [r for r in graded_records if not _answerable(r)]
    if unanswerable:
        declined_unanswerable = sum(1 for r in unanswerable if r["declined"])
        abstention_recall = declined_unanswerable / len(unanswerable)
    else:
        abstention_recall = None

    total_declined = sum(1 for r in graded_records if r["declined"])
    if total_declined:
        correct_declines = sum(1 for r in graded_records if r["declined"] and not _answerable(r))
        abstention_precision = correct_declines / total_declined
    else:
        abstention_precision = None

    return {
        "n": n,
        "coverage": coverage,
        "selective_risk": selective_risk,
        "faithfulness": faithfulness_mean,
        "context_relevance": context_relevance_mean,
        "abstention_precision": abstention_precision,
        "abstention_recall": abstention_recall,
    }


def risk_coverage_auc(graded_records_with_scores: list) -> float:
    """Sweep S as a selective-prediction threshold (answer iff S >= tau); return AUC
    of the risk-coverage curve via the trapezoidal rule over coverage in [0,1]."""
    scored = [r for r in graded_records_with_scores if r.get("S") is not None]
    if not scored:
        return None
    scored = sorted(scored, key=lambda r: -r["S"])
    n = len(scored)
    coverages, risks = [], []
    errors_so_far = 0
    for i, r in enumerate(scored, start=1):
        would_be_wrong = (not r["question_answerable"]) or (not r.get("correct_if_answered", False))
        if would_be_wrong:
            errors_so_far += 1
        coverages.append(i / n)
        risks.append(errors_so_far / i)
    order = np.argsort(coverages)
    cov_sorted = np.array(coverages)[order]
    risk_sorted = np.array(risks)[order]
    trapezoid = getattr(np, "trapezoid", None) or np.trapz  # trapz is deprecated in NumPy 2
    return float(trapezoid(risk_sorted, cov_sorted))
