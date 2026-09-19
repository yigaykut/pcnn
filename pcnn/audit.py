"""Health checks for a network.

A context graph fails quietly: an anchor rots when a file is renamed, a neuron
that nothing links to stops being reachable by retrieval, a fact with no
evidence cannot be trusted.  None of that raises an error at write time, so it
has to be swept for.  Findings are rendered as badges in the HTML output so the
decay is visible rather than discovered months later.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from . import schema
from .store import Network, Registry

_ANCHOR_RE = re.compile(r"^(?P<path>[^:]+?)(?::(?P<start>\d+)(?:-(?P<end>\d+))?)?$")


@dataclass
class Report:
    project: str
    neuron_count: int = 0
    active_count: int = 0
    orphans: list[str] = field(default_factory=list)
    unsourced: list[str] = field(default_factory=list)
    stale_anchors: list[tuple[str, str, str]] = field(default_factory=list)
    contradictions: list[tuple[str, str]] = field(default_factory=list)
    quarantined: list[str] = field(default_factory=list)
    coverage: dict = field(default_factory=dict)
    schema_errors: list[str] = field(default_factory=list)
    schema_warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not (self.schema_errors or self.orphans or self.stale_anchors
                    or self.contradictions or self.quarantined)

    def badges(self) -> list[dict]:
        """Compact form consumed by the HTML renderer."""
        def badge(label: str, count: int, tone: str) -> dict:
            return {"label": label, "count": count, "tone": tone if count else "ok"}
        return [
            badge("schema errors", len(self.schema_errors), "bad"),
            badge("orphans", len(self.orphans), "warn"),
            badge("unsourced", len(self.unsourced), "warn"),
            badge("stale anchors", len(self.stale_anchors), "bad"),
            badge("contradictions", len(self.contradictions), "bad"),
            badge("quarantined", len(self.quarantined), "warn"),
        ]

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "neuron_count": self.neuron_count,
            "active_count": self.active_count,
            "orphans": self.orphans,
            "unsourced": self.unsourced,
            "stale_anchors": [list(t) for t in self.stale_anchors],
            "contradictions": [list(t) for t in self.contradictions],
            "quarantined": self.quarantined,
            "coverage": self.coverage,
            "schema_errors": self.schema_errors,
            "schema_warnings": self.schema_warnings,
            "badges": self.badges(),
            "ok": self.ok,
        }

    def render(self) -> str:
        lines = [f"audit: {self.project}",
                 f"  neurons: {self.neuron_count} ({self.active_count} active)"]
        if self.schema_errors:
            lines.append(f"  schema errors: {len(self.schema_errors)}")
            lines += [f"    {e}" for e in self.schema_errors[:20]]
        if self.orphans:
            lines.append(f"  orphans (unreachable by spreading activation): "
                         f"{', '.join(self.orphans)}")
        if self.unsourced:
            lines.append(f"  unsourced (no evidence): {', '.join(self.unsourced)}")
        for nid, anchor, why in self.stale_anchors:
            lines.append(f"  stale anchor: {nid} -> {anchor} ({why})")
        for a, b in self.contradictions:
            lines.append(f"  active contradiction: {a} vs {b}")
        if self.quarantined:
            lines.append(f"  quarantined mutations: {len(self.quarantined)}")
        if self.coverage:
            lines.append(f"  intake coverage: {self.coverage.get('percent', 0):.1f}% "
                         f"({self.coverage.get('covered', 0)}/"
                         f"{self.coverage.get('total', 0)} paragraphs)")
        if self.ok:
            lines.append("  clean")
        return "\n".join(lines)


def check_anchors(net: Network, project_path: Path | None) -> list[tuple[str, str, str]]:
    """Verify every `anchors:` entry still points at real code."""
    if project_path is None or not project_path.is_dir():
        return []
    stale: list[tuple[str, str, str]] = []
    for n in net.sorted_neurons():
        if n.status != "active":
            continue
        for anchor in n.anchors:
            m = _ANCHOR_RE.match(anchor.strip())
            if not m:
                stale.append((n.id, anchor, "unparseable"))
                continue
            rel = m.group("path").strip()
            target = project_path / rel
            if not target.exists():
                stale.append((n.id, anchor, "file missing"))
                continue
            start = m.group("start")
            if start and target.is_file():
                try:
                    total = sum(1 for _ in target.open("r", encoding="utf-8",
                                                       errors="ignore"))
                except OSError:
                    continue
                end = int(m.group("end") or start)
                if end > total:
                    stale.append((n.id, anchor,
                                  f"line {end} beyond end of file ({total} lines)"))
    return stale


def intake_coverage(net: Network) -> dict:
    """Share of numbered intake paragraphs that at least one neuron cites.

    Onboarding a project is the one moment where silent omission is most
    likely, so it gets a number instead of a hope.
    """
    if not net.intake_dir.is_dir():
        return {}
    para_ids: set[str] = set()
    para_re = re.compile(r"^\s*\[(P\d+)\]", re.M)
    for path in sorted(net.intake_dir.glob("*.md")):
        para_ids.update(para_re.findall(path.read_text(encoding="utf-8")))
    if not para_ids:
        return {}
    cited: set[str] = set()
    for n in net.neurons.values():
        for ev in n.evidence:
            cited.update(re.findall(r"\b(P\d+)\b", ev))
    covered = para_ids & cited
    return {
        "total": len(para_ids),
        "covered": len(covered),
        "percent": 100.0 * len(covered) / len(para_ids),
        "missing": sorted(para_ids - covered, key=lambda p: int(p[1:])),
    }


def run(net: Network, *, registry: Registry | None = None) -> Report:
    rep = Report(project=net.slug)
    neurons = list(net.neurons.values())
    rep.neuron_count = len(neurons)
    rep.active_count = sum(1 for n in neurons if n.status == "active")

    findings = net.validate()
    rep.schema_errors = [str(f) for f in schema.errors(findings)]
    rep.schema_warnings = [str(f) for f in schema.warnings(findings)]

    linked: set[str] = set()
    for n in neurons:
        for e in n.edges:
            linked.add(n.id)
            linked.add(e.dst)
    rep.orphans = sorted(n.id for n in neurons
                         if n.id not in linked and n.status == "active")
    rep.unsourced = sorted(n.id for n in neurons
                           if not n.evidence and n.status == "active")

    seen: set[tuple[str, str]] = set()
    for n in neurons:
        if n.status != "active":
            continue
        for e in n.outgoing("contradicts"):
            tgt = net.neurons.get(e.dst)
            if tgt and tgt.status == "active":
                pair = tuple(sorted((n.id, e.dst)))
                if pair not in seen:
                    seen.add(pair)
                    rep.contradictions.append(pair)  # type: ignore[arg-type]

    if net.quarantine_dir.is_dir():
        rep.quarantined = sorted(p.name for p in net.quarantine_dir.glob("*.json"))

    reg = registry or Registry(net.home)
    meta = reg.get(net.slug) or {}
    path = Path(meta["path"]) if meta.get("path") else None
    rep.stale_anchors = check_anchors(net, path)
    rep.coverage = intake_coverage(net)
    return rep


def write_report(net: Network, rep: Report) -> Path:
    out = net.dir / "audit.json"
    out.write_text(json.dumps(rep.to_dict(), indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    return out
