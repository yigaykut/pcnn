"""Retrieval by spreading activation.

Linear reading does not scale: a mature network holds hundreds of neurons and
a session can only afford to load a handful.  Seeding by term match alone
misses everything phrased differently, which is exactly how context gets lost.

So retrieval works the way the graph is shaped: terms light up seed neurons,
activation flows along typed edges, and a neuron that no query term touched can
still surface because a decision three hops away depends on it.  Each result
carries the path that activated it, so the reader can see *why* it matched.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

from .schema import Neuron

#: how much activation survives one hop
HOP_DECAY = 0.60
#: edges are semantically directed, but relevance flows both ways at a discount
REVERSE_FACTOR = 0.80
MAX_HOPS = 3
CUTOFF = 0.15
TOP_K = 12

#: field -> how strongly a term hit there seeds the neuron
FIELD_WEIGHTS = {
    "signals": 1.00,   # curated retrieval keys
    "head": 0.85,
    "anchors": 0.70,   # file paths, so a code question finds its context
    "id": 0.90,
    "description": 0.45,
    "rationale": 0.35,
    "note": 0.20,
}

_TOKEN_RE = re.compile(r"[a-z0-9_.]+")
_STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "is", "are",
    "was", "were", "be", "how", "what", "why", "does", "do", "did", "with",
    "from", "by", "at", "it", "its", "this", "that", "we", "our", "i",
}


def tokenize(text: str) -> list[str]:
    out = []
    for raw in _TOKEN_RE.findall(text.lower()):
        for part in re.split(r"[._/\\-]+", raw):
            if len(part) < 2 or part in _STOPWORDS:
                continue
            out.append(_stem(part))
    return out


def _stem(word: str) -> str:
    """Deliberately crude: enough to join plural/gerund forms, nothing more."""
    for suffix in ("ing", "ed", "es", "s"):
        if len(word) > 4 and word.endswith(suffix):
            return word[: -len(suffix)]
    return word


@dataclass
class Hit:
    neuron: Neuron
    activation: float
    hops: int
    via: list[str]          # activation path, seed first
    seeded: float           # direct term-match contribution

    @property
    def direct(self) -> bool:
        return self.hops == 0


def _field_tokens(n: Neuron) -> dict[str, set[str]]:
    return {
        "signals": set(tokenize(" ".join(n.signals))),
        "head": set(tokenize(n.head)),
        "anchors": set(tokenize(" ".join(n.anchors))),
        "id": set(tokenize(n.id)),
        "description": set(tokenize(n.description)),
        "rationale": set(tokenize(n.rationale)),
        "note": set(tokenize(n.note)),
    }


def seed(neurons: list[Neuron], query: str) -> dict[str, float]:
    """Term-match score per neuron, normalised to 0..1."""
    terms = set(tokenize(query))
    if not terms:
        return {}
    raw: dict[str, float] = {}
    for n in neurons:
        fields = _field_tokens(n)
        score = 0.0
        for fname, weight in FIELD_WEIGHTS.items():
            hits = terms & fields[fname]
            if hits:
                # diminishing returns per field, so one verbose description
                # cannot outrank a precise signals match
                score += weight * (1.0 + math.log(len(hits)))
        if score > 0:
            raw[n.id] = score
    if not raw:
        return {}
    top = max(raw.values())
    return {k: v / top for k, v in raw.items()}


def activate(neurons: list[Neuron], query: str, *, max_hops: int = MAX_HOPS,
             cutoff: float = CUTOFF, top_k: int = TOP_K) -> list[Hit]:
    """Seed by term match, then spread along edges.  Returns ranked hits."""
    by_id = {n.id: n for n in neurons}
    seeds = seed(neurons, query)
    if not seeds:
        return []

    adjacency: dict[str, list[tuple[str, float, str]]] = {nid: [] for nid in by_id}
    for n in neurons:
        for e in n.edges:
            if e.dst not in by_id:
                continue
            adjacency[n.id].append((e.dst, e.weight, e.type))
            adjacency[e.dst].append((n.id, e.weight * REVERSE_FACTOR, e.type))

    activation: dict[str, float] = {}
    hops: dict[str, int] = {}
    via: dict[str, list[str]] = {}

    frontier: dict[str, float] = {}
    for nid, s in seeds.items():
        a = s * by_id[nid].salience
        frontier[nid] = a
        activation[nid] = a
        hops[nid] = 0
        via[nid] = [nid]

    for hop in range(1, max_hops + 1):
        nxt: dict[str, float] = {}
        for src, a_src in frontier.items():
            for dst, w, _etype in adjacency.get(src, ()):
                delivered = a_src * w * (HOP_DECAY ** hop)
                if delivered < cutoff * 0.5:
                    continue
                if delivered > nxt.get(dst, 0.0):
                    nxt[dst] = delivered
                    if delivered > activation.get(dst, 0.0):
                        hops[dst] = hop
                        via[dst] = via[src] + [dst]
                activation[dst] = activation.get(dst, 0.0) + delivered
        if not nxt:
            break
        frontier = nxt

    hits = [
        Hit(neuron=by_id[nid], activation=round(a, 4), hops=hops.get(nid, 0),
            via=via.get(nid, [nid]), seeded=round(seeds.get(nid, 0.0), 3))
        for nid, a in activation.items() if a >= cutoff
    ]
    hits.sort(key=lambda h: (-h.activation, h.hops, h.neuron.id))
    return hits[:top_k]


def format_hits(hits: list[Hit], *, verbose: bool = False) -> str:
    """Render results for a terminal or for injection into a session."""
    if not hits:
        return "no neurons above the activation cutoff; try broader terms"
    out = []
    for h in hits:
        n = h.neuron
        flag = "direct" if h.direct else f"{h.hops}-hop via {' -> '.join(h.via[:-1])}"
        out.append(f"{n.id} | a={h.activation:.2f} | s={n.salience:.2f} | "
                   f"{n.layer} | {flag}")
        out.append(f"    {n.head}")
        if verbose:
            out.append(f"    fact: {n.description}")
            if n.rationale:
                out.append(f"    why: {n.rationale}")
        if n.anchors:
            out.append(f"    anchors: {', '.join(n.anchors)}")
    return "\n".join(out)
