#!/usr/bin/env python3
"""Render the figure for the eval sample-size post.

    python3 scripts/fig_evalsize.py

The smallest score gap each benchmark can resolve, given how many items it has.
Numbers come from abeval's own power functions, not from anything typed in
here, so the chart cannot drift from the package the post recommends.

Benchmark sizes are the published test-split counts, each checked against a
primary source: HumanEval 164, GPQA Diamond 198, SWE-bench Verified 500,
GSM8K test 1,319 (HuggingFace openai/gsm8k), MMLU test 14,042
(HuggingFace cais/mmlu, "all" config).
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from abeval.power import mde, sd_diff_from_rates

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "img" / "blog" / "eval-size.png"
OUT2 = ROOT / "assets" / "img" / "newsletter" / "003-floors.png"

PAPER, INK, INK3, ACCENT, RULE, FLAG = (
    "#fafaf7", "#1a1a1a", "#6e6e6e", "#1e3a5f", "#e3e1dc", "#a4373a")

BENCHMARKS = [
    ("MMLU (test)", 14042),
    ("GSM8K (test)", 1319),
    ("SWE-bench Verified", 500),
    ("GPQA Diamond", 198),
    ("HumanEval", 164),
]
BASE, DELTA, CORR = 0.75, 0.03, 0.5
REPORTED = 3.0          # a gap leaderboards treat as a clear result


def main() -> None:
    sd = sd_diff_from_rates(BASE, BASE + DELTA, corr=CORR)
    rows = [(name, n, 100 * mde(n, sd)) for name, n in BENCHMARKS]

    plt.rcParams.update({"font.family": ["Helvetica Neue", "Helvetica", "DejaVu Sans"]})
    fig, ax = plt.subplots(figsize=(12, 6.4), dpi=100)
    fig.patch.set_facecolor(PAPER); ax.set_facecolor(PAPER)

    ys = range(len(rows))
    for y, (name, n, gap) in zip(ys, rows):
        colour = ACCENT if gap <= REPORTED else FLAG
        ax.barh(y, gap, height=0.5, color=colour, zorder=3)
        ax.annotate(f"{gap:.1f} points", (gap, y), textcoords="offset points",
                    xytext=(9, -4), fontsize=14, fontweight="600", color=colour)


    ax.axvline(REPORTED, color=INK, lw=1.4, ls="--", zorder=5)
    ax.annotate("a three-point gap", (REPORTED, len(rows) - 0.6),
                textcoords="offset points", xytext=(9, 0),
                fontsize=12.5, color=INK, va="top")

    ax.set_yticks(list(ys))
    ax.set_yticklabels([f"{r[0]}\n{r[1]:,} items" for r in rows], fontsize=12.5)
    ax.set_xlim(0, 11.5)
    ax.set_ylim(-0.7, len(rows) - 0.3)
    ax.set_xlabel("smallest score gap the benchmark can resolve (percentage points)",
                  fontsize=13, color=INK)
    ax.set_title("What a benchmark can actually tell apart",
                 fontsize=17, fontweight="600", loc="left", pad=34)
    ax.text(0, 1.015,
            "paired runs, 75% baseline, correlation 0.5; a true gap shorter than the bar is missed more often than found",
            transform=ax.transAxes, fontsize=12, color=INK3)
    ax.grid(axis="x", color=RULE, lw=1)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(RULE)
    ax.tick_params(colors=INK3, labelsize=12)
    ax.tick_params(axis="y", length=0, labelcolor=INK)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(OUT, facecolor=PAPER)
    OUT2.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT2, facecolor=PAPER)
    print(OUT.relative_to(ROOT)); print(OUT2.relative_to(ROOT))
    for name, n, gap in rows:
        print(f"  {name:22s} {n:6,d} items -> {gap:.1f} points")


if __name__ == "__main__":
    main()
