"""PCNN DSL v1 - grammar, data model, parser, canonical writer, validator.

The DSL is line oriented so that a language model can emit it without escaping
rules and a regex parser can read it back deterministically.  Every write goes
through `dumps()` so stored files are always canonical; that is what makes the
round-trip guarantee (parse -> dump -> parse == identity) hold.
"""

from __future__ import annotations

import re
import textwrap
from dataclasses import dataclass, field, replace
from typing import Iterable

DSL_VERSION = "1.0"

# --------------------------------------------------------------------------
# Closed vocabularies.  Closed sets are what make model output deterministic.
# --------------------------------------------------------------------------

#: layer -> salience floor.  A neuron may never be stored below its floor.
LAYERS: dict[str, float] = {
    "IDENT": 0.90,  # what the project is, goal, users, done-criteria
    "DEC": 0.85,    # a choice made + rationale + rejected alternatives
    "CON": 0.95,    # invariants: must/never rules, platform limits
    "ARC": 0.70,    # components, boundaries, data flow
    "IMP": 0.50,    # concrete modules/functions and what they do
    "DAT": 0.65,    # schemas, API shapes, config keys, env vars, formats
    "OPS": 0.60,    # run/build/deploy commands, ports, secrets, versions
    "GOT": 0.80,    # what broke, why, the fix, what not to retry
    "TODO": 0.60,   # open threads, unknowns, deferred work
    "GLO": 0.55,    # domain terms + canonical naming
    "PAT": 0.70,    # reusable cross-project pattern (XPRJ scope only)
}

LAYER_ORDER = list(LAYERS)

#: layers that may only appear under the cross-project scope
XPRJ_ONLY_LAYERS = {"PAT"}
XPRJ_SCOPE = "XPRJ"

EDGE_TYPES: dict[str, str] = {
    "depends_on": "source cannot function without target",
    "implements": "source is the concrete realisation of target",
    "constrained_by": "target limits what source may do",
    "caused_by": "target is the reason source exists",
    "refines": "source narrows or details target",
    "instance_of": "source is a specific case of the general target",
    "contradicts": "source and target cannot both be true",
    "supersedes": "source replaces target",
    "blocks": "source prevents target from progressing",
    "verified_by": "target is the evidence that source holds",
    "mirrors": "source and target solve the same problem in different projects",
    "relates_to": "weak fallback association",
}

#: short codes used in MAP.md, chosen to stay unambiguous when truncated
EDGE_ABBR: dict[str, str] = {
    "depends_on": "dep", "implements": "imp", "constrained_by": "con",
    "caused_by": "cause", "refines": "ref", "instance_of": "inst",
    "contradicts": "vs", "supersedes": "sup", "blocks": "blk",
    "verified_by": "ver", "mirrors": "mir", "relates_to": "rel",
}

#: `relates_to` is the escape hatch; it is capped so it can never dominate
#: retrieval and crowd out a typed edge.
WEAK_EDGE_TYPES = {"relates_to"}
WEAK_EDGE_MAX_WEIGHT = 0.40

STATUSES = ("active", "superseded", "deprecated", "hypothesis")
CONFIDENCES = ("verified", "stated", "inferred")

#: layers whose facts are expensive to rediscover, so a rationale is mandatory
RATIONALE_REQUIRED = {"DEC", "CON", "GOT"}

# --------------------------------------------------------------------------
# Grammar
# --------------------------------------------------------------------------

SCOPE_RE = r"[A-Z][A-Z0-9_]{0,15}"
NEURON_ID_RE = re.compile(rf"^(?P<scope>{SCOPE_RE})\.(?P<layer>[A-Z]+)-(?P<num>\d{{3,4}})$")

