"""Consolidation - keep the graph from silting up with near-duplicates.

Distillation runs once per session with only that session's view, so the same
fact can enter the network twice under different wording.  Left alone, the
duplicates split a fact's edges and weaken retrieval for both copies.

Merging is the one operation that could destroy context, so it is deliberately
timid: it only fires on near-identical neurons, it unions every field rather
than choosing between them, and the loser is superseded rather than deleted.
Anything less certain is reported as a candidate for a human to judge.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import weights
from .query import tokenize
from .schema import Edge, Neuron
from .store import Network

#: auto-merge only above this similarity; below it, report and move on
AUTO_MERGE = 0.90
REPORT_FROM = 0.72


def similarity(a: Neuron, b: Neuron) -> float:
    """Jaccard over head + signals, bonused by shared code anchors."""
    ta = set(tokenize(a.head)) | set(tokenize(" ".join(a.signals)))
    tb = set(tokenize(b.head)) | set(tokenize(" ".join(b.signals)))
    if not ta or not tb:
        return 0.0
    jaccard = len(ta & tb) / len(ta | tb)
    anchors = set(a.anchors) & set(b.anchors)
    bonus = 0.10 if anchors else 0.0
    return min(1.0, jaccard + bonus)


@dataclass
class Consolidation:
    merged: list[tuple[str, str]]
    candidates: list[tuple[str, str, float]]
    reweighted: int

    def __str__(self) -> str:
        bits = [f"{len(self.merged)} merged", f"{len(self.candidates)} candidate(s)",
                f"{self.reweighted} edge weight(s) reinforced"]
        out = ", ".join(bits)
        for a, b, score in self.candidates:
            out += f"\n    candidate {a} ~ {b} ({score:.2f}) - review manually"
        return out


def overlaps(a: Neuron, b: Neuron) -> bool:
    """Same layer, shared retrieval keys and shared code: a duplicate by evidence.

    Lexical similarity misses two neurons that state the same fact in different
    words, which is exactly what a repeated distillation produces.  When they
    also point at the same code and answer to the same signals, that is worth a
    human look even though the wording barely overlaps.
    """
    # signals are free text, so "duplicate" and "duplicate neurons" are the same
    # key written twice; compare them tokenised rather than as exact strings
    sa = set(tokenize(" ".join(a.signals)))
    sb = set(tokenize(" ".join(b.signals)))
    return len(sa & sb) >= 2 and bool(set(a.anchors) & set(b.anchors))


def pairs(net: Network) -> list[tuple[Neuron, Neuron, float]]:
    active = [n for n in net.sorted_neurons() if n.status == "active"]
    out = []
    for i, a in enumerate(active):
        for b in active[i + 1:]:
            if a.layer != b.layer:
                continue
            score = similarity(a, b)
            if score >= REPORT_FROM or overlaps(a, b):
                out.append((a, b, score))
    return sorted(out, key=lambda t: -t[2])


def absorb(keeper: Neuron, loser: Neuron) -> Neuron:
    """Union every field into the keeper.  Nothing the loser knew is dropped."""
    keeper.salience = max(keeper.salience, loser.salience)
    keeper.pin = keeper.pin or loser.pin
    keeper.signals = sorted(set(keeper.signals) | set(loser.signals))
    keeper.anchors = sorted(set(keeper.anchors) | set(loser.anchors))
    keeper.evidence = sorted(set(keeper.evidence) | set(loser.evidence))
    keeper.first_seen = min(x for x in (keeper.first_seen, loser.first_seen) if x) \
        if (keeper.first_seen or loser.first_seen) else keeper.first_seen
    keeper.last_touched = max(keeper.last_touched, loser.last_touched)
    keeper.revision += 1

    if loser.description and loser.description not in keeper.description:
        keeper.description = f"{keeper.description} {loser.description}".strip()
    if loser.rationale and loser.rationale not in keeper.rationale:
        keeper.rationale = f"{keeper.rationale} {loser.rationale}".strip()
    if loser.alternatives_rejected and \
            loser.alternatives_rejected not in keeper.alternatives_rejected:
        keeper.alternatives_rejected = (
            f"{keeper.alternatives_rejected} {loser.alternatives_rejected}").strip()

    keyed = {(e.type, e.dst): e for e in keeper.edges}
    for e in loser.edges:
        if e.dst == keeper.id:
            continue
        prev = keyed.get((e.type, e.dst))
        if prev is None or e.weight > prev.weight:
            keyed[(e.type, e.dst)] = Edge(keeper.id, e.dst, e.type, e.weight)
    keeper.edges = list(keyed.values())
    return keeper


def redirect_inbound(net: Network, old_id: str, new_id: str) -> None:
    """Point every edge that referenced the loser at the keeper instead."""
    for n in list(net.neurons.values()):
        if n.id in (old_id, new_id):
            continue
        changed = False
        keyed: dict[tuple[str, str], Edge] = {}
        for e in n.edges:
            dst = new_id if e.dst == old_id else e.dst
            if dst != e.dst:
                changed = True
            key = (e.type, dst)
            prev = keyed.get(key)
            if prev is None or e.weight > prev.weight:
                keyed[key] = Edge(n.id, dst, e.type, e.weight)
        if changed:
            n.edges = list(keyed.values())
            net.put(n)


def consolidate(net: Network, *, auto: bool = True) -> Consolidation:
    merged: list[tuple[str, str]] = []
    candidates: list[tuple[str, str, float]] = []
    done: set[str] = set()

    for a, b, score in pairs(net):
        if a.id in done or b.id in done:
            continue
        if score < AUTO_MERGE or not auto or (a.pin and b.pin):
            candidates.append((a.id, b.id, round(score, 2)))
            continue
        # the older neuron keeps its id so existing references stay valid
        keeper, loser = (a, b) if (a.first_seen or "9999") <= (b.first_seen or "9999") else (b, a)
        keeper = absorb(net.neurons[keeper.id], net.neurons[loser.id])
        net.put(keeper)
        redirect_inbound(net, loser.id, keeper.id)
        weights.supersede(net, loser.id, keeper.id, cause="consolidate/duplicate")
        net.log("merge", keeper.id, cause="consolidate/duplicate",
                detail={"absorbed": loser.id, "similarity": round(score, 2)})
        merged.append((keeper.id, loser.id))
        done.update({keeper.id, loser.id})

    reweighted = len(weights.reinforce_edges(net))
    return Consolidation(merged=merged, candidates=candidates, reweighted=reweighted)
