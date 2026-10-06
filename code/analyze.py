"""
Phase 2 (CPU, seconds): calibrate and evaluate from run_full.py's records.

Two protocols are reported side by side:

  paper  - exactly the pilot's method: equal weights over R/C/A/T, thresholds
           grid-searched (tau_A in [0.45, 0.80]) on the fixed 30% calibration split,
           evaluated on the remaining test split.
  cv     - repeated stratified K-fold over all questions. Inside each training fold:
           logistic-regression weights over the signals (the paper states weights are
           "fit on a labelled validation set"; the pilot code fixed them at 0.25),
           tau_A chosen from the observed S values rather than a fixed grid, and tau_C
           chosen on the ECERAG+CR outcome (the pilot objective never looked at tau_C,
           so it always took the grid minimum). Every question is scored out-of-fold,
           so all 60 items are test items, and repeats average out split luck.

The cv protocol includes an ablation ladder so each change's contribution is visible:
  equal_RCAT -> fit_RCAT -> fit_RCATG (+ grounding signal) -> fit_RCATG_veto (+ conflict veto)

Usage:
  python code/analyze.py results/kaggle/Qwen2.5-7B-Instruct [more run dirs...] [--grader judge]
"""
import argparse
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ecerag.bootstrap import calibration_test_split, load_benchmark
from ecerag.metrics import (NOT_SUPPORTED_MARK, aggregate_metrics, answer_correct, answer_in_context,
                            context_relevance, faithfulness_score, risk_coverage_auc)
from ecerag.sufficiency import DEFAULT_WEIGHTS, combine

CONDITIONS = ["clean", "irrelevant", "contradictory", "counterfactual"]
LAMBDA = 0.5          # cost = selective_risk + LAMBDA * (1 - coverage), as in the pilot
MIN_COVERAGE = 0.25   # never calibrate to "abstain on everything" (zero risk, useless system)
K_FOLDS, REPEATS = 5, 20
N_BOOT = 2000

PAPER_TAU_A_GRID = [0.45, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80]
PAPER_TAU_C_GRID = [0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50]

VARIANTS = {
    "equal_RCAT":     {"fit": False, "features": ["R", "C", "A", "T"], "veto": False},
    "fit_RCAT":       {"fit": True, "features": ["R", "C", "A", "T"], "veto": False},
    "fit_RCATG":      {"fit": True, "features": ["R", "C", "A", "T", "G"], "veto": False},
    "fit_RCATG_veto": {"fit": True, "features": ["R", "C", "A", "T", "G"], "veto": True},
}
MAIN_VARIANT = "fit_RCATG_veto"
# Round 2 (needs augment.jsonl): equal weights -- fitting did not beat them at n=60 --
# with conflicts quarantined instead of refused and the merged, margin-gated CR pass.
POLICY_FLAGS = ("quarantine", "cr_merged", "cr_margin", "noref_answers")
ROUND2_VARIANT = "v2_equal_RCAT"
ROUND2_VARIANTS = {
    ROUND2_VARIANT: {"fit": False, "features": ["R", "C", "A", "T"], "veto": True,
                     "quarantine": True, "cr_merged": True, "cr_margin": 0.05},
    # isolates the paper's mechanism: R/C/A/T gate (+ conflict veto) over answers from the
    # no-refusal prompt, compared against the unconditional baseline on the same answers
    "gate_only_equal_RCAT": {"fit": False, "features": ["R", "C", "A", "T"], "veto": True,
                             "noref_answers": True},
}
# leave-one-signal-out: the main variant with each signal removed in turn
for _sig in ["R", "C", "A", "T", "G"]:
    VARIANTS[f"main_minus_{_sig}"] = {**VARIANTS[MAIN_VARIANT],
                                      "features": [f for f in VARIANTS[MAIN_VARIANT]["features"] if f != _sig]}


# ---------------------------------------------------------------- grading