_HEADER_RE = re.compile(r"^@neuron\s+(?P<id>\S+)\s*$")
#: an edge line is matched whole, before the generic field rule, because its
#: key contains a dot, uppercase and a hyphen that no plain field name carries
_ID = rf"{SCOPE_RE}\.[A-Z]+-\d{{3,4}}"
_EDGE_LINE_RE = re.compile(
    rf"^connected\.(?P<src>{_ID})\s*->\s*(?P<dst>{_ID})\s*:\s*"
    r"(?P<type>[a-z_]+)(?:\s+w=(?P<w>[01](?:\.\d+)?))?\s*$"
)
_EDGE_PREFIX_RE = re.compile(r"^connected\.")
_FIELD_RE = re.compile(r"^(?P<key>[a-z][a-z0-9_]*)\s*:\s?(?P<val>.*)$")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

#: canonical field order used by the writer
FIELD_ORDER = (
    "head", "layer", "project", "status", "confidence", "salience", "pin",
    "signals", "description", "rationale", "alternatives_rejected",
    "anchors", "__edges__", "evidence", "first_seen", "last_touched",
    "revision", "note",
)

LIST_FIELDS = {"signals", "anchors", "evidence"}
TEXT_FIELDS = {"head", "description", "rationale", "alternatives_rejected", "note"}
WRAP_FIELDS = {"description", "rationale", "alternatives_rejected", "note"}
WRAP_WIDTH = 96

#: AI-readability contract.  These are warnings, never hard errors, because a
#: rejected write loses knowledge - the whole point of PCNN is to never do that.
_RELATIVE_TIME = re.compile(
    r"\b(recently|currently|right now|nowadays|lately|today|yesterday|tomorrow|"
    r"soon|at the moment|for now|these days)\b", re.I)
_PERSON_PRONOUN = re.compile(r"\b(we|our|ours|us|i|my|you|your)\b", re.I)
_VAGUE_OPENER = re.compile(r"^\s*(it|this|that|they|these|those|there)\b", re.I)


class DSLError(ValueError):
    """Raised when a document cannot be parsed at all."""


@dataclass(frozen=True)
class Finding:
    """One validation result.  `level` is 'error' or 'warn'."""
    level: str
    code: str
    message: str
    neuron: str = ""
    line: int = 0

    def __str__(self) -> str:  # pragma: no cover - display only
        where = self.neuron or "<network>"
        loc = f":{self.line}" if self.line else ""
        return f"[{self.level}] {self.code} {where}{loc}: {self.message}"


@dataclass(frozen=True)
class Edge:
    src: str
    dst: str
    type: str
    weight: float = 0.50


@dataclass
class Neuron:
    id: str
    head: str = ""
    layer: str = ""
    project: str = ""
    status: str = "active"
    confidence: str = "stated"
    salience: float = 0.0
    pin: bool = False
    signals: list[str] = field(default_factory=list)
    description: str = ""
    rationale: str = ""
    alternatives_rejected: str = ""
    anchors: list[str] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    first_seen: str = ""
    last_touched: str = ""
    revision: int = 1
    note: str = ""
    #: source line of `@neuron`, for diagnostics only; not serialised
    line: int = 0

    # -- derived -----------------------------------------------------------
    @property
    def scope(self) -> str:
        m = NEURON_ID_RE.match(self.id)
        return m.group("scope") if m else ""

    @property
    def id_layer(self) -> str:
        m = NEURON_ID_RE.match(self.id)
        return m.group("layer") if m else ""

    @property
    def floor(self) -> float:
        return LAYERS.get(self.layer, 0.0)

    def outgoing(self, *types: str) -> list[Edge]:
        if not types:
            return list(self.edges)
        return [e for e in self.edges if e.type in types]

    def canonical(self) -> "Neuron":
        """Return a copy with derived and ordered fields normalised."""
        edges = sorted({(e.type, e.dst, round(e.weight, 2)) for e in self.edges})
        return replace(
            self,
            head=" ".join(self.head.split()),
            description=" ".join(self.description.split()),
            rationale=" ".join(self.rationale.split()),
            alternatives_rejected=" ".join(self.alternatives_rejected.split()),
            note=" ".join(self.note.split()),
            signals=sorted({s.strip() for s in self.signals if s.strip()}),
            anchors=sorted({a.strip() for a in self.anchors if a.strip()}),
            evidence=sorted({e.strip() for e in self.evidence if e.strip()}),
            edges=[Edge(self.id, dst, typ, w) for typ, dst, w in edges],
            salience=round(float(self.salience), 2),
        )


