#!/usr/bin/env python3
"""SessionEnd hook - harvest the finished session, then distil it in the background.

Registered in Claude Code settings as a `SessionEnd` hook.  Claude Code hands it
a JSON object on stdin:

    {"session_id": "...", "transcript_path": "...", "cwd": "...",
     "hook_event_name": "SessionEnd", "reason": "clear|logout|exit|..."}

Two rules govern everything here:

1. **Always exit 0.**  A context tool that can break the user's session is worse
   than no context tool.  Every failure is swallowed and logged to
   `hooks/hook.log` instead.
2. **Do the free work synchronously, the paid work detached.**  Parsing the
   transcript takes milliseconds and costs nothing, so it happens inline and the
   session is recorded no matter what.  The model call is spawned detached so it
   never delays the user.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

HOME = Path(__file__).resolve().parent.parent
LOG = Path(__file__).resolve().parent / "hook.log"

sys.path.insert(0, str(HOME))


def log(message: str) -> None:
    try:
        stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with LOG.open("a", encoding="utf-8") as fh:
            fh.write(f"{stamp} session_end: {message}\n")
    except OSError:
        pass


def spawn_distill(slug: str) -> None:
    """Fire `pcnn distill` detached so the session never waits on a model call."""
    cmd = [sys.executable, "-m", "pcnn", "distill", slug]
    env = dict(os.environ, PCNN_HOME=str(HOME))
    kwargs: dict = {"cwd": str(HOME), "env": env,
                    "stdin": subprocess.DEVNULL,
                    "stdout": subprocess.DEVNULL,
                    "stderr": subprocess.DEVNULL}
    if sys.platform == "win32":
        kwargs["creationflags"] = (getattr(subprocess, "DETACHED_PROCESS", 0)
                                   | getattr(subprocess, "CREATE_NO_WINDOW", 0))
    else:
        kwargs["start_new_session"] = True
    subprocess.Popen(cmd, **kwargs)


def reap_written(net, written) -> int:
    """Apply any `@pcnn` block the session left in its closing message."""
    from pcnn import distill, ingest, reap

    applied = 0
    for raw in written:
        try:
            delta = json.loads(raw.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        block = delta.get("self_report") or reap.extract(delta.get("recap", ""))
        if not block:
            continue
        cause = f"self/{raw.parent.name}/{raw.name}"
        result = distill.apply_mutations(net, block, cause=cause)
        distill.quarantine(net, result, cause=cause)
        ingest.mark_applied(raw, result.to_dict())
        applied += len(result.applied)
        if result.rejected:
            log(f"{net.slug}: {len(result.rejected)} self-reported mutation(s) "
                f"quarantined")
    if applied:
        net.rebuild()
    return applied


def read_payload() -> dict:
    """Read the hook payload from stdin.

    Decoded as UTF-8 explicitly: Claude Code writes UTF-8, but Python on
    Windows decodes stdin with the console codepage, which mangles any
    non-ASCII character in a path and makes the project unresolvable.
    """
    try:
        raw = sys.stdin.buffer.read().decode("utf-8", errors="replace")
    except (OSError, ValueError, AttributeError):
        return {}
    try:
        payload = json.loads(raw or "{}")
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def main() -> int:
    payload = read_payload()

    if os.environ.get("PCNN_INTERNAL"):
        # this session is the distiller's own headless model call; harvesting it
        # would feed the pipeline its own output and loop
        log("PCNN_INTERNAL set; this is a pipeline-owned session, standing down")
        return 0

    transcript = payload.get("transcript_path") or ""
    cwd = payload.get("cwd") or os.getcwd()
    session_id = payload.get("session_id") or ""

    if not transcript or not Path(transcript).exists():
        log(f"no transcript at {transcript!r}; nothing to harvest")
        return 0

    try:
        from pcnn import ingest
        from pcnn.store import Network, Registry

        reg = Registry(HOME)
        slug = reg.resolve_path(cwd)
        if not slug:
            log(f"cwd {cwd!r} is not a registered project; "
                f"register it with: python -m pcnn init <slug> \"{cwd}\"")
            return 0

        net = Network(slug, HOME)
        net.init()
        # load before applying: a self-report links to neurons that already
        # exist, and an unloaded network knows about none of them
        net.load()
        written = ingest.harvest(transcript, slug, net.dir, session_id=session_id)
        if not written:
            log(f"{slug}: nothing new in the transcript; no delta written")
            return 0
        log(f"{slug}: wrote {', '.join(p.name for p in written)}")

        # The zero-token path: the session reported what it learned in its own
        # closing message, so there is nothing left to pay a model to work out.
        applied = reap_written(net, written)
        if applied:
            log(f"{slug}: applied {applied} self-reported mutation(s), no model call")
            return 0

        if not os.environ.get("PCNN_AUTODISTILL"):
            log(f"{slug}: no self-report; delta waits (set PCNN_AUTODISTILL=1 to "
                f"pay a model to read it)")
            return 0
        spawn_distill(slug)
        log(f"{slug}: spawned detached distillation")
    except Exception:  # noqa: BLE001 - a hook must never fail a session
        log("unhandled error:\n" + traceback.format_exc())
    return 0


if __name__ == "__main__":
    sys.exit(main())
