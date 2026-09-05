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
# last column marks the two policies whose 2,048-token figure the post quotes;
# head_tail and recency track each other too closely to label both.
POLICIES = [
    ("session_summary", "summarise each closed session", "#b07d2b", False),
    ("head_tail", "keep the first and last turns", INK3, False),
    ("recency", "keep the last N turns", FLAG, True),
    ("retrieval", "search the transcript", "#4a7ba7", False),
    ("fact_memory", "search a long-term store", ACCENT, True),
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
    fig, ax = plt.subplots(figsize=(12, 6.4), dpi=100)
    fig.patch.set_facecolor(PAPER)
    ax.set_facecolor(PAPER)

    ax.axvline(MARK, color=RULE, lw=1.4, zorder=1)
    ax.annotate(f"{MARK:,} tokens, {MARK / full:.1%} of the conversation",
                (MARK, 108), fontsize=12, color=INK3, ha="center", va="bottom")

    for policy, label, colour, mark in POLICIES:
        ys = [recall[(policy, b)] for b in budgets]
        ax.plot(budgets, ys, color=colour, lw=2.2, marker="o", markersize=5,
                zorder=3, label=label)
        if mark:
            ax.annotate(f"{recall[(policy, MARK)]:.0f}%", (MARK, recall[(policy, MARK)]),
                        textcoords="offset points", xytext=(-11, -5), fontsize=13,
                        fontweight="600", color=colour, ha="right")

    ax.set_xscale("log", base=2)
    ax.set_xticks(budgets)
    ax.set_xticklabels([f"{b:,}" for b in budgets], fontsize=12)
    ax.set_xlim(budgets[0] * 0.9, budgets[-1] * 1.15)
    ax.set_ylim(-3, 116)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_xlabel("context budget (tokens)", fontsize=13, color=INK)
    ax.set_ylabel("questions whose evidence survived (%)", fontsize=13, color=INK)
    ax.set_title("What a context window forgets", fontsize=17, fontweight="600",
                 loc="left", pad=34)
    ax.text(0, 1.015,
            f"{data['probes']:,} LoCoMo questions over {data['cases']} conversations "
            f"averaging {full:,.0f} tokens; the evidence itself is 84 tokens",
            transform=ax.transAxes, fontsize=12, color=INK3)
    ax.grid(axis="y", color=RULE, lw=1)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("bottom", "left"):
        ax.spines[side].set_color(RULE)
    ax.tick_params(colors=INK3, labelsize=12)
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles[::-1], labels[::-1], loc="upper left", frameon=False,
              fontsize=12.5, labelcolor="linecolor", handlelength=1.6,
              borderaxespad=1.2, labelspacing=0.55)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(OUT, facecolor=PAPER)
    print(OUT.relative_to(ROOT))
    for policy, label, _, _mark in POLICIES:
        print(f"  {label:24s} {recall[(policy, MARK)]:5.1f}% at {MARK}")


if __name__ == "__main__":
    main()