def grade_branch(branch, q, grader):
    ans = branch.get("answer") or ""
    self_declined = NOT_SUPPORTED_MARK in ans
    if grader == "judge":
        if "judge_correct" not in branch:
            sys.exit("records have no judge_correct field -- run judge_answers.py first")
        correct = branch["judge_correct"]
    else:
        correct = q["answerable"] and answer_correct(q["gold_answer"], ans)
    return {
        "self_declined": self_declined,
        "correct": bool(correct and q["answerable"] and not self_declined),
        "faithfulness": faithfulness_score(ans, branch["evidence"]),
        "context_relevance": context_relevance(branch["evidence"], q["gold_evidence_chunk_ids"]),
        "answer_in_context": answer_in_context(branch["evidence"], q.get("gold_answer"),
                                               q["gold_evidence_chunk_ids"]),
    }


def load_records(run_dir, by_qid, grader):
    recs = [json.loads(l) for l in open(run_dir / "records.jsonl", encoding="utf-8")]
    recs = [r for r in recs if r["applicable"]]
    for r in recs:
        q = by_qid[r["qid"]]
        r["graded"] = grade_branch(r, q, grader)
        r["cr"]["graded"] = grade_branch(r["cr"], q, grader)
    aug_path = run_dir / "augment.jsonl"
    if aug_path.exists():
        augs = {a["key"]: a for a in map(json.loads, open(aug_path, encoding="utf-8"))}
        for r in recs:
            a = augs.get(f"{r['qid']}|{r['condition']}")
            if a is None:
                continue
            q = by_qid[r["qid"]]
            r["noref"] = {**a["noref"], "evidence": r["evidence"]}
            for name in ("noref", "quarantine", "cr_merged"):
                branch = r["noref"] if name == "noref" else a.get(name)
                if branch:
                    branch["graded"] = grade_branch(branch, q, grader)
                    r[name] = branch
    return recs


# ---------------------------------------------------------------- policy

def decide(S, signals, p):
    if S >= p["tau_a"] and not (p["veto"] and signals.get("X", 0) >= 1):
        return "answer"
    return "clarify" if S >= p["tau_c"] else "abstain"


def outcome(r, decision, branch, S):
    g = branch["graded"]
    declined = decision != "answer" or g["self_declined"]
    o = {"qid": r["qid"], "decision": decision, "declined": declined, "S": S,
         "question_answerable": r["answerable"], "correct_if_answered": r["graded"]["correct"],
         "context_relevance": g["context_relevance"], "answer_in_context": g["answer_in_context"]}
    if declined:
        o.update(correct=None, error=False, faithfulness=None)
    else:
        o.update(correct=g["correct"], error=not g["correct"], faithfulness=g["faithfulness"])
    return o


def run_system(r, system, p):
    if system == "baseline":
        return outcome(r, "answer", r, None)
    if system == "baseline_unconditional":  # same evidence, prompt without the refusal clause
        return outcome(r, "answer", r["noref"], None)
    S = combine(r["signals"], p["weights"])
    d = decide(S, r["signals"], p)
    if p.get("noref_answers"):
        # the evidence gate alone: the generator may not refuse, so every decline is the gate's
        return outcome(r, d, r["noref"], S)
    vetoed = d != "answer" and S >= p["tau_a"]  # sufficient score, blocked only by the conflict veto
    if vetoed and p.get("quarantine") and r.get("quarantine"):
        # answer from the evidence left after dropping both conflicting passages
        qb = r["quarantine"]
        Sq = combine(qb["signals"], p["weights"])
        if decide(Sq, qb["signals"], p) == "answer":
            o = outcome(r, "answer", qb, Sq)
            o["quarantined"] = True
            return o
    if system == "ecerag" or d != "clarify":
        return outcome(r, d, r, S)
    # ECERAG+CR clarify band: one corrective retrieval pass, rescored against the original query.
    # v2 keeps the original evidence (merged + conflicts quarantined) and accepts the pass
    # only when it scores clearly better than what it replaces.
    branch = r.get("cr_merged") if p.get("cr_merged") else r["cr"]
    if branch is None:
        return outcome(r, "abstain", r, S)
    S2 = combine(branch["signals"], p["weights"])
    accept = decide(S2, branch["signals"], p) == "answer"
    if "cr_margin" in p:  # v2 only; the pilot's CR accepted any pass that cleared tau_A
        accept = accept and S2 >= S + p["cr_margin"]
    o = outcome(r, "answer" if accept else "abstain", branch, S2)
    o["corrective_pass"] = True
    return o


