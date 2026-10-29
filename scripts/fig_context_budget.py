#!/usr/bin/env python3
"""Render the figure for the context-budget post.

    python3 scripts/fig_context_budget.py

Evidence recall against context budget on LoCoMo, one line per context policy.
The numbers are read from retainkit's committed results rather than typed in
here, so the chart cannot drift from the package the post recommends. Set
RETAINKIT_RESULTS to a local copy of examples/locomo/results/locomo.json to
draw it offline.
"""
from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "img" / "blog" / "context-budget.png"
SOURCE = ("https://raw.githubusercontent.com/mohammadi-hadi/retainkit/main/"
          "examples/locomo/results/locomo.json")

PAPER, INK, INK3, ACCENT, RULE, FLAG = (
    "#fafaf7", "#1a1a1a", "#6e6e6e", "#1e3a5f", "#e3e1dc", "#a4373a")

# Drawn cheapest-looking first so the two query-aware lines sit on top. The
# last column is where to put the 2,048-token figure the post quotes (offset in
# points and alignment), or None; head_tail and recency track each other too
# closely to label both.
POLICIES = [
    ("session_summary", "summarise each closed session", "#b07d2b", None),
    ("head_tail", "keep the first and last turns", INK3, None),
    ("recency", "keep the last N turns", FLAG, ((6, -8), "left", "top")),
    ("retrieval", "search the transcript", "#4a7ba7", ((7, -6), "left", "top")),
    ("fact_memory", "search a long-term store", ACCENT, ((-6, 9), "right", "bottom")),
]
MARK = 2048


def load() -> dict:
    local = os.environ.get("RETAINKIT_RESULTS")
    if local:
        return json.loads(Path(local).read_text(encoding="utf-8"))
    with urllib.request.urlopen(SOURCE, timeout=60) as response:  # noqa: S310
        return json.loads(response.read().decode("utf-8"))


def main() -> None:
    data = load()
    budgets = data["budgets"]
    full = data["full_tokens"]
    recall = {(r["policy"], r["budget"]): r["recall"] * 100 for r in data["rows"]}

    plt.rcParams.update({"font.family": ["Helvetica Neue", "Helvetica", "DejaVu Sans"]})
    fig, ax = plt.subplots(figsize=(7.2, 4.9), dpi=200)
    fig.patch.set_facecolor(PAPER)
    ax.set_facecolor(PAPER)

    ax.axvline(MARK, color=RULE, lw=1.4, zorder=1)
    ax.annotate(f"{MARK:,} tokens, {MARK / full:.1%} of the conversation",
                (MARK, 103), fontsize=10.5, color=INK3, ha="center", va="bottom")

    for policy, label, colour, mark in POLICIES:
        ys = [recall[(policy, b)] for b in budgets]
        ax.plot(budgets, ys, color=colour, lw=1.8, marker="o", markersize=3.5,
                zorder=3, label=label)
        if mark:
            offset, ha, va = mark
            ax.annotate(f"{recall[(policy, MARK)]:.1f}%", (MARK, recall[(policy, MARK)]),
                        textcoords="offset points", xytext=offset, fontsize=12,
                        fontweight="600", color=colour, ha=ha, va=va, zorder=6,
                        bbox=dict(boxstyle="square,pad=0.1", fc=PAPER, ec="none"))

    ax.set_xscale("log", base=2)
    ax.set_xticks(budgets)
    ax.set_xticklabels([f"{b:,}" for b in budgets], fontsize=10.5)
    ax.set_xlim(budgets[0] * 0.9, budgets[-1] * 1.15)
    ax.set_ylim(-9, 112)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_xlabel("context budget (tokens)", fontsize=12, color=INK)
    ax.set_ylabel("evidence still in context (%)", fontsize=12, color=INK)
    ax.set_title("What a context window forgets", fontsize=16, fontweight="600",
                 loc="left", pad=40)
    ax.text(0, 1.02,
            f"{data['probes']:,} LoCoMo questions over {data['cases']} conversations "
            f"averaging {full:,.0f} tokens\nthe evidence itself is 84 tokens",
            transform=ax.transAxes, fontsize=11, color=INK3, linespacing=1.3)
    ax.grid(axis="y", color=RULE, lw=1)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("bottom", "left"):
        ax.spines[side].set_color(RULE)
    ax.tick_params(colors=INK3, labelsize=11)
    handles, labels = ax.get_legend_handles_labels()
    # Under the axes: inside, the legend would sit on the lines it names.
    ax.legend(handles[::-1], labels[::-1], loc="upper center", bbox_to_anchor=(0.5, -0.2),
              ncol=2, frameon=False, fontsize=10.5, labelcolor="linecolor",
              handlelength=1.4, labelspacing=0.4, columnspacing=1.6)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(OUT, facecolor=PAPER, bbox_inches="tight", pad_inches=0.15)
    print(OUT.relative_to(ROOT))
    for policy, label, _, _mark in POLICIES:
        print(f"  {label:24s} {recall[(policy, MARK)]:5.1f}% at {MARK}")


if __name__ == "__main__":
    main()
