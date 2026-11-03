#!/usr/bin/env python3
"""Fetch Google Scholar stats for profile w4Jt-FAAAAAJ into assets/data/scholar.json.

Run by .github/workflows/scholar.yml daily (or manually: python scripts/fetch_scholar.py).
On any failure the script exits nonzero WITHOUT writing, so the last good JSON
is never clobbered by a blocked or partial response.

Exit codes: 0 updated or unchanged; 2 Scholar blocked or unreachable on every
attempt (expected now and then, the workflow stays green); anything else is a
crash or bad data (an import error, a bug, a failed sanity check) and turns the
workflow run red.
"""

import json
import re
import socket
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx
import requests
from scholarly import scholarly, ProxyGenerator, DOSException, MaxTriesExceededException

socket.setdefaulttimeout(30)  # fail fast when Google blocks the runner

EXIT_BLOCKED = 2

# Errors that mean Google refused or dropped the connection. Anything else is a
# real failure and is not retried.
BLOCKED_ERRORS = (
    MaxTriesExceededException,
    DOSException,
    httpx.HTTPError,
    requests.RequestException,
    OSError,  # includes socket timeouts and connection resets
)

SCHOLAR_ID = "w4Jt-FAAAAAJ"
OUT = Path(__file__).resolve().parents[1] / "assets" / "data" / "scholar.json"

# Normalized Scholar-title prefix -> stable site slug.
# Slugs match data-scholar-pub attributes in publications/index.html and the
# detail-page directory names under /publications/.
SLUGS = {
    "evalmoraal": "evalmoraal",
    "do large language models understand morality": "morality-across-cultures",
    "exploring cultural variations in moral judgments": "cultural-moral-judgments",
    "assessing the reliability of llms": "llm-annotation-reliability",
    "explainability based token replacement": "ai-text-undetectability",
    "explainability in practice": "explainability-survey",
    "evaluating grpo and dpo": "grpo-dpo-cot",
    "reasoning answer entailment under grpo": "grpo-dpo-cot",
    "measuring firm characteristics": "firm-characteristics-nlp",
    "llms as mirrors of societal moral standards": "mirrors-cultural-divergence",
    "large language models as mirrors of societal moral standards": "mirrors-societal-moral-standards",
    "novel approaches in financial fraud detection": "financial-fraud-detection",
    "a transparent pipeline for identifying sexism": "sexism-detection",
    "the clin33 shared task": "clin33-shared-task",
    "towards robust online sexism detection": "exist-2023",
    "statistical reinforcement learning": "statistical-rl-book",
    "home health care problem": "home-health-care",
}


def norm(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()


def slug_for(title: str) -> str:
    n = norm(title)
    for prefix, slug in SLUGS.items():
        if n.startswith(prefix):
            return slug
    return re.sub(r"\s+", "-", n)[:60]


def fetch() -> dict:
    author = scholarly.fill(
        scholarly.search_author_id(SCHOLAR_ID),
        sections=["basics", "indices", "publications"],
    )
    pubs = {}
    for p in author["publications"]:
        title = p["bib"]["title"]
        year = p["bib"].get("pub_year")
        slug = slug_for(title)
        cited_by = p.get("num_citations", 0)
        # A preprint and its published version share a slug; keep the better-cited one.
        if slug in pubs and pubs[slug]["cited_by"] >= cited_by:
            continue
        pubs[slug] = {
            "title": title,
            "year": int(year) if year else None,
            "cited_by": cited_by,
        }
    return {
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "citations": author.get("citedby", 0),
        "h_index": author.get("hindex", 0),
        "i10_index": author.get("i10index", 0),
        "publications": pubs,
    }


def sane(new: dict, old: dict | None) -> bool:
    if new["citations"] <= 0 or new["h_index"] <= 0:
        return False
    if len(new["publications"]) < 8:  # partial-profile guard
        return False
    if old and new["citations"] < 0.5 * old.get("citations", 0):
        return False
    return True


def main() -> None:
    old = json.loads(OUT.read_text()) if OUT.exists() else None
    for attempt, use_proxy in enumerate((False, False, True), start=1):
        via = " through free proxies" if use_proxy else ""
        print(f"attempt {attempt}: fetching Scholar profile {SCHOLAR_ID}{via}")
        try:
            if use_proxy:  # last-ditch attempt through free proxies (flaky)
                pg = ProxyGenerator()
                if pg.FreeProxies():
                    scholarly.use_proxy(pg)
            data = fetch()
            if not sane(data, old):
                print("::error::fetched data failed sanity check")
                sys.exit(1)
            strip = lambda d: {k: v for k, v in d.items() if k != "fetched_at"}
            if old and strip(data) == strip(old):
                print("No change in Scholar data.")
                return
            OUT.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
            print(f"Updated {OUT}")
            return
        except BLOCKED_ERRORS as e:
            print(f"::warning::attempt {attempt} failed: {type(e).__name__}: {e}")
            time.sleep(15 * attempt)
    sys.exit(EXIT_BLOCKED)


if __name__ == "__main__":
    main()
