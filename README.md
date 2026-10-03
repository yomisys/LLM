# ECERAG: Evidence-Calibrated Enterprise RAG

Code, corpus, benchmark, and experiment results for the paper
"Evidence-Calibrated Enterprise RAG for Hallucination-Resistant Question Answering."

## Contents

- `code/` — the ECERAG pipeline: hybrid retrieval (BM25 + dense), cross-encoder
  reranking, evidence sufficiency scoring (Relevance/Coverage/Agreement/Trust),
  a calculator-assisted local generator, and the Baseline RAG / ECERAG / ECERAG+CR
  systems compared in the paper. Also includes the corpus builder, benchmark
  calibration/experiment runners, figure generation, and paper-rewrite scripts.
- `data/` — the corpus (6 public source documents: two SEC 10-K filings, the
  NIST AI RMF, OWASP Top 10:2021, and paired RFC 2616/RFC 9110), chunked into
  passages, plus the 60-item hand-authored benchmark (`benchmark.json`).
- `papers/` — the 13 works cited in the paper's related-work section,
  downloaded from arXiv.
- `results/` — calibration output, raw per-question experiment outputs,
  aggregated metrics, and generated figures.
- `ECERAG_Conference_Paper.docx` — original paper draft.
- `ECERAG_Conference_Paper_REVISED.docx` — paper rewritten with measured results.
- `ECERAG_Experiment_Results_Report.docx` — standalone results report with visuals.

## Running it

```bash
pip install rank_bm25 sentence-transformers transformers torch pymupdf beautifulsoup4 python-docx
python code/build_corpus.py           # extract + chunk the corpus
python code/calibrate_thresholds.py   # fit tau_A, tau_C on the calibration split
python code/run_experiment.py         # run Baseline RAG / ECERAG / ECERAG+CR on the test split
python code/make_figures.py           # generate report figures
python code/build_report.py           # assemble the results Word report
```

Generation uses a small local open-weight model (configurable via the
`ECERAG_GENERATOR_MODEL` environment variable) — no API keys required.

## Running on Kaggle (GPU) — scale sweep + improved calibration

`kaggle/ecerag_kaggle.ipynb` runs the whole experiment on a free Kaggle GPU. Import it
(Kaggle → Create → New Notebook → File → Import Notebook), set **Accelerator: GPU T4 x2**
and **Internet: On**, then **Save Version → Save & Run All**. It:

1. runs `code/run_full.py` for each generator (Qwen2.5 0.5B / 1.5B / 3B / 7B) — all 60
   questions × 4 conditions, storing evidence, every signal, answers, and the
   corrective-retrieval branch (resumable if the session dies);
2. optionally grades every answer with an LLM judge from another model family
   (`code/judge_answers.py`) as a semantic check on the lexical grader;
3. runs `code/analyze.py`, which reports the paper's original protocol alongside a
   cross-validated one, with an ablation ladder and paired bootstrap CIs, and writes
   `results/kaggle/scale_sweep_*.md` plus per-model `report_*.md`.

What changed relative to the pilot, and why:

| Change | Why |
|---|---|
| GPU generator (fp16, sharded over 2 GPUs), model sweep up to 7B | The paper attributes most errors to the 0.5B generator's reasoning; the sweep tests that directly. |
| Agreement signal detects near-duplicate passages that disagree on a figure; conflict flag `X` vetoes answering | The pilot's check required two passages to share *no* numbers, so a contradictory duplicate (one number changed) was never detected — all three systems scored identically under contradictory injection. |
| Grounding signal `G` (NLI entailment of the drafted answer by the evidence) | R/C/A/T score only the evidence; G scores the generator's use of it — the failure mode the pilot found dominant. |
| Logistic-regression weights, thresholds from observed S values, τ_C tuned on the ECERAG+CR outcome | The paper says weights are fit on validation data (code used 0.25 each); τ_A hit the grid floor; the pilot objective never used τ_C. |
| Repeated stratified 5-fold CV over all 60 items + paired bootstrap CIs | A 12–18 item calibration split is too small; CV makes every item a test item. |
| Grader credits an answer stating the headline gold figure; `answer_in_context` retrieval metric | Correct answers were marked wrong when the gold text appended context figures; strict chunk-id relevance scored 0.09 because overlapping chunks restate the same fact. |
| Counterfactual injection substitutes the *nearest* obsolete-version passage | A random obsolete chunk is rarely a plausible substitute; the nearest one is what a stale index actually serves. |

Optional stronger retrieval: set `ECERAG_EMBED_MODEL=BAAI/bge-base-en-v1.5` and
`ECERAG_RERANKER_MODEL=BAAI/bge-reranker-base`.
