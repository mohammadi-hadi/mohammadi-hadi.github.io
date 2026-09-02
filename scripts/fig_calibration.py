#!/usr/bin/env python3
"""Render the figure and print the numbers for the stated-confidence post.

    python3 scripts/fig_calibration.py

Reads the per-model answer files written by scripts/calibration_mmlu.py and
draws stated confidence against the share of answers that were right, one dot
per stated value, dot area proportional to how often the model gave that
value. Every number in the post's table comes out of this script, via calikit's
own binning, Brier and bootstrap functions, so the table cannot drift from the
package the post recommends.

Needs calikit and matplotlib.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from calikit import bin_predictions, bootstrap_ci, brier, ece, fit_platt

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "assets" / "data" / "blog" / "calibration"
OUT = ROOT / "assets" / "img" / "blog" / "calibration.png"
OUT2 = ROOT / "assets" / "img" / "newsletter" / "005-calibration.png"

PAPER, INK, INK3, RULE = "#fafaf7", "#1a1a1a", "#6e6e6e", "#e3e1dc"
MODELS = [  # name, file stem, colour (validated as a set: CVD and normal-vision separation both pass)
    ("llama3.1:8b", "llama3.1-8b", "#1e3a5f"),
    ("qwen2.5:14b", "qwen2.5-14b", "#a8751a"),
    ("aya-expanse:8b", "aya-expanse-8b", "#7a4e8c"),
]
MIN_N = 10  # stated values given fewer times than this are not drawn


def load(stem: str) -> tuple[list[float], list[int], list[int]]:
    probs, labels, idx = [], [], []
    for line in (DATA / f"{stem}.jsonl").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        if rec["p"] is None or rec["y"] is None:
            continue
        probs.append(rec["p"] / 100.0)
        labels.append(int(rec["y"]))
        idx.append(int(rec["idx"]))
    return probs, labels, idx


def main() -> None:
    plt.rcParams.update({"font.family": ["Helvetica Neue", "Helvetica", "DejaVu Sans"]})
    fig, ax = plt.subplots(figsize=(12, 6.4), dpi=100)
    fig.patch.set_facecolor(PAPER)
    ax.set_facecolor(PAPER)

    ax.plot([70, 100], [70, 100], color=INK3, lw=1.2, zorder=2)
    ax.annotate("stated = observed", (100, 100), textcoords="offset points",
                xytext=(-2, 8), ha="right", fontsize=12, color=INK3)

    print(f"{'model':16s} {'acc':>6s} {'conf':>6s} {'gap':>5s} {'>=90':>6s} {'acc>=90':>8s} "
          f"{'ECE':>6s} {'CI':>15s} {'Brier':>6s} {'base':>6s} values")
    for name, stem, colour in MODELS:
        probs, labels, idx = load(stem)
        n = len(probs)
        acc = sum(labels) / n
        conf = sum(probs) / n
        hi = [(p, y) for p, y in zip(probs, labels) if p >= 0.9]
        acc_hi = sum(y for _, y in hi) / len(hi)

        # One bin per stated percentage point for the dots: with values this
        # clustered the bins are the values themselves. The table's ECE uses
        # calikit's default ten equal-mass bins, so it matches `calikit audit`.
        per_value = bin_predictions(probs, labels, k=100, scheme="width")
        ten = bin_predictions(probs, labels, k=10, scheme="mass")
        lo, hi_ci = bootstrap_ci(
            probs, labels, lambda ps, ys: ece(bin_predictions(ps, ys, k=10, scheme="mass")),
            reps=1000, seed=0)
        base = acc * (1 - acc)  # Brier of always predicting the model's own hit rate
        values = ", ".join(f"{100 * b.conf:.0f}:{b.n}" for b in per_value)
        print(f"{name:16s} {acc:6.3f} {conf:6.3f} {100 * (conf - acc):5.1f} {len(hi) / n:6.1%} "
              f"{acc_hi:8.3f} {ece(ten):6.3f} [{lo:.3f}, {hi_ci:.3f}] {brier(probs, labels):6.4f} "
              f"{base:6.4f} {values}")

        drawn = [b for b in per_value if b.n >= MIN_N]
        xs = [100 * b.conf for b in drawn]
        ys = [100 * b.acc for b in drawn]
        sizes = [3.2 * b.n for b in drawn]
        ax.scatter(xs, ys, s=sizes, color=colour, alpha=0.92, zorder=4,
                   edgecolors=PAPER, linewidths=2,
                   label=f"{name}: says {100 * conf:.0f} on average, right {100 * acc:.0f}%")
        big = max(drawn, key=lambda b: b.n)
        radius = (3.2 * big.n / 3.14159) ** 0.5  # marker size is an area in points squared
        ax.annotate(f"{big.n:,} answers", (100 * big.conf, 100 * big.acc),
                    textcoords="offset points", xytext=(0, -(radius + 4)), ha="center", va="top",
                    fontsize=11.5, color=INK3, zorder=5)

        # Platt scaling fitted on the odd-numbered questions, scored on the even ones.
        fit = [(p, y) for p, y, i in zip(probs, labels, idx) if i % 2 == 1]
        held = [(p, y) for p, y, i in zip(probs, labels, idx) if i % 2 == 0]
        mapping = fit_platt([p for p, _ in fit], [y for _, y in fit])
        hp, hy = [p for p, _ in held], [y for _, y in held]
        before = ece(bin_predictions(hp, hy, k=10, scheme="mass"))
        after = ece(bin_predictions(mapping.apply(hp), hy, k=10, scheme="mass"))
        sends = ", ".join(f"{v}->{100 * mapping.apply_one(v / 100):.0f}" for v in (80, 90, 95, 100))
        print(f"{'':16s} platt a={mapping.params['a']:+.3f} b={mapping.params['b']:.3f}  "
              f"held-out ECE {before:.3f} -> {after:.3f}  Brier {brier(hp, hy):.4f} -> "
              f"{brier(mapping.apply(hp), hy):.4f}   {sends}")

    ax.set_xlim(72, 103)
    ax.set_ylim(45, 104)
    ax.set_xlabel("confidence the model stated (%)", fontsize=13, color=INK)
    ax.set_ylabel("share of those answers that were right (%)", fontsize=13, color=INK)
    ax.set_title("Ask a model how sure it is", fontsize=17, fontweight="600", loc="left", pad=34)
    ax.text(0, 1.015,
            "1,000 MMLU questions each, temperature 0; a dot's area is how often the model gave that number",
            transform=ax.transAxes, fontsize=12, color=INK3)
    ax.grid(color=RULE, lw=1)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("bottom", "left"):
        ax.spines[side].set_color(RULE)
    ax.tick_params(colors=INK3, labelsize=12)
    leg = ax.legend(loc="upper left", frameon=False, fontsize=12, markerscale=0.35,
                    labelcolor=INK, handletextpad=0.6)
    for handle in leg.legend_handles:
        handle.set_sizes([70])

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(OUT, facecolor=PAPER)
    OUT2.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT2, facecolor=PAPER)
    print(OUT.relative_to(ROOT))
    print(OUT2.relative_to(ROOT))


if __name__ == "__main__":
    main()
