"""
Human evaluation of answer correctness, faithfulness and citation support -- the
check reviewers asked for on top of the automated graders.

  export: sample answered items (stratified by question type x condition) into a
          CSV with question, gold answer, generated answer and the cited evidence,
          plus empty label columns. Item order is shuffled and the automated grades
          are kept out of the sheet so annotators are blind to them.
  score:  read back one or more labelled CSVs and report human-vs-human agreement
          (Cohen's kappa) and how well the lexical grader and the LLM judge agree
          with the human majority label.

Label columns (fill with 1 or 0):
  correct     the answer states the asked-for value/entity correctly
  faithful    every claim in the answer is supported by the evidence shown
  citation_ok the cited [doc_id] tags point to passages that support the claims

Usage:
  python code/human_eval.py export results/kaggle/Qwen2.5-7B-Instruct --n 100
  python code/human_eval.py score results/kaggle/Qwen2.5-7B-Instruct annot_A.csv annot_B.csv
"""
import argparse
import csv
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ecerag.bootstrap import load_benchmark
from ecerag.metrics import NOT_SUPPORTED_MARK, answer_correct

LABELS = ["correct", "faithful", "citation_ok"]
SEED = 0


def item_id(rec):
    return f"{rec['qid']}|{rec['condition']}"


def export(run_dir: Path, n: int):
    by_qid = {q["qid"]: q for q in load_benchmark()}
    recs = [json.loads(l) for l in open(run_dir / "records.jsonl", encoding="utf-8")]
    answered = [r for r in recs if r["applicable"] and NOT_SUPPORTED_MARK not in (r["answer"] or "")]
    strata = defaultdict(list)
    for r in answered:
        strata[(r["type"], r["condition"])].append(r)
    rng = random.Random(SEED)
    for items in strata.values():
        rng.shuffle(items)
    sample, keys = [], sorted(strata)
    while len(sample) < n and any(strata[k] for k in keys):  # round-robin across strata
        for k in keys:
            if strata[k] and len(sample) < n:
                sample.append(strata[k].pop())
    rng.shuffle(sample)

    out = run_dir / "human_eval_sheet.csv"
    with open(out, "w", newline="", encoding="utf-8-sig") as f:  # BOM so Excel opens UTF-8 correctly
        w = csv.writer(f)
        w.writerow(["item_id", "question", "gold_answer", "generated_answer", "evidence"] + LABELS + ["notes"])
        for r in sample:
            q = by_qid[r["qid"]]
            evidence = "\n\n".join(f"[{e['doc_id']}] {e['text']}" for e in r["evidence"])
            if r.get("hint"):
                evidence = f"[computed] {r['hint']}\n\n{evidence}"
            gold = q["gold_answer"] if q["answerable"] else "(UNANSWERABLE -- any direct answer is incorrect)"
            w.writerow([item_id(r), q["question"], gold, r["answer"], evidence] + [""] * (len(LABELS) + 1))
    print(f"Wrote {len(sample)} items to {out}")


def cohen_kappa(a, b):
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    pa, pb = sum(a) / n, sum(b) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return (po - pe) / (1 - pe) if pe < 1 else 1.0


def read_labels(path):
    out = {}
    with open(path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if all(row[l].strip() in ("0", "1") for l in LABELS):
                out[row["item_id"]] = {l: int(row[l]) for l in LABELS}
    return out


def score(run_dir: Path, sheets):
    by_qid = {q["qid"]: q for q in load_benchmark()}
    recs = {item_id(r): r for r in map(json.loads, open(run_dir / "records.jsonl", encoding="utf-8"))
            if r["applicable"]}
    annots = [read_labels(s) for s in sheets]
    common = sorted(set.intersection(*(set(a) for a in annots)))
    report = {"n_items": len(common), "n_annotators": len(annots)}
    if len(annots) >= 2:
        report["inter_annotator_kappa"] = {
            l: cohen_kappa([annots[0][i][l] for i in common], [annots[1][i][l] for i in common]) for l in LABELS}
    # majority label (ties -> 0, the conservative reading)
    human = {i: int(sum(a[i]["correct"] for a in annots) * 2 > len(annots)) for i in common}
    lexical = {i: int(by_qid[recs[i]["qid"]]["answerable"]
                      and answer_correct(by_qid[recs[i]["qid"]]["gold_answer"], recs[i]["answer"] or ""))
               for i in common}
    h = [human[i] for i in common]
    report["lexical_vs_human"] = {"agreement": sum(lexical[i] == human[i] for i in common) / len(common),
                                  "kappa": cohen_kappa([lexical[i] for i in common], h),
                                  "false_positives": sum(lexical[i] and not human[i] for i in common),
                                  "false_negatives": sum(human[i] and not lexical[i] for i in common)}
    if all("judge_correct" in recs[i] for i in common):
        judge = {i: int(recs[i]["judge_correct"]) for i in common}
        report["judge_vs_human"] = {"agreement": sum(judge[i] == human[i] for i in common) / len(common),
                                    "kappa": cohen_kappa([judge[i] for i in common], h),
                                    "false_positives": sum(judge[i] and not human[i] for i in common),
                                    "false_negatives": sum(human[i] and not judge[i] for i in common)}
    for l in ("faithful", "citation_ok"):
        report[f"human_{l}_rate"] = sum(a[i][l] for a in annots for i in common) / (len(common) * len(annots))
    json.dump(report, open(run_dir / "human_eval_report.json", "w"), indent=2)
    print(json.dumps(report, indent=2))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("export")
    e.add_argument("run_dir")
    e.add_argument("--n", type=int, default=100)
    s = sub.add_parser("score")
    s.add_argument("run_dir")
    s.add_argument("sheets", nargs="+")
    args = ap.parse_args()
    if args.cmd == "export":
        export(Path(args.run_dir), args.n)
    else:
        score(Path(args.run_dir), args.sheets)


if __name__ == "__main__":
    main()
