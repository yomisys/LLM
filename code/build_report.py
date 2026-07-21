# -*- coding: utf-8 -*-
"""Assemble a standalone Word report of the ECERAG experiment results, with
embedded figures and tables, from results/metrics.json, raw_outputs.jsonl,
and calibration.json. Separate from the IEEE paper itself."""
import json
from pathlib import Path

import docx
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
FIG_DIR = RESULTS / "figures"
OUT_PATH = ROOT / "ECERAG_Experiment_Results_Report.docx"

INK = RGBColor(0x0B, 0x0B, 0x0B)
SECONDARY = RGBColor(0x52, 0x51, 0x4E)
MUTED = RGBColor(0x89, 0x87, 0x81)
ACCENT = RGBColor(0x2A, 0x78, 0xD6)


def shade_cell(cell, hex_color):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = docx.oxml.OxmlElement("w:shd")
    shd.set(qn("w:fill"), hex_color)
    tc_pr.append(shd)


def add_table(doc, headers, rows, col_widths=None):
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Light Grid Accent 1"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = table.rows[0].cells
    for i, h in enumerate(headers):
        hdr[i].text = h
        for p in hdr[i].paragraphs:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for r in p.runs:
                r.bold = True
                r.font.size = Pt(9.5)
        shade_cell(hdr[i], "2A78D6")
        for p in hdr[i].paragraphs:
            for r in p.runs:
                r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    for row_vals in rows:
        cells = table.add_row().cells
        for i, v in enumerate(row_vals):
            cells[i].text = str(v)
            for p in cells[i].paragraphs:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for r in p.runs:
                    r.font.size = Pt(9.5)
    if col_widths:
        for row in table.rows:
            for i, w in enumerate(col_widths):
                row.cells[i].width = Inches(w)
    return table


