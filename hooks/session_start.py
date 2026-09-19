#!/usr/bin/env python3
"""SessionStart hook - load the project's context network into the new session.

Claude Code hands it a JSON object on stdin:

    {"session_id": "...", "cwd": "...", "hook_event_name": "SessionStart",
     "source": "startup|resume|clear|compact"}

It answers with `additionalContext`: the invariants in full, the L0 map, and the
standing instructions for how to use them.  This is the automatic half of
requirement 3 - the session consults the network without anyone pasting a
prompt.  `prompts/SESSION_CONTEXT.md` is the manual half, for sessions that run
without hooks.

Like the SessionEnd hook, this always exits 0 and never blocks a session.
"""

from __future__ import annotations

import json
import os
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

HOME = Path(__file__).resolve().parent.parent
LOG = Path(__file__).resolve().parent / "hook.log"

sys.path.insert(0, str(HOME))

#: keeps the injected block from swallowing the session's budget on a huge graph
MAX_CONTEXT_CHARS = 60_000

PREAMBLE = """\
# PROJECT CONTEXT NETWORK ({slug})

This is the durable context for this project, carried over from previous
sessions. Treat it as established fact about the codebase.

How to use it:
- INVARIANTS below are decisions, constraints and gotchas that must not be
  contradicted. If the task requires going against one, say so explicitly and
  name the neuron id before doing it.
- The MAP is an index, not the whole story. Each line is one neuron. To read a
  fact in full, open `networks/{slug}/neurons/<id>--*.md` under the orchestrator
  at `{home}`.
- Before concluding that something does not exist in this project, run
  `python -m pcnn query {slug} "<question>"` from `{home}`. It retrieves by
  spreading activation and surfaces neurons no keyword would have matched.
## REPORTING BACK

{contract}
"""


def log(message: str) -> None:
    try:
        stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with LOG.open("a", encoding="utf-8") as fh:
            fh.write(f"{stamp} session_start: {message}\n")
    except OSError:
        pass


def build_context(slug: str) -> str:
    from pcnn import ingest
    from pcnn.store import Network

    net = Network(slug, HOME)
    if not net.exists():
        return ""
    from pcnn import reap
    example = next((n.id for n in net.sorted_neurons()
                    if n.status == "active" and n.pin), f"{slug.upper()}.ARC-001")
    parts = [PREAMBLE.format(slug=slug, home=HOME,
                             contract=reap.contract_for(slug, example))]
    if net.invariants_path.exists():
        parts.append(net.invariants_path.read_text(encoding="utf-8"))
    if net.map_path.exists():
        parts.append(net.map_path.read_text(encoding="utf-8"))

    waiting = ingest.pending(net.dir)
    if waiting:
        parts.append(
            f"## PENDING\n\n{len(waiting)} harvested session(s) have not been "
            f"distilled into the network yet, so the map may lag behind the code. "
            f"Run `python -m pcnn distill {slug}` from `{HOME}` to catch up.\n")

    text = "\n\n".join(p.strip() for p in parts if p.strip())
    if len(text) > MAX_CONTEXT_CHARS:
        # never truncate the invariants; drop map detail instead
        head = parts[0] + "\n\n" + (parts[1] if len(parts) > 1 else "")
        text = head[:MAX_CONTEXT_CHARS] + (
            f"\n\n[map omitted: over {MAX_CONTEXT_CHARS} chars. Read "
            f"networks/{slug}/MAP.md or use `python -m pcnn query {slug} \"...\"`.]\n")
    return text


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
    cwd = payload.get("cwd") or os.getcwd()

    try:
        from pcnn.store import Registry
        slug = Registry(HOME).resolve_path(cwd)
        if not slug:
            return 0
        context = build_context(slug)
        if not context:
            return 0
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": context,
            }
        }))
        log(f"{slug}: injected {len(context)} chars")
    except Exception:  # noqa: BLE001 - a hook must never fail a session
        log("unhandled error:\n" + traceback.format_exc())
    return 0


if __name__ == "__main__":
    sys.exit(main())
