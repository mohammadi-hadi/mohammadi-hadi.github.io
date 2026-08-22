#!/usr/bin/env python3
"""Render the site's social share cards.

Each card is laid out as a 1200x630 HTML page in the site's own typography and
screenshotted with headless Chrome, so the cards and the site never drift apart.

    python3 scripts/make_cards.py                    # every card
    python3 scripts/make_cards.py book-card          # just one

Cards land in assets/img/blog/ unless the entry carries an explicit "out".
Needs Google Chrome installed and a network connection (the page pulls the
webfonts). Re-run it after adding a post; commit the PNGs alongside it.
"""
from __future__ import annotations

import html
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "img" / "blog"

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

SERIES = "Modern AI Engineering"

CARDS = [
    dict(name="index", kicker="Hadi Mohammadi", title="Blog",
         subtitle="field notes and open guides",
         bullets=[
             ("Modern AI Engineering", "six chapters on production LLM systems"),
             ("Master’s programmes in the Netherlands", "every degree, and how Dutch admissions work"),
             ("Machine learning summer schools in Europe", "which ones, how to get in, how to fund it"),
             ("ML learning paths", "ordered course paths for five different jobs"),
             ("Awesome explainable NLP", "papers, tools and resources"),
         ],
         foot_left="mohammadi.cv/blog", foot_right="Free · open · citable"),
    dict(name="calling-llms-well", kicker=f"{SERIES} · Chapter 1",
         title="Calling LLMs well",
         subtitle="Structured outputs, retries, caching and cost control",
         foot_left="mohammadi.cv/blog", foot_right="4 min read"),
    dict(name="retrieval-augmented-generation", kicker=f"{SERIES} · Chapter 2",
         title="Retrieval-augmented generation",
         subtitle="Chunking, hybrid search, rerankers, and how RAG fails",
         foot_left="mohammadi.cv/blog", foot_right="4 min read"),
    dict(name="agents-and-mcp", kicker=f"{SERIES} · Chapter 3",
         title="Agents and MCP",
         subtitle="Tool loops, the Model Context Protocol, and when not to build an agent",
         foot_left="mohammadi.cv/blog", foot_right="4 min read"),
    dict(name="fine-tuning-and-preference-optimization", kicker=f"{SERIES} · Chapter 4",
         title="Fine-tuning and preference optimization",
         subtitle="Prompting vs. RAG vs. LoRA vs. DPO and GRPO",
         foot_left="mohammadi.cv/blog", foot_right="4 min read"),
    dict(name="evaluation-and-llm-as-judge", kicker=f"{SERIES} · Chapter 5",
         title="Evaluation and LLM-as-judge",
         subtitle="Evals that predict production, judges you can trust",
         foot_left="mohammadi.cv/blog", foot_right="4 min read"),
    dict(name="serving-and-inference-optimization", kicker=f"{SERIES} · Chapter 6",
         title="Serving and inference optimization",
         subtitle="vLLM, KV caches, quantization, and cost budgets that hold",
         foot_left="mohammadi.cv/blog", foot_right="4 min read"),
    dict(name="what-an-llm-judge-actually-does", kicker="Field notes",
         title="What an LLM judge actually does",
         subtitle="One model picked whichever answer was shown first 91% of the time",
         foot_left="mohammadi.cv/blog", foot_right="5 min read"),
    dict(name="the-labels-under-the-benchmark", kicker="Field notes",
         title="The labels under the benchmark",
         subtitle="27 of 28 GoEmotions emotions fall below the reliability floor",
         foot_left="mohammadi.cv/blog", foot_right="5 min read"),
    dict(name="what-arena-votes-can-and-cannot-order", kicker="Field notes",
         title="What arena votes cannot order",
         subtitle="Of 54 neighbouring pairs on the board, exactly one separates",
         foot_left="mohammadi.cv/blog", foot_right="6 min read"),
    dict(name="4873-experiments-and-the-winners-curse", kicker="Field notes",
         title="4,873 experiments and the winner’s curse",
         subtitle="16% fail their traffic-split check before anyone reads the p-value",
         foot_left="mohammadi.cv/blog", foot_right="5 min read"),
    dict(name="how-much-text-a-watermark-needs", kicker="Field notes",
         title="How much text a watermark needs",
         subtitle="208 words if every token is a choice, 1,388 if only a sixth are",
         foot_left="mohammadi.cv/blog", foot_right="5 min read"),
    dict(name="research-card", out="assets/img", kicker="Hadi Mohammadi",
         title="Research",
         subtitle="Explainable NLP, cultural fairness in LLMs, human–AI collaboration",
         foot_left="mohammadi.cv/research", foot_right="Grants · talks · posters"),
    dict(name="publications-card", out="assets/img", kicker="Hadi Mohammadi",
         title="Publications",
         subtitle="Peer-reviewed work on explainability, moral alignment and LLM evaluation",
         foot_left="mohammadi.cv/publications", foot_right="ACL · ECAI · *SEM"),
    dict(name="projects-card", out="assets/img", kicker="Hadi Mohammadi",
         title="Projects",
         subtitle="Research code, applied ML systems, and earlier engineering work",
         foot_left="mohammadi.cv/projects", foot_right="Papers · grants · code"),
    dict(name="experience-card", out="assets/img", kicker="Hadi Mohammadi",
         title="Experience",
         subtitle="Six years from data scientist to Senior AI & Data Science Expert",
         foot_left="mohammadi.cv/experience", foot_right="Production ML and LLM systems"),
    dict(name="teaching-card", out="assets/img", kicker="Hadi Mohammadi",
         title="Teaching",
         subtitle="Supervision, lecturing, and a free course in explainable AI",
         foot_left="mohammadi.cv/teaching", foot_right="Utrecht University"),
    dict(name="news-card", out="assets/img", kicker="Hadi Mohammadi",
         title="News",
         subtitle="Grants, awards, accepted papers and service",
         foot_left="mohammadi.cv/news", foot_right="Updated as things land"),
    dict(name="playground-card", out="assets/img", kicker="Interactive",
         title="Poke the Black Box",
         subtitle="Type a sentence, watch a model decide, then try to change its mind",
         foot_left="mohammadi.cv/playground", foot_right="Runs in your browser"),
    dict(name="book-card", out="assets/img", kicker="Hadi Mohammadi",
         title="Hands-On Explainable AI",
         subtitle="Interpreting, evaluating, and trusting large language models",
         foot_left="mohammadi.cv/book", foot_right="13 chapters · 13 labs"),
    dict(name="summer-school-card", out="assets/img", kicker="Summer school",
         title="Opening the Black Box",
         subtitle="Five hands-on days inside large language models",
         foot_left="mohammadi.cv/summer-school", foot_right="10 lectures · 13 labs"),
    dict(name="software-card", out="assets/img", kicker="Hadi Mohammadi",
         title="Software",
         subtitle="Libraries for not trusting your own numbers",
         bullets=[
             ("judgekit · judgepanel · arenakit", "is this judge, or this leaderboard, telling the truth?"),
             ("abkit · abeval · calikit", "does the experiment support the decision?"),
             ("raterkit · rankkit · explainkit", "are the labels, the ranking, the explanation sound?"),
         ],
         foot_left="mohammadi.cv/software", foot_right="MIT · tested · citable"),
]

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&family=Inter:wght@400;500&family=JetBrains+Mono:wght@500&display=swap" rel="stylesheet">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  html, body {{ width: 1200px; height: 630px; }}
  body {{
    background: #fafaf7;
    font-family: "Inter", sans-serif;
    color: #1a1a1a;
    border-top: 10px solid #1e3a5f;
    padding: 62px 84px 52px;
    display: flex;
    flex-direction: column;
  }}
  .kicker {{
    font-family: "JetBrains Mono", monospace;
    font-size: 20px; font-weight: 500;
    letter-spacing: 0.16em; text-transform: uppercase;
    color: #6e6e6e;
  }}
  h1 {{
    font-family: "Source Serif 4", serif;
    font-weight: 600; font-size: {size}px; line-height: 1.06;
    letter-spacing: -0.02em; margin-top: 26px;
  }}
  .subtitle {{
    font-family: "Source Serif 4", serif;
    font-size: 34px; line-height: 1.3; color: #1e3a5f;
    margin-top: 20px; max-width: 30ch;
  }}
  ul {{ list-style: none; margin-top: 30px; }}
  li {{ font-size: 24px; margin-bottom: 13px; display: flex; gap: 14px; align-items: baseline; }}
  li::before {{ content: ""; width: 5px; height: 20px; background: #1e3a5f; flex: none; }}
  li em {{ font-style: normal; color: #6e6e6e; font-size: 21px; }}
  .stack {{ margin: auto 0; }}
  footer {{
    padding-top: 26px; border-top: 1px solid #e3e1dc;
    display: flex; justify-content: space-between;
    font-size: 24px; color: #6e6e6e;
  }}
  footer .left {{ color: #1e3a5f; }}
</style>
</head>
<body>
  <div class="stack">
    <span class="kicker">{kicker}</span>
    <h1>{title}</h1>
    {middle}
  </div>
  <footer><span class="left">{foot_left}</span><span>{foot_right}</span></footer>
</body>
</html>
"""


def build(card: dict) -> str:
    title = html.escape(card["title"])
    size = 92 if len(card["title"]) <= 18 else (74 if len(card["title"]) <= 30 else 62)
    if card.get("bullets"):
        size = 92
        items = "\n    ".join(
            "<li><span><strong>%s</strong> <em>— %s</em></span></li>"
            % (html.escape(a), html.escape(b)) for a, b in card["bullets"])
        middle = ('<div class="subtitle">%s</div>\n  <ul>\n    %s\n  </ul>'
                  % (html.escape(card["subtitle"]), items))
    else:
        middle = '<div class="subtitle">%s</div>' % html.escape(card["subtitle"])
    return TEMPLATE.format(kicker=html.escape(card["kicker"]), title=title, size=size,
                           middle=middle, foot_left=html.escape(card["foot_left"]),
                           foot_right=html.escape(card["foot_right"]))


def main() -> None:
    if not Path(CHROME).exists():
        raise SystemExit(f"Chrome not found at {CHROME}")
    # Name one or more cards to render just those; re-rendering all of them
    # rewrites PNGs that have not changed and churns the diff.
    wanted = set(sys.argv[1:])
    cards = [c for c in CARDS if c["name"] in wanted] if wanted else CARDS
    if wanted and not cards:
        raise SystemExit("no card matches %s; known: %s"
                         % (", ".join(sorted(wanted)), ", ".join(c["name"] for c in CARDS)))
    OUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        for card in cards:
            page = tmp / f"{card['name']}.html"
            shot = tmp / f"{card['name']}.png"
            page.write_text(build(card), encoding="utf-8")
            cmd = [CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                   "--no-first-run", "--no-default-browser-check",
                   f"--user-data-dir={tmp / 'profile'}",
                   "--virtual-time-budget=8000",
                   f"--screenshot={shot}",
                   "--window-size=1200,630", page.as_uri()]
            # Chrome's updater keeps the process alive well past the screenshot,
            # so treat "the file exists" as success rather than waiting on exit.
            try:
                subprocess.run(cmd, timeout=60, capture_output=True)
            except subprocess.TimeoutExpired:
                pass
            if not shot.exists():
                raise SystemExit(f"Chrome produced no screenshot for {card['name']}")
            out = ROOT / card["out"] if card.get("out") else OUT
            out.mkdir(parents=True, exist_ok=True)
            shutil.move(shot, out / f"{card['name']}.png")
            print("%s/%s.png" % (out.relative_to(ROOT), card["name"]))


if __name__ == "__main__":
    main()
