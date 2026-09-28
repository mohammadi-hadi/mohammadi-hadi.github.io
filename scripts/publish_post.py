#!/usr/bin/env python3
"""Publish a drafted blog post.

Drafts are kept outside this repository, so nothing unpublished is public.
Each one is a finished folder <drafts>/<slug>/. Publishing one moves it into
blog/<slug>/, stamps it with the time it goes live, links it from the top of
the field notes list, adds it to the sitemap, and rebuilds the feed.

    WL_DRAFTS=/path/to/site-drafts python3 scripts/publish_post.py <slug>
    python3 scripts/publish_post.py --drafts /path/to/site-drafts --list

The drafts directory comes from --drafts, else the WL_DRAFTS environment
variable, else ~/Documents/Weekend-Learning/site-drafts if that exists.

The date a post carries is the moment it goes live, which is why this stamps
the current time in Europe/Amsterdam rather than letting a draft keep an
invented one. Write whenever; publish when you want it read.

Standard library only. Re-run scripts/make_cards.py afterwards if the post
needs a share card.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
BLOG = ROOT / "blog"
DEFAULT_DRAFTS = Path.home() / "Documents" / "Weekend-Learning" / "site-drafts"
INDEX = BLOG / "index.html"
SITEMAP = ROOT / "sitemap.xml"
MARKER = "<!-- field-notes:insert -->"


def die(msg: str) -> None:
    raise SystemExit(f"publish_post: {msg}")


def drafts_dir(arg: str | None) -> Path:
    """Resolve the drafts directory: --drafts, then WL_DRAFTS, then the default."""
    if arg:
        chosen, source = Path(arg).expanduser(), "--drafts"
    elif os.environ.get("WL_DRAFTS"):
        chosen, source = Path(os.environ["WL_DRAFTS"]).expanduser(), "WL_DRAFTS"
    elif DEFAULT_DRAFTS.is_dir():
        return DEFAULT_DRAFTS
    else:
        die("no drafts directory. Drafts live outside this repository: pass "
            "--drafts <dir> or set WL_DRAFTS=<dir> to the folder that holds "
            "<slug>/index.html.")
    if not chosen.is_dir():
        die(f"{source} points at {chosen}, which is not a directory")
    return chosen


def list_drafts(drafts: Path) -> None:
    found = sorted(p.parent.name for p in drafts.glob("*/index.html"))
    if not found:
        print(f"no drafts under {drafts}")
        return
    print("drafts ready to publish:")
    for slug in found:
        title = re.search(r"<h1>(.*?)</h1>",
                          (drafts / slug / "index.html").read_text(encoding="utf-8"))
        print(f"  {slug}\n      {title.group(1) if title else ''}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("slug", nargs="?", help="folder name of the draft to publish")
    parser.add_argument("--list", action="store_true", help="list the drafts and exit")
    parser.add_argument("--drafts", metavar="DIR",
                        help="drafts directory (default: $WL_DRAFTS, then "
                             "~/Documents/Weekend-Learning/site-drafts)")
    opts = parser.parse_args()
    if not opts.slug and not opts.list:
        parser.print_help()
        return 0

    drafts = drafts_dir(opts.drafts)
    if opts.list:
        list_drafts(drafts)
        return 0

    slug = opts.slug.strip("/")
    src = drafts / slug
    dst = BLOG / slug
    if not (src / "index.html").is_file():
        die(f"no draft at {src / 'index.html'} (try --list)")
    if dst.exists():
        die(f"blog/{slug}/ already exists")

    now = datetime.now(ZoneInfo("Europe/Amsterdam"))
    today = now.date()
    iso = now.isoformat(timespec="seconds")
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
            shutil.move(str(extra), str(dst / extra.name))
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
