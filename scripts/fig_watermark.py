#!/usr/bin/env python3
"""Render the figure for the watermarking post.

    python3 scripts/fig_watermark.py

How much text a statistical watermark needs before a detector can call it,
as a function of how many of the tokens carry any signal at all. Closed form,
no data file, so the numbers cannot drift.

A green-list style detector asks whether the share of favoured tokens exceeds
chance. With a per-token bias of p against a null of 0.5, reaching a one-sided
95% call needs n = (z * sqrt(0.25) / (p - 0.5))^2 SCORED tokens. Only
high-entropy positions are scored, so the text has to be longer by 1/f.
"""
from __future__ import annotations

import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "img" / "blog" / "watermark-length.png"

PAPER, INK, INK3, ACCENT, RULE, FLAG = (
    "#fafaf7", "#1a1a1a", "#6e6e6e", "#1e3a5f", "#e3e1dc", "#a4373a")
Z = 1.645          # one-sided 95%
BIAS = 0.55        # the 55:45 split in the simulation being discussed
TOKENS_PER_WORD = 1.3


def words_needed(f: float) -> float:
    n_scored = (Z * math.sqrt(0.25) / (BIAS - 0.5)) ** 2
    return n_scored / f / TOKENS_PER_WORD


def main() -> None:
    plt.rcParams.update({"font.family": ["Helvetica Neue", "Helvetica", "DejaVu Sans"]})
    fig, ax = plt.subplots(figsize=(7.2, 4.2), dpi=200)
    fig.patch.set_facecolor(PAPER); ax.set_facecolor(PAPER)

    fs = [x / 100 for x in range(10, 101)]
    ax.plot([f * 100 for f in fs], [words_needed(f) for f in fs],
            color=ACCENT, lw=2.2, zorder=3)

    # offsets chosen so no label crosses the axis or the curve
    for f, label, colour, dx, dy, ha in [
            (1.00, "every token carries signal", ACCENT, -10, 16, "right"),
            (1/3, "a third of tokens", FLAG, 14, 10, "left"),
            (1/6, "a sixth of tokens", FLAG, 16, 2, "left")]:
        w = words_needed(f)
        ax.plot(f * 100, w, "o", ms=7, color=colour, zorder=4)
        ax.annotate(f"{w:,.0f} words\n{label}", (f * 100, w),
                    textcoords="offset points", xytext=(dx, dy),
                    ha=ha, fontsize=12, fontweight="600", color=colour)

    ax.set_xlim(8, 104); ax.set_ylim(0, 2100)
    ax.set_xlabel("share of tokens where the model had a real choice (%)",
                  fontsize=12, color=INK)
    ax.set_ylabel("words needed for a 95% call", fontsize=12, color=INK)
    ax.set_title("How much text a 55:45 watermark needs before it shows up",
                 fontsize=15, fontweight="600", loc="left", pad=40)
    ax.text(0, 1.02,
            "the 208-word figure assumes every token is a real choice\n"
            "in real text only some are, and that share sets the length",
            transform=ax.transAxes, fontsize=11, color=INK3, linespacing=1.3)
    ax.grid(axis="y", color=RULE, lw=1)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.spines["left"].set_color(RULE); ax.spines["bottom"].set_color(RULE)
    ax.tick_params(colors=INK3, labelsize=11)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(OUT, facecolor=PAPER)
    print(OUT.relative_to(ROOT))
    for f in (1.0, 0.5, 1/3, 1/6):
        print(f"  f={f:<5} -> {words_needed(f):,.0f} words")


if __name__ == "__main__":
    main()
