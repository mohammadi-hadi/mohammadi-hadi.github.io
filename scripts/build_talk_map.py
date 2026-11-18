#!/usr/bin/env python3
"""Draw the map of talks, posters and papers at the top of /research/#talks.

    python3 scripts/build_talk_map.py            # rewrite the map in research/index.html
    python3 scripts/build_talk_map.py --check    # exit 1 if the page and the data disagree

The places come from scripts/data/talk_places.json. Places in Europe go on the
main map; anything further away goes on a small world inset beside it. Land is
plain inline SVG and the dots are HTML links, so the map needs no script, no
tiles and no request to another site, and the labels stay readable at phone
width.

The run refuses to write (exit 1) when the map and the list below it could
drift apart: a presentation card without an id, a card listed under no place
or under two, a listed id that is not on the page, or a card whose venue line
does not name the city it is filed under.

The outlines are Natural Earth's countries (public domain): 1:50m cropped to
Europe for the main map, 1:110m for the inset. Each is simplified once:

    python3 scripts/build_talk_map.py --outline-from ne_50m_admin_0_countries.geojson
    python3 scripts/build_talk_map.py --world-outline-from ne_110m_admin_0_countries.geojson
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
WORLD = ROOT / "scripts" / "data" / "world_outline.json"
START, END = "<!-- talk-map:start -->", "<!-- talk-map:end -->"

REGION = (-25.0, 33.0, 45.0, 72.0)  # lon_min, lat_min, lon_max, lat_max: "Europe" here
WIDTH, ASPECT = 720, 1.25           # main map viewBox width, and width / height
PAD_LON, PAD_LAT = 2.6, 1.7         # degrees of context around the outermost places
INSET_WIDTH = 360                   # inset viewBox width
INSET_EXTENT = (-180.0, -56.0, 180.0, 78.0)
TYPE_ORDER = ("talk", "paper", "poster", "workshop")
NUMBER = {1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five", 6: "Six", 7: "Seven",
          8: "Eight", 9: "Nine", 10: "Ten", 11: "Eleven", 12: "Twelve", 13: "Thirteen",
          14: "Fourteen", 15: "Fifteen", 16: "Sixteen", 17: "Seventeen", 18: "Eighteen",
          19: "Nineteen", 20: "Twenty"}


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


# ------------------------------------------------------------------ outlines

def make_outline(source: Path, target: Path, region, tol: float, label: str) -> None:
    data = json.loads(source.read_text(encoding="utf-8"))
    rings = []
    for feature in data["features"]:
        geom = feature["geometry"]
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        for poly in polys:
            pts = clip([tuple(p) for p in poly[0][:-1]], *region)  # outer ring; holes are lakes
            pts = simplify_ring(pts, tol)
            if len(pts) >= 4 and area(pts) > tol * tol:
                rings.append([[round(x, 3), round(y, 3)] for x, y in pts])
    target.write_text(json.dumps({"source": label, "rings": rings}, separators=(",", ":")) + "\n",
                      encoding="utf-8")
    print(f"wrote {target.relative_to(ROOT)}: {len(rings)} rings")


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
        if place.get("upcoming") and not place.get("when"):
            out.append(f"{place['city']} is upcoming but has no 'when'")
    for cid in found:
        if cid not in filed:
            out.append(f"{cid} is not filed under any place")
        elif len(filed[cid]) > 1:
            out.append(f"{cid} is filed under {', '.join(filed[cid])}")
    return out


def plural(n: int, word: str) -> str:
    return f"a {word}" if n == 1 else f"{n} {word}s"


def listing(counts: dict[str, int]) -> str:
    parts = [plural(n, t) for t, n in counts.items() if n]
    return parts[0] if len(parts) == 1 else ", ".join(parts[:-1]) + " and " + parts[-1]


def in_europe(place: dict) -> bool:
    return REGION[0] <= place["lon"] <= REGION[2] and REGION[1] <= place["lat"] <= REGION[3]


def land_path(rings, xy, width, height, tol, min_area):
    paths = []
    for ring in rings:
        pts = clip([xy(*p) for p in ring], -3, -3, width + 3, height + 3)
        if len(pts) < 3:
            continue
        pts = simplify_ring(pts, tol)
        if len(pts) < 3 or area(pts) < min_area:
            continue
        coords = [f"{x:.0f} {y:.0f}" for x, y in pts]
        coords = [c for i, c in enumerate(coords) if i == 0 or c != coords[i - 1]]
        if len(coords) >= 3:
            paths.append("M" + "L".join(coords) + "Z")
    return "".join(paths)


def pin(place: dict, found: dict[str, dict], x: float, y: float, width: float, height: float) -> str:
    side = {"left": " talk-map__pin--left", "above": " talk-map__pin--above"}.get(
        place.get("label", "right"), "")
    where = f"left:{100 * x / width:.2f}%;top:{100 * y / height:.2f}%"
    if "attended" in place:
        label = f"{place['city']}: attended the {place['what']}"
        return (f'<a class="talk-map__pin talk-map__pin--attended{side}" href="#{place["attended"]}" '
                f'style="{where};--d:10px" aria-label="{html.escape(label)}">'
                f'<span class="talk-map__dot"></span><span class="talk-map__label">{place["city"]}'
                f'</span></a>')
    counts: dict[str, int] = {}
    for cid in place["cards"]:
        counts[found[cid]["type"]] = counts.get(found[cid]["type"], 0) + 1
    n = len(place["cards"])
    if place.get("upcoming"):
        label = f"{place['city']}: {listing(counts)}, coming up in {place['when']}"
        return (f'<a class="talk-map__pin talk-map__pin--upcoming{side}" href="#{place["cards"][0]}" '
                f'style="{where};--d:10px" aria-label="{html.escape(label)}">'
                f'<span class="talk-map__dot"></span><span class="talk-map__label">{place["city"]} '
                f'<span class="talk-map__when">{place["when"][:3]} {place["when"].split()[-1]}</span></span></a>')
    size = 10 + 2 * (math.sqrt(n) - 1)
    label = f"{place['city']}: {listing(counts)}"
    return (f'<a class="talk-map__pin{side}" href="#{place["cards"][0]}" '
            f'style="{where};--d:{size:.0f}px" aria-label="{html.escape(label)}">'
            f'<span class="talk-map__dot"></span><span class="talk-map__label">{place["city"]} '
            f'<span class="talk-map__count">{n}</span></span></a>')


def build(places: list[dict], found: dict[str, dict]) -> str:
    europe = [p for p in places if in_europe(p)]
    world = [p for p in places if not in_europe(p)]
    pad = "        "

    # main map: Europe, framed on the places it holds
    lons, lats = [p["lon"] for p in europe], [p["lat"] for p in europe]
    lon0, lon1 = min(lons) - PAD_LON, max(lons) + PAD_LON
    lat0, lat1 = min(lats) - PAD_LAT, max(lats) + PAD_LAT
    k = math.cos(math.radians((lat0 + lat1) / 2))
    w, h = (lon1 - lon0) * k, lat1 - lat0
    if w / h < ASPECT:
        extra = (ASPECT * h - w) / k / 2
        lon0, lon1 = lon0 - extra, lon1 + extra
    else:
        extra = (w / ASPECT - h) / 2
        lat0, lat1 = lat0 - extra, lat1 + extra
    height = round(WIDTH / ASPECT)
    scale = WIDTH / ((lon1 - lon0) * k)

    def xy(lon, lat):
        return (lon - lon0) * k * scale, (lat1 - lat) * scale

    rings = json.loads(OUTLINE.read_text(encoding="utf-8"))["rings"]
    main = [f'{pad}  <div class="talk-map__frame talk-map__frame--main">',
            f'{pad}    <svg viewBox="0 0 {WIDTH} {height}" aria-hidden="true" focusable="false">'
            f'<path class="talk-map__land" d="{land_path(rings, xy, WIDTH, height, 1.2, 8)}"/></svg>']
    main += [f"{pad}    {pin(p, found, *xy(p['lon'], p['lat']), WIDTH, height)}" for p in europe]
    main.append(f"{pad}  </div>")

    # inset: the world, with a box where the main map sits
    inset = []
    if world:
        ix0, iy0, ix1, iy1 = INSET_EXTENT
        iscale = INSET_WIDTH / (ix1 - ix0)
        iheight = round((iy1 - iy0) * iscale)

        def ixy(lon, lat):
            return (lon - ix0) * iscale, (iy1 - lat) * iscale

        wrings = json.loads(WORLD.read_text(encoding="utf-8"))["rings"]
        (bx0, by0), (bx1, by1) = ixy(lon0, lat1), ixy(lon1, lat0)
        inset = [f'{pad}  <div class="talk-map__frame talk-map__frame--inset">',
                 f'{pad}    <svg viewBox="0 0 {INSET_WIDTH} {iheight}" aria-hidden="true" '
                 f'focusable="false"><path class="talk-map__land" '
                 f'd="{land_path(wrings, ixy, INSET_WIDTH, iheight, 1.0, 4)}"/>'
                 f'<rect class="talk-map__box" x="{bx0:.1f}" y="{by0:.1f}" width="{bx1 - bx0:.1f}" '
                 f'height="{by1 - by0:.1f}"/></svg>',
                 f'{pad}    <span class="talk-map__inset-title">Outside Europe</span>']
        inset += [f"{pad}    {pin(p, found, *ixy(p['lon'], p['lat']), INSET_WIDTH, iheight)}"
                  for p in world]
        inset.append(f"{pad}  </div>")

    # caption, counted from the cards so it cannot disagree with the list
    totals: dict[str, int] = {}
    years: list[int] = []
    cities = 0
    for place in places:
        if "cards" not in place or place.get("upcoming"):
            continue
        cities += 1
        for cid in place["cards"]:
            totals[found[cid]["type"]] = totals.get(found[cid]["type"], 0) + 1
            years += [int(v) for v in re.findall(r"\b(20\d\d)\b", found[cid]["venue"])]
    order = {t: totals[t] for t in TYPE_ORDER if t in totals}
    order.update({t: n for t, n in totals.items() if t not in order})
    total = sum(totals.values())
    span = f"{min(years)} to {max(years)}" if min(years) != max(years) else str(min(years))
    caption = (f"{NUMBER.get(total, total)} presentations in {NUMBER.get(cities, cities).lower()} "
               f"cities, {span}: {listing(order)}.")
    attended = [p for p in places if "attended" in p]
    if attended:
        caption += (" The open ring is a summer school I attended." if len(attended) == 1
                    else " Open rings are events I attended.")
    for p in places:
        if p.get("upcoming"):
            caption += f" The dashed ring is still to come: {p['city']}, {p['when']}."
    caption += " Each dot links to its entry below. Outlines: Natural Earth."

    return "\n".join([START, f'{pad}<figure class="talk-map">', *main, *inset,
                      f"{pad}  <figcaption>{caption}</figcaption>", f"{pad}</figure>",
                      f"{pad}{END}"])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--outline-from", type=Path)
    ap.add_argument("--world-outline-from", type=Path)
    args = ap.parse_args()
    if args.outline_from:
        make_outline(args.outline_from, OUTLINE, REGION, 0.02,
                     "Natural Earth 1:50m Admin 0 Countries, v5.1.2 (public domain), outer rings "
                     "cropped to lon -25..45, lat 33..72 and simplified at 0.02 degrees")
    if args.world_outline_from:
        make_outline(args.world_outline_from, WORLD, INSET_EXTENT, 0.3,
                     "Natural Earth 1:110m Admin 0 Countries, v5.1.2 (public domain), outer rings "
                     "cropped to lat -56..78 and simplified at 0.3 degrees")
    if args.outline_from or args.world_outline_from:
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
    block = build(places, found)
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
