# -*- coding: utf-8 -*-
"""
Rewrite ECERAG_Conference_Paper.docx in place with real experimental results
from results/metrics.json and results/raw_outputs.jsonl, replacing:
  - the fabricated reference [11] with two real, verified citations
  - Section V-A (Corpora and Benchmark) with the actual corpus/benchmark built
  - Section VI (Results and Analysis) with measured numbers
  - Section VII-B (Limitations) with concrete small-scale caveats
  - light touch-ups to the Abstract and Conclusion
Saves to ECERAG_Conference_Paper_REVISED.docx alongside the original (which is left untouched).
"""
import copy

import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH

SRC = r"C:\Users\yomis\Downloads\ieee\ECERAG_Conference_Paper.docx"
DST = r"C:\Users\yomis\Downloads\ieee\ECERAG_Conference_Paper_REVISED.docx"


def set_paragraph_text(p, text, bold=False, italic=False):
    for r in list(p.runs):
        r._element.getparent().remove(r._element)
    run = p.add_run(text)
    run.font.name = "Times New Roman"
    run.bold = bold
    run.italic = italic


def new_body_paragraph_before(anchor_para, text):
    """Insert a new justified body paragraph immediately before anchor_para,
    formatted like a normal ECERAG body paragraph."""
    p = anchor_para.insert_paragraph_before("", style=anchor_para.style)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    run = p.add_run(text)
    run.font.name = "Times New Roman"
    return p


