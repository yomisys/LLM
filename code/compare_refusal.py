"""
Paired bootstrap of ECERAG (round-2 variant) against self-refusal RAG -- the comparison
that isolates what the evidence gate adds on top of the generator's own refusal.

Reuses analyze.py's CV loop and bootstrap, restricted to the round-2 variant, so the
ECERAG outcomes match analysis_*.json exactly.

Usage:
  python code/compare_refusal.py results/kaggle/Qwen2.5-7B-Instruct results/kaggle/Qwen2.5-14B-Instruct
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from analyze import (CONDITIONS, K_FOLDS, REPEATS, ROUND2_VARIANT, ROUND2_VARIANTS, bootstrap_ci,
                     fit_params, load_records, run_system, stratified_folds, summarize)
from ecerag.bootstrap import load_benchmark


def compare(run_dir, benchmark, grader):
    by_qid = {q["qid"]: q for q in benchmark}
    recs = load_records(run_dir, by_qid, grader)
    by_cond = defaultdict(list)
    for r in recs:
        by_cond[r["condition"]].append(r)
    clean_by_qid = {r["qid"]: r for r in by_cond["clean"]}
    qids_by_type = defaultdict(list)
    for qid, r in clean_by_qid.items():
        qids_by_type[r["type"]].append(qid)
    variant = ROUND2_VARIANTS[ROUND2_VARIANT]
    outs_by_repeat = defaultdict(list)
    for rep in range(REPEATS):
        fold_of = stratified_folds(qids_by_type, K_FOLDS, seed=rep)
        rep_outs = defaultdict(list)
        for fold in range(K_FOLDS):
            train = [r for qid, r in clean_by_qid.items() if fold_of[qid] != fold]
            p = fit_params(train, variant)
            for cond in CONDITIONS:
                rep_outs[cond] += [run_system(r, "ecerag", p) for r in by_cond[cond] if fold_of[r["qid"]] == fold]
        for cond in CONDITIONS:
            outs_by_repeat[cond].append(rep_outs[cond])
    out = {}
    for cond in CONDITIONS:
        if not by_cond[cond]:
            continue
        refusal = [run_system(r, "baseline", None) for r in by_cond[cond]]
        out[cond] = {"self_refusal": summarize(refusal),
                     "ci_ecerag_minus_refusal": bootstrap_ci(refusal, outs_by_repeat[cond])}
    return out


def main():
    benchmark = load_benchmark()
    result = {}
    for d in sys.argv[1:]:
        run_dir = Path(d)
        for grader in ("judge", "lexical"):
            result.setdefault(run_dir.name, {})[grader] = compare(run_dir, benchmark, grader)
    dest = Path(sys.argv[1]).parent / "refusal_vs_ecerag.json"
    json.dump(result, open(dest, "w"), indent=1)
    for m, gs in result.items():
        for g, conds in gs.items():
            for c, v in conds.items():
                print(m, g, c, "ECERAG - refusal:", [round(x, 3) for x in v["ci_ecerag_minus_refusal"]["b_minus_a"]])
    print("wrote", dest)


if __name__ == "__main__":
    main()
