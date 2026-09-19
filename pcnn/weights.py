"""Salience and edge-weight policy.

The single rule this module exists to enforce: **weight only ever goes up on
its own.**  Every automated path (distillation, consolidation, touch boosts)
may raise a neuron's salience and may never lower it.  Lowering is a deliberate
human act (`pcnn demote`) and is written to the changelog with a reason.

This is the opposite of the usual recency-decay design, and it is intentional.
A decision taken on day one must not fade because nobody touched it for a
month - that fading is exactly how context gets lost.
"""

from __future__ import annotations

from collections import Counter

from . import schema
from .schema import Edge, Neuron
from .store import Network, today

#: a neuron touched repeatedly earns a little weight, but never enough to
#: outrank a layer that is structurally more important
TOUCH_BOOST = 0.02
TOUCH_BOOST_CEILING = 0.15

#: bounds for co-occurrence driven edge reinforcement
EDGE_MIN = 0.10
EDGE_MAX = 1.00
EDGE_REINFORCE = 0.05


def floor_for(n: Neuron) -> float:
    return schema.LAYERS.get(n.layer, 0.0)


def ceiling_for(n: Neuron) -> float:
    """Touch boosts saturate here; explicit writes may still set up to 1.00."""
    return min(1.0, floor_for(n) + TOUCH_BOOST_CEILING)


def enforce_floors(net: Network) -> list[str]:
    """Raise any neuron that sits below its layer floor.  Returns changed ids."""
    changed = []
    for n in list(net.neurons.values()):
        f = floor_for(n)
        if n.salience < f - 1e-9:
            n.salience = f
            net.put(n)
            net.log("floor", n.id, cause="enforce_floors",
                    detail={"salience": round(f, 2)})
            changed.append(n.id)
    return changed


def raise_salience(net: Network, nid: str, value: float, *, cause: str) -> bool:
    """Set salience to `value` if that is an increase.  Never lowers."""
    n = net.neurons[nid]
    value = min(1.0, round(float(value), 2))
    if value <= n.salience + 1e-9:
        return False
    before = n.salience
    n.salience = value
    net.put(n)
    net.log("salience", nid, cause=cause,
            detail={"from": round(before, 2), "to": value})
    return True


def boost_on_touch(net: Network, nid: str, *, cause: str = "session-touch") -> None:
    """Small reinforcement for a neuron the day's work actually involved."""
    n = net.neurons.get(nid)
    if n is None:
        return
    target = min(ceiling_for(n), round(n.salience + TOUCH_BOOST, 2))
    if target > n.salience + 1e-9:
        n.salience = target
        net.put(n)
    net.touch(nid)


def demote(net: Network, nid: str, value: float, *, reason: str) -> Neuron:
    """The only way salience goes down.  Human-invoked, always logged."""
    if not reason.strip():
        raise ValueError("demote requires a reason; unexplained weight loss is the "
                         "failure mode this system exists to prevent")
    n = net.neurons[nid]
    value = round(float(value), 2)
    f = floor_for(n)
    if value < f:
        raise ValueError(
            f"{nid} is a {n.layer} neuron; salience cannot go below the layer floor "
            f"{f:.2f}. Supersede or deprecate it instead of hiding it.")
    before = n.salience
    n.salience = value
    net.put(n)
    net.log("demote", nid, cause=reason,
            detail={"from": round(before, 2), "to": value})
    return n


def supersede(net: Network, old_id: str, new_id: str, *, cause: str) -> None:
    """Retire a fact without deleting it, and record what replaced it."""
    old = net.neurons[old_id]
    old.status = "superseded"
    net.put(old)
    net.link(new_id, old_id, "supersedes", 1.00)
    net.log("supersede", old_id, cause=cause, detail={"by": new_id})


def co_touch_counts(net: Network) -> Counter:
    """How often two neurons were changed by the same recap."""
    by_cause: dict[str, set[str]] = {}
    for entry in net.read_changelog():
        cause = entry.get("cause", "")
        if not cause.startswith("recap/"):
            continue
        by_cause.setdefault(cause, set()).add(entry.get("neuron", ""))
    counts: Counter = Counter()
    for ids in by_cause.values():
        ordered = sorted(i for i in ids if i in net.neurons)
        for i, a in enumerate(ordered):
            for b in ordered[i + 1:]:
                counts[(a, b)] += 1
    return counts


def reinforce_edges(net: Network) -> list[tuple[str, str, float]]:
    """Strengthen existing edges between neurons that keep changing together.

    Deliberately never *creates* an edge: an invented relationship is a
    fabricated fact.  Unlinked but co-changing pairs are reported instead, so a
    human or the distiller can choose the correct typed edge.
    """
    counts = co_touch_counts(net)
    changed: list[tuple[str, str, float]] = []
    for (a, b), hits in counts.items():
        if hits < 2:
            continue
        for src, dst in ((a, b), (b, a)):
            n = net.neurons.get(src)
            if n is None:
                continue
            updated = False
            edges: list[Edge] = []
            for e in n.edges:
                if e.dst == dst:
                    cap = schema.WEAK_EDGE_MAX_WEIGHT if e.type in schema.WEAK_EDGE_TYPES \
                        else EDGE_MAX
                    new_w = min(cap, round(e.weight + EDGE_REINFORCE * (hits - 1), 2))
                    if new_w > e.weight + 1e-9:
                        e = Edge(e.src, e.dst, e.type, new_w)
                        updated = True
                        changed.append((src, dst, new_w))
                edges.append(e)
            if updated:
                n.edges = edges
                net.put(n)
    return changed


def unlinked_co_changes(net: Network, *, min_hits: int = 3) -> list[tuple[str, str, int]]:
    """Pairs that keep changing together but carry no edge - link candidates."""
    counts = co_touch_counts(net)
    out = []
    for (a, b), hits in counts.items():
        if hits < min_hits:
            continue
        na, nb = net.neurons.get(a), net.neurons.get(b)
        if not na or not nb:
            continue
        linked = any(e.dst == b for e in na.edges) or any(e.dst == a for e in nb.edges)
        if not linked:
            out.append((a, b, hits))
    return sorted(out, key=lambda t: -t[2])


def stamp_touched(net: Network, ids: list[str], when: str | None = None) -> None:
    when = when or today()
    for nid in ids:
        if nid in net.neurons:
            net.touch(nid, when)
