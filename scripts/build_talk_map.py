#!/usr/bin/env python3
"""Draw the map of talks and posters at the top of /research/#talks.

    python3 scripts/build_talk_map.py            # rewrite the map in research/index.html
    python3 scripts/build_talk_map.py --check    # exit 1 if the page and the data disagree

The places come from scripts/data/talk_places.json. The map is plain inline
SVG for the land and HTML links for the dots, so it needs no script, no tiles
and no request to another site, and the labels stay readable at phone width.

The run refuses to write (exit 1) when the map and the list below it could
drift apart: a presentation card without an id, a card listed under no place
or under two, a listed id that is not on the page, or a card whose venue line
does not name the city it is filed under.

The outline is Natural Earth's 1:50m countries (public domain), cropped to
Europe and simplified once with --outline-from:

    python3 scripts/build_talk_map.py --outline-from ne_50m_admin_0_countries.geojson
"""
from __future__ import annotations

import argparse
import html
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "research" / "index.html"
PLACES = ROOT / "scripts" / "data" / "talk_places.json"
OUTLINE = ROOT / "scripts" / "data" / "europe_outline.json"
START, END = "<!-- talk-map:start -->", "<!-- talk-map:end -->"

REGION = (-25.0, 33.0, 45.0, 72.0)  # lon_min, lat_min, lon_max, lat_max kept in the outline
WIDTH = 720                         # viewBox width; the height follows the extent
ASPECT = 1.5                        # width / height of the drawn area
PAD_LON, PAD_LAT = 2.6, 1.7         # degrees of context around the outermost places


# ------------------------------------------------------------------ geometry

def clip(ring, x0, y0, x1, y1):
    """Sutherland-Hodgman against an axis-aligned rectangle."""
    def cut(points, inside, cross):
        out = []
        for i, p in enumerate(points):
            q = points[i - 1]
            if inside(p):
                if not inside(q):
                    out.append(cross(q, p))
                out.append(p)
            elif inside(q):
                out.append(cross(q, p))
        return out

    def at_x(x):
        return lambda a, b: (x, a[1] + (b[1] - a[1]) * (x - a[0]) / (b[0] - a[0]))

    def at_y(y):
        return lambda a, b: (a[0] + (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]), y)

    for inside, cross in ((lambda p: p[0] >= x0, at_x(x0)), (lambda p: p[0] <= x1, at_x(x1)),
                          (lambda p: p[1] >= y0, at_y(y0)), (lambda p: p[1] <= y1, at_y(y1))):
        if not ring:
            break
        ring = cut(ring, inside, cross)
    return ring


def simplify(points, tol):
    """Douglas-Peucker on an open polyline."""
    if len(points) < 3:
        return points
    keep = [False] * len(points)
    keep[0] = keep[-1] = True
    stack = [(0, len(points) - 1)]
    while stack:
        a, b = stack.pop()
        (ax, ay), (bx, by) = points[a], points[b]
        dx, dy = bx - ax, by - ay
        norm = math.hypot(dx, dy) or 1e-12
        far, idx = -1.0, -1
        for i in range(a + 1, b):
            px, py = points[i]
            d = abs(dy * (px - ax) - dx * (py - ay)) / norm
            if d > far:
                far, idx = d, i
        if far > tol:
            keep[idx] = True
            stack += [(a, idx), (idx, b)]
    return [p for p, k in zip(points, keep) if k]


def simplify_ring(ring, tol):
    """Douglas-Peucker on a closed ring: split at the point farthest from the first."""
    if len(ring) < 4:
        return ring
    x0, y0 = ring[0]
    m = max(range(len(ring)), key=lambda i: (ring[i][0] - x0) ** 2 + (ring[i][1] - y0) ** 2)
    return simplify(ring[:m + 1], tol)[:-1] + simplify(ring[m:] + ring[:1], tol)[:-1]


def area(ring):
    return abs(sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(ring, ring[1:] + ring[:1]))) / 2


# ------------------------------------------------------------------ outline

