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
