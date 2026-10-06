"""Collect every number cited in the paper from results/kaggle/*/analysis_*.json into
paper/numbers.json, so each figure in the text is traceable to the analysis outputs."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODELS = ["0.5B", "1.5B", "3B", "7B", "14B"]
GRADERS = ["judge", "lexical"]
CONDS = ["clean", "irrelevant", "contradictory", "counterfactual"]


def load(m, g):
    return json.load(open(ROOT / f"results/kaggle/Qwen2.5-{m}-Instruct/analysis_{g}.json"))


def rc(m):
    return None if not m else {"risk": m["selective_risk"], "cov": m["coverage"],
                               "abst_recall": m["abstention_recall"], "self_declined": m["n_self_declined"]}


out = {"scale": {}, "auc": {}, "round2": {}, "grader_agreement": {}, "paper_protocol": {}, "ablation": {}}
for g in GRADERS:
    for m in MODELS:
        a = load(m, g)
        cv = a["cv_protocol"]
        out["scale"].setdefault(g, {})[m] = {
            "baseline": rc(cv["baseline"]["clean"]),
            "ecerag_equal": rc(cv["variants"]["equal_RCAT"]["clean"]["ecerag"]),
            "baseline_cf": rc(cv["baseline"]["counterfactual"]),
            "ecerag_equal_cf": rc(cv["variants"]["equal_RCAT"]["counterfactual"]["ecerag"]),
        }
        out["auc"].setdefault(g, {})[m] = a["risk_coverage_auc_generator_answered_only"]
        if "grader_agreement" in a and g == "judge":
            out["grader_agreement"][m] = a["grader_agreement"]
        out["paper_protocol"].setdefault(g, {})[m] = {
            "params": a["paper_protocol"]["params"],
            "clean": {s: rc(v) for s, v in a["paper_protocol"]["metrics"]["clean"].items()}}
        out["ablation"].setdefault(g, {})[m] = {
            v: rc(cv["variants"][v]["clean"]["ecerag"]) for v in cv["variants"]}
        if a.get("has_round2"):
            r2 = {}
            for c in CONDS:
                r2[c] = {
                    "unconditional": rc(cv["baseline_unconditional"][c]),
                    "gate_only": rc(cv["variants"]["gate_only_equal_RCAT"][c]["ecerag"]),
                    "refusal_prompt": rc(cv["baseline"][c]),
                    "ecerag_v2": rc(cv["variants"]["v2_equal_RCAT"][c]["ecerag"]),
                    "ecerag_cr_v2": rc(cv["variants"]["v2_equal_RCAT"][c]["ecerag_cr"]),
                    "v1_cr": rc(cv["variants"]["fit_RCATG_veto"][c]["ecerag_cr"]),
                    "ci_gate_vs_uncond": cv["bootstrap_unconditional_vs_gate_only"][c],
                    "ci_v2_vs_uncond": cv["bootstrap_unconditional_vs_round2"][c],
                }
            out["round2"].setdefault(g, {})[m] = r2
json.dump(out, open(ROOT / "paper/numbers.json", "w"), indent=1)
print("wrote paper/numbers.json")