def make_outline(source: Path) -> None:
    data = json.loads(source.read_text(encoding="utf-8"))
    rings = []
    for feature in data["features"]:
        geom = feature["geometry"]
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        for poly in polys:
            for ring in poly[:1]:  # outer rings; holes are lakes, not needed at this scale
                pts = clip([tuple(p) for p in ring[:-1]], *REGION)
                pts = simplify_ring(pts, 0.02)
                if len(pts) >= 4 and area(pts) > 0.01:
                    rings.append([[round(x, 3), round(y, 3)] for x, y in pts])
    OUTLINE.write_text(json.dumps({
        "source": "Natural Earth 1:50m Admin 0 Countries, v5.1.2 (public domain), "
                  "outer rings cropped to lon -25..45, lat 33..72 and simplified at 0.02 degrees",
        "rings": rings}, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"wrote {OUTLINE.relative_to(ROOT)}: {len(rings)} rings")


# ------------------------------------------------------------------ the page

def cards(page: str) -> dict[str, dict]:
    sec = page[page.index('id="talks"'):]
    sec = sec[:sec.index("</section>")]
    found = {}
    for m in re.finditer(r'<article class="pub-card"([^>]*)>.*?<span class="pub-type">(.*?)</span>'
                         r'.*?<p class="pub-venue">(.*?)</p>', sec, re.S):
        cid = re.search(r'id="([^"]+)"', m.group(1))
        found[cid.group(1) if cid else f"(card {len(found) + 1}, no id)"] = {
            "type": m.group(2).strip().lower(), "venue": html.unescape(m.group(3))}
    return found


def element_text(page: str, eid: str) -> str | None:
    m = re.search(rf'<(\w+)[^>]*\bid="{re.escape(eid)}"[^>]*>(.*?)</\1>', page, re.S)
    return html.unescape(re.sub(r"<[^>]+>", " ", m.group(2))) if m else None


def problems_with(page: str, places: list[dict], found: dict[str, dict]) -> list[str]:
    out = []
    filed: dict[str, list[str]] = {}
    for place in places:
        for cid in place.get("cards", []):
            filed.setdefault(cid, []).append(place["city"])
            if cid not in found:
                out.append(f"{place['city']} lists {cid}, which is not a card on the page")
            elif place["city"] not in found[cid]["venue"]:
                out.append(f"{cid} is filed under {place['city']}, but its venue line says: "
                           f"{found[cid]['venue']}")
        if "attended" in place:
            text = element_text(page, place["attended"])
            if text is None:
                out.append(f"{place['city']} points at #{place['attended']}, which is not on the page")
            elif place["city"] not in text:
                out.append(f"#{place['attended']} does not mention {place['city']}")
    for cid in found:
        if cid not in filed:
            out.append(f"{cid} is not filed under any place")
        elif len(filed[cid]) > 1:
            out.append(f"{cid} is filed under {', '.join(filed[cid])}")
    return out


def plural(n: int, word: str) -> str:
    if n == 1:
        return f"a {word}"
    return f"{n} {word}s"


def listing(counts: dict[str, int]) -> str:
    parts = [plural(n, t) for t, n in counts.items() if n]
    return parts[0] if len(parts) == 1 else ", ".join(parts[:-1]) + " and " + parts[-1]


NUMBER = {1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five", 6: "Six", 7: "Seven", 8: "Eight",
          9: "Nine", 10: "Ten", 11: "Eleven", 12: "Twelve"}


def build(page: str, places: list[dict], found: dict[str, dict]) -> str:
    rings = json.loads(OUTLINE.read_text(encoding="utf-8"))["rings"]
    lons = [p["lon"] for p in places]
    lats = [p["lat"] for p in places]
    lon0, lon1 = min(lons) - PAD_LON, max(lons) + PAD_LON
    lat0, lat1 = min(lats) - PAD_LAT, max(lats) + PAD_LAT
    if lon0 < REGION[0] or lon1 > REGION[2] or lat0 < REGION[1] or lat1 > REGION[3]:
        raise SystemExit("a place lies outside the outline's region; widen REGION and rerun "
                         "--outline-from")
    k = math.cos(math.radians((lat0 + lat1) / 2))
    w, h = (lon1 - lon0) * k, lat1 - lat0
    if w / h < ASPECT:  # widen to the aspect, keeping the places centred
        extra = (ASPECT * h - w) / k / 2
        lon0, lon1 = lon0 - extra, lon1 + extra
    else:
        extra = (w / ASPECT - h) / 2
        lat0, lat1 = lat0 - extra, lat1 + extra
    height = round(WIDTH / ASPECT)
    scale = WIDTH / ((lon1 - lon0) * k)

    def xy(lon, lat):
        return (lon - lon0) * k * scale, (lat1 - lat) * scale

    paths = []
    for ring in rings:
        pts = clip([xy(*p) for p in ring], -3, -3, WIDTH + 3, height + 3)
        if len(pts) < 3:
            continue
        pts = simplify_ring(pts, 0.45)
        if len(pts) < 3 or area(pts) < 2:
            continue
        paths.append("M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in pts) + "Z")

    pins, totals, years, cities = [], {}, [], 0
    for place in places:
        x, y = xy(place["lon"], place["lat"])
        left, top = f"{100 * x / WIDTH:.2f}%", f"{100 * y / height:.2f}%"
        side = " talk-map__pin--left" if place.get("label") == "left" else ""
        if "cards" in place:
            cities += 1
            counts: dict[str, int] = {}
            for cid in place["cards"]:
                counts[found[cid]["type"]] = counts.get(found[cid]["type"], 0) + 1
                totals[found[cid]["type"]] = totals.get(found[cid]["type"], 0) + 1
                years += [int(v) for v in re.findall(r"\b(20\d\d)\b", found[cid]["venue"])]
            n = len(place["cards"])
            size = 12 + 5 * (math.sqrt(n) - 1)
            label = f"{place['city']}: {listing(counts)}"
            pins.append(
                f'<a class="talk-map__pin{side}" href="#{place["cards"][0]}" '
                f'style="left:{left};top:{top};--d:{size:.0f}px" aria-label="{html.escape(label)}">'
                f'<span class="talk-map__dot"></span><span class="talk-map__label">{place["city"]} '
                f'<span class="talk-map__count">{n}</span></span></a>')
        else:
            label = f"{place['city']}: attended the {place['what']}"
            pins.append(
                f'<a class="talk-map__pin talk-map__pin--attended{side}" href="#{place["attended"]}" '
                f'style="left:{left};top:{top};--d:12px" aria-label="{html.escape(label)}">'
                f'<span class="talk-map__dot"></span><span class="talk-map__label">{place["city"]}'
                f'</span></a>')

    order = {t: totals[t] for t in ("talk", "poster", "workshop") if t in totals}
    order.update({t: n for t, n in totals.items() if t not in order})
    total = sum(totals.values())
    span = f"{min(years)} to {max(years)}" if min(years) != max(years) else str(min(years))
    attended = [p for p in places if "attended" in p]
    caption = (f"{NUMBER.get(total, total)} presentations in {NUMBER.get(cities, cities).lower()} "
               f"cities, {span}: {listing(order)}.")
    if attended:
        caption += (" The open ring is a summer school I attended." if len(attended) == 1
                    else " Open rings are events I attended.")
    caption += " Each dot links to its entry below."
    pad = "        "
    return "\n".join([
        START,
        f'{pad}<figure class="talk-map">',
        f'{pad}  <div class="talk-map__frame">',
        f'{pad}    <svg viewBox="0 0 {WIDTH} {height}" aria-hidden="true" focusable="false">'
        f'<path class="talk-map__land" d="{"".join(paths)}"/></svg>',
        *[f"{pad}    {p}" for p in pins],
        f"{pad}  </div>",
        f"{pad}  <figcaption>{caption} Outlines: Natural Earth.</figcaption>",
        f"{pad}</figure>",
        f"{pad}{END}"])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--outline-from", type=Path)
    args = ap.parse_args()
    if args.outline_from:
        make_outline(args.outline_from)
        return 0

    page = PAGE.read_text(encoding="utf-8")
    places = json.loads(PLACES.read_text(encoding="utf-8"))["places"]
    found = cards(page)
    problems = problems_with(page, places, found)
    for p in problems:
        print("FAIL", p)
    if problems:
        return 1
    if page.count(START) != 1 or page.count(END) != 1:
        print(f"FAIL the page needs exactly one {START} and one {END}")
        return 1
    block = build(page, places, found)
    new = page[:page.index(START)] + block + page[page.index(END) + len(END):]
    if args.check:
        if new != page:
            print("FAIL the map is out of date; run scripts/build_talk_map.py")
            return 1
        print("map up to date")
        return 0
    PAGE.write_text(new, encoding="utf-8")
    print(f"wrote the map: {len(places)} places, {len(found)} cards, "
          f"{len(block.encode()) / 1024:.1f} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