# --------------------------------------------------------------------------
# Parsing
# --------------------------------------------------------------------------

def _logical_lines(text: str) -> list[tuple[int, str]]:
    """Fold continuation lines (leading whitespace) into their owner."""
    out: list[tuple[int, str]] = []
    for lineno, raw in enumerate(text.splitlines(), 1):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if raw[:1].isspace() and out:
            n, prev = out[-1]
            out[-1] = (n, prev + " " + raw.strip())
        else:
            out.append((lineno, raw.rstrip()))
    return out


def loads(text: str, *, source: str = "<string>") -> list[Neuron]:
    """Parse a DSL document into neurons.  Raises DSLError on broken syntax."""
    neurons: list[Neuron] = []
    cur: Neuron | None = None
    seen: set[str] = set()

    for lineno, line in _logical_lines(text):
        header = _HEADER_RE.match(line)
        if header:
            nid = header.group("id")
            if not NEURON_ID_RE.match(nid):
                raise DSLError(f"{source}:{lineno}: malformed neuron id {nid!r}")
            if nid in seen:
                raise DSLError(f"{source}:{lineno}: duplicate neuron id {nid!r}")
            seen.add(nid)
            cur = Neuron(id=nid, line=lineno)
            cur.layer = NEURON_ID_RE.match(nid).group("layer")
            neurons.append(cur)
            continue

        if cur is None:
            raise DSLError(f"{source}:{lineno}: field outside of any @neuron block")

        if _EDGE_PREFIX_RE.match(line):
            em = _EDGE_LINE_RE.match(line)
            if not em:
                raise DSLError(
                    f"{source}:{lineno}: malformed edge line {line[:70]!r}; expected "
                    "'connected.SCOPE.LAY-000 -> SCOPE.LAY-000 : edge_type w=0.00'")
            if em.group("src") != cur.id:
                raise DSLError(
                    f"{source}:{lineno}: edge source {em.group('src')} "
                    f"does not match enclosing neuron {cur.id}")
            weight = float(em.group("w")) if em.group("w") else 0.50
            cur.edges.append(Edge(cur.id, em.group("dst"), em.group("type"), weight))
            continue

        fm = _FIELD_RE.match(line)
        if not fm:
            raise DSLError(f"{source}:{lineno}: not a 'key: value' line -> {line[:60]!r}")
        _assign(cur, fm.group("key"), fm.group("val").strip(), source, lineno)

    return [n.canonical() for n in neurons]


def _assign(n: Neuron, key: str, val: str, source: str, lineno: int) -> None:
    if key in LIST_FIELDS:
        getattr(n, key).extend(p.strip() for p in val.split(",") if p.strip())
    elif key in TEXT_FIELDS:
        prev = getattr(n, key)
        setattr(n, key, (prev + " " + val).strip() if prev else val)
    elif key == "salience":
        try:
            n.salience = float(val)
        except ValueError as exc:
            raise DSLError(f"{source}:{lineno}: salience must be a number, got {val!r}") from exc
    elif key == "revision":
        try:
            n.revision = int(val)
        except ValueError as exc:
            raise DSLError(f"{source}:{lineno}: revision must be an integer, got {val!r}") from exc
    elif key == "pin":
        n.pin = val.strip().lower() in ("true", "yes", "1")
    elif key in ("layer", "project", "status", "confidence", "first_seen", "last_touched"):
        setattr(n, key, val)
    else:
        raise DSLError(f"{source}:{lineno}: unknown field {key!r}")


