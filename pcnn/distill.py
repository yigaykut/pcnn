"""Stage B - turn a harvested session delta into neuron mutations.

The model never writes into `neurons/` directly.  It emits a *mutation block*
in a small, closed grammar; this module parses it, validates every mutation
against the schema, and applies only what survives.  Anything rejected is
written to `quarantine/` with the reason instead of being dropped, so a bad
distillation is visible rather than silent.

Mutation grammar
----------------

    @mutation upsert $IMP-1          # $LAYER-n = "allocate a new id for me"
    head: ...
    layer: IMP
    ...
    connected.$IMP-1 -> YISOC.ARC-002 : implements w=0.80

    @mutation link YISOC.DEC-007 -> $IMP-1 : implements w=0.90
    @mutation supersede YISOC.IMP-012 by $IMP-1
    @mutation touch YISOC.DEC-007
    @mutation raise YISOC.CON-003 to 1.00 : reason text

`$IMP-1` placeholders exist because the model cannot know which ids are free.
They are allocated here and substituted everywhere before parsing.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

from . import schema, weights
from .schema import Neuron
from .store import Network, today

PLACEHOLDER_RE = re.compile(r"\$(?P<layer>[A-Z]+)-(?P<n>\d+)")
_OP_RE = re.compile(r"^@mutation\s+(?P<op>\w+)\s*(?P<rest>.*)$")
_LINK_RE = re.compile(
    r"^(?P<src>\S+)\s*->\s*(?P<dst>\S+)\s*:\s*(?P<type>[a-z_]+)"
    r"(?:\s+w=(?P<w>[01](?:\.\d+)?))?\s*$")
_UNLINK_RE = re.compile(r"^(?P<src>\S+)\s*->\s*(?P<dst>\S+)\s*:\s*(?P<type>[a-z_]+)\s*$")
_SUPERSEDE_RE = re.compile(r"^(?P<old>\S+)\s+by\s+(?P<new>\S+)\s*$")
_RAISE_RE = re.compile(r"^(?P<id>\S+)\s+to\s+(?P<val>[01](?:\.\d+)?)\s*:\s*(?P<reason>.+)$")
_TOUCH_RE = re.compile(r"^(?P<id>\S+)\s*$")

#: a rewrite that drops this much of an existing description is treated as
#: detail loss and quarantined, never applied
SHRINK_LIMIT = 0.60


@dataclass
class Rejection:
    op: str
    payload: str
    reason: str


@dataclass
class ApplyResult:
    applied: list[dict] = field(default_factory=list)
    rejected: list[Rejection] = field(default_factory=list)
    allocated: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "applied": self.applied,
            "rejected": [{"op": r.op, "payload": r.payload, "reason": r.reason}
                         for r in self.rejected],
            "allocated": self.allocated,
            "ts": today(),
        }

    def summary(self) -> str:
        return (f"{len(self.applied)} mutation(s) applied, "
                f"{len(self.rejected)} quarantined")


# --------------------------------------------------------------------------
# Parsing
# --------------------------------------------------------------------------

def split_blocks(text: str) -> list[tuple[str, str, list[str]]]:
    """Split a mutation document into (op, rest-of-header, body-lines)."""
    blocks: list[tuple[str, str, list[str]]] = []
    current: tuple[str, str, list[str]] | None = None
    for raw in text.splitlines():
        m = _OP_RE.match(raw.strip())
        if m:
            if current:
                blocks.append(current)
            current = (m.group("op").lower(), m.group("rest").strip(), [])
        elif current is not None:
            current[2].append(raw)
    if current:
        blocks.append(current)
    return blocks


def allocate_ids(net: Network, text: str) -> tuple[str, dict[str, str]]:
    """Replace `$LAYER-n` placeholders with freshly allocated neuron ids."""
    mapping: dict[str, str] = {}
    used: dict[str, int] = {}
    for m in PLACEHOLDER_RE.finditer(text):
        token = m.group(0)
        if token in mapping:
            continue
        layer = m.group("layer")
        if layer not in schema.LAYERS:
            continue
        base = net.next_id(layer)
        bump = used.get(layer, 0)
        if bump:
            prefix, num = base.rsplit("-", 1)
            base = f"{prefix}-{int(num) + bump:03d}"
        used[layer] = bump + 1
        mapping[token] = base
    for token, real in mapping.items():
        text = text.replace(token, real)
    return text, mapping


# --------------------------------------------------------------------------
# Applying
# --------------------------------------------------------------------------

def apply_mutations(net: Network, text: str, *, cause: str) -> ApplyResult:
    """Validate and apply a mutation document.  Rejections are never silent."""
    result = ApplyResult()
    text, result.allocated = allocate_ids(net, text)

    blocks = split_blocks(text)
    upserts: list[tuple[Neuron, str]] = []
    others: list[tuple[str, str]] = []

    for op, rest, body in blocks:
        payload = "\n".join([f"@mutation {op} {rest}".rstrip(), *body]).strip()
        if op == "upsert":
            doc = "\n".join([f"@neuron {rest}", *body])
            try:
                parsed = schema.loads(doc, source="<mutation>")
            except schema.DSLError as exc:
                result.rejected.append(Rejection(op, payload, str(exc)))
                continue
            if len(parsed) != 1:
                result.rejected.append(
                    Rejection(op, payload, "an upsert block must define exactly one neuron"))
                continue
            upserts.append((parsed[0], payload))
        elif op in ("link", "unlink", "supersede", "touch", "raise"):
            others.append((op, rest.strip()))
        else:
            result.rejected.append(Rejection(op, payload, f"unknown mutation op {op!r}"))

    # -- upserts first, so later ops can reference the new neurons ---------
    for neuron, payload in upserts:
        reason = _reject_reason(net, neuron)
        if reason:
            result.rejected.append(Rejection("upsert", payload, reason))
            continue
        existing = net.neurons.get(neuron.id)
        merged = _merge(existing, neuron)
        net.put(merged)
        net.log("upsert", merged.id, cause=cause,
                detail={"revision": merged.revision,
                        "new": existing is None,
                        "salience": merged.salience})
        result.applied.append({"op": "upsert", "neuron": merged.id,
                               "new": existing is None})

    for op, rest in others:
        try:
            _apply_simple(net, op, rest, cause, result)
        except Exception as exc:  # noqa: BLE001 - never let one bad op stop the rest
            result.rejected.append(Rejection(op, rest, f"{type(exc).__name__}: {exc}"))

    return result


def _apply_simple(net: Network, op: str, rest: str, cause: str,
                  result: ApplyResult) -> None:
    if op == "link":
        m = _LINK_RE.match(rest)
        if not m:
            result.rejected.append(Rejection(op, rest, "expected 'SRC -> DST : type w=0.00'"))
            return
        src, dst, etype = m.group("src"), m.group("dst"), m.group("type")
        w = float(m.group("w")) if m.group("w") else 0.50
        if etype not in schema.EDGE_TYPES:
            result.rejected.append(Rejection(op, rest, f"unknown edge type {etype!r}"))
            return
        for nid in (src, dst):
            if nid not in net.neurons:
                result.rejected.append(Rejection(op, rest, f"unknown neuron {nid}"))
                return
        net.link(src, dst, etype, w)
        net.log("link", src, cause=cause, detail={"dst": dst, "type": etype, "w": w})
        result.applied.append({"op": "link", "neuron": src, "dst": dst, "type": etype})

    elif op == "unlink":
        # A wrong edge has to be removable. Everything else in PCNN is additive
        # because a fact stated once stays true, but an edge is a claim about a
        # relationship, and a claim can simply be mistaken. The neuron and its
        # history are untouched; only the assertion goes.
        m = _UNLINK_RE.match(rest)
        if not m:
            result.rejected.append(Rejection(op, rest, "expected 'SRC -> DST : type'"))
            return
        src, dst, etype = m.group("src"), m.group("dst"), m.group("type")
        n = net.neurons.get(src)
        if n is None:
            result.rejected.append(Rejection(op, rest, f"unknown neuron {src}"))
            return
        kept = [e for e in n.edges if not (e.dst == dst and e.type == etype)]
        if len(kept) == len(n.edges):
            result.rejected.append(
                Rejection(op, rest, f"{src} has no {etype} edge to {dst}"))
            return
        n.edges = kept
        net.put(n)
        net.log("unlink", src, cause=cause, detail={"dst": dst, "type": etype})
        result.applied.append({"op": "unlink", "neuron": src, "dst": dst, "type": etype})

    elif op == "supersede":
        m = _SUPERSEDE_RE.match(rest)
        if not m:
            result.rejected.append(Rejection(op, rest, "expected 'OLD by NEW'"))
            return
        old, new = m.group("old"), m.group("new")
        for nid in (old, new):
            if nid not in net.neurons:
                result.rejected.append(Rejection(op, rest, f"unknown neuron {nid}"))
                return
        weights.supersede(net, old, new, cause=cause)
        result.applied.append({"op": "supersede", "neuron": old, "by": new})

    elif op == "touch":
        m = _TOUCH_RE.match(rest)
        if not m or m.group("id") not in net.neurons:
            result.rejected.append(Rejection(op, rest, "expected a known neuron id"))
            return
        weights.boost_on_touch(net, m.group("id"), cause=cause)
        result.applied.append({"op": "touch", "neuron": m.group("id")})

    elif op == "raise":
        m = _RAISE_RE.match(rest)
        if not m:
            result.rejected.append(Rejection(op, rest, "expected 'ID to 0.00 : reason'"))
            return
        nid = m.group("id")
        if nid not in net.neurons:
            result.rejected.append(Rejection(op, rest, f"unknown neuron {nid}"))
            return
        changed = weights.raise_salience(net, nid, float(m.group("val")),
                                         cause=f"{cause}: {m.group('reason')}")
        if changed:
            result.applied.append({"op": "raise", "neuron": nid,
                                   "to": float(m.group("val"))})
        else:
            result.rejected.append(
                Rejection(op, rest, "salience only ever moves up automatically; "
                                    "use `pcnn demote` to lower it deliberately"))


def _reject_reason(net: Network, neuron: Neuron) -> str:
    """Schema errors plus the detail-loss guard."""
    findings = schema.validate_neuron(neuron)
    errs = schema.errors(findings)
    if errs:
        return "; ".join(f"{f.code} {f.message}" for f in errs)
    if neuron.scope not in (net.scope, schema.XPRJ_SCOPE):
        return (f"neuron id scope {neuron.scope} does not belong to network "
                f"{net.slug} (scope {net.scope})")
    existing = net.neurons.get(neuron.id)
    if existing and existing.description:
        ratio = len(neuron.description) / max(len(existing.description), 1)
        if ratio < SHRINK_LIMIT:
            return (f"rewrite would drop {100 * (1 - ratio):.0f}% of the existing "
                    "description; supersede the neuron instead of shrinking it")
        if existing.rationale and not neuron.rationale:
            return "rewrite would drop the existing rationale"
    return ""


def _merge(existing: Neuron | None, incoming: Neuron) -> Neuron:
    """Union the two, never losing information the old neuron already held."""
    if existing is None:
        incoming.revision = max(1, incoming.revision)
        incoming.first_seen = incoming.first_seen or today()
        incoming.last_touched = today()
        return incoming

    merged = incoming
    merged.salience = max(existing.salience, incoming.salience)
    merged.pin = existing.pin or incoming.pin
    merged.first_seen = existing.first_seen or incoming.first_seen or today()
    merged.last_touched = today()
    merged.revision = existing.revision + 1
    merged.signals = sorted(set(existing.signals) | set(incoming.signals))
    merged.anchors = sorted(set(existing.anchors) | set(incoming.anchors))
    merged.evidence = sorted(set(existing.evidence) | set(incoming.evidence))
    merged.rationale = incoming.rationale or existing.rationale
    merged.alternatives_rejected = (incoming.alternatives_rejected
                                    or existing.alternatives_rejected)
    merged.note = incoming.note or existing.note
    # edges are additive: a relationship that was true once stays recorded
    keyed = {(e.type, e.dst): e for e in existing.edges}
    for e in incoming.edges:
        prev = keyed.get((e.type, e.dst))
        keyed[(e.type, e.dst)] = e if prev is None or e.weight >= prev.weight else prev
    merged.edges = list(keyed.values())
    return merged


def quarantine(net: Network, result: ApplyResult, *, cause: str) -> Path | None:
    if not result.rejected:
        return None
    net.quarantine_dir.mkdir(parents=True, exist_ok=True)
    stamp = re.sub(r"[^A-Za-z0-9]+", "-", cause).strip("-")[:60] or "unknown"
    out = net.quarantine_dir / f"{today()}--{stamp}.json"
    out.write_text(json.dumps(result.to_dict(), indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    return out


# --------------------------------------------------------------------------
# Prompt assembly + model invocation
# --------------------------------------------------------------------------

#: how much of a delta is worth paying tokens for
PROMPT_COMMANDS = 20
PROMPT_COMMAND_CHARS = 120
PROMPT_INSTRUCTIONS = 12
PROMPT_INSTRUCTION_CHARS = 700
PROMPT_FAILURES = 10
PROMPT_FAILURE_CHARS = 260


def slim_delta(delta: dict) -> dict:
    """Shrink a raw delta into the part worth paying tokens for.

    The delta on disk stays complete - it is the evidence, and nothing is ever
    dropped from it.  This is a *view* of it for the prompt.  Measured on a real
    day, verbatim shell commands were 67% of the payload and the least useful
    signal in it: what a session decided lives in its closing recap, its file
    changes and its failures, not in the forty times it re-ran the same script.
    """
    out = dict(delta)
    cmds = delta.get("commands") or []
    buckets: dict[str, int] = {}
    for c in cmds:
        key = c.get("bucket", "other")
        buckets[key] = buckets.get(key, 0) + int(c.get("repeats", 1))
    out["commands"] = [
        {"command": str(c.get("command", ""))[:PROMPT_COMMAND_CHARS],
         "bucket": c.get("bucket", "other"), "repeats": c.get("repeats", 1)}
        for c in cmds[:PROMPT_COMMANDS]]
    out["command_summary"] = buckets
    if len(cmds) > PROMPT_COMMANDS:
        out["commands_omitted"] = len(cmds) - PROMPT_COMMANDS

    out["user_instructions"] = [
        {"text": str(i.get("text", ""))[:PROMPT_INSTRUCTION_CHARS]}
        for i in (delta.get("user_instructions") or [])[-PROMPT_INSTRUCTIONS:]]
    out["failures"] = [
        {"tool": f.get("tool"), "target": str(f.get("target", ""))[:80],
         "error": str(f.get("error", ""))[:PROMPT_FAILURE_CHARS]}
        for f in (delta.get("failures") or [])[-PROMPT_FAILURES:]]

    # reading a file is not a fact about the project
    for noise in ("files_read", "transcript", "truncated", "cli_version"):
        out.pop(noise, None)
    return out


def invariants_digest(net: Network, limit_chars: int = 4000) -> str:
    """Ids, heads and reasons only - enough to notice a contradiction.

    The full INVARIANTS.md is what a *session* loads.  A distillation only has
    to recognise that a fact already exists or is being contradicted, and that
    fits in one line each, which keeps prompt cost flat as the network grows.
    """
    lines = []
    for n in net.sorted_neurons():
        if n.status != "active":
            continue
        if not (n.pin or (n.layer in ("CON", "DEC", "GOT") and n.salience >= 0.85)):
            continue
        why = f" -- {n.rationale[:160]}" if n.rationale else ""
        lines.append(f"{n.id} [{n.layer} {n.salience:.2f}] {n.head}{why}")
    text = "\n".join(lines)
    return text[:limit_chars] if text else "(none yet)"


def build_prompt(net: Network, delta: dict, *, template_path: Path) -> str:
    """Assemble the distillation prompt: instructions + state + the delta."""
    template = template_path.read_text(encoding="utf-8")
    map_md = net.map_path.read_text(encoding="utf-8") if net.map_path.exists() else "(empty)"
    return "\n\n".join([
        template,
        "## WHAT THIS NETWORK ALREADY HOLDS",
        "```",
        map_md.strip(),
        "```",
        "## INVARIANTS - do not contradict these silently",
        "```",
        invariants_digest(net),
        "```",
        f"## SESSION DELTA (project: {net.slug})",
        "```json",
        json.dumps(slim_delta(delta), indent=2, ensure_ascii=False),
        "```",
        "Emit only the mutation block. No prose, no code fences.",
    ])


#: set on the headless model call so its own SessionEnd hook stands down.
#: Without it the distiller harvests itself: `claude -p` runs as a Claude Code
#: session in the orchestrator directory, the hook treats that session as
#: project work, and distilling it spawns another distillation - a loop that
#: spends tokens forever and records the distiller's own prompt as if it were a
#: fact about the project.
INTERNAL_ENV = "PCNN_INTERNAL"


#: Distillation is structured extraction against a closed grammar, and every
#: answer is checked by a validator that quarantines anything malformed - so the
#: cheapest capable model is the right one. A frontier model costs roughly ten
#: times as much to produce the same mutation block.
DEFAULT_MODEL = "haiku"


def run_model(prompt: str, *, timeout: int = 900, executable: str = "claude",
              model: str = DEFAULT_MODEL) -> str:
    """Invoke Claude Code headlessly and return its raw text answer."""
    cmd = [executable, "-p", "--output-format", "text"]
    if model:
        cmd += ["--model", model]
    env = dict(os.environ, **{INTERNAL_ENV: "1"})
    proc = subprocess.run(
        cmd, input=prompt, capture_output=True, text=True, timeout=timeout,
        encoding="utf-8", errors="replace",
        shell=(sys.platform == "win32"), env=env,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"{executable} -p exited {proc.returncode}: {proc.stderr.strip()[:500]}")
    return proc.stdout


def strip_fences(text: str) -> str:
    """Models like to wrap output in code fences; the grammar has no room for them."""
    lines = [ln for ln in text.splitlines() if not ln.strip().startswith("```")]
    return "\n".join(lines)
