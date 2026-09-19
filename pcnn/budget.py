"""A hard ceiling on what the pipeline may spend in a day.

The point of PCNN is to spend fewer tokens overall, so the automatic half has
to be bounded by something other than good intentions.  Every model call is
counted against a daily quota; when it runs out the pipeline stops and says so,
and the undistilled deltas simply wait - they are on disk and lose nothing.
"""

from __future__ import annotations

import json
import os
from datetime import date
from pathlib import Path

#: model calls per day across every project; override with PCNN_DAILY_CALLS
DEFAULT_DAILY_CALLS = 30
LEDGER = ".budget.json"


def limit() -> int:
    raw = os.environ.get("PCNN_DAILY_CALLS")
    try:
        return max(0, int(raw)) if raw is not None else DEFAULT_DAILY_CALLS
    except ValueError:
        return DEFAULT_DAILY_CALLS


def _path(home: Path) -> Path:
    return home / LEDGER


def _load(home: Path) -> dict:
    p = _path(home)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def spent(home: Path, day: str | None = None) -> int:
    return int(_load(home).get(day or date.today().isoformat(), 0))


def remaining(home: Path) -> int:
    return max(0, limit() - spent(home))


def charge(home: Path, calls: int = 1) -> int:
    """Record `calls` model calls against today and return what is left."""
    day = date.today().isoformat()
    data = _load(home)
    data[day] = int(data.get(day, 0)) + calls
    # a fortnight of history is enough to answer "what did this cost me"
    for old in sorted(data)[:-14]:
        data.pop(old, None)
    _path(home).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return remaining(home)


def history(home: Path) -> dict:
    return _load(home)