def cost(outs):
    answered = [o for o in outs if not o["declined"]]
    coverage = len(answered) / len(outs)
    if coverage < MIN_COVERAGE:
        return float("inf")
    risk = sum(o["error"] for o in answered) / len(answered)
    return risk + LAMBDA * (1 - coverage)


# ---------------------------------------------------------------- calibration

def fit_weights(train, features):
    X = np.array([[r["signals"][f] for f in features] for r in train])
    y = np.array([r["graded"]["correct"] for r in train])
    if len(set(y.tolist())) < 2:
        return dict(DEFAULT_WEIGHTS)
    lr = LogisticRegression(C=1.0, max_iter=1000).fit(X, y)
    return {"mode": "logistic", "features": features,
            "coef": lr.coef_[0].tolist(), "intercept": float(lr.intercept_[0])}


def fit_params(train, variant):
    weights = fit_weights(train, variant["features"]) if variant["fit"] else dict(DEFAULT_WEIGHTS)
    S_vals = sorted({combine(r["signals"], weights) for r in train})
    candidates = [0.0] + S_vals  # thresholds at observed scores: no grid floor/ceiling
    best_a, best_cost = 0.0, float("inf")  # 0.0 = answer everything, if nothing meets MIN_COVERAGE
    for ta in candidates:
        p = {"weights": weights, "tau_a": ta, "tau_c": 0.0, "veto": variant["veto"],
             **{k: variant[k] for k in POLICY_FLAGS if k in variant}}
        c = cost([run_system(r, "ecerag", p) for r in train])
        if c < best_cost:
            best_a, best_cost = ta, c
    best_c, best_cost_cr = best_a, float("inf")
    for tc in [t for t in candidates if t <= best_a]:
        p = {"weights": weights, "tau_a": best_a, "tau_c": tc, "veto": variant["veto"],
             **{k: variant[k] for k in POLICY_FLAGS if k in variant}}
        c = cost([run_system(r, "ecerag_cr", p) for r in train])
        if c < best_cost_cr:
            best_c, best_cost_cr = tc, c
    return {"weights": weights, "tau_a": best_a, "tau_c": best_c, "veto": variant["veto"],
            **{k: variant[k] for k in POLICY_FLAGS if k in variant}}


def fit_paper(train):
    """The pilot's calibrate_thresholds.py, reproduced exactly (incl. ignoring tau_c)."""
    best = None
    for ta in PAPER_TAU_A_GRID:
        for tc in PAPER_TAU_C_GRID:
            if tc >= ta:
                continue
            answered = [r for r in train if combine(r["signals"], DEFAULT_WEIGHTS) >= ta]
            coverage = len(answered) / len(train)
            risk = (sum(1 for r in answered if not r["answerable"] or not r["graded"]["correct"])
                    / len(answered)) if answered else 0.0
            c = risk + LAMBDA * (1 - coverage)
            if best is None or c < best[0]:
                best = (c, ta, tc)
    return {"weights": dict(DEFAULT_WEIGHTS), "tau_a": best[1], "tau_c": best[2], "veto": False}


# ---------------------------------------------------------------- evaluation helpers

def summarize(outs):
    m = aggregate_metrics(outs)
    aic = [o["answer_in_context"] for o in outs if o["answer_in_context"] is not None]
    m["answer_in_context"] = float(np.mean(aic)) if aic else None
    m["n_errors"] = sum(1 for o in outs if not o["declined"] and o["error"])
    # declines that came from the generator's own NOT_SUPPORTED reply rather than the gate;
    # both systems share the same prompt, so this is reported separately, not hidden
    m["n_self_declined"] = sum(1 for o in outs if o["decision"] == "answer" and o["declined"])
    return m


