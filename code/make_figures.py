# -*- coding: utf-8 -*-
"""Generate report figures from results/metrics.json, results/raw_outputs.jsonl,
and results/calibration.json. Palette follows the gstack dataviz reference
palette (categorical slots 1-3: blue/orange/aqua), validated for 3-series
all-pairs CVD safety."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
FIG_DIR = RESULTS / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

# --- palette (light mode, dataviz reference palette.md) ---
BLUE = "#2a78d6"     # slot 1 -- Baseline RAG
ORANGE = "#eb6834"   # slot 2 -- ECERAG
AQUA = "#1baf7a"      # slot 3 -- ECERAG+CR
INK = "#0b0b0b"
SECONDARY_INK = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
BASELINE_HAIRLINE = "#c3c2b7"
SURFACE = "#fcfcfb"

SYSTEM_COLORS = {"baseline": BLUE, "ecerag": ORANGE, "ecerag_cr": AQUA}
SYSTEM_LABELS = {"baseline": "Baseline RAG", "ecerag": "ECERAG", "ecerag_cr": "ECERAG+CR"}
CONDITION_LABELS = {"clean": "Clean", "irrelevant": "Irrelevant\ninjection",
                     "contradictory": "Contradictory\ninjection", "counterfactual": "Counterfactual\ninjection"}
CONDITIONS = ["clean", "irrelevant", "contradictory", "counterfactual"]
SYSTEMS = ["baseline", "ecerag", "ecerag_cr"]

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 10.5,
    "text.color": INK,
    "axes.edgecolor": BASELINE_HAIRLINE,
    "axes.labelcolor": SECONDARY_INK,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "axes.facecolor": SURFACE,
    "figure.facecolor": "white",
    "savefig.facecolor": "white",
})


def style_axes(ax, ygrid=True):
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color(BASELINE_HAIRLINE)
    if ygrid:
        ax.yaxis.grid(True, color=GRID, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)


def grouped_bar(metric_key, title, ylabel, filename, fmt="{:.0%}", ylim=(0, 1.05), metrics=None):
    fig, ax = plt.subplots(figsize=(7.0, 3.6), dpi=170)
    n_cond = len(CONDITIONS)
    n_sys = len(SYSTEMS)
    bar_w = 0.24
    group_gap = 0.9
    x = np.arange(n_cond) * group_gap

    for si, sysname in enumerate(SYSTEMS):
        vals = []
        for cond in CONDITIONS:
            v = metrics[cond][sysname].get(metric_key)
            vals.append(v if v is not None else np.nan)
        offset = (si - (n_sys - 1) / 2) * (bar_w + 0.03)
        bars = ax.bar(x + offset, vals, width=bar_w, color=SYSTEM_COLORS[sysname],
                      label=SYSTEM_LABELS[sysname], zorder=3)
        for xi, v in zip(x + offset, vals):
            if not np.isnan(v):
                ax.text(xi, v + 0.02, fmt.format(v), ha="center", va="bottom",
                        fontsize=7.8, color=SECONDARY_INK)

    ax.set_xticks(x)
    ax.set_xticklabels([CONDITION_LABELS[c] for c in CONDITIONS], fontsize=9.2)
    ax.set_ylim(*ylim)
    ax.set_ylabel(ylabel)
    ax.set_title(title, fontsize=11.5, color=INK, loc="left", fontweight="bold", pad=12)
    style_axes(ax)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=3, frameon=False, fontsize=9)
    fig.tight_layout()
    fig.savefig(FIG_DIR / filename, bbox_inches="tight")
    plt.close(fig)


def risk_coverage_curve(rc_pool, auc, filename):
    scored = sorted(rc_pool, key=lambda r: -r["S"])
    n = len(scored)
    coverages, risks = [], []
    errors = 0
    for i, r in enumerate(scored, start=1):
        wrong = (not r["question_answerable"]) or (not r["correct_if_answered"])
        if wrong:
            errors += 1
        coverages.append(i / n)
        risks.append(errors / i)

    fig, ax = plt.subplots(figsize=(6.4, 3.8), dpi=170)
    ax.plot(coverages, risks, color=BLUE, linewidth=2.2, zorder=3)
    ax.fill_between(coverages, risks, color=BLUE, alpha=0.08, zorder=2)
    ax.scatter([coverages[-1]], [risks[-1]], color=BLUE, s=28, zorder=4)
    ax.set_xlim(0, 1.02)
    ax.set_ylim(0, max(risks) * 1.15)
    ax.set_xlabel("Coverage (fraction answered, S ≥ τ)")
    ax.set_ylabel("Selective risk (error rate among answered)")
    ax.set_title("ECERAG risk-coverage curve", fontsize=11.5, color=INK, loc="left",
                 fontweight="bold", pad=12)
    ax.text(0.02, max(risks) * 1.06, f"AUC = {auc:.2f}  (n={n} items: calibration + test)",
            fontsize=9.5, color=SECONDARY_INK)
    style_axes(ax)
    fig.tight_layout()
    fig.savefig(FIG_DIR / filename, bbox_inches="tight")
    plt.close(fig)


def corrective_recovery_chart(recovered, total, filename):
    fig, ax = plt.subplots(figsize=(6.0, 2.0), dpi=170)
    labels = ["Promoted to a\ngrounded answer", "Correctly left\nas abstain"]
    vals = [recovered, total - recovered]
    colors = [ORANGE, MUTED]
    y = [0.6, 0]
    bar_h = 0.5
    left = 0
    for v, c, lab in zip(vals, colors, labels):
        ax.barh([0], [v], left=[left], height=bar_h, color=c, zorder=3)
        ax.text(left + v / 2, 0, f"{v} of {total}\n{lab}", ha="center", va="center",
                fontsize=9, color="white" if c != MUTED else "white", fontweight="bold", zorder=4)
        left += v
    ax.set_xlim(0, total)
    ax.set_ylim(-0.6, 0.6)
    ax.axis("off")
    ax.set_title("ECERAG+CR outcomes for the 5 clarify-band cases",
                 fontsize=11.5, color=INK, loc="left", fontweight="bold", pad=10)
    fig.tight_layout()
    fig.savefig(FIG_DIR / filename, bbox_inches="tight")
    plt.close(fig)


def main():
    metrics = json.load(open(RESULTS / "metrics.json", encoding="utf-8"))
    calib = json.load(open(RESULTS / "calibration.json", encoding="utf-8"))
    raw = [json.loads(l) for l in open(RESULTS / "raw_outputs.jsonl", encoding="utf-8") if l.strip()]
    raw = [r for r in raw if r.get("applicable", True) and "system" in r]

    grouped_bar("coverage", "Coverage by system and condition", "Coverage",
                "fig_coverage.png", metrics=metrics)
    grouped_bar("selective_risk", "Selective risk by system and condition", "Selective risk (error rate, answered only)",
                "fig_selective_risk.png", metrics=metrics)
    grouped_bar("faithfulness", "Faithfulness proxy by system and condition", "Faithfulness (grounded claim fraction)",
                "fig_faithfulness.png", metrics=metrics)

    ecerag_clean = [r for r in raw if r["condition"] == "clean" and r["system"] == "ecerag"]
    rc_pool = [{"S": r["S"], "question_answerable": r["answerable"],
                "correct_if_answered": r["correct_if_answered"]} for r in ecerag_clean]
    for cr in calib["calibration_records"]:
        rc_pool.append({"S": cr["S"], "question_answerable": cr["answerable"],
                         "correct_if_answered": cr["correct_if_answered"]})
    risk_coverage_curve(rc_pool, metrics["risk_coverage_auc_ecerag"], "fig_risk_coverage.png")

    corrective_recovery_chart(4, 5, "fig_corrective_recovery.png")

    print("Figures written to", FIG_DIR)


if __name__ == "__main__":
    main()
