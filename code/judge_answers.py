"""
Optional phase 1b: grade every generated answer with an LLM judge, as a semantic
check on the lexical grader (paper Sec. VII-B: the lexical proxy errs both ways).

Run as its own process after run_full.py so the judge never shares GPU memory with
the generator. Use a judge from a different model family than the generator to
avoid self-preference bias. Adds "judge_correct" (and "cr.judge_correct") to each
record and rewrites records.jsonl in place; already-judged records are skipped.

Usage:
  ECERAG_JUDGE_MODEL=microsoft/Phi-3.5-mini-instruct python code/judge_answers.py results/kaggle/<model>
"""
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ecerag.bootstrap import load_benchmark
from ecerag.generator import chat

JUDGE_MODEL = os.environ.get("ECERAG_JUDGE_MODEL", "microsoft/Phi-3.5-mini-instruct")

JUDGE_SYSTEM = (
    "You grade answers to factual questions against a reference answer. A candidate is "
    "CORRECT if it states the same value, entity, or conclusion the question asks for as the "
    "reference -- different units or rounding of the same figure are fine (\"$383.3 billion\" "
    "equals \"$383,285 million\"), and extra correct detail is fine. It is INCORRECT if the "
    "asked-for value is missing, wrong, attributed to the wrong year/document, or contradicted. "
    "Reply with exactly one word: CORRECT or INCORRECT."
)


def judge(question: str, gold: str, answer: str) -> bool:
    out = chat([
        {"role": "system", "content": JUDGE_SYSTEM},
        {"role": "user", "content": f"Question: {question}\nReference answer: {gold}\nCandidate answer: {answer}"},
    ], max_new_tokens=4, model_name=JUDGE_MODEL)
    return bool(re.match(r"\s*CORRECT", out.upper()))


def judge_branch(branch: dict, q: dict):
    ans = branch.get("answer") or ""
    if "judge_correct" in branch:
        return
    if not q["answerable"] or "NOT_SUPPORTED" in ans:
        branch["judge_correct"] = False
    else:
        branch["judge_correct"] = judge(q["question"], q["gold_answer"], ans)


def main():
    run_dir = Path(sys.argv[1])
    path = run_dir / "records.jsonl"
    by_qid = {q["qid"]: q for q in load_benchmark()}
    records = [json.loads(l) for l in open(path, encoding="utf-8")]
    for i, rec in enumerate(records, start=1):
        if rec["applicable"]:
            q = by_qid[rec["qid"]]
            judge_branch(rec, q)
            judge_branch(rec["cr"], q)
        if i % 20 == 0:
            print(f"judged {i}/{len(records)}", flush=True)
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    tmp.replace(path)
    json.dump({"judge_model": JUDGE_MODEL}, open(run_dir / "judge_config.json", "w"), indent=2)
    print(f"Judged with {JUDGE_MODEL}; updated {path}")


if __name__ == "__main__":
    main()