def add_caption(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(text)
    run.italic = True
    run.font.size = Pt(9)
    run.font.color.rgb = MUTED
    p.paragraph_format.space_after = Pt(14)
    return p


def add_figure(doc, filename, caption, width=6.3):
    doc.add_picture(str(FIG_DIR / filename), width=Inches(width))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_caption(doc, caption)


def pct(x):
    return "—" if x is None else f"{x*100:.0f}%"


def main():
    metrics = json.load(open(RESULTS / "metrics.json", encoding="utf-8"))
    calib = json.load(open(RESULTS / "calibration.json", encoding="utf-8"))

    doc = docx.Document()
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)
    style.font.color.rgb = INK

    for section in doc.sections:
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)

    # ---------------- Title ----------------
    title = doc.add_heading("ECERAG Experiment Results", level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = sub.add_run(
        "A small-scale, fully-implemented pilot of Evidence-Calibrated Enterprise RAG\n"
        "Baseline RAG vs. ECERAG vs. ECERAG+CR, evaluated on a 40-item benchmark"
    )
    run.font.size = Pt(12.5)
    run.font.color.rgb = SECONDARY
    doc.add_paragraph()

    # ---------------- Executive summary ----------------
    doc.add_heading("Executive Summary", level=1)
    doc.add_paragraph(
        "This report presents measured results from a working implementation of the ECERAG "
        "pipeline described in the accompanying paper: hybrid BM25 + dense retrieval, cross-encoder "
        "reranking, a four-signal evidence-sufficiency score (Relevance, Coverage, Agreement, "
        "Trust/Temporal), and a selective Answer / Clarify / Abstain policy — compared against an "
        "unconditional Baseline RAG and a corrective-retrieval variant (ECERAG+CR). Generation used "
        "a small local open-weight model (Qwen2.5-0.5B-Instruct); thresholds were calibrated on a "
        "held-out 12-question split and evaluated on a disjoint 28-question test split."
    )
    bullets = [
        ("Mechanism validated: ", "the Trust/Temporal signal correctly detected superseded "
         "(stale) documents, dropping the sufficiency score from 0.70 to 0.65 when a current-year "
         "figure was replaced with a prior-year one."),
        ("Corrective retrieval works: ", "of the 5 cases that fell into the clarify band across all "
         "conditions, ECERAG+CR's single corrective pass promoted 4 (80%) to a grounded answer and "
         "correctly left 1 as an abstention when re-retrieval still could not clear the bar."),
        ("Accuracy is capped by generator scale, not evidence: ", "most wrong answers came from the "
         "0.5B-parameter model's own arithmetic/reasoning mistakes on correctly-retrieved evidence, "
         "not from missing or poor evidence — so evidence-side gating alone did not reduce selective "
         "risk versus Baseline at this generator scale."),
        ("Threshold calibration was data-starved: ", "with only 12 calibration items, correctness "
         "correlated weakly with the sufficiency score, so the grid search settled on a permissive "
         "threshold (τ_A = 0.45) — a specific, fixable limitation of this pilot's scale, not "
         "of the architecture."),
    ]
    for lead, rest in bullets:
        p = doc.add_paragraph(style="List Bullet")
        r1 = p.add_run(lead)
        r1.bold = True
        p.add_run(rest)

    doc.add_page_break()

    # ---------------- Methodology ----------------
    doc.add_heading("Methodology at a Glance", level=1)
    add_table(
        doc,
        ["Component", "Choice"],
        [
            ["Corpus", "6 public documents, 1,207 chunks (~220 words each): 2 SEC 10-K filings "
                       "(Apple, FY2022 & FY2023 — a natural version pair), NIST AI RMF, OWASP Top 10:2021, "
                       "RFC 2616 (obsolete) & RFC 9110 (current) — a second natural version pair"],
            ["Benchmark", "40 hand-authored questions: 10 single-hop, 10 multi-hop, 9 temporal, "
                          "11 unanswerable — split 12 calibration / 28 test (stratified)"],
            ["Dense retrieval", "all-MiniLM-L6-v2 sentence embeddings"],
            ["Lexical retrieval", "BM25 (rank_bm25), equally weighted with dense"],
            ["Reranker", "cross-encoder/ms-marco-MiniLM-L-6-v2"],
            ["Generator", "Qwen2.5-0.5B-Instruct, local CPU inference"],
            ["Sufficiency weights", f"α=β=γ=δ={calib['weights']['alpha']} (paper's lightweight default)"],
            ["Calibrated thresholds", f"τ_A = {calib['tau_a']},  τ_C = {calib['tau_c']} "
                                       f"(grid search on 12-item calibration split)"],
            ["Grading", "Fully automated / code-based (no LLM judge): numeric + keyword recall "
                        "against gold answers; strict chunk-id match for context relevance"],
        ],
        col_widths=[1.6, 4.9],
    )
    doc.add_paragraph()

    # ---------------- Headline results ----------------
    doc.add_heading("Headline Results", level=1)
    doc.add_paragraph(
        "All figures below are computed on the 28-item held-out test split. Percentages in each bar "
        "are exact fractions given the small N — see the appendix table for counts."
    )
    add_figure(doc, "fig_coverage.png",
               "Figure 1. Coverage (fraction of queries answered) by system and condition.")
    add_figure(doc, "fig_selective_risk.png",
               "Figure 2. Selective risk — error rate among answered queries only — by system and condition. "
               "Lower is better.")
    add_figure(doc, "fig_faithfulness.png",
               "Figure 3. Faithfulness proxy — fraction of generated numeric/entity claims grounded in "
               "retrieved evidence — by system and condition.")

    doc.add_paragraph(
        "Reading these together: coverage and selective risk move in the same direction across systems "
        "in the clean condition (ECERAG trades a little coverage without reducing risk at this generator "
        "scale), while the counterfactual condition is the one place ECERAG's coverage drops more than "
        "Baseline's — exactly where the Trust/Temporal signal is designed to react."
    )

    doc.add_page_break()

    # ---------------- Risk-coverage ----------------
    doc.add_heading("Risk-Coverage Analysis", level=1)
    doc.add_paragraph(
        "The risk-coverage curve sweeps ECERAG's sufficiency score S as a selective-prediction threshold "
        "and traces the resulting risk/coverage operating points, using all 40 benchmark items "
        "(calibration + test) for a better-resolved curve. An ideal selective classifier's curve stays low "
        "at low coverage and rises only as more (harder) items are admitted. Here the curve rises quickly "
        "and stays in the 0.6-0.8 band for most of the range — the visual signature of the same finding "
        "above: at this generator scale, S is only weakly predictive of whether the eventual answer will "
        "be correct."
    )
    add_figure(doc, "fig_risk_coverage.png",
               f"Figure 4. ECERAG risk-coverage curve (AUC = {metrics['risk_coverage_auc_ecerag']:.2f}).")

    # ---------------- Corrective retrieval ----------------
    doc.add_heading("Corrective Retrieval Recovery", level=1)
    doc.add_paragraph(
        "Across all four conditions (112 total question × condition evaluations), 5 fell into ECERAG's "
        "clarify band (2 clean, 1 irrelevant-injection, 2 counterfactual-injection; 0 contradictory-"
        "injection). ECERAG+CR's single corrective pass — an LLM query rewrite followed by one "
        "re-retrieval and re-scoring — resolved 4 of these 5 to a grounded answer."
    )
    add_figure(doc, "fig_corrective_recovery.png",
               "Figure 5. Outcome of ECERAG+CR's corrective-retrieval pass on the 5 clarify-band cases.",
               width=5.8)
    doc.add_paragraph(
        "The one case left as an abstention is a clean illustration of the architecture's intended "
        "fail-safe behavior: under counterfactual injection, the question “Which of the two HTTP RFCs "
        "in this corpus was published more recently?” had its evidence corrupted toward the obsolete "
        "RFC 2616. After query rewriting and re-retrieval, the rescored evidence still did not clear "
        "τ_A, so ECERAG+CR correctly declined — while Baseline RAG, given the identical corrupted "
        "evidence, answered confidently and wrongly: “the second HTTP RFC, RFC 2616, was published more "
        "recently... by approximately 19 years” (wrong on both the ordering and the interval)."
    )

    doc.add_page_break()

    # ---------------- Qualitative example ----------------
    doc.add_heading("Qualitative Example: the Trust/Temporal Signal in Action", level=1)
    doc.add_paragraph(
        "Question: “What is Apple's most recently reported total net sales figure in this corpus, and "
        "for which fiscal year?” (gold answer: $383,285 million, FY2023)."
    )
    add_table(
        doc,
        ["Condition", "Evidence", "Sufficiency score S", "System answer"],
        [
            ["Clean", "Current FY2023 10-K chunks", "0.70", "“...$383.3 billion, for fiscal year 2023” "
                                                             "(numerically right, wrong units vs. gold label)"],
            ["Counterfactual", "Swapped to prior-year FY2022 10-K chunks", "0.65 ↓",
             "“...$394,328 million, for the fiscal year ending September 24, 2022” (stale, wrong)"],
        ],
        col_widths=[1.1, 2.2, 1.1, 2.1],
    )
    doc.add_paragraph()
    doc.add_paragraph(
        "The signal moved in exactly the intended direction when stale evidence was substituted in "
        "(0.70 → 0.65). It did not fall far enough to drop below the calibrated τ_A of 0.45, so the "
        "system still answered with outdated information in this instance — the clearest concrete "
        "evidence in this pilot that the mechanism works correctly while the threshold, calibrated on "
        "only 12 examples, was not tight enough to always act on it."
    )

    # ---------------- Limitations ----------------
    doc.add_heading("Limitations of This Pilot", level=1)
    lims = [
        ("Generator scale dominates errors: ", "with a 0.5B-parameter local model, most wrong answers "
         "were arithmetic or reasoning mistakes made despite correct evidence being retrieved — a failure "
         "mode evidence-side sufficiency gating cannot catch by construction."),
        ("Grading is a lexical-overlap proxy: ", "fully automated (no LLM judge), which produced both a "
         "false positive (right entities, wrong relationship, credited as correct) and a false negative "
         "(“$383.3 billion” marked wrong against “$383,285 million” due to a unit mismatch)."),
        ("Context relevance measured low (9-10%) across all systems: ", "the strict chunk-id match metric "
         "undercounts retrieval quality here, because overlapping fixed-window chunking often surfaces an "
         "informationally equivalent passage rather than the single one annotated as gold."),
        ("Calibration set (12 items) is small: ", "correctness correlated only weakly with S at this "
         "scale, which is why the grid search settled on a permissive threshold rather than a "
         "risk-reducing one."),
    ]
    for lead, rest in lims:
        p = doc.add_paragraph(style="List Bullet")
        r1 = p.add_run(lead)
        r1.bold = True
        p.add_run(rest)
    doc.add_paragraph(
        "These results should be read as evidence that the ECERAG architecture is mechanically sound and "
        "that its Trust/Temporal signal responds correctly to document staleness — not as an accuracy "
        "benchmark comparable to a production deployment with a frontier-scale generator."
    )

    doc.add_page_break()

    # ---------------- Appendix ----------------
    doc.add_heading("Appendix: Full Metrics Table", level=1)
    rows = []
    for cond in ["clean", "irrelevant", "contradictory", "counterfactual"]:
        for sysname in ["baseline", "ecerag", "ecerag_cr"]:
            m = metrics[cond][sysname]
            rows.append([
                cond, {"baseline": "Baseline RAG", "ecerag": "ECERAG", "ecerag_cr": "ECERAG+CR"}[sysname],
                m["n_applicable"], pct(m["coverage"]), pct(m["selective_risk"]),
                pct(m["faithfulness"]), pct(m["context_relevance"]),
                pct(m["abstention_precision"]), pct(m["abstention_recall"]),
            ])
    add_table(
        doc,
        ["Condition", "System", "N", "Coverage", "Sel. Risk", "Faithfulness", "Ctx. Relevance",
         "Abst. Precision", "Abst. Recall"],
        rows,
        col_widths=[0.9, 0.95, 0.35, 0.75, 0.7, 0.85, 0.85, 0.85, 0.75],
    )
    doc.add_paragraph()
    p = doc.add_paragraph()
    r = p.add_run(
        f"Risk-coverage AUC (ECERAG, all 40 items): {metrics['risk_coverage_auc_ecerag']:.3f}   |   "
        f"No-op counts (perturbation not applicable): "
        f"{metrics.get('no_op_counts_by_condition', {})}"
    )
    r.font.size = Pt(9)
    r.font.color.rgb = MUTED

    doc.save(OUT_PATH)
    print(f"Saved report to {OUT_PATH}")


if __name__ == "__main__":
    main()
