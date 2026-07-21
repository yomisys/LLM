"""
Main experiment runner. For every test-split question, builds one clean
retrieved/reranked evidence set, then evaluates Baseline RAG, ECERAG, and
ECERAG+CR on: (a) that clean evidence, and (b) three adversarially perturbed
variants of it (irrelevant / contradictory / counterfactual injection).

Writes:
  results/raw_outputs.jsonl  - one line per (qid, condition, system) run
  results/metrics.json       - aggregated metrics per (condition, system)
"""
import json
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ecerag.bootstrap import build_retriever, load_benchmark
from ecerag.metrics import aggregate_metrics, grade_record, risk_coverage_auc
from ecerag.perturbations import inject_contradictory, inject_counterfactual, inject_irrelevant
from ecerag.pipeline import retrieve_and_rerank, run_baseline, run_ecerag, run_ecerag_cr_from_ecerag

ROOT = Path(__file__).resolve().parent.parent
CALIBRATION_PATH = ROOT / "results" / "calibration.json"
RAW_OUT_PATH = ROOT / "results" / "raw_outputs.jsonl"
METRICS_OUT_PATH = ROOT / "results" / "metrics.json"

CONDITIONS = ["clean", "irrelevant", "contradictory", "counterfactual"]
SEED = 13


def strip_evidence_for_json(evidence):
    return [{"chunk_id": e["chunk_id"], "doc_id": e["doc_id"], "rerank_score": e.get("rerank_score")}
            for e in evidence]


def main():
    calib = json.load(open(CALIBRATION_PATH, encoding="utf-8"))
    weights, tau_a, tau_c = calib["weights"], calib["tau_a"], calib["tau_c"]
    test_qids = set(calib["test_qids"])

    retriever, chunks, chunks_by_doc = build_retriever()
    benchmark = load_benchmark()
    by_qid = {q["qid"]: q for q in benchmark}
    test_questions = [by_qid[qid] for qid in test_qids]
    test_questions.sort(key=lambda q: q["qid"])

    print(f"Running experiment on {len(test_questions)} held-out test questions, "
          f"tau_a={tau_a}, tau_c={tau_c}, weights={weights}")

    rng = random.Random(SEED)
    raw_f = open(RAW_OUT_PATH, "w", encoding="utf-8")
    all_records = []
    t_start = time.time()

    for qi, q in enumerate(test_questions, start=1):
        t_q = time.time()
        gold_ids = set(q["gold_evidence_chunk_ids"])
        clean_evidence = retrieve_and_rerank(retriever, q["question"])

        ecerag_clean = run_ecerag(q["question"], clean_evidence, weights, tau_a, tau_c, shadow_generate=True)
        baseline_clean = run_baseline(q["question"], clean_evidence)
        ecerag_cr_clean = run_ecerag_cr_from_ecerag(ecerag_clean, q["question"], weights, tau_a, tau_c, retriever)

        condition_evidence = {"clean": (clean_evidence, True)}
        irr_ev, irr_ok = inject_irrelevant(clean_evidence, retriever, q["question"], gold_ids, rng)
        condition_evidence["irrelevant"] = (irr_ev, irr_ok)
        contra_ev, contra_ok = inject_contradictory(clean_evidence, gold_ids, rng)
        condition_evidence["contradictory"] = (contra_ev, contra_ok)
        cf_ev, cf_ok = inject_counterfactual(clean_evidence, chunks_by_doc, rng)
        condition_evidence["counterfactual"] = (cf_ev, cf_ok)

        for condition in CONDITIONS:
            evidence, applicable = condition_evidence[condition]
            if condition == "clean":
                baseline_res, ecerag_res, ecerag_cr_res = baseline_clean, ecerag_clean, ecerag_cr_clean
            else:
                if not applicable:
                    rec = {"qid": q["qid"], "type": q["type"], "condition": condition,
                           "applicable": False}
                    raw_f.write(json.dumps(rec) + "\n")
                    continue
                baseline_res = run_baseline(q["question"], evidence)
                ecerag_res = run_ecerag(q["question"], evidence, weights, tau_a, tau_c, shadow_generate=True)
                ecerag_cr_res = run_ecerag_cr_from_ecerag(ecerag_res, q["question"], weights, tau_a, tau_c, retriever)

            for res in (baseline_res, ecerag_res, ecerag_cr_res):
                graded = grade_record(res, q)
                out_rec = {
                    "qid": q["qid"], "type": q["type"], "condition": condition,
                    "applicable": True, "answerable": q["answerable"],
                    "system": graded["system"], "decision": graded["decision"],
                    "answer": graded.get("answer"), "declined": graded["declined"],
                    "correct": graded["correct"], "error": graded["error"],
                    "faithfulness": graded["faithfulness"],
                    "context_relevance": graded["context_relevance"],
                    "S": graded.get("S"), "correct_if_answered": graded.get("correct_if_answered"),
                    "evidence": strip_evidence_for_json(evidence),
                }
                raw_f.write(json.dumps(out_rec) + "\n")
                all_records.append(out_rec)
        raw_f.flush()
        print(f"[{qi}/{len(test_questions)}] {q['qid']} ({q['type']}) done in {time.time()-t_q:.1f}s "
              f"(elapsed {time.time()-t_start:.0f}s)")

    raw_f.close()

    # Aggregate metrics per (condition, system)
    metrics_out = {}
    for condition in CONDITIONS:
        metrics_out[condition] = {}
        for system in ("baseline", "ecerag", "ecerag_cr"):
            recs = [r for r in all_records if r["condition"] == condition and r["system"] == system]
            metrics_out[condition][system] = aggregate_metrics(recs)
            metrics_out[condition][system]["n_applicable"] = len(recs)

    # Risk-coverage AUC for ECERAG using clean-condition test records plus the
    # calibration-set records already computed during threshold search (more points
    # -> a better-resolved curve; this is descriptive analysis, not model selection).
    ecerag_clean_recs = [r for r in all_records if r["condition"] == "clean" and r["system"] == "ecerag"]
    rc_pool = [{"S": r["S"], "question_answerable": r["answerable"],
                "correct_if_answered": r["correct_if_answered"]} for r in ecerag_clean_recs]
    for cr in calib["calibration_records"]:
        rc_pool.append({"S": cr["S"], "question_answerable": cr["answerable"],
                         "correct_if_answered": cr["correct_if_answered"]})
    metrics_out["risk_coverage_auc_ecerag"] = risk_coverage_auc(rc_pool)
    metrics_out["risk_coverage_curve_n_points"] = len(rc_pool)
    metrics_out["test_n"] = len(test_questions)
    metrics_out["tau_a"] = tau_a
    metrics_out["tau_c"] = tau_c
    metrics_out["weights"] = weights

    with open(METRICS_OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics_out, f, indent=2)

    print(f"\nDone in {time.time()-t_start:.0f}s. Wrote {RAW_OUT_PATH} and {METRICS_OUT_PATH}")


if __name__ == "__main__":
    main()