def main():
    d = docx.Document(SRC)
    paras = d.paragraphs

    # ---- locate anchors by content (robust to any small offset drift) ----
    def find(substr, start=0):
        for i in range(start, len(paras)):
            if substr in paras[i].text:
                return i
        raise ValueError(f"paragraph containing {substr!r} not found")

    idx_abstract = find("Abstract—")
    idx_selective_pred = find("Selective prediction studies the problem")
    idx_pipeline_step3 = find("Cross-Encoder Reranking: Rerank top-k")
    idx_va_body = find("We construct an enterprise-style QA benchmark")
    idx_metrics_last = find("We report full tradeoff curves")
    idx_vi_intro = find("We report the expected outcome pattern")
    idx_via_body = find("ECERAG is expected to reduce unsupported claims")
    idx_vib_body = find("Under adversarial passage injection, Baseline RAG faithfulness")
    idx_vic_body = find("ECERAG+CR recovers part of the coverage lost")
    idx_limitations = find("Threshold values calibrated in one enterprise domain")
    idx_conclusion = find("Enterprise RAG must advance from retrieve-then-generate")
    idx_ref11 = find("Geifman and R. El-Yaniv")
    idx_ref12_bert = find("BERT: Pre-training of Deep Bidirectional")

    print("Anchors found at:", dict(
        abstract=idx_abstract, selective_pred=idx_selective_pred, pipeline_step3=idx_pipeline_step3,
        va_body=idx_va_body, metrics_last=idx_metrics_last, vi_intro=idx_vi_intro,
        via_body=idx_via_body, vib_body=idx_vib_body, vic_body=idx_vic_body,
        limitations=idx_limitations, conclusion=idx_conclusion,
        ref11=idx_ref11, ref12_bert=idx_ref12_bert,
    ))

    # ---- Abstract: append empirical sentence ----
    abstract_new = (
        "Abstract—Large language models (LLMs) remain prone to fluent but unsupported answers in "
        "enterprise question answering (QA). Retrieval-Augmented Generation (RAG) reduces this risk by "
        "conditioning generation on external documents, yet practical systems still fail under weak "
        "retrieval, noisy context, and contradictory evidence. We propose Evidence-Calibrated Enterprise "
        "RAG (ECERAG), a selective QA framework that answers only when retrieved evidence is sufficient "
        "and otherwise requests clarification or abstains. ECERAG combines hybrid retrieval, reranking, "
        "evidence sufficiency scoring, and decision-thresholded generation. We define calibration-aware "
        "evaluation using faithfulness, selective risk, abstention quality, and risk-coverage curves, and "
        "introduce robustness stress tests with irrelevant, contradictory, and counterfactual passages. We "
        "implement the full pipeline and evaluate it on a 40-item enterprise-style benchmark built from "
        "public SEC filings, the NIST AI Risk Management Framework, the OWASP Top 10, and paired "
        "current/obsolete IETF specifications, using a small open-weight local generator. The clearest "
        "measured effect is mechanistic rather than accuracy-level: under counterfactual (superseded-"
        "document) injection, ECERAG's evidence sufficiency score moves in the expected direction and its "
        "corrective-retrieval variant recovers 4 of 5 clarify-band queries to a grounded answer, while raw "
        "answer accuracy at this generator scale remains bounded more by generation-time reasoning errors "
        "than by evidence availability. The work frames enterprise RAG not as “always answer with "
        "retrieval,” but as retrieve–assess–decide under explicit evidence constraints, and "
        "reports where that framing helps—and where it does not—at small scale."
    )
    set_paragraph_text(paras[idx_abstract], abstract_new)

    # ---- II-D: fix fabricated citation, cite real replacements ----
    set_paragraph_text(paras[idx_selective_pred], (
        "Selective prediction studies the problem of abstaining under uncertainty to minimize "
        "high-confidence errors [11]. Applied specifically to question answering, Kamath et al. [12] "
        "show that a calibrated selective answerer can reject low-confidence predictions to control error "
        "under domain shift. Together these define a risk-coverage tradeoff: lower error on answered "
        "queries at the cost of reduced coverage. We adapt this principle to RAG by using evidence "
        "sufficiency as the decision variable, making calibration explicit and actionable."
    ))

    # ---- IV-A pipeline step 3: cite BERT for the cross-encoder ----
    set_paragraph_text(paras[idx_pipeline_step3], (
        "(3) Cross-Encoder Reranking: Rerank top-k candidates using a BERT-based cross-encoder [13] to "
        "improve precision before sufficiency scoring."
    ))

    # ---- V-A: real corpus/benchmark description (replace + insert extra paragraph) ----
    set_paragraph_text(paras[idx_va_body], (
        "We construct a small enterprise-style QA benchmark from six public documents spanning four "
        "categories: two SEC Form 10-K filings for the same company in consecutive fiscal years (financial "
        "disclosure, chosen specifically to create a natural current-vs-superseded document pair), the "
        "NIST AI Risk Management Framework (AI 100-1) (regulatory policy), the OWASP Top 10:2021 "
        "(technical operating standard), and RFC 2616 and RFC 9110 — the obsolete and current IETF "
        "HTTP specifications, respectively (engineering manual, our second natural version pair). "
        "Documents are chunked into 1,207 passages of approximately 220 words. We hand-author 40 "
        "questions, verified against the source text and classified into the four types above: 10 "
        "single-hop factual, 10 multi-hop synthesis (9 of which require combining facts from two "
        "different document versions), 9 temporal/version-sensitive, and 11 unanswerable or "
        "underspecified. Each answerable item carries a gold answer and gold evidence chunk id(s); each "
        "unanswerable item is a verified false-premise, out-of-corpus, or over-specific query (e.g., "
        "asking for a CVSS score that OWASP's Top 10 report does not assign, or a fiscal year covered by "
        "neither filing). Given the benchmark's size, we hold out a stratified 30% calibration split (12 "
        "items) to fit ECERAG's decision thresholds and evaluate on the remaining 28-item test split; all "
        "results in Sec. VI are computed on the held-out test split unless stated otherwise."
    ))
    new_body_paragraph_before(paras[idx_va_body + 1], (
        "Implementation: retrieval combines BM25 (rank_bm25) with dense retrieval over all-MiniLM-L6-v2 "
        "sentence embeddings (min-max normalized, equally weighted); reranking uses the "
        "cross-encoder/ms-marco-MiniLM-L-6-v2 cross-encoder [13]; generation uses Qwen2.5-0.5B-Instruct, "
        "a small open-weight instruction-tuned model run locally on CPU. This generator is orders of "
        "magnitude smaller than the frontier LLMs an enterprise deployment would use; Sec. VII-B discusses "
        "the consequences of that choice."
    ))
    paras = d.paragraphs  # re-fetch after insertion shifts indices

    idx_metrics_last = find("We report full tradeoff curves")
    new_body_paragraph_before(paras[idx_metrics_last + 1], (
        "All grading in this study is fully automated and code-based rather than human- or LLM-judged: "
        "answer correctness and faithfulness are computed via recall of gold numeric values and salient "
        "keywords inside generated text, and context relevance uses strict retrieved-chunk-id matching "
        "against annotated gold evidence. This keeps evaluation reproducible without external API calls, "
        "but it is a coarser proxy than semantic entailment; Sec. VII-B reports specific cases where this "
        "produces false positives and false negatives."
    ))
    paras = d.paragraphs

    # ---- VI intro ----
    idx_vi_intro = find("We report the expected outcome pattern")
    set_paragraph_text(paras[idx_vi_intro], (
        "We report measured results from running the full pipeline — Baseline RAG, ECERAG, and "
        "ECERAG+CR — on the 28-item held-out test split described in Sec. V-A, using the local "
        "Qwen2.5-0.5B-Instruct generator. Thresholds (τ_A = 0.45, τ_C = 0.20) and equal signal "
        "weights (α=β=γ=δ=0.25) were fixed by grid search on the 12-item calibration "
        "split before any test-split evaluation. We treat this as a small-scale feasibility study rather "
        "than a claim of production-level accuracy: the generator is a 0.5B-parameter open-weight model, "
        "roughly three orders of magnitude smaller than the frontier LLMs an enterprise deployment would "
        "use, and the test split is too small to support significance testing. We therefore report exact "
        "counts throughout."
    ))

    # ---- VI-A ----
    idx_via_body = find("ECERAG is expected to reduce unsupported claims")
    set_paragraph_text(paras[idx_via_body], (
        "On clean (unperturbed) retrieval, Baseline RAG answered 19 of 28 test queries (68% coverage, "
        "occasionally self-declining via its own prompt-level refusal instruction) with 6 of those 19 "
        "judged correct (selective risk 0.68); ECERAG answered 17 of 28 (61% coverage) with 5 of 17 "
        "correct (selective risk 0.71); ECERAG+CR answered 19 of 28 (68%) with 5 correct (selective risk "
        "0.74). Faithfulness — the fraction of numeric/entity claims in each generated answer that are "
        "grounded in the retrieved evidence — was 0.80 for Baseline, 0.83 for ECERAG, and 0.79 for "
        "ECERAG+CR. The risk-coverage AUC for ECERAG's sufficiency score, computed over all 40 benchmark "
        "items (calibration + test) by sweeping τ_A as a selective-prediction threshold, is 0.64. At "
        "this generator scale, ECERAG does not show a clear selective-risk advantage over Baseline RAG on "
        "clean retrieval: inspecting the answered-but-incorrect cases shows that most errors are "
        "generation-time reasoning failures — e.g., correctly retrieved figures combined into a wrong "
        "percentage change, or a numerically correct answer stated in different units than the gold label "
        "(“$383.3 billion” vs. “$383,285 million”) — rather than the retrieval or "
        "evidence-sufficiency failures the R/C/A/T signals are designed to catch. This is consistent with "
        "a calibration-split finding (Sec. V-A): answer correctness correlated only weakly with the "
        "sufficiency score S at this model scale, which is why the calibrated τ_A settled at the low "
        "end of the search grid — raising it further reduced coverage without measurably reducing "
        "error, because most errors were not evidence-availability errors."
    ))

    # ---- VI-B ----
    idx_vib_body = find("Under adversarial passage injection, Baseline RAG faithfulness")
    set_paragraph_text(paras[idx_vib_body], (
        "Under irrelevant-passage injection (applicable to 27 of 28 queries; one had no eligible "
        "distractor document), Baseline RAG's answered-error rate rose to 0.81 (17 of 21 answered) and "
        "ECERAG's to 0.80 (16 of 20 answered), with ECERAG showing higher abstention recall on "
        "unanswerable queries under this condition (0.57 vs. 0.43 for Baseline) — a modest but "
        "directionally consistent protective effect. Under contradictory-number injection, only 10 of 28 "
        "queries had a genuine gold-evidence chunk containing an extractable number to contradict (the "
        "rest were skipped as inapplicable); on this subset all three systems behaved identically "
        "(coverage 0.90, selective risk 0.33), because in every case ECERAG's sufficiency score remained "
        "above τ_A regardless of the injected contradiction — the Agreement (A) signal registered "
        "the conflict but not strongly enough, at this threshold, to change the routing decision. This is "
        "the stress test where ECERAG's calibrated policy provided the least measurable protection in this "
        "pilot. Counterfactual (superseded-document) injection produced the clearest and most "
        "mechanistically legible effect: applicable to 22 of 28 queries (6 questions' evidence had no "
        "versioned counterpart, e.g. NIST/OWASP), it dropped ECERAG's coverage to 0.68 (15 of 22, vs. "
        "Baseline's 0.77, 17 of 22) by pushing two additional queries into the clarify band that had "
        "answered directly on clean evidence. For example, on “What is Apple's most recently reported "
        "total net sales figure...” the Trust/Temporal (T) signal correctly lowered S from 0.70 "
        "(clean, current-year evidence) to 0.65 (counterfactual, prior-year evidence substituted) — "
        "registering the staleness in the intended direction — but 0.65 still cleared the calibrated "
        "τ_A of 0.45, so both Baseline and ECERAG still answered with the outdated figure ($394,328 "
        "million, FY2022, instead of $383,285 million, FY2023). This illustrates a specific, honest "
        "limitation: the T signal moves correctly, but a threshold calibrated on only 12 examples was not "
        "always tight enough to convert that movement into a safe abstention."
    ))

    # ---- VI-C ----
    idx_vic_body = find("ECERAG+CR recovers part of the coverage lost")
    set_paragraph_text(paras[idx_vic_body], (
        "Across all four conditions, 5 of 112 total (question, condition) evaluations fell into ECERAG's "
        "clarify band (2 under clean retrieval, 1 under irrelevant injection, 2 under counterfactual "
        "injection; none under contradictory injection). ECERAG+CR's single corrective-retrieval pass (LLM "
        "query rewrite, re-retrieval, re-scoring) promoted 4 of these 5 (80%) to a grounded answer that "
        "ECERAG alone would have left as an unanswered clarification request — directly recovering "
        "coverage without any change to the thresholds. The fifth case arose under counterfactual "
        "injection (“Which of the two HTTP RFCs...was published more recently?”, with evidence "
        "corrupted toward the obsolete RFC 2616): after query rewriting and re-retrieval, the rescored "
        "evidence still did not clear τ_A, and ECERAG+CR correctly abstained rather than force an "
        "answer — avoiding the date-confusion error Baseline RAG committed on the identical corrupted "
        "evidence (Baseline answered: “the second HTTP RFC, RFC 2616, was published more recently... "
        "by approximately 19 years,” which is wrong on both the ordering and the interval). This one "
        "case is a concrete instance of the paper's central claim operating correctly end-to-end: retrieve, "
        "assess, and — when even a corrective attempt cannot clear the bar — decide not to answer."
    ))

    # ---- VII-B Limitations: append concrete pilot-specific caveats ----
    idx_limitations = find("Threshold values calibrated in one enterprise domain")
    orig_limitations = paras[idx_limitations].text
    set_paragraph_text(paras[idx_limitations], orig_limitations + " " + (
        "The proof-of-concept implementation reported in Sec. VI adds four further, specific limitations. "
        "First, generator scale dominates: with a 0.5B-parameter local model, most answer errors were "
        "arithmetic or reasoning mistakes made despite correct evidence being retrieved (e.g., computing a "
        "percentage change incorrectly, or confusing which of two adjacent fiscal years a figure belonged "
        "to), which evidence-side sufficiency gating cannot catch by construction — the R/C/A/T "
        "signals score the evidence, not the generator's use of it. We expect selective-risk reduction "
        "from calibration gating to be more visible with a frontier-scale generator, where residual errors "
        "are more likely to stem from evidence problems the signals are designed to detect. Second, our "
        "automated grading is a lexical-overlap proxy, not a semantic judgment, and it errs in both "
        "directions: it credited one clearly incorrect answer as correct because the right entities "
        "happened to co-occur without being correctly related (a false positive), and penalized one "
        "numerically correct answer stated in different units than the gold label as incorrect (a false "
        "negative, “$383.3 billion” vs. “$383,285 million”). Third, our strict "
        "chunk-id context-relevance metric measured only 0.09–0.10 across all systems and conditions "
        "on this corpus, substantially lower than retrieval quality appeared to be on manual inspection, "
        "because fixed-window chunking produces multiple overlapping passages that restate the same fact "
        "— the system frequently retrieved an informationally equivalent but differently-indexed chunk "
        "rather than the single passage annotated as gold. Fourth, a 12-item calibration split is too "
        "small to fit reliable thresholds on its own: the grid search settled on a permissive τ_A "
        "because measured correctness correlated only weakly with S at this scale, which limits how much "
        "of Sec. VI's clean-condition results can be attributed to the calibration methodology versus "
        "chance. The Sec. VI findings should accordingly be read as evidence that the ECERAG architecture "
        "is mechanically sound and that its Trust/Temporal signal moves in the correct direction under "
        "document staleness, not as an accuracy benchmark comparable to a production system."
    ))

    # ---- VIII Conclusion: append pilot summary before "Future work" ----
    idx_conclusion = find("Enterprise RAG must advance from retrieve-then-generate")
    conclusion_text = paras[idx_conclusion].text
    marker = "Future work will extend ECERAG"
    before, _, after = conclusion_text.partition(marker)
    new_conclusion = before + (
        "A small-scale, fully-implemented pilot — six public documents, 40 hand-authored questions, "
        "and a 0.5B-parameter local generator — confirms that the pipeline operates end-to-end as "
        "designed and that its Trust/Temporal signal responds correctly to document staleness, while "
        "showing that realizing the hypothesized selective-risk gains requires a generator whose own "
        "reasoning errors are no longer the dominant failure mode. "
    ) + marker + after
    set_paragraph_text(paras[idx_conclusion], new_conclusion)

    # ---- References: fix fabricated [11], insert real [12], renumber BERT to [13] ----
    idx_ref11 = find("Geifman and R. El-Yaniv")
    set_paragraph_text(paras[idx_ref11], (
        "[11]\tY. Geifman and R. El-Yaniv, “SelectiveNet: A Deep Neural Network with an Integrated "
        "Reject Option,” in Proc. ICML, 2019, pp. 2151–2159."
    ))
    idx_ref12_bert = find("BERT: Pre-training of Deep Bidirectional")
    new_body_paragraph_before(paras[idx_ref12_bert], (
        "[12]\tA. Kamath, R. Jia, and P. Liang, “Selective Question Answering under Domain Shift,” "
        "in Proc. ACL, 2020, pp. 5684–5696."
    ))
    paras = d.paragraphs
    idx_ref12_bert = find("BERT: Pre-training of Deep Bidirectional")
    bert_text = paras[idx_ref12_bert].text.replace("[12]", "[13]", 1)
    set_paragraph_text(paras[idx_ref12_bert], bert_text)

    d.save(DST)
    print(f"\nSaved revised paper to {DST}")


if __name__ == "__main__":
    main()
