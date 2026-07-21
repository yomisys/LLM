"""
Arithmetic assist ("calculator tool"): the diagnosed failure mode in the pilot
was the small local generator doing mental arithmetic wrong even when the right
raw numbers were sitting in front of it (e.g. computing a percentage change).
Rather than trust the LLM's mental math, this module computes the requested
comparison directly from (a) numbers in retrieved evidence text, or (b) known
document version metadata, and hands the generator a ready-made "Computed"
fact to restate instead of derive.

This is deliberately narrow: it only fires for the two patterns this
benchmark's multi-hop/temporal questions actually use (year-over-year dollar
figures in a financial table; two-document publication-date comparisons). If
neither pattern matches, it returns None and generation proceeds unassisted.
"""
import re

from .corpus import DOC_META

YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")
YEAR_HEADER_RE = re.compile(r"\b((?:19|20)\d{2})\b(?:\s+Change)?\s+\b((?:19|20)\d{2})\b(?:\s+Change)?\s+\b((?:19|20)\d{2})\b")
DOLLAR_NUM_RE = re.compile(r"\$\s*\(?\s*([\d,]+(?:\.\d+)?)\s*\)?")

ARITHMETIC_TRIGGERS = (
    "change", "grew", "grow", "growth", "increase", "decrease", "difference",
    "how much did", "compare", "compared", "percent", "percentage", "higher",
    "lower", "faster", "slower", "share of", "grow faster",
)

# metric name -> keyword(s) to locate its row within a flattened table chunk.
# Ordered most-specific-first: a query mentioning "Japan" or "R&D" should not
# fall through to the generic "net sales" match.
METRIC_KEYWORDS = {
    "greater china": ["Greater China"],
    "japan": ["Japan"],
    "r&d": ["Research and development"],
    "research and development": ["Research and development"],
    "tax rate": ["Effective tax rate"],
    "services": ["Services"],
    "net sales": ["Total net sales", "net sales"],
}


def _query_years(query: str):
    return sorted({int(y) for y in YEAR_RE.findall(query)})


def _query_metric(query: str):
    q = query.lower()
    for metric in METRIC_KEYWORDS:  # dict preserves insertion order (most-specific-first)
        if metric in q:
            return metric
    return None


def _extract_year_value_row(evidence_text: str, metric: str):
    """Find a '<year> <year> <year>' header and the dollar figures following
    the metric's row label, and zip them together positionally (10-K tables in
    this corpus always list years in the same descending order as their
    dollar-figure columns)."""
    header = YEAR_HEADER_RE.search(evidence_text)
    if not header:
        return {}
    years = [int(header.group(i)) for i in (1, 2, 3)]

    keywords = METRIC_KEYWORDS.get(metric, [metric])
    row_start = None
    for kw in keywords:
        idx = evidence_text.find(kw)
        if idx != -1:
            row_start = idx + len(kw)
            break
    if row_start is None:
        return {}

    # narrow window: real rows in this corpus place all N years' $-figures
    # within ~15-20 chars of each other right after the row label (e.g.
    # "Research and development $ 29,915 14 % $ 26,251 20 % $ 21,914"). A wide
    # window risks running past this row's own (non-$-prefixed) figures into
    # the NEXT row's $-prefixed ones when this metric's figures lack a "$".
    window = evidence_text[row_start:row_start + 25 * len(years)]
    nums = DOLLAR_NUM_RE.findall(window)
    if len(nums) < len(years):
        return {}
    values = []
    for n in nums[:len(years)]:
        try:
            values.append(float(n.replace(",", "")))
        except ValueError:
            return {}
    return dict(zip(years, values))


RATIO_QUESTION_TERMS = ("percentage of", "share of", "as a percentage", "percent of", "% of")


def _financial_hint(query: str, evidence: list):
    years = _query_years(query)
    metric = _query_metric(query)
    if len(years) < 2 or metric is None:
        return None
    if not any(t in query.lower() for t in ARITHMETIC_TRIGGERS):
        return None
    if any(t in query.lower() for t in RATIO_QUESTION_TERMS):
        # a ratio-of-two-different-metrics question (e.g. "R&D as a % of net
        # sales") needs a different calculation than a same-metric year-over-year
        # delta; offering the latter here would answer the wrong sub-question
        return None

    year_values = {}
    for e in evidence:
        for y, v in _extract_year_value_row(e["text"], metric).items():
            year_values.setdefault(y, v)  # first (highest-reranked) chunk wins
    y_lo, y_hi = min(years), max(years)
    if y_lo not in year_values or y_hi not in year_values:
        return None

    v_lo, v_hi = year_values[y_lo], year_values[y_hi]
    delta = v_hi - v_lo
    pct = (delta / v_lo * 100) if v_lo else None
    direction = "increase" if delta >= 0 else "decrease"
    pct_str = f", a {abs(pct):.1f}% {direction}" if pct is not None else ""
    return (
        f"[Computed check -- verify against evidence, do not recompute]: {metric} was "
        f"${v_lo:,.0f} million in {y_lo} and ${v_hi:,.0f} million in {y_hi}, "
        f"a change of ${abs(delta):,.0f} million{pct_str}."
    )


DOCUMENT_IDENTITY_TRIGGERS = (
    "which document", "which rfc", "which of the two", "postdate", "authoritative",
    "obsolete", "supersede", "should a system cite", "up-to-date source", "up to date source",
)
# if the question is asking for a *value* (a number), the document-identity hint
# would be off-topic and could mislead the generator into answering the wrong question
VALUE_SEEKING_TERMS = ("net sales", "expense", "income", "tax rate", "figure", "how much")


def _document_date_hint(query: str, evidence: list):
    q = query.lower()
    if not any(t in q for t in DOCUMENT_IDENTITY_TRIGGERS):
        return None
    if any(t in q for t in VALUE_SEEKING_TERMS):
        return None
    doc_ids = {e["doc_id"] for e in evidence if e["doc_id"] in DOC_META}
    if len(doc_ids) < 2:
        return None
    dated = []
    for d in doc_ids:
        meta = DOC_META[d]
        y, m, day = (int(x) for x in meta["version_date"].split("-"))
        dated.append((d, y, m, day, meta["obsolete"]))
    dated.sort(key=lambda t: (t[1], t[2], t[3]))
    older, newer = dated[0], dated[-1]
    years_apart = newer[1] - older[1]
    year_word = "year" if years_apart == 1 else "years"
    return (
        f"[Computed check -- verify against evidence, do not recompute]: of the documents in "
        f"the retrieved evidence, '{newer[0]}' ({newer[1]}) is the current/more recent one; "
        f"'{older[0]}' ({older[1]}) is obsolete/superseded, about {years_apart} {year_word} apart."
    )


def arithmetic_hint(query: str, evidence: list):
    """Try each calculator strategy; return the first hint that fires, or None."""
    for strategy in (_financial_hint, _document_date_hint):
        hint = strategy(query, evidence)
        if hint:
            return hint
    return None