def mean_metrics(list_of_metrics):
    out = {}
    for k in list_of_metrics[0]:
        vals = [m[k] for m in list_of_metrics if m.get(k) is not None]
        out[k] = float(np.mean(vals)) if vals else None
    return out


def stratified_folds(qids_by_type, k, seed):
    rng = random.Random(seed)
    fold_of = {}
    offset = 0
    for qtype in sorted(qids_by_type):
        items = sorted(qids_by_type[qtype])
        rng.shuffle(items)
        for i, qid in enumerate(items):
            fold_of[qid] = (i + offset) % k
        offset += len(items)  # rotate so small types don't all land in fold 0
    return fold_of


def selective_risk(outs):
    answered = [o for o in outs if not o["declined"]]
    return sum(o["error"] for o in answered) / len(answered) if answered else float("nan")


def bootstrap_ci(outs_a, outs_b_by_repeat, seed=0):
    """95% CI for selective risk of a, of b, and the paired difference b - a,
    resampling questions with replacement. b is a cross-validated system, so within
    each resample its risk is averaged over all CV repeats -- a single repeat's fold
    assignment is luck of the split and can sit at either end of the range."""
    by_q_a = {o["qid"]: o for o in outs_a}
    by_q_b = [{o["qid"]: o for o in outs} for outs in outs_b_by_repeat]
    qids = sorted(set(by_q_a).intersection(*by_q_b))
    rng = np.random.default_rng(seed)
    ra, rb, diff = [], [], []
    for _ in range(N_BOOT):
        sample = rng.choice(qids, size=len(qids), replace=True)
        a = selective_risk([by_q_a[q] for q in sample])
        b = float(np.nanmean([selective_risk([bq[q] for q in sample]) for bq in by_q_b]))
        ra.append(a), rb.append(b), diff.append(b - a)

    def ci(v):
        v = np.array(v)
        v = v[~np.isnan(v)]
        return [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))] if len(v) else None
    return {"a": ci(ra), "b": ci(rb), "b_minus_a": ci(diff),
            "p_b_not_better": float(np.mean(np.array(diff)[~np.isnan(diff)] >= 0))}


def auc_gain_ci(points, seed=0):
    """95% bootstrap CI (over questions) for how much lower the risk-coverage AUC of a
    ranking is than a random ranking's (whose expected AUC is the overall error rate).
    A CI above 0 means the score ranks wrong answers below right ones better than chance."""
    rng = np.random.default_rng(seed)
    gains = []
    for _ in range(N_BOOT):
        sample = [points[i] for i in rng.integers(0, len(points), len(points))]
        err = np.mean([(not p["question_answerable"]) or (not p["correct_if_answered"]) for p in sample])
        gains.append(err - risk_coverage_auc(sample))
    return [float(np.percentile(gains, 2.5)), float(np.percentile(gains, 97.5))] if points else None


# ---------------------------------------------------------------- main analysis

