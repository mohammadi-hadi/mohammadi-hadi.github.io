#!/usr/bin/env python3
"""Fetch GitHub, OpenAlex, and ORCID data into assets/data/site-data.json.

All three are stable JSON APIs (no scraping), so unlike the Scholar fetch this
script should succeed every run. Exits nonzero without writing on failure.
Run by .github/workflows/scholar.yml daily.
"""

import json
import os
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "assets" / "data" / "site-data.json"
GITHUB_USER = "mohammadi-hadi"
ORCID_ID = "0000-0003-0860-9200"


def get_json(url: str, headers: dict | None = None) -> dict | list:
    req = urllib.request.Request(url, headers={"User-Agent": "mohammadi.cv site bot", **(headers or {})})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def fetch_github() -> dict:
    headers = {}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    repos = get_json(
        f"https://api.github.com/users/{GITHUB_USER}/repos?per_page=100&sort=pushed", headers
    )
    own = [r for r in repos if not r.get("fork")]
    return {
        "public_repos": len(own),
        "total_stars": sum(r.get("stargazers_count", 0) for r in own),
        "repos": {
            r["name"]: {
                "stars": r.get("stargazers_count", 0),
                "forks": r.get("forks_count", 0),
                "description": r.get("description"),
                "language": r.get("language"),
                "pushed_at": r.get("pushed_at"),
                "url": r.get("html_url"),
            }
            for r in own
        },
    }


def fetch_openalex() -> dict:
    a = get_json(f"https://api.openalex.org/authors/orcid:{ORCID_ID}")
    stats = a.get("summary_stats", {})
    if not a.get("works_count"):
        raise ValueError("OpenAlex author record empty — keeping previous data")
    return {
        "works_count": a.get("works_count", 0),
        "cited_by_count": a.get("cited_by_count", 0),
        "h_index": stats.get("h_index", 0),
        "i10_index": stats.get("i10_index", 0),
    }


def fetch_orcid() -> dict:
    w = get_json(
        f"https://pub.orcid.org/v3.0/{ORCID_ID}/works", {"Accept": "application/json"}
    )
    groups = w.get("group", [])
    latest = None
    for g in groups:
        for s in g.get("work-summary", []):
            t = (s.get("title") or {}).get("title", {}).get("value")
            y = ((s.get("publication-date") or {}).get("year") or {}).get("value")
            if t and (latest is None or (y or "0") > (latest[1] or "0")):
                latest = (t, y)
    return {
        "works_count": len(groups),
        "latest_work": {"title": latest[0], "year": latest[1]} if latest else None,
    }


def main() -> None:
    data = {"fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    failures = []
    for key, fn in (("github", fetch_github), ("openalex", fetch_openalex), ("orcid", fetch_orcid)):
        try:
            data[key] = fn()
        except Exception as e:  # noqa: BLE001
            failures.append(f"{key}: {e}")
            print(f"::warning::{key} fetch failed: {e}")
    if len(failures) == 3:
        print("::error::all sources failed")
        sys.exit(1)
    if OUT.exists():  # carry forward sections that failed this run
        old = json.loads(OUT.read_text())
        for key in ("github", "openalex", "orcid"):
            if key not in data and key in old:
                data[key] = old[key]
    OUT.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print(f"Updated {OUT}")


if __name__ == "__main__":
    main()