# --------------------------------------------------------------------------
# Canonical writing
# --------------------------------------------------------------------------

def _wrap(key: str, value: str) -> list[str]:
    prefix = f"{key}: "
    if key not in WRAP_FIELDS or len(prefix) + len(value) <= WRAP_WIDTH:
        return [prefix + value]
    lines = textwrap.wrap(
        value, width=WRAP_WIDTH, initial_indent=prefix, subsequent_indent="  ",
        break_long_words=False, break_on_hyphens=False)
    return lines or [prefix]


def dump_neuron(n: Neuron) -> str:
    """Serialise one neuron canonically."""
    n = n.canonical()
    out = [f"@neuron {n.id}"]
    for key in FIELD_ORDER:
        if key == "__edges__":
            for e in n.edges:
                out.append(f"connected.{n.id} -> {e.dst} : {e.type} w={e.weight:.2f}")
            continue
        val = getattr(n, key)
        if key in LIST_FIELDS:
            if val:
                out.extend(_wrap(key, ", ".join(val)))
        elif key == "pin":
            if val:
                out.append("pin: true")
        elif key == "salience":
            out.append(f"salience: {val:.2f}")
        elif key == "revision":
            out.append(f"revision: {int(val)}")
        elif val:
            out.extend(_wrap(key, str(val)))
    return "\n".join(out) + "\n"


def dumps(neurons: Iterable[Neuron]) -> str:
    return "\n".join(dump_neuron(n) for n in neurons)


# --------------------------------------------------------------------------
# Validation
# --------------------------------------------------------------------------

def validate_neuron(n: Neuron) -> list[Finding]:
    """Structural and style checks for a single neuron (no graph context)."""
    f: list[Finding] = []

    def err(code: str, msg: str) -> None:
        f.append(Finding("error", code, msg, n.id, n.line))

    def warn(code: str, msg: str) -> None:
        f.append(Finding("warn", code, msg, n.id, n.line))

    m = NEURON_ID_RE.match(n.id)
    if not m:
        err("E001", f"malformed neuron id {n.id!r}")
        return f

    scope, id_layer = m.group("scope"), m.group("layer")

    if n.layer not in LAYERS:
        err("E002", f"unknown layer {n.layer!r}; expected one of {', '.join(LAYER_ORDER)}")
    elif n.layer != id_layer:
        err("E003", f"layer field {n.layer!r} disagrees with id segment {id_layer!r}")
    elif n.layer in XPRJ_ONLY_LAYERS and scope != XPRJ_SCOPE:
        err("E004", f"layer {n.layer} is only valid under the {XPRJ_SCOPE} scope")

    if not n.project:
        err("E005", "project is required")
    elif scope != XPRJ_SCOPE and n.project.replace("-", "_").upper() != scope:
        err("E006", f"project {n.project!r} disagrees with id scope {scope!r}")

    if n.status not in STATUSES:
        err("E007", f"unknown status {n.status!r}; expected {', '.join(STATUSES)}")
    if n.confidence not in CONFIDENCES:
        err("E008", f"unknown confidence {n.confidence!r}; expected {', '.join(CONFIDENCES)}")

    if not 0.0 <= n.salience <= 1.0:
        err("E009", f"salience {n.salience} outside 0.00-1.00")
    elif n.layer in LAYERS and n.salience < LAYERS[n.layer] - 1e-9:
        err("E010", f"salience {n.salience:.2f} below the {n.layer} floor "
                    f"{LAYERS[n.layer]:.2f}; weight may never be lowered below a floor")

    if not n.head:
        err("E011", "head is required")
    elif len(n.head) > 110:
        warn("W001", f"head is {len(n.head)} chars; keep it under 110 so MAP.md stays scannable")

    if not n.description:
        err("E012", "description is required")
    elif len(n.description) < 40:
        warn("W002", "description under 40 chars; a neuron must carry the whole fact, "
                     "not a pointer to it")

    if n.layer in RATIONALE_REQUIRED and not n.rationale:
        err("E013", f"{n.layer} neurons must carry a rationale (the why is the expensive part)")

    for e in n.edges:
        if e.type not in EDGE_TYPES:
            err("E014", f"unknown edge type {e.type!r} -> {e.dst}")
        if not 0.0 <= e.weight <= 1.0:
            err("E015", f"edge weight {e.weight} to {e.dst} outside 0.00-1.00")
        if e.type in WEAK_EDGE_TYPES and e.weight > WEAK_EDGE_MAX_WEIGHT + 1e-9:
            err("E016", f"{e.type} edge to {e.dst} capped at {WEAK_EDGE_MAX_WEIGHT:.2f}, "
                        f"got {e.weight:.2f}; use a typed edge instead")
        if e.dst == n.id:
            err("E017", "self edge")

    for datefield in ("first_seen", "last_touched"):
        val = getattr(n, datefield)
        if val and not _DATE_RE.match(val):
            err("E018", f"{datefield} must be YYYY-MM-DD, got {val!r}")
    if not n.first_seen:
        warn("W003", "first_seen missing; the timeline view needs it")

    if n.revision < 1:
        err("E019", f"revision must be >= 1, got {n.revision}")

    if not n.evidence:
        warn("W004", "no evidence; this neuron cannot be audited back to a source")
    if len(n.signals) < 2:
        warn("W005", "fewer than 2 signals; retrieval will struggle to seed this neuron")
    if not n.anchors and n.layer in ("IMP", "ARC", "DAT", "OPS"):
        warn("W006", f"{n.layer} neuron without anchors; nothing ties it to the code")

    for label, text in (("description", n.description), ("rationale", n.rationale)):
        if not text:
            continue
        if _RELATIVE_TIME.search(text):
            warn("W007", f"{label} uses relative time; use an absolute date so the fact "
                         "stays true when read later")
        if _PERSON_PRONOUN.search(text):
            warn("W008", f"{label} uses first or second person; state the fact impersonally")
        if _VAGUE_OPENER.match(text):
            warn("W009", f"{label} opens with a pronoun; name the entity so the neuron "
                         "is readable out of context")
    return f


