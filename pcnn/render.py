"""Render a network to a single self-contained HTML file.

No CDN, no build step, no vendored library: the payload is injected into a
template that carries its own force-directed layout and canvas renderer.  The
output has to survive being opened from disk months from now, so it depends on
nothing but the browser.

Colour encoding follows the data-viz rule that only three hues clear the
all-pairs colour-vision floor.  The eleven layers therefore share three hues by
*family* and are told apart by node *shape* - composite encoding rather than a
cycled palette - with every layer named in the legend and labels drawn on the
canvas.  The three pigments were validated against a true-black surface:
worst all-pairs CVD dE 11.3, normal-vision dE 17.0.

Position carries salience: the page is a radial field whose concentric rings
are salience bands, so a neuron's distance from the core *is* its weight.  That
is the one promise the system makes, drawn as the geometry of the page rather
than stated beside it.
"""

from __future__ import annotations

import json
from pathlib import Path

from . import audit as audit_mod
from . import layout
from .store import Network, home

TEMPLATE = Path(__file__).parent / "templates" / "network.html.tmpl"
DATA_MARKER = "/*__PCNN_DATA__*/"

#: layer -> (family, shape).  Families map to the three validated hues.
LAYER_STYLE: dict[str, tuple[str, str]] = {
    "IDENT": ("intent", "hexagon"),
    "DEC":   ("intent", "diamond"),
    "CON":   ("intent", "square"),
    "ARC":   ("structure", "hexagon"),
    "IMP":   ("structure", "circle"),
    "DAT":   ("structure", "square"),
    "OPS":   ("structure", "triangle"),
    "GOT":   ("experience", "triangle"),
    "TODO":  ("experience", "circle"),
    "GLO":   ("experience", "square"),
    "PAT":   ("experience", "diamond"),
}

FAMILY_LABEL = {
    "intent": "intent",
    "structure": "structure",
    "experience": "experience",
}

#: salience stops the radial rings are drawn at, outermost last
SALIENCE_RINGS = [1.00, 0.85, 0.70, 0.55]


def payload(nets: dict[str, Network], reports: dict[str, audit_mod.Report]) -> dict:
    nodes: list[dict] = []
    edges: list[dict] = []
    for slug, net in nets.items():
        g = net.graph_dict()
        for node in g["nodes"]:
            family, shape = LAYER_STYLE.get(node["layer"], ("experience", "circle"))
            node["family"] = family
            node["shape"] = shape
            node["project"] = slug
            nodes.append(node)
        for e in g["edges"]:
            e["project"] = slug
            edges.append(e)
    # Where each neuron sits on the ring is worked out here, once, and shipped
    # with the data. The page then draws the same picture instantly instead of
    # solving a layout every time it is opened.
    live = [n for n in nodes if n["status"] == "active"]
    ids = [n["id"] for n in live]
    have = set(ids)
    ties = [(e["src"], e["dst"]) for e in edges
            if e["src"] in have and e["dst"] in have and e["src"] != e["dst"]]
    salience = {n["id"]: float(n.get("salience") or 0) for n in live}
    kin: dict[str, set[str]] = {i: set() for i in ids}
    for a, b in ties:
        kin[a].add(b)
        kin[b].add(a)
    plan = layout.settle(ids, ties, salience, kin)

    return {
        "generated": next(iter(nets.values())).graph_dict()["generated"] if nets else "",
        "projects": sorted(nets),
        "nodes": nodes,
        "edges": edges,
        "layerStyle": {k: {"family": v[0], "shape": v[1]} for k, v in LAYER_STYLE.items()},
        "familyLabel": FAMILY_LABEL,
        "rings": SALIENCE_RINGS,
        "order": plan.order,
        "crossings": {"settled": plan.crossings, "before": plan.seeded_crossings},
        "reports": {slug: rep.to_dict() for slug, rep in reports.items()},
    }


def write_html(data: dict, out: Path, *, title: str, subtitle: str) -> Path:
    template = TEMPLATE.read_text(encoding="utf-8")
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    html = (template
            .replace("__PCNN_TITLE__", title)
            .replace("__PCNN_SUBTITLE__", subtitle)
            .replace(DATA_MARKER, blob))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return out


def render_project(net: Network, report: audit_mod.Report | None = None) -> Path:
    rep = report or audit_mod.run(net)
    data = payload({net.slug: net}, {net.slug: rep})
    active = sum(1 for n in net.neurons.values() if n.status == "active")
    return write_html(
        data, home() / "output" / f"{net.slug}.html",
        title=f"{net.slug} context network",
        subtitle=f"{len(net.neurons)} neurons, {active} active")


def render_global(nets: dict[str, Network]) -> Path:
    reports = {slug: audit_mod.run(net) for slug, net in nets.items()}
    data = payload(nets, reports)
    total = sum(len(n.neurons) for n in nets.values())
    return write_html(
        data, home() / "output" / "network.html",
        title="Project context network",
        subtitle=f"{len(nets)} projects, {total} neurons")
