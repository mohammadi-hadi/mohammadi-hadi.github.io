#!/usr/bin/env python3
"""Rebuild blog/feed.xml from the posts in blog/*/index.html.

Each post carries its own metadata in a JSON-LD BlogPosting block, so the post
files stay the single source of truth: write a post, run this, commit both.

    python3 scripts/build_blog.py

Also warns when a post on disk is missing from the list on blog/index.html.
Standard library only; no build step, no dependencies.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from email.utils import format_datetime
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
BLOG = ROOT / "blog"
FEED = BLOG / "feed.xml"

SITE = "https://mohammadi.cv"
TITLE = "Hadi Mohammadi — Blog"
DESCRIPTION = (
    "Field notes on building and evaluating production LLM systems, and open "
    "guides for people studying AI and data science."
)
COPYRIGHT = "CC BY-SA 4.0, Hadi Mohammadi"


def read_post(path: Path) -> dict:
    """Pull the BlogPosting node and the article section out of one post."""
    html = path.read_text(encoding="utf-8")

    block = re.search(
        r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    if not block:
        raise SystemExit(f"{path}: no JSON-LD block")
    graph = json.loads(block.group(1)).get("@graph", [])
    posting = next((n for n in graph if n.get("@type") == "BlogPosting"), None)
    if posting is None:
        raise SystemExit(f"{path}: no BlogPosting node in the JSON-LD")

    section = re.search(
        r'<meta property="article:section" content="([^"]*)"', html)

    return {
        "slug": path.parent.name,
        "title": posting["headline"],
        "description": posting["description"],
        "url": posting["url"],
        "published": datetime.fromisoformat(posting["datePublished"]),
        "position": posting.get("position", 0),
        "section": section.group(1) if section else "",
    }


def build_feed(posts: list[dict]) -> str:
    latest = max(p["published"] for p in posts)
    items = []
    for p in posts:
        category = (f"\n      <category>{escape(p['section'])}</category>"
                    if p["section"] else "")
        items.append(f"""    <item>
      <title>{escape(p['title'])}</title>
      <link>{p['url']}</link>
      <guid isPermaLink="true">{p['url']}</guid>
      <pubDate>{format_datetime(p['published'])}</pubDate>
      <description>{escape(p['description'])}</description>{category}
    </item>""")

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>{escape(TITLE)}</title>
    <link>{SITE}/blog/</link>
    <description>{escape(DESCRIPTION)}</description>
    <language>en</language>
    <copyright>{escape(COPYRIGHT)}</copyright>
    <lastBuildDate>{format_datetime(latest)}</lastBuildDate>
    <atom:link href="{SITE}/blog/feed.xml" rel="self" type="application/rss+xml"/>
{chr(10).join(items)}
  </channel>
</rss>
"""


def main() -> int:
    paths = sorted(BLOG.glob("*/index.html"))
    if not paths:
        raise SystemExit("no posts found under blog/")
    posts = [read_post(p) for p in paths]

    # Newest first, then in series order when several share a date.
    posts.sort(key=lambda p: (-p["published"].timestamp(), p["position"]))

    FEED.write_text(build_feed(posts), encoding="utf-8")
    print(f"blog/feed.xml — {len(posts)} posts, newest {max(p['published'] for p in posts):%Y-%m-%d}")

    index = (BLOG / "index.html").read_text(encoding="utf-8")
    missing = [p["slug"] for p in posts if f'href="/blog/{p["slug"]}/"' not in index]
    for slug in missing:
        print(f"  warning: {slug} is not linked from blog/index.html", file=sys.stderr)
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
