"""Recompute results/metrics.json from the already-completed results/raw_outputs.jsonl
and results/calibration.json, without re-running retrieval/generation."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ecerag.metrics import aggregate_metrics, risk_coverage_auc

ROOT = Path(__file__).resolve().parent.parent
RAW_PATH = ROOT / "results" / "raw_outputs.jsonl"
CALIB_PATH = ROOT / "results" / "calibration.json"
METRICS_OUT_PATH = ROOT / "results" / "metrics.json"

CONDITIONS = ["clean", "irrelevant", "contradictory", "counterfactual"]


def main():
    calib = json.load(open(CALIB_PATH, encoding="utf-8"))
    all_records = [json.loads(l) for l in open(RAW_PATH, encoding="utf-8")]
    all_records = [r for r in all_records if r.get("applicable", True) and "system" in r]

    metrics_out = {}
    for condition in CONDITIONS:
        metrics_out[condition] = {}
        for system in ("baseline", "ecerag", "ecerag_cr"):
            recs = [r for r in all_records if r["condition"] == condition and r["system"] == system]
            metrics_out[condition][system] = aggregate_metrics(recs)
            metrics_out[condition][system]["n_applicable"] = len(recs)

    ecerag_clean_recs = [r for r in all_records if r["condition"] == "clean" and r["system"] == "ecerag"]
    rc_pool = [{"S": r["S"], "question_answerable": r["answerable"],
                "correct_if_answered": r["correct_if_answered"]} for r in ecerag_clean_recs]
    for cr in calib["calibration_records"]:
        rc_pool.append({"S": cr["S"], "question_answerable": cr["answerable"],
                         "correct_if_answered": cr["correct_if_answered"]})
    metrics_out["risk_coverage_auc_ecerag"] = risk_coverage_auc(rc_pool)
    metrics_out["risk_coverage_curve_n_points"] = len(rc_pool)
    metrics_out["test_n"] = len({r["qid"] for r in all_records})
    metrics_out["tau_a"] = calib["tau_a"]
    metrics_out["tau_c"] = calib["tau_c"]
    metrics_out["weights"] = calib["weights"]

    no_op_counts = {}
    raw_all = [json.loads(l) for l in open(RAW_PATH, encoding="utf-8")]
    for r in raw_all:
        if not r.get("applicable", True):
            no_op_counts[r["condition"]] = no_op_counts.get(r["condition"], 0) + 1
    metrics_out["no_op_counts_by_condition"] = no_op_counts

    with open(METRICS_OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics_out, f, indent=2)
    print(json.dumps(metrics_out, indent=2))


if __name__ == "__main__":
    main()
