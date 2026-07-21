"""
Calibrate ECERAG's decision thresholds (tau_A, tau_C) on a held-out calibration
split (30% of the benchmark, stratified by question type), as described in the
paper (Sec. III: "Thresholds tau_A and tau_C are calibrated on validation data").

Sufficiency-score weights are kept at the paper's stated lightweight default
(alpha=beta=gamma=delta=0.25) -- with only ~12 calibration examples, fitting four
continuous weights would overfit; only the two thresholds are grid-searched here.

Objective minimized on the calibration set:
    cost = selective_risk + 0.5 * (1 - coverage)
i.e. balance hallucination reduction against retaining useful coverage.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ecerag.bootstrap import build_retriever, calibration_test_split, load_benchmark
from ecerag.generator import generate_answer
from ecerag.metrics import answer_correct
from ecerag.pipeline import retrieve_and_rerank
from ecerag.sufficiency import DEFAULT_WEIGHTS, sufficiency_score

ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = ROOT / "results" / "calibration.json"

TAU_A_GRID = [round(x, 2) for x in [0.45, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80]]
TAU_C_GRID = [round(x, 2) for x in [0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50]]


def main():
    retriever, chunks, chunks_by_doc = build_retriever()
    benchmark = load_benchmark()
    calibration, test = calibration_test_split(benchmark)

    print(f"Calibration set: {len(calibration)} questions; Test set: {len(test)} questions")

    records = []
    for q in calibration:
        evidence = retrieve_and_rerank(retriever, q["question"])
        scores = sufficiency_score(q["question"], evidence, DEFAULT_WEIGHTS)
        shadow_answer = generate_answer(q["question"], evidence)
        correct_if_answered = answer_correct(q["gold_answer"], shadow_answer) if q["answerable"] else False
        records.append({
            "qid": q["qid"], "type": q["type"], "answerable": q["answerable"],
            "S": scores["S"], "signals": scores, "shadow_answer": shadow_answer,
            "correct_if_answered": correct_if_answered,
        })
        print(f"  {q['qid']:6s} S={scores['S']:.3f}  answerable={q['answerable']}  "
              f"correct_if_answered={correct_if_answered}")

    best = None
    for tau_a in TAU_A_GRID:
        for tau_c in TAU_C_GRID:
            if tau_c >= tau_a:
                continue
            answered = [r for r in records if r["S"] >= tau_a]
            n = len(records)
            coverage = len(answered) / n if n else 0.0
            if answered:
                errors = sum(1 for r in answered if (not r["answerable"]) or (not r["correct_if_answered"]))
                selective_risk = errors / len(answered)
            else:
                selective_risk = 0.0
            cost = selective_risk + 0.5 * (1 - coverage)
            candidate = {"tau_a": tau_a, "tau_c": tau_c, "coverage": coverage,
                         "selective_risk": selective_risk, "cost": cost}
            if best is None or cost < best["cost"]:
                best = candidate

    print("\nBest thresholds on calibration set:", best)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump({
            "weights": DEFAULT_WEIGHTS,
            "tau_a": best["tau_a"],
            "tau_c": best["tau_c"],
            "calibration_metrics": best,
            "calibration_qids": [q["qid"] for q in calibration],
            "test_qids": [q["qid"] for q in test],
            "calibration_records": records,
        }, f, indent=2)
    print(f"\nSaved calibration to {OUT_PATH}")


if __name__ == "__main__":
    main()
