"""A still of a network, as SVG.

The HTML view is the thing you use; this is the thing you paste into a README or
an issue. It draws the same picture with the same rules - weight as radius, the
settled ring order, family hue, layer shape, bundled ties - into a file that
needs no browser and survives being viewed anywhere.

It is a second renderer, which is a cost. It earns that by being the only way to
show the view somewhere the view cannot run, and by regenerating from the same
data, so it can never drift into showing something the network does not say.
"""

from __future__ import annotations

import math
from pathlib import Path
from xml.sax.saxutils import escape

from . import layout
from .render import LAYER_STYLE
from .store import Network

WIDTH, HEIGHT, MARGIN = 1200, 760, 54

VOID = "#000000"
LINE = "#1b1916"
LINE_LIT = "#34302a"
INK = "#e8e3d9"
INK_SOFT = "#8c8578"
INK_FAINT = "#56514a"
HUE = {"intent": "#b4862f", "structure": "#27a08c", "experience": "#8e79ef"}

SERIF = ("Constantia, 'Palatino Linotype', Palatino, 'Iowan Old Style', "
         "'Book Antiqua', Georgia, serif")
GEOM = ("'Century Gothic', 'URW Gothic', Futura, 'Avenir Next', "
        "'Trebuchet MS', system-ui, sans-serif")

#: matches the HTML view
BUNDLE_FAR, BUNDLE_NEAR = 0.38, 0.90
NEAR_GAP = 0.9
LABEL_FLOOR = 0.6


def _shape(cx: float, cy: float, r: float, kind: str) -> str:
    if kind == "circle":
        return f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}"/>'
    if kind == "square":
        s = r * 0.88
        return (f'<rect x="{cx - s:.1f}" y="{cy - s:.1f}" '
                f'width="{s * 2:.1f}" height="{s * 2:.1f}"/>')
    if kind == "diamond":
        d = r * 1.2
        pts = [(cx, cy - d), (cx + d, cy), (cx, cy + d), (cx - d, cy)]
    elif kind == "triangle":
        pts = [(cx, cy - r * 1.25), (cx + r * 1.1, cy + r * 0.78),
               (cx - r * 1.1, cy + r * 0.78)]
    else:                                     # hexagon
        pts = [(cx + math.cos(math.pi / 6 + i * math.pi / 3) * r * 1.06,
                cy + math.sin(math.pi / 6 + i * math.pi / 3) * r * 1.06)
               for i in range(6)]
    return '<polygon points="' + " ".join(f"{x:.1f},{y:.1f}" for x, y in pts) + '"/>'