def analyze_run(run_dir, benchmark, grader):
    by_qid = {q["qid"]: q for q in benchmark}
    recs = load_records(run_dir, by_qid, grader)
    by_cond = defaultdict(list)
    for r in recs:
        by_cond[r["condition"]].append(r)
    clean_by_qid = {r["qid"]: r for r in by_cond["clean"]}
    result = {"run_dir": str(run_dir), "grader": grader, "n_questions": len(clean_by_qid)}
    has_round2 = all("noref" in r for r in recs)
    variants = {**VARIANTS, **(ROUND2_VARIANTS if has_round2 else {})}
    result["has_round2"] = has_round2
    cfg = run_dir / "run_config.json"
    if cfg.exists():
        result["run_config"] = json.load(open(cfg))

    # --- paper protocol
    calib, test = calibration_test_split(benchmark)
    calib_ids = {q["qid"] for q in calib} & set(clean_by_qid)
    test_ids = {q["qid"] for q in test} & set(clean_by_qid)
    p_paper = fit_paper([clean_by_qid[q] for q in sorted(calib_ids)]) if calib_ids else None
    paper = {"params": p_paper, "n_calibration": len(calib_ids), "n_test": len(test_ids), "metrics": {}}
    for cond in CONDITIONS if p_paper else []:
        rs = [r for r in by_cond[cond] if r["qid"] in test_ids]
        paper["metrics"][cond] = {s: summarize([run_system(r, s, p_paper) for r in rs])
                                  for s in ("baseline", "ecerag", "ecerag_cr")} if rs else {}
    result["paper_protocol"] = paper

    # --- cross-validated protocol
    qids_by_type = defaultdict(list)
    for qid, r in clean_by_qid.items():
        qids_by_type[r["type"]].append(qid)
    per_repeat = {v: defaultdict(lambda: defaultdict(list)) for v in variants}
    outs_by_repeat = {v: defaultdict(list) for v in variants}  # variant -> cond -> [ECERAG outcomes per repeat]
    oof_S = defaultdict(list)
    fold_params = []
    for rep in range(REPEATS):
        fold_of = stratified_folds(qids_by_type, K_FOLDS, seed=rep)
        rep_outs = {v: defaultdict(lambda: defaultdict(list)) for v in variants}
        for fold in range(K_FOLDS):
            train = [r for qid, r in clean_by_qid.items() if fold_of[qid] != fold]
            for vname, variant in variants.items():
                p = fit_params(train, variant)
                if rep == 0 and vname == MAIN_VARIANT:
                    fold_params.append(p)
                for cond in CONDITIONS:
                    for r in by_cond[cond]:
                        if fold_of[r["qid"]] != fold:
                            continue
                        for s in ("ecerag", "ecerag_cr"):
                            rep_outs[vname][cond][s].append(run_system(r, s, p))
                        if vname == MAIN_VARIANT and cond == "clean":
                            oof_S[r["qid"]].append(combine(r["signals"], p["weights"]))
        for vname in variants:
            for cond in CONDITIONS:
                for s in ("ecerag", "ecerag_cr"):
                    per_repeat[vname][cond][s].append(summarize(rep_outs[vname][cond][s]))
        for vname in variants:
            for cond in CONDITIONS:
                outs_by_repeat[vname][cond].append(rep_outs[vname][cond]["ecerag"])

    cv = {"k_folds": K_FOLDS, "repeats": REPEATS, "main_variant": MAIN_VARIANT,
          "example_fold_params": fold_params, "baseline": {}, "variants": {}}
    for cond in CONDITIONS:
        cv["baseline"][cond] = summarize([run_system(r, "baseline", None) for r in by_cond[cond]])
    for vname in variants:
        cv["variants"][vname] = {cond: {s: mean_metrics(per_repeat[vname][cond][s])
                                        for s in ("ecerag", "ecerag_cr")}
                                 for cond in CONDITIONS if by_cond[cond]}
    cv["bootstrap_baseline_vs_main"] = {}
    for cond in CONDITIONS:
        if by_cond[cond]:
            base = [run_system(r, "baseline", None) for r in by_cond[cond]]
            cv["bootstrap_baseline_vs_main"][cond] = bootstrap_ci(base, outs_by_repeat[MAIN_VARIANT][cond])
    if has_round2:
        # the reviewers' requested comparison: the gate vs a baseline that never refuses
        cv["baseline_unconditional"] = {}
        cv["bootstrap_unconditional_vs_round2"] = {}
        for cond in CONDITIONS:
            if by_cond[cond]:
                base_u = [run_system(r, "baseline_unconditional", None) for r in by_cond[cond]]
                cv["baseline_unconditional"][cond] = summarize(base_u)
                cv["bootstrap_unconditional_vs_round2"][cond] = bootstrap_ci(
                    base_u, outs_by_repeat[ROUND2_VARIANT][cond])
        cv["bootstrap_unconditional_vs_gate_only"] = {
            cond: bootstrap_ci([run_system(r, "baseline_unconditional", None) for r in by_cond[cond]],
                               outs_by_repeat["gate_only_equal_RCAT"][cond])
            for cond in CONDITIONS if by_cond[cond]}
    result["cv_protocol"] = cv

    # --- risk-coverage AUC (lower is better) for the score used as a selective-prediction ranking
    def pool(score_of, items=None):
        return [{"S": score_of(r), "question_answerable": r["answerable"],
                 "correct_if_answered": r["graded"]["correct"]} for r in (items or clean_by_qid.values())]
    errs = [not r["graded"]["correct"] for r in clean_by_qid.values()]
    paper_S = lambda r: combine(r["signals"], DEFAULT_WEIGHTS)
    fitted_S = lambda r: float(np.mean(oof_S[r["qid"]]))  # out-of-fold, averaged over repeats
    # Same rankings restricted to questions the generator actually answered. G is 0 for every
    # NOT_SUPPORTED reply and those count as errors, so on all items G partly gets credit for
    # ranking the generator's own refusals last; this subset removes that advantage.
    gen_answered = [r for r in clean_by_qid.values() if not r["graded"]["self_declined"]]
    result["risk_coverage_auc_generator_answered_only"] = {
        "n": len(gen_answered),
        "paper_S_equal_RCAT": risk_coverage_auc(pool(paper_S, gen_answered)),
        "cv_S_main_variant_out_of_fold": risk_coverage_auc(pool(fitted_S, gen_answered)),
        "G_alone": risk_coverage_auc(pool(lambda r: r["signals"]["G"], gen_answered)),
        **{f"{sig}_alone": risk_coverage_auc(pool(lambda r, sig=sig: r["signals"][sig], gen_answered))
           for sig in ("R", "C", "A", "T")},
        "random_ranking_expected": float(np.mean([not r["graded"]["correct"] for r in gen_answered]))
        if gen_answered else None,
        "paper_S_gain_over_random_ci95": auc_gain_ci(pool(paper_S, gen_answered)),
    }
    result["risk_coverage_auc"] = {
        "paper_S_equal_RCAT": risk_coverage_auc(pool(lambda r: combine(r["signals"], DEFAULT_WEIGHTS))),
        "paper_S_equal_RCAT_test_split_only": risk_coverage_auc(
            [p for p, r in zip(pool(lambda r: combine(r["signals"], DEFAULT_WEIGHTS)), clean_by_qid.values())
             if r["qid"] in test_ids]),
        "cv_S_main_variant_out_of_fold": risk_coverage_auc(pool(fitted_S)),
        "G_alone": risk_coverage_auc(pool(lambda r: r["signals"]["G"])),
        "random_ranking_expected": float(np.mean(errs)),
    }

    # --- grader agreement, if the LLM judge has been run
    pairs = [(answer_correct(by_qid[r["qid"]]["gold_answer"], r["answer"] or ""), r["judge_correct"])
             for r in recs if r["answerable"] and "judge_correct" in r and NOT_SUPPORTED_MARK not in (r["answer"] or "")]
    if pairs:
        result["grader_agreement"] = {
            "n": len(pairs),
            "agreement": float(np.mean([a == b for a, b in pairs])),
            "lexical_only_correct": sum(1 for a, b in pairs if a and not b),
            "judge_only_correct": sum(1 for a, b in pairs if b and not a),
        }
    return result


