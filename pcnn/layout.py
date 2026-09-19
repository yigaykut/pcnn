"""Where each neuron sits on the ring.

Radius is fixed - it carries weight rank, which is the one thing the picture
promises. Angle is free.

Two orderings live here. **Barycentre** repeatedly moves each neuron to the
circular mean angle of its neighbours; it leaves the ring evenly populated and
is what the renderer uses. **solve** goes further and reduces tie crossings
directly, by lifting each neuron out and putting it back wherever it causes the
fewest: on this network it cut crossings from 460 to 38, but it buys that by
clustering the ring unevenly, and the even ring was judged the better picture.
Set `PCNN_LAYOUT=crossings` to use it instead.

Two ties cross when exactly one end of the second lies between the ends of the
first, going round. That makes a move cheap to score: lifting one neuron out and
dropping it elsewhere leaves every other neuron in the same relative order, so
only the ties touching the neuron that moved can change. Scoring a candidate
costs its degree times the number of ties, not the number of ties squared.

This runs when the HTML is written, not when it is opened. The order ships in
the payload, so the page draws the same picture instantly every time.
"""

from __future__ import annotations

import math
import os
from dataclasses import dataclass

#: the radial band the rings occupy, matching the renderer
R_IN, R_OUT = 0.13, 0.94

MAX_PASSES = 20
#: work ceiling, so a large network still renders promptly
MAX_TRIALS = 400_000


@dataclass
class Layout:
    order: list[str]
    crossings: int
    seeded_crossings: int
    passes: int
    trials: int


def rank_radius(salience: float, sorted_desc: list[float]) -> float:
    """Share of the network heavier than this, mapped onto the radial band."""
    if len(sorted_desc) < 2:
        return (R_IN + R_OUT) / 2
    above = sum(1 for s in sorted_desc if s > salience)
    same = sum(1 for s in sorted_desc if s == salience)
    rank = (above + above + same - 1) / 2
    return R_IN + (rank / (len(sorted_desc) - 1)) * (R_OUT - R_IN)


# --------------------------------------------------------------------------
# crossings
# --------------------------------------------------------------------------

def _between(lo: int, hi: int, p: int) -> bool:
    return lo < p < hi


def count_crossings(order: list[str], ties: list[tuple[str, str]]) -> int:
    """How many pairs of ties cross, counted on the cyclic order."""
    pos = {nid: i for i, nid in enumerate(order)}
    spans = []
    for a, b in ties:
        pa, pb = pos[a], pos[b]
        spans.append((pa, pb) if pa < pb else (pb, pa))
    total = 0
    for i in range(len(spans)):
        lo, hi = spans[i]
        for j in range(i + 1, len(spans)):
            x, y = spans[j]
            if x in (lo, hi) or y in (lo, hi):
                continue
            if _between(lo, hi, x) != _between(lo, hi, y):
                total += 1
    return total


def _incident_crossings(restpos: dict[str, int], slot: int, nid: str,
                        mine: list[tuple[str, str]],
                        others: list[tuple[str, str]]) -> int:
    """Crossings between one neuron's ties and every tie that does not touch it.

    Positions are derived from the candidate slot rather than materialised:
    building a dictionary of every position for every candidate is what made
    this cubic in the number of neurons.
    """
    def at(k: str) -> int:
        i = restpos[k]
        return i if i < slot else i + 1

    total = 0
    for a, b in mine:
        pa = slot if a == nid else at(a)
        pb = slot if b == nid else at(b)
        lo, hi = (pa, pb) if pa < pb else (pb, pa)
        for x, y in others:
            px, py = at(x), at(y)
            if px == lo or px == hi or py == lo or py == hi:
                continue
            if (lo < px < hi) != (lo < py < hi):
                total += 1
    return total


# --------------------------------------------------------------------------
# ordering
# --------------------------------------------------------------------------

def barycentre(order: list[str], kin: dict[str, set[str]],
               passes: int = 40) -> list[str]:
    """Move each neuron to the circular mean angle of its neighbours."""
    seq = list(order)
    n = len(seq)
    if n < 4:
        return seq
    index = {nid: i for i, nid in enumerate(seq)}
    for _ in range(passes):
        score = {}
        for nid in seq:
            mates = [m for m in kin.get(nid, ()) if m in index]
            if not mates:
                score[nid] = (index[nid] / n) * 2 * math.pi
                continue
            sx = sum(math.cos(index[m] / n * 2 * math.pi) for m in mates)
            sy = sum(math.sin(index[m] / n * 2 * math.pi) for m in mates)
            score[nid] = math.atan2(sy, sx) % (2 * math.pi)
        seq.sort(key=lambda k: (score[k], k))
        index = {nid: i for i, nid in enumerate(seq)}
    return seq


