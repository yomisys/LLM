"""
Phase 1 of the Kaggle experiment (GPU): run every benchmark question under every
condition once and store everything any threshold/weight setting could need, so
calibration and evaluation (analyze.py) become pure offline computation.

Per (question, condition) it records the evidence, all sufficiency signals
(R, C, A, T, G, X), the generated answer, and the corrective-retrieval branch
(rewritten query, re-retrieved evidence, its signals and answer). Greedy decoding
makes the Baseline answer and ECERAG's shadow answer the same generation, so each
is produced once here rather than twice as in run_experiment.py.

Resumable: questions already present in the output file are skipped, so a Kaggle
session that dies mid-run can be restarted with the same command.

Usage:
  ECERAG_GENERATOR_MODEL=Qwen/Qwen2.5-7B-Instruct python code/run_full.py [--out DIR] [--limit N]
"""
import argparse
import json
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ecerag.arithmetic import arithmetic_hint
from ecerag.bootstrap import build_retriever, load_benchmark
from ecerag.generator import MODEL_NAME, generate_answer, rewrite_query
from ecerag.perturbations import inject_contradictory, inject_counterfactual, inject_irrelevant
from ecerag.pipeline import retrieve_and_rerank
from ecerag.sufficiency import compute_signals, conflict_flag, grounding_signal

ROOT = Path(__file__).resolve().parent.parent
CONDITIONS = ["clean", "irrelevant", "contradictory", "counterfactual"]
SEED = 13


def slim(evidence):
    return [{"chunk_id": e["chunk_id"], "doc_id": e["doc_id"], "rerank_prob": e.get("rerank_prob"),
             "perturbation": e.get("_perturbation"), "text": e["text"]} for e in evidence]


def assess(query, evidence):
    """Signals + answer for one evidence set."""
    signals = compute_signals(query, evidence)
    signals["X"] = conflict_flag(evidence)
    hint = arithmetic_hint(query, evidence)
    answer = generate_answer(query, evidence)
    signals["G"] = grounding_signal(query, answer, evidence, extra_premises=[hint])
    return {"evidence": slim(evidence), "signals": signals, "hint": hint, "answer": answer}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None, help="output dir (default results/kaggle/<model>)")
    ap.add_argument("--limit", type=int, default=None, help="only the first N questions (smoke test)")
    ap.add_argument("--counterfactual", choices=["nearest", "random"], default="nearest")
    args = ap.parse_args()

    out_dir = Path(args.out) if args.out else ROOT / "results" / "kaggle" / MODEL_NAME.split("/")[-1]
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "records.jsonl"
    done = set()
    if out_path.exists():
        for line in open(out_path, encoding="utf-8"):
            done.add(json.loads(line)["qid"])

    retriever, chunks, chunks_by_doc = build_retriever()
    benchmark = sorted(load_benchmark(), key=lambda q: q["qid"])
    if args.limit:
        benchmark = benchmark[:args.limit]
    print(f"generator={MODEL_NAME}  questions={len(benchmark)}  already done={len(done)}  out={out_path}")

    json.dump({"generator": MODEL_NAME, "counterfactual": args.counterfactual, "seed": SEED},
              open(out_dir / "run_config.json", "w"), indent=2)

    t0 = time.time()
    with open(out_path, "a", encoding="utf-8") as f:
        for qi, q in enumerate(benchmark, start=1):
            if q["qid"] in done:
                continue
            t_q = time.time()
            # per-question RNG so a resumed run perturbs identically to an uninterrupted one
            rng = random.Random(f"{SEED}-{q['qid']}")
            gold_ids = set(q["gold_evidence_chunk_ids"])
            clean = retrieve_and_rerank(retriever, q["question"])
            perturbed = {
                "clean": (clean, True),
                "irrelevant": inject_irrelevant(clean, retriever, q["question"], gold_ids, rng),
                "contradictory": inject_contradictory(clean, gold_ids, rng),
                "counterfactual": inject_counterfactual(
                    clean, chunks_by_doc, rng, retriever if args.counterfactual == "nearest" else None),
            }
            recs = []
            for condition in CONDITIONS:
                evidence, applicable = perturbed[condition]
                rec = {"qid": q["qid"], "type": q["type"], "answerable": q["answerable"],
                       "condition": condition, "applicable": applicable}
                if applicable:
                    rec.update(assess(q["question"], evidence))
                    rewritten = rewrite_query(q["question"], evidence)
                    cr_evidence = retrieve_and_rerank(retriever, rewritten)
                    rec["cr"] = {"rewritten_query": rewritten, **assess(q["question"], cr_evidence)}
                recs.append(rec)
            for rec in recs:  # write a question's records together so resume never sees half a question
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()
            print(f"[{qi}/{len(benchmark)}] {q['qid']} ({q['type']}) {time.time()-t_q:.1f}s "
                  f"(elapsed {time.time()-t0:.0f}s)", flush=True)
    print(f"Done. Records in {out_path}")


if __name__ == "__main__":
    main()
