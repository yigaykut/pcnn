"""Was there anything to do today?

The nightly pass is cheap, but running it on a day nobody opened a session is
pure noise: it rewrites four HTML files to say exactly what they said yesterday,
and it puts a line in the log that means nothing.  So it asks first.

The signal is the Claude Code transcript itself.  A session writes to
`~/.claude/projects/<slug>/<session>.jsonl` as it runs, so a transcript touched
today is a session opened today.  That is true even for a session that changed
nothing, which is the right bar: the question is whether a session happened, not
whether it was productive.
"""

from __future__ import annotations

import os
import re
from datetime import date, datetime
from pathlib import Path

from .store import Registry, home


def transcript_root() -> Path:
    """Where Claude Code keeps session transcripts on this machine."""
    override = os.environ.get("CLAUDE_CONFIG_DIR")
    base = Path(override) if override else Path.home() / ".claude"
    return base / "projects"


def _slug_for(path: Path) -> str:
    """Claude Code's directory name for a working directory.

    Every character that is not a letter or a digit becomes a hyphen - which
    includes the drive colon, both separators, spaces, and any non-ASCII letter,
    so `C:\\Users\\Renee\\OneDrive\\Desktop\\project orchestrator` is stored as
    `C--Users-Renee-OneDrive-Desktop-project-orchestrator`.
    """
    return re.sub(r"[^A-Za-z0-9]", "-", str(path))


def sessions_today(root: Path | None = None, day: str | None = None) -> list[Path]:
    """Transcripts of registered projects that were written to on `day`."""
    day = day or date.today().isoformat()
    projects = transcript_root()
    if not projects.is_dir():
        return []

    reg = Registry(root or home())
    wanted = set()
    for slug, meta in reg.projects.items():
        raw = meta.get("path")
        if not raw:
            continue
        # Claude Code names the folder after the resolved working directory, so
        # a registry entry holding a short or relative form must be resolved to
        # match it
        wanted.add(_slug_for(Path(raw)).lower())
        try:
            wanted.add(_slug_for(Path(raw).resolve()).lower())
        except OSError:
            pass

    touched = []
    for folder in projects.iterdir():
        if not folder.is_dir() or folder.name.lower() not in wanted:
            continue
        for jsonl in folder.glob("*.jsonl"):
            try:
                stamp = datetime.fromtimestamp(jsonl.stat().st_mtime).date().isoformat()
            except OSError:
                continue
            if stamp == day:
                touched.append(jsonl)
    return touched


def anything_happened(root: Path | None = None, day: str | None = None) -> bool:
    return bool(sessions_today(root, day))