def fmt(x, pct=False):
    if x is None:
        return "–"
    return f"{100*x:.0f}%" if pct else f"{x:.2f}"


def markdown_report(res):
    name = res.get("run_config", {}).get("generator", res["run_dir"])
    lines = [f"## {name} (grader: {res['grader']}, n={res['n_questions']})", ""]
    cv = res["cv_protocol"]
    lines += ["### Cross-validated (all questions out-of-fold, mean of "
              f"{cv['repeats']}x{cv['k_folds']}-fold)", "",
              "| condition | system | coverage | selective risk | errors | self-declined | faithfulness | abstain recall | answer-in-context |",
              "|---|---|---|---|---|---|---|---|---|"]
    for cond in CONDITIONS:
        if cond not in cv["baseline"] or not cv["baseline"][cond]:
            continue
        rows = [("baseline", cv["baseline"][cond])]
        for s in ("ecerag", "ecerag_cr"):
            rows.append((s, cv["variants"][MAIN_VARIANT][cond][s]))
        for s, m in rows:
            lines.append(f"| {cond} | {s} | {fmt(m['coverage'], True)} | {fmt(m['selective_risk'])} | "
                         f"{m['n_errors']:.1f} | {m['n_self_declined']:.1f} | {fmt(m['faithfulness'])} | {fmt(m['abstention_recall'])} | "
                         f"{fmt(m['answer_in_context'], True)} |")
    lines += ["", "### Ablation (ECERAG selective risk / coverage, clean and perturbed)", "",
              "| variant | " + " | ".join(CONDITIONS) + " |", "|---|" + "---|" * len(CONDITIONS)]
    lines.append("| baseline | " + " | ".join(
        f"{fmt(cv['baseline'][c]['selective_risk'])} / {fmt(cv['baseline'][c]['coverage'], True)}"
        if cv["baseline"].get(c) else "–" for c in CONDITIONS) + " |")
    for vname in VARIANTS:
        cells = []
        for c in CONDITIONS:
            m = cv["variants"][vname].get(c, {}).get("ecerag")
            cells.append(f"{fmt(m['selective_risk'])} / {fmt(m['coverage'], True)}" if m else "–")
        lines.append(f"| {vname} | " + " | ".join(cells) + " |")
    if res.get("has_round2"):
        u, v2 = cv["baseline_unconditional"], cv["variants"][ROUND2_VARIANT]
        lines += ["", "### Round 2: unconditional baseline vs ECERAG v2 (equal weights, conflict quarantine, merged CR)", "",
                  "| condition | system | coverage | selective risk | errors | self-declined | abstain recall |",
                  "|---|---|---|---|---|---|---|"]
        for cond in CONDITIONS:
            if cond not in u:
                continue
            g = cv["variants"]["gate_only_equal_RCAT"][cond]["ecerag"]
            for name, m in (("baseline (refusal prompt)", cv["baseline"][cond]), ("baseline (unconditional)", u[cond]),
                            ("evidence gate only (unconditional answers)", g),
                            ("ECERAG v2", v2[cond]["ecerag"]), ("ECERAG+CR v2", v2[cond]["ecerag_cr"])):
                lines.append(f"| {cond} | {name} | {fmt(m['coverage'], True)} | {fmt(m['selective_risk'])} | "
                             f"{m['n_errors']:.1f} | {m['n_self_declined']:.1f} | {fmt(m['abstention_recall'])} |")
        lines += ["", "| condition | unconditional | ECERAG v2 | v2 − unconditional | P(v2 not better) |",
                  "|---|---|---|---|---|"]
        for cond, b in cv["bootstrap_unconditional_vs_round2"].items():
            f2 = lambda ci: f"[{ci[0]:.2f}, {ci[1]:.2f}]" if ci else "–"
            lines.append(f"| {cond} | {f2(b['a'])} | {f2(b['b'])} | {f2(b['b_minus_a'])} | {b['p_b_not_better']:.2f} |")
        lines += ["", "| condition | unconditional | gate only | gate − unconditional | P(gate not better) |",
                  "|---|---|---|---|---|"]
        for cond, b in cv["bootstrap_unconditional_vs_gate_only"].items():
            lines.append(f"| {cond} | {f2(b['a'])} | {f2(b['b'])} | {f2(b['b_minus_a'])} | {b['p_b_not_better']:.2f} |")
    lines += ["", "### Paired bootstrap, baseline vs ECERAG (selective risk, 95% CI)", "",
              "| condition | baseline | ECERAG | ECERAG − baseline | P(ECERAG not better) |", "|---|---|---|---|---|"]
    for cond, b in cv["bootstrap_baseline_vs_main"].items():
        f2 = lambda ci: f"[{ci[0]:.2f}, {ci[1]:.2f}]" if ci else "–"
        lines.append(f"| {cond} | {f2(b['a'])} | {f2(b['b'])} | {f2(b['b_minus_a'])} | {b['p_b_not_better']:.2f} |")
    auc = res["risk_coverage_auc"]
    lines += ["", "### Risk-coverage AUC (lower is better)", ""] + [f"- {k}: {fmt(v)}" for k, v in auc.items()]
    sub = res["risk_coverage_auc_generator_answered_only"]
    lines += ["", f"### Risk-coverage AUC on the {sub['n']} questions the generator answered (no credit for "
              "ranking its own refusals)", ""] + [f"- {k}: {fmt(v) if not isinstance(v, list) else f'[{v[0]:.2f}, {v[1]:.2f}]'}"
                                                 for k, v in sub.items() if k != "n"]
    pp = res["paper_protocol"]
    if not pp["params"]:
        return "\n".join(lines) + "\n"
    lines += ["", f"### Paper protocol (fixed split: {pp['n_calibration']} calibration / {pp['n_test']} test, "
              f"tau_A={pp['params']['tau_a']}, tau_C={pp['params']['tau_c']})", "",
              "| condition | system | coverage | selective risk |", "|---|---|---|---|"]
    for cond, systems in pp["metrics"].items():
        for s, m in systems.items():
            lines.append(f"| {cond} | {s} | {fmt(m['coverage'], True)} | {fmt(m['selective_risk'])} |")
    if "grader_agreement" in res:
        g = res["grader_agreement"]
        lines += ["", f"### Grader agreement (lexical vs judge): {fmt(g['agreement'], True)} on {g['n']} answers; "
                  f"lexical-only correct {g['lexical_only_correct']}, judge-only correct {g['judge_only_correct']}"]
    return "\n".join(lines) + "\n"


