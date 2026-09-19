"""`python -m pcnn <command>` - the whole engine from one entry point."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import audit as audit_mod
from . import budget, distill, ingest, merge, poster, query, render, schema, weights
from .store import Network, Registry, home, load_all, today


def _net(slug: str, root: Path | None = None) -> Network:
    net = Network(slug, root)
    if not net.exists():
        raise SystemExit(f"no network for {slug!r}; run: python -m pcnn init {slug} <path>")
    return net.load()


def _targets(args) -> list[str]:
    if getattr(args, "all", False):
        reg = Registry(home())
        slugs = [s for s in reg.slugs() if Network(s).exists()]
        # the cross-project scope has no source directory, so it is never in the
        # registry; add it here and keep the list unique
        if Network("xprj").exists() and "xprj" not in slugs:
            slugs.append("xprj")
        return slugs
    if not getattr(args, "project", None):
        raise SystemExit("name a project or pass --all")
    return [args.project]


# --------------------------------------------------------------------------

def cmd_init(args) -> int:
    reg = Registry(home())
    path = Path(args.path).resolve()
    if not path.is_dir():
        print(f"warning: {path} is not a directory yet", file=sys.stderr)
    reg.add(args.project, path)
    reg.save()
    net = Network(args.project)
    net.init()
    net.load()
    net.rebuild()
    print(f"registered {args.project} -> {path}")
    print(f"network at {net.dir}")
    print(f"next: onboard it with prompts/INGEST_PROJECT.md")
    return 0


def cmd_status(args) -> int:
    reg = Registry(home())
    nets = load_all()
    if not reg.projects:
        print("no projects registered; run: python -m pcnn init <slug> <path>")
        return 0
    print(f"{'project':<18} {'neurons':>8} {'active':>7} {'pending':>8}  path")
    for slug in reg.slugs():
        net = nets.get(slug)
        if net is None:
            print(f"{slug:<18} {'-':>8} {'-':>7} {'-':>8}  (not initialised)")
            continue
        active = sum(1 for n in net.neurons.values() if n.status == "active")
        pend = len(ingest.pending(net.dir))
        print(f"{slug:<18} {len(net.neurons):>8} {active:>7} {pend:>8}  "
              f"{reg.get(slug).get('path', '')}")
    if "xprj" in nets:
        net = nets["xprj"]
        print(f"{'xprj':<18} {len(net.neurons):>8} "
              f"{sum(1 for n in net.neurons.values() if n.status == 'active'):>7} "
              f"{'-':>8}  (cross-project)")
    return 0


def cmd_cost(args) -> int:
    hist = budget.history(home())
    if not hist:
        print("no model calls charged yet")
        return 0
    for day in sorted(hist):
        print(f"{day}  {hist[day]:>3} call(s)")
    print(f"\ntoday: {budget.spent(home())} of {budget.limit()}; "
          f"raise with PCNN_DAILY_CALLS")
    return 0


def cmd_validate(args) -> int:
    worst = 0
    for slug in _targets(args):
        net = _net(slug)
        findings = net.validate()
        errs = schema.errors(findings)
        warns = schema.warnings(findings)
        print(f"{slug}: {len(net.neurons)} neurons, {len(errs)} error(s), "
              f"{len(warns)} warning(s)")
        for f in errs:
            print(f"  {f}")
        if args.verbose:
            for f in warns:
                print(f"  {f}")
        worst = max(worst, 1 if errs else 0)
    return worst


def cmd_rebuild(args) -> int:
    for slug in _targets(args):
        net = _net(slug)
        weights.enforce_floors(net)
        net.rebuild()
        print(f"{slug}: rebuilt MAP.md, INVARIANTS.md, graph.json "
              f"({len(net.neurons)} neurons)")
    return 0


def cmd_query(args) -> int:
    nets = load_all() if args.all else {args.project: _net(args.project)}
    neurons = [n for net in nets.values() for n in net.neurons.values()]
    if args.include_retired is False:
        neurons = [n for n in neurons if n.status == "active"]
    hits = query.activate(neurons, args.text, top_k=args.top)
    if args.json:
        print(json.dumps([{
            "id": h.neuron.id, "activation": h.activation, "hops": h.hops,
            "via": h.via, "head": h.neuron.head, "layer": h.neuron.layer,
            "salience": h.neuron.salience, "description": h.neuron.description,
            "anchors": h.neuron.anchors,
        } for h in hits], indent=2, ensure_ascii=False))
    else:
        print(query.format_hits(hits, verbose=args.verbose))
    return 0


def cmd_context(args) -> int:
    """Print what a session should load: the L0 map plus the invariants."""
    net = _net(args.project)
    parts = []
    if net.invariants_path.exists():
        parts.append(net.invariants_path.read_text(encoding="utf-8"))
    if net.map_path.exists():
        parts.append(net.map_path.read_text(encoding="utf-8"))
    print("\n\n".join(parts))
    return 0


def cmd_harvest(args) -> int:
    reg = Registry(home())
    slug = args.project or reg.resolve_path(args.cwd or Path.cwd())
    if not slug:
        print(f"no registered project for cwd {args.cwd}", file=sys.stderr)
        return 0
    net = Network(slug)
    net.init()
    written = ingest.harvest(args.transcript, slug, net.dir,
                             session_id=args.session_id or "",
                             incremental=not args.full)
    if not written:
        print("nothing new in this transcript; no delta written")
        return 0
    for out in written:
        print(f"wrote {out.relative_to(net.home)}")
    return 0


def _worth_distilling(delta: dict) -> bool:
    """A day that changed no file and hit no failure holds nothing durable.

    Skipping it costs nothing - the delta stays on disk - and it is the
    difference between paying for every day a project was merely opened and
    paying only for the days something happened.
    """
    return bool(delta.get("file_changes") or delta.get("failures"))


def cmd_distill(args) -> int:
    template = home() / "prompts" / "DISTILL_RECAP.md"
    if not template.exists():
        raise SystemExit(f"missing prompt template: {template}")
    total = done = skipped = 0
    left = budget.remaining(home())

    for slug in _targets(args):
        net = _net(slug)
        for raw in ingest.pending(net.dir):
            delta = json.loads(raw.read_text(encoding="utf-8"))
            cause = f"recap/{raw.parent.name}/{raw.name}"

            if not args.all_days and not _worth_distilling(delta):
                ingest.mark_applied(raw, {
                    "applied": [], "rejected": [], "allocated": {},
                    "skipped": "no file changed and nothing failed; nothing durable "
                               "to learn from this day",
                    "ts": today()})
                skipped += 1
                continue

            prompt = distill.build_prompt(net, delta, template_path=template)
            if args.dry_run:
                print(f"{slug} :: {raw.parent.name}  {len(prompt):>7,} chars "
                      f"~{len(prompt)//4:>6,} tokens")
                if args.verbose:
                    print(prompt)
                continue

            if args.limit and done >= args.limit:
                print(f"stopped at --limit {args.limit}")
                return _distill_report(total, done, skipped)
            if left <= 0:
                print(f"daily budget of {budget.limit()} model call(s) is spent; "
                      f"the rest wait for tomorrow (PCNN_DAILY_CALLS raises it)")
                return _distill_report(total, done, skipped)

            try:
                answer = distill.run_model(prompt, executable=args.claude,
                                           model=args.model)
            except Exception as exc:  # noqa: BLE001
                print(f"{slug}: distillation failed for {raw.name}: {exc}",
                      file=sys.stderr)
                continue
            left = budget.charge(home())
            result = distill.apply_mutations(
                net, distill.strip_fences(answer), cause=cause)
            distill.quarantine(net, result, cause=cause)
            ingest.mark_applied(raw, result.to_dict())
            net.rebuild()
            total += len(result.applied)
            done += 1
            print(f"{slug} :: {raw.parent.name}: {result.summary()}")

    if args.dry_run:
        return 0
    return _distill_report(total, done, skipped)


def _distill_report(total: int, done: int, skipped: int) -> int:
    bits = [f"{total} mutation(s) from {done} day(s)"]
    if skipped:
        bits.append(f"{skipped} quiet day(s) skipped free")
    bits.append(f"{budget.remaining(home())} of {budget.limit()} call(s) left today")
    print(" | ".join(bits))
    return 0


def summary() -> tuple[str, str]:
    """Two short lines for a notification: what is held, and whether it is sound."""
    reg = Registry(home())
    nets = load_all()
    facts = waiting = 0
    unsound = []
    for slug in reg.slugs():
        net = nets.get(slug)
        if net is None:
            continue
        facts += sum(1 for n in net.neurons.values() if n.status == "active")
        waiting += len(ingest.pending(net.dir))
        if not audit_mod.run(net, registry=reg).ok:
            unsound.append(slug)

    first = f"{facts} facts across {len(nets)} projects"
    if waiting:
        first += f", {waiting} day(s) waiting"
    second = ("nothing needs attention" if not unsound
              else "needs a look: " + ", ".join(unsound))
    return first, second


def cmd_notify(args) -> int:
    """Hand one toast to the shell and exit.  Never fails the caller."""
    import subprocess

    line1, line2 = summary()
    script = home() / "scripts" / "notify.ps1"
    link = home() / "output" / "network.html"
    if args.dry_run or not script.exists():
        print(f"{line1}\n{line2}")
        return 0
    try:
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
             "-File", str(script), "-Line1", line1, "-Line2", line2,
             "-Link", str(link)],
            capture_output=True, text=True, timeout=60,
            encoding="utf-8", errors="replace")
        print((proc.stdout or proc.stderr).strip() or "toast dispatched")
    except Exception as exc:  # noqa: BLE001 - a missed toast is not a failure
        print(f"could not notify: {exc}", file=sys.stderr)
    return 0


def cmd_dashboard(args) -> int:
    """Everything worth knowing, in one read-only command that costs nothing."""
    reg = Registry(home())
    if not reg.projects:
        print("Nothing registered yet.\n"
              '  python -m pcnn init <name> "<path to the project>"')
        return 0

    nets = load_all()
    rows, faults, pending_total = [], [], 0
    for slug in list(reg.slugs()) + (["xprj"] if "xprj" in nets else []):
        net = nets.get(slug)
        if net is None:
            rows.append((slug, "-", "-", "-", "not initialised"))
            continue
        rep = audit_mod.run(net, registry=reg)
        pend = len(ingest.pending(net.dir)) if slug != "xprj" else 0
        pending_total += pend
        note = "sound" if rep.ok else "needs a look"
        rows.append((slug, str(rep.neuron_count), str(rep.active_count),
                     str(pend) if slug != "xprj" else "-", note))
        if not rep.ok:
            faults.append((slug, rep))

    width = max(len(r[0]) for r in rows) + 2
    print(f"{'project':<{width}}{'facts':>7}{'live':>6}{'waiting':>9}  state")
    for slug, n, a, p, note in rows:
        print(f"{slug:<{width}}{n:>7}{a:>6}{p:>9}  {note}")

    spent, cap = budget.spent(home()), budget.limit()
    print(f"\nmodel calls today: {spent} of {cap}"
          f"   (sessions report themselves; a call is only for a day none did)")
    if pending_total:
        print(f"{pending_total} day(s) waiting with no self-report. "
              f"They cost nothing where they are.")
        print(f"  python -m pcnn distill --all --limit 5   "
              f"pays a model to read them")
    for slug, rep in faults:
        for line in rep.render().splitlines()[2:]:
            print(f"  {slug}:{line}")
    out = home() / "output" / "network.html"
    if out.exists():
        print(f"\nthe picture: {out}")
    return 0


def cmd_apply(args) -> int:
    net = _net(args.project)
    text = Path(args.file).read_text(encoding="utf-8")
    cause = args.cause or f"manual/{Path(args.file).name}"
    result = distill.apply_mutations(net, distill.strip_fences(text), cause=cause)
    q = distill.quarantine(net, result, cause=cause)
    net.rebuild()
    print(result.summary())
    for r in result.rejected:
        print(f"  rejected [{r.op}]: {r.reason}")
    if q:
        print(f"  quarantine: {q}")
    return 0


def cmd_audit(args) -> int:
    reg = Registry(home())
    bad = 0
    for slug in _targets(args):
        net = _net(slug)
        rep = audit_mod.run(net, registry=reg)
        audit_mod.write_report(net, rep)
        print(rep.render())
        bad = max(bad, 0 if rep.ok else 1)
    return bad if args.strict else 0


def cmd_consolidate(args) -> int:
    reg = Registry(home())
    for slug in _targets(args):
        net = _net(slug)
        report = merge.consolidate(net)
        weights.enforce_floors(net)
        weights.reinforce_edges(net)
        net.rebuild()
        rep = audit_mod.run(net, registry=reg)
        audit_mod.write_report(net, rep)
        render.render_project(net, rep)
        print(f"{slug}: {report}")
        print(rep.render())
    render.render_global(load_all())
    return 0


def cmd_render(args) -> int:
    reg = Registry(home())
    nets = {}
    for slug in _targets(args):
        net = _net(slug)
        rep = audit_mod.run(net, registry=reg)
        out = render.render_project(net, rep)
        nets[slug] = net
        print(f"{slug}: {out}")
    if args.all:
        print(f"global: {render.render_global(load_all())}")
    return 0


def cmd_poster(args) -> int:
    """A still of one network, for a README or an issue."""
    net = _net(args.project)
    out = Path(args.out) if args.out else home() / "docs" / f"{net.slug}.svg"
    poster.draw(net, out, title=args.title or f"{net.slug} context network")
    print(f"{net.slug}: {out}")
    return 0


def cmd_demote(args) -> int:
    net = _net(args.project)
    n = weights.demote(net, args.neuron, args.value, reason=args.reason)
    net.rebuild()
    print(f"{n.id} salience -> {n.salience:.2f} ({args.reason})")
    return 0


def cmd_suggest(args) -> int:
    net = _net(args.project)
    pairs = weights.unlinked_co_changes(net)
    if not pairs:
        print("no unlinked neurons co-change often enough to suggest an edge")
        return 0
    print("neurons that keep changing together but carry no edge:")
    for a, b, hits in pairs:
        print(f"  {a} <-> {b}  ({hits} shared recaps)")
        print(f"    {net.neurons[a].head}")
        print(f"    {net.neurons[b].head}")
    return 0


# --------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="pcnn", description=__doc__)
    p.set_defaults(func=cmd_dashboard)
    sub = p.add_subparsers(dest="command")

    def add_target(sp, *, required_project=True):
        sp.add_argument("project", nargs="?" if not required_project else None,
                        help="project slug")
        sp.add_argument("--all", action="store_true", help="every registered project")

    sp = sub.add_parser("init", help="register a project and create its network")
    sp.add_argument("project")
    sp.add_argument("path")
    sp.set_defaults(func=cmd_init)

    sp = sub.add_parser("status", help="overview of every network")
    sp.set_defaults(func=cmd_status)

    sp = sub.add_parser("notify", help="show the nightly toast")
    sp.add_argument("--dry-run", action="store_true", help="print it instead")
    sp.set_defaults(func=cmd_notify)

    sp = sub.add_parser("cost", help="model calls charged per day")
    sp.set_defaults(func=cmd_cost)

    sp = sub.add_parser("validate", help="schema check a network")
    sp.add_argument("project", nargs="?")
    sp.add_argument("--all", action="store_true")
    sp.add_argument("-v", "--verbose", action="store_true", help="show warnings too")
    sp.set_defaults(func=cmd_validate)

    sp = sub.add_parser("rebuild", help="regenerate MAP.md, INVARIANTS.md, graph.json")
    sp.add_argument("project", nargs="?")
    sp.add_argument("--all", action="store_true")
    sp.set_defaults(func=cmd_rebuild)

    sp = sub.add_parser("query", help="retrieve neurons by spreading activation")
    sp.add_argument("project", nargs="?")
    sp.add_argument("text")
    sp.add_argument("--all", action="store_true", help="search every project at once")
    sp.add_argument("--top", type=int, default=query.TOP_K)
    sp.add_argument("--json", action="store_true")
    sp.add_argument("-v", "--verbose", action="store_true")
    sp.add_argument("--include-retired", action="store_true", default=False)
    sp.set_defaults(func=cmd_query)

    sp = sub.add_parser("context", help="print INVARIANTS.md + MAP.md for a session")
    sp.add_argument("project")
    sp.set_defaults(func=cmd_context)

    sp = sub.add_parser("harvest", help="stage A: transcript -> raw delta")
    sp.add_argument("--transcript", required=True)
    sp.add_argument("--cwd", default="")
    sp.add_argument("--project", default="")
    sp.add_argument("--session-id", default="")
    sp.add_argument("--full", action="store_true",
                    help="ignore the cursor and re-read the whole transcript")
    sp.set_defaults(func=cmd_harvest)

    sp = sub.add_parser("distill", help="stage B: raw deltas -> neuron mutations")
    sp.add_argument("project", nargs="?")
    sp.add_argument("--all", action="store_true")
    sp.add_argument("--pending", action="store_true", default=True)
    sp.add_argument("--dry-run", action="store_true",
                    help="build the prompt, do not call the model")
    sp.add_argument("--limit", type=int, default=0,
                    help="stop after N deltas; a fresh backlog is one model call each")
    sp.add_argument("--model", default=distill.DEFAULT_MODEL,
                    help=f"model for distillation (default {distill.DEFAULT_MODEL})")
    sp.add_argument("--all-days", action="store_true",
                    help="also distil days that changed no file and hit no failure")
    sp.add_argument("--claude", default="claude", help="claude executable")
    sp.add_argument("-v", "--verbose", action="store_true")
    sp.set_defaults(func=cmd_distill)

    sp = sub.add_parser("apply", help="apply a mutation file written by hand or by a model")
    sp.add_argument("project")
    sp.add_argument("--file", required=True)
    sp.add_argument("--cause", default="")
    sp.set_defaults(func=cmd_apply)

    sp = sub.add_parser("audit", help="health check: orphans, stale anchors, coverage")
    sp.add_argument("project", nargs="?")
    sp.add_argument("--all", action="store_true")
    sp.add_argument("--strict", action="store_true", help="exit non-zero when unhealthy")
    sp.set_defaults(func=cmd_audit)

    sp = sub.add_parser("consolidate", help="nightly: merge, reweight, audit, render")
    sp.add_argument("project", nargs="?")
    sp.add_argument("--all", action="store_true")
    sp.set_defaults(func=cmd_consolidate)

    sp = sub.add_parser("render", help="write the HTML view")
    sp.add_argument("project", nargs="?")
    sp.add_argument("--all", action="store_true")
    sp.set_defaults(func=cmd_render)

    sp = sub.add_parser("poster", help="write a still of a network as SVG")
    sp.add_argument("project")
    sp.add_argument("--out", default="")
    sp.add_argument("--title", default="")
    sp.set_defaults(func=cmd_poster)

    sp = sub.add_parser("demote", help="the only way to lower salience; needs a reason")
    sp.add_argument("project")
    sp.add_argument("neuron")
    sp.add_argument("value", type=float)
    sp.add_argument("--reason", required=True)
    sp.set_defaults(func=cmd_demote)

    sp = sub.add_parser("suggest", help="unlinked neurons that keep changing together")
    sp.add_argument("project")
    sp.set_defaults(func=cmd_suggest)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