#: local search lands where its start sent it, so small networks try several
#: starts and keep the best; each start is deterministic, so the result is too
RESTART_MAX_NODES = 220


def _seeds(ids: list[str], salience: dict[str, float],
           kin: dict[str, set[str]]) -> list[list[str]]:
    """A handful of deterministic starting orders, most promising first."""
    by_weight = sorted(ids, key=lambda k: (-salience[k], k))
    if len(ids) > RESTART_MAX_NODES:
        return [by_weight]
    by_degree = sorted(ids, key=lambda k: (-len(kin.get(k, ())), k))
    by_name = sorted(ids)
    # walking the graph puts whole neighbourhoods together before anything moves
    walked, seen = [], set()
    for start in by_degree:
        if start in seen:
            continue
        stack = [start]
        while stack:
            cur = stack.pop()
            if cur in seen:
                continue
            seen.add(cur)
            walked.append(cur)
            stack.extend(sorted(kin.get(cur, ()), reverse=True))
    return [by_weight, by_degree, walked, by_name]


def settle(ids: list[str], ties: list[tuple[str, str]],
           salience: dict[str, float], kin: dict[str, set[str]]) -> Layout:
    """The ordering the renderer uses: an evenly populated ring.

    `PCNN_LAYOUT=crossings` switches to the crossing-minimising `solve` instead,
    which draws fewer crossings but a lumpier ring.
    """
    if os.environ.get("PCNN_LAYOUT") == "crossings":
        return solve(ids, ties, salience, kin)
    if len(ids) < 4 or not ties:
        return Layout(sorted(ids, key=lambda k: (-salience.get(k, 0), k)),
                      0, 0, 0, 0)
    seed = sorted(ids, key=lambda k: (-salience[k], k))
    order = barycentre(seed, kin)
    crossings = count_crossings(order, ties)
    return Layout(order=order, crossings=crossings, seeded_crossings=crossings,
                  passes=0, trials=0)


def solve(ids: list[str], ties: list[tuple[str, str]],
          salience: dict[str, float], kin: dict[str, set[str]]) -> Layout:
    """Order the neurons around the ring so that as few ties cross as possible."""
    if len(ids) < 4 or not ties:
        return Layout(sorted(ids, key=lambda k: (-salience.get(k, 0), k)),
                      0, 0, 0, 0)

    best_plan = None
    for seed in _seeds(ids, salience, kin):
        plan = _from(seed, ids, ties, kin)
        if best_plan is None or plan.crossings < best_plan.crossings:
            best_plan = plan
    return best_plan


def _from(seed: list[str], ids: list[str], ties: list[tuple[str, str]],
          kin: dict[str, set[str]]) -> Layout:
    order = barycentre(seed, kin)
    seeded = count_crossings(order, ties)

    touching: dict[str, list[tuple[str, str]]] = {nid: [] for nid in ids}
    for a, b in ties:
        touching[a].append((a, b))
        touching[b].append((a, b))
    apart = {nid: [t for t in ties if nid not in t] for nid in ids}

    # a big network gets fewer sweeps: the first two do nearly all the work,
    # and a render must not take minutes
    cap = max(2, min(MAX_PASSES, 2000 // max(1, len(ids))))
    trials = 0
    passes = 0
    for passes in range(1, cap + 1):
        improved = False
        for nid in sorted(ids):                    # fixed order keeps it repeatable
            mine, others = touching[nid], apart[nid]
            if not mine:
                continue
            here = order.index(nid)
            rest = order[:here] + order[here + 1:]
            restpos = {k: i for i, k in enumerate(rest)}

            def scored(slot: int) -> int:
                return _incident_crossings(restpos, slot, nid, mine, others)

            # only slots beside something this neuron is tied to can help
            slots = {here}
            for a, b in mine:
                mate = b if a == nid else a
                if mate in restpos:
                    slots.add(restpos[mate])
                    slots.add(restpos[mate] + 1)

            best_score, best_slot = scored(here), here
            for slot in sorted(slots):
                if slot == here or slot > len(rest):
                    continue
                trials += 1
                score = scored(slot)
                if score < best_score:
                    best_score, best_slot = score, slot
            if best_slot != here:
                order = rest[:best_slot] + [nid] + rest[best_slot:]
                improved = True
            if trials > MAX_TRIALS:
                break
        if not improved or trials > MAX_TRIALS:
            break

    return Layout(order=order, crossings=count_crossings(order, ties),
                  seeded_crossings=seeded, passes=passes, trials=trials)