def scale_table(results):
    lines = ["# Generator-scale sweep (cross-validated, main variant)", "",
             "| generator | grader | clean: baseline risk / cov | clean: ECERAG risk / cov | clean: ECERAG+CR risk / cov "
             "| contradictory: base → ECERAG risk | counterfactual: base → ECERAG risk | RC-AUC paper S → fitted S |",
             "|---|---|---|---|---|---|---|---|"]
    for res in results:
        cv = res["cv_protocol"]
        v = cv["variants"][MAIN_VARIANT]
        b = cv["baseline"]

        def rc(m):
            return f"{fmt(m['selective_risk'])} / {fmt(m['coverage'], True)}" if m else "–"

        def arrow(cond):
            if not b.get(cond) or cond not in v:
                return "–"
            return f"{fmt(b[cond]['selective_risk'])} → {fmt(v[cond]['ecerag']['selective_risk'])}"
        auc = res["risk_coverage_auc"]
        lines.append(f"| {res.get('run_config', {}).get('generator', res['run_dir'])} | {res['grader']} | "
                     f"{rc(b['clean'])} | {rc(v['clean']['ecerag'])} | {rc(v['clean']['ecerag_cr'])} | "
                     f"{arrow('contradictory')} | {arrow('counterfactual')} | "
                     f"{fmt(auc['paper_S_equal_RCAT'])} → {fmt(auc['cv_S_main_variant_out_of_fold'])} |")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dirs", nargs="+")
    ap.add_argument("--grader", choices=["lexical", "judge"], default="lexical")
    args = ap.parse_args()
    benchmark = load_benchmark()
    results = []
    for d in args.run_dirs:
        run_dir = Path(d)
        res = analyze_run(run_dir, benchmark, args.grader)
        json.dump(res, open(run_dir / f"analysis_{args.grader}.json", "w"), indent=2)
        report = markdown_report(res)
        (run_dir / f"report_{args.grader}.md").write_text(report, encoding="utf-8")
        print(report)
        results.append(res)
    if len(results) > 1:
        table = scale_table(results)
        out = Path(args.run_dirs[0]).parent / f"scale_sweep_{args.grader}.md"
        out.write_text(table, encoding="utf-8")
        print(table)


if __name__ == "__main__":
    main()