def draw(net: Network, out: Path, *, title: str = "") -> Path:
    live = [n for n in net.sorted_neurons() if n.status == "active"]
    if not live:
        raise ValueError(f"{net.slug} has no active neurons to draw")

    ids = [n.id for n in live]
    have = set(ids)
    ties = [(e.src, e.dst) for n in live for e in n.edges
            if e.dst in have and e.src != e.dst]
    salience = {n.id: n.salience for n in live}
    kin: dict[str, set[str]] = {i: set() for i in ids}
    for a, b in ties:
        kin[a].add(b)
        kin[b].add(a)
    order = layout.settle(ids, ties, salience, kin).order

    rx, ry = WIDTH / 2 - MARGIN, HEIGHT / 2 - MARGIN
    aspect = min(1.75, max(0.6, rx / ry))
    ax, ay = math.sqrt(aspect), 1 / math.sqrt(aspect)
    field = ry / (ay * layout.R_OUT)
    cx, cy = WIDTH / 2, HEIGHT / 2

    desc = sorted(salience.values(), reverse=True)
    place, angle_of = {}, {}
    step = 2 * math.pi / len(order)
    for i, nid in enumerate(order):
        a = -math.pi / 2 + step * i
        r = layout.rank_radius(salience[nid], desc) * field
        angle_of[nid] = a
        place[nid] = (cx + math.cos(a) * r * ax, cy + math.sin(a) * r * ay)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
        f'viewBox="0 0 {WIDTH} {HEIGHT}" role="img">',
        f'<rect width="{WIDTH}" height="{HEIGHT}" fill="{VOID}"/>',
    ]

    # the weight rings, captioned with the real weight at each boundary
    stops = []
    for f in (0.0, 1 / 3, 2 / 3, 1.0):
        s = desc[min(len(desc) - 1, round(f * (len(desc) - 1)))]
        if not stops or abs(stops[-1] - s) > 1e-9:
            stops.append(s)
    for s in stops:
        rr = layout.rank_radius(s, desc) * field
        parts.append(f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rr * ax:.1f}" '
                     f'ry="{rr * ay:.1f}" fill="none" stroke="{LINE}"/>')
        parts.append(f'<text x="{cx:.1f}" y="{cy - rr * ay:.1f}" fill="{INK_FAINT}" '
                     f'font-family="{SERIF}" font-size="11" text-anchor="middle" '
                     f'dominant-baseline="middle">{s:.2f}</text>')

    # ties, bundled towards the core exactly as the view bundles them
    for a, b in ties:
        ax0, ay0 = place[a]
        bx0, by0 = place[b]
        gap = abs(angle_of[a] - angle_of[b]) % (2 * math.pi)
        gap = 2 * math.pi - gap if gap > math.pi else gap
        pull = BUNDLE_NEAR if gap < NEAR_GAP else BUNDLE_FAR
        c1 = (cx + (ax0 - cx) * pull, cy + (ay0 - cy) * pull)
        c2 = (cx + (bx0 - cx) * pull, cy + (by0 - cy) * pull)
        colour = HUE[LAYER_STYLE.get(_layer(net, a), ("experience", ""))[0]]
        parts.append(
            f'<path d="M{ax0:.1f},{ay0:.1f} C{c1[0]:.1f},{c1[1]:.1f} '
            f'{c2[0]:.1f},{c2[1]:.1f} {bx0:.1f},{by0:.1f}" fill="none" '
            f'stroke="{colour}" stroke-width="1" opacity="0.45"/>')

    # neurons: a lit core inside a compass outline, ringed when pinned
    for n in sorted(live, key=lambda n: n.salience):
        x, y = place[n.id]
        fam, kind = LAYER_STYLE.get(n.layer, ("experience", "circle"))
        colour = HUE[fam]
        r = 5.4 + 7.0 * (n.salience ** 2)
        if n.pin:
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r + 5.5:.1f}" '
                         f'fill="none" stroke="{LINE_LIT}"/>')
        parts.append(f'<g fill="none" stroke="{colour}" stroke-width="1.3">'
                     + _shape(x, y, r, kind) + "</g>")
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{max(1, r * .34):.1f}" '
                     f'fill="{colour}"/>')

    parts.extend(_labels(live, place, salience))

    if title:
        parts.append(f'<text x="{MARGIN - 20}" y="34" fill="{INK}" '
                     f'font-family="{SERIF}" font-size="19">{escape(title)}</text>')
    parts.append(f'<text x="{MARGIN - 20}" y="{HEIGHT - 22}" fill="{INK_FAINT}" '
                 f'font-family="{GEOM}" font-size="11.5">'
                 f'distance from the core is weight'
                 f' · shape is layer · colour is family</text>')
    parts.append("</svg>")

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(parts) + "\n", encoding="utf-8")
    return out


def _layer(net: Network, nid: str) -> str:
    n = net.neurons.get(nid)
    return n.layer if n else "GLO"


def _labels(live, place, salience) -> list[str]:
    """Name the heavier neurons, skipping any that would land on another."""
    out, taken = [], []
    for n in sorted(live, key=lambda n: -n.salience):
        if n.salience < LABEL_FLOOR and not n.pin:
            continue
        text = n.head if len(n.head) <= 42 else n.head[:41] + "…"
        x, y = place[n.id]
        width = len(text) * 5.6
        y += 5.4 + 7.0 * (n.salience ** 2) + 13
        box = (x - width / 2, y - 9, x + width / 2, y + 4)
        if any(not (box[2] < t[0] or box[0] > t[2] or box[3] < t[1] or box[1] > t[3])
               for t in taken):
            continue
        taken.append(box)
        out.append(f'<text x="{x:.1f}" y="{y:.1f}" fill="{INK}" '
                   f'font-family="{SERIF}" font-size="12" text-anchor="middle" '
                   f'stroke="{VOID}" stroke-width="3" paint-order="stroke">'
                   f'{escape(text)}</text>')
    return out
