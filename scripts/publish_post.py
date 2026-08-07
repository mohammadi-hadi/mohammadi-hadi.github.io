#!/usr/bin/env python3
"""Publish a drafted blog post.

Drafts live finished under blog/_drafts/<slug>/. Publishing one moves it into
blog/<slug>/, stamps it with today's date, links it from the top of the field
notes list, adds it to the sitemap, and rebuilds the feed.

    python3 scripts/publish_post.py the-labels-under-the-benchmark
    python3 scripts/publish_post.py --list

The date a post carries is the date it goes live, which is why this stamps
today rather than letting a draft keep an invented one. Write whenever; publish
when you want it read.

Standard library only. Re-run scripts/make_cards.py afterwards if the post
needs a share card.
"""
from __future__ import annotations

import re
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BLOG = ROOT / "blog"
DRAFTS = BLOG / "_drafts"
INDEX = BLOG / "index.html"
SITEMAP = ROOT / "sitemap.xml"
MARKER = "<!-- field-notes:insert -->"


def die(msg: str) -> None:
    raise SystemExit(f"publish_post: {msg}")


def list_drafts() -> None:
    found = sorted(p.parent.name for p in DRAFTS.glob("*/index.html"))
    if not found:
        print("no drafts under blog/_drafts/")
        return
    print("drafts ready to publish:")
    for slug in found:
        title = re.search(r"<h1>(.*?)</h1>",
                          (DRAFTS / slug / "index.html").read_text(encoding="utf-8"))
        print(f"  {slug}\n      {title.group(1) if title else ''}")


def main() -> int:
    args = [a for a in sys.argv[1:] if a]
    if not args or args[0] in {"-h", "--help"}:
        print(__doc__)
        return 0
    if args[0] == "--list":
        list_drafts()
        return 0

    slug = args[0].strip("/")
    src = DRAFTS / slug
    dst = BLOG / slug
    if not (src / "index.html").is_file():
        die(f"no draft at blog/_drafts/{slug}/index.html (try --list)")
    if dst.exists():
        die(f"blog/{slug}/ already exists")

    today = date.today()
    iso = f"{today:%Y-%m-%d}T09:00:00+02:00"
    human = f"{today.day} {today:%B %Y}"

    html = (src / "index.html").read_text(encoding="utf-8")

    # Stamp the real publication date everywhere the draft carried a placeholder.
    html = re.sub(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+\d{2}:\d{2}', iso, html)
    html = re.sub(r'<time datetime="\d{4}-\d{2}-\d{2}">[^<]*</time>',
                  f'<time datetime="{today:%Y-%m-%d}">{human}</time>', html)
    html = re.sub(r'\n *<meta name="robots" content="noindex, nofollow">', "", html)

    title = re.search(r"<h1>(.*?)</h1>", html)
    dek = re.search(r'<p class="post-dek">(.*?)</p>', html, re.S)
    read = re.search(r"<span>(\d+) min read</span>", html)
    if not (title and dek and read):
        die("draft is missing an <h1>, a .post-dek or a read time")

    dst.mkdir(parents=True)
    (dst / "index.html").write_text(html, encoding="utf-8")
    for extra in src.iterdir():
        if extra.name != "index.html":
            extra.rename(dst / extra.name)
    (src / "index.html").unlink()
    src.rmdir()

    # Newest field note goes at the top of the list.
    index = INDEX.read_text(encoding="utf-8")
    if MARKER not in index:
        die(f"marker {MARKER} not found in blog/index.html")
    entry = f"""{MARKER}
          <li class="post-item">
            <div class="post-index"><time datetime="{today:%Y-%m-%d}">{today.day} {today:%b %Y}</time></div>
            <div>
              <h3><a href="/blog/{slug}/">{title.group(1)}</a></h3>
              <p>{' '.join(dek.group(1).split())}</p>
              <p class="post-byline"><span>{read.group(1)} min read</span></p>
            </div>
          </li>"""
    index = index.replace(MARKER, entry, 1)
    index = index.replace(
        '        "blogPost": [\n',
        f'        "blogPost": [\n          {{ "@id": "https://mohammadi.cv/blog/{slug}/#post" }},\n', 1)
    INDEX.write_text(index, encoding="utf-8")

    loc = f"https://mohammadi.cv/blog/{slug}/"
    sitemap = SITEMAP.read_text(encoding="utf-8")
    if loc not in sitemap:
        anchor = "  <url>\n    <loc>https://mohammadi.cv/blog/</loc>"
        sitemap = sitemap.replace(
            anchor,
            f"  <url>\n    <loc>{loc}</loc>\n    <priority>0.7</priority>\n  </url>\n{anchor}", 1)
        SITEMAP.write_text(sitemap, encoding="utf-8")

    print(f"published blog/{slug}/  ({human})")
    subprocess.run([sys.executable, str(ROOT / "scripts" / "build_blog.py")], check=False)
    print(f"\nnext: add a CARDS row for '{slug}' in scripts/make_cards.py, then\n"
          f"  git add -A blog sitemap.xml && git commit -m 'Publish: {title.group(1)}'")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
