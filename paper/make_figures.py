"""Figures for the camera-ready paper (vector PDF, sized for an IEEE column).

  fig_scale.pdf     (a) baseline error rate vs generator size; (b) how much better than
                    a random ranking the evidence score orders answers (AUC gain, 95% CI)
  fig_tradeoff.pdf  risk-coverage curve of the evidence-score gate over unconditional
                    answers, against the operating points of the other systems (7B, 14B)

Palette: reference categorical slots 1-4 (validated: CVD dE >= 9.2 adjacent); every series
also has its own marker / line style and a direct label, so the figures survive grayscale print.
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "code"))

BLUE, ORANGE, AQUA, VIOLET = "#2a78d6", "#eb6834", "#1baf7a", "#4a3aa7"
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#d9d8d4"
SIZES = {"0.5B": 0.5, "1.5B": 1.5, "3B": 3, "7B": 7, "14B": 14}

plt.rcParams.update({
    "font.family": "serif", "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
    "font.size": 7.5, "axes.labelsize": 7.5, "axes.titlesize": 8, "legend.fontsize": 7,
    "xtick.labelsize": 7, "ytick.labelsize": 7, "axes.edgecolor": MUTED, "axes.labelcolor": INK,
    "xtick.color": MUTED, "ytick.color": MUTED, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.5, "lines.linewidth": 1.4,
    "pdf.fonttype": 42,
})

N = json.load(open(ROOT / "paper" / "numbers.json"))


def fig_scale():
    xs = [SIZES[m] for m in SIZES]
    fig, (a, b) = plt.subplots(1, 2, figsize=(3.5, 1.75))
    for g, col, mk, ls, lab in (("judge", BLUE, "o", "-", "LLM judge"), ("lexical", ORANGE, "s", "--", "Lexical")):
        ys = [N["scale"][g][m]["baseline"]["risk"] for m in SIZES]
        a.plot(xs, ys, color=col, marker=mk, ms=4, ls=ls)
        a.annotate(lab, (xs[-1], ys[-1]), xytext=(-2, 7 if g == "lexical" else -10),
                   textcoords="offset points", ha="right", color=INK, fontsize=6.5)
        gains, lo, hi = [], [], []
        for m in SIZES:
            auc = N["auc"][g][m]
            gain = auc["random_ranking_expected"] - auc["paper_S_equal_RCAT"]
            ci = auc["paper_S_gain_over_random_ci95"]
            gains.append(gain), lo.append(gain - ci[0]), hi.append(ci[1] - gain)
        off = 0.93 if g == "judge" else 1.07  # dodge the two series on the log axis
        b.errorbar([x * off for x in xs], gains, yerr=[lo, hi], color=col, marker=mk, ms=4,
                   ls="none", elinewidth=0.9, capsize=1.5, label=lab)
    a.set(xscale="log", xlabel="Generator size (B params)", ylabel="Selective risk", ylim=(0, 0.7),
          title="(a) Baseline error rate")
    b.axhline(0, color=MUTED, lw=0.8, ls=":")
    b.set(xscale="log", xlabel="Generator size (B params)", ylabel="AUC gain vs. random",
          title="(b) Evidence-score ranking", ylim=(-0.05, 0.38))
    for ax in (a, b):
        ax.set_xticks(xs)
        ax.set_xticklabels([m for m in SIZES])
        ax.minorticks_off()
    b.legend(frameon=False, loc="upper right", ncol=2, handletextpad=0.1, columnspacing=0.6,
             borderaxespad=0.0)
    fig.tight_layout(pad=0.3, w_pad=0.8)
    fig.savefig(ROOT / "paper" / "fig_scale.pdf")


def gate_curve(model, grader):
    """Risk-coverage of the equal-weight R/C/A/T score swept over unconditional answers."""
    from analyze import load_records
    from ecerag.bootstrap import load_benchmark
    from ecerag.sufficiency import DEFAULT_WEIGHTS, combine
    by_qid = {q["qid"]: q for q in load_benchmark()}
    recs = load_records(ROOT / f"results/kaggle/Qwen2.5-{model}-Instruct", by_qid, grader)
    clean = [r for r in recs if r["condition"] == "clean"]
    clean.sort(key=lambda r: -combine(r["signals"], DEFAULT_WEIGHTS))
    cov, risk, errors = [], [], 0
    for i, r in enumerate(clean, start=1):
        errors += not r["noref"]["graded"]["correct"]
        cov.append(i / len(clean)), risk.append(errors / i)
    return np.array(cov), np.array(risk)


def fig_tradeoff():
    fig, axes = plt.subplots(1, 2, figsize=(3.5, 1.85), sharey=True)
    for ax, m in zip(axes, ("7B", "14B")):
        cov, risk = gate_curve(m, "judge")
        keep = cov >= 0.1  # the first few points are single-answer noise
        ax.plot(cov[keep], risk[keep], color=BLUE, lw=1.3)
        ax.text(0.03, 0.5, "evidence gate\n(sweep)", color=INK, fontsize=6, va="center")
        r2 = N["round2"]["judge"][m]["clean"]
        same = (abs(r2["ecerag_v2"]["cov"] - r2["refusal_prompt"]["cov"]) < 0.01
                and abs(r2["ecerag_v2"]["risk"] - r2["refusal_prompt"]["risk"]) < 0.01)
        pts = [("unconditional", r2["unconditional"], ORANGE, "s", (-4, 5), "right"),
               ("self-refusal" + (" = ECERAG" if same else ""), r2["refusal_prompt"], AQUA, "^",
                (0, -11) if same else (5, -3), "center" if same else "left")]
        if not same:
            pts.append(("ECERAG", r2["ecerag_v2"], VIOLET, "D", (0, -11), "center"))
        for lab, d, col, mk, off, ha in pts:
            ax.plot([d["cov"]], [d["risk"]], marker=mk, color=col, ms=5, ls="none",
                    markeredgecolor="white", markeredgewidth=0.6)
            ax.annotate(lab, (d["cov"], d["risk"]), xytext=off, textcoords="offset points",
                        ha=ha, color=INK, fontsize=6)
        ax.set(xlim=(0, 1.04), ylim=(0, 0.6), xlabel="Coverage", title=f"Qwen2.5-{m}")
    axes[0].set_ylabel("Selective risk")
    fig.tight_layout(pad=0.3, w_pad=0.6)
    fig.savefig(ROOT / "paper" / "fig_tradeoff.pdf")


if __name__ == "__main__":
    fig_scale()
    fig_tradeoff()
    print("wrote paper/fig_scale.pdf, paper/fig_tradeoff.pdf")