def validate_graph(neurons: Iterable[Neuron]) -> list[Finding]:
    """Cross-neuron checks: dangling targets, contradictions, supersession."""
    items = list(neurons)
    by_id = {n.id: n for n in items}
    superseded_by: dict[str, list[str]] = {}
    for n in items:
        for e in n.outgoing("supersedes"):
            superseded_by.setdefault(e.dst, []).append(n.id)

    f: list[Finding] = []
    for n in items:
        f.extend(validate_neuron(n))
        for e in n.edges:
            if e.dst not in by_id:
                f.append(Finding("error", "E020",
                                 f"edge {e.type} points at unknown neuron {e.dst}",
                                 n.id, n.line))
        if n.status == "superseded" and not superseded_by.get(n.id):
            f.append(Finding("warn", "W010",
                             "status is superseded but no neuron claims to supersede it",
                             n.id, n.line))
        for e in n.outgoing("supersedes"):
            tgt = by_id.get(e.dst)
            if tgt and tgt.status == "active":
                f.append(Finding("warn", "W011",
                                 f"supersedes {e.dst}, which is still marked active",
                                 n.id, n.line))
        for e in n.outgoing("contradicts"):
            tgt = by_id.get(e.dst)
            if tgt and tgt.status == "active" and n.status == "active":
                f.append(Finding("warn", "W012",
                                 f"contradicts {e.dst} and both are active; one must be "
                                 "superseded or the conflict resolved", n.id, n.line))
    return f


def errors(findings: Iterable[Finding]) -> list[Finding]:
    return [x for x in findings if x.level == "error"]


def warnings(findings: Iterable[Finding]) -> list[Finding]:
    return [x for x in findings if x.level == "warn"]
