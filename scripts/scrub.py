#!/usr/bin/env python3
"""Take machine-local paths out of a network before it is published.

Evidence written by early distillation runs carried the absolute path of the
session transcript, which names the home directory and so the user. The session
id is the part that identifies the evidence; the rest is noise on any other
machine. The root cause is fixed - `distill.slim_delta` no longer shows the
model the transcript path - so this is for what was written before that, and for
any network being opened up for the first time.

Nothing is removed: a path becomes a shorter reference to the same session.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

TRANSCRIPT = re.compile(
    r"(?P<key>evidence:\s*)[A-Za-z]:[\\/][^\s,]*?[\\/](?P<id>[0-9a-fA-F-]{36})\.jsonl")
SLUG = re.compile(r"C--Users-[^\s\\/,]*?--")
ABS_PATH = re.compile(r"[A-Za-z]:\\Users\\[^\s\\]+")


def scrub(text: str, home: str) -> str:
    text = TRANSCRIPT.sub(r"\g<key>recap/session-\g<id>", text)
    text = text.replace(home, "<home>")
    text = SLUG.sub("C--Users-ME--", text)
    return ABS_PATH.sub("<home>", text)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("project", help="network slug, e.g. pcnn")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    from pcnn.store import Network

    net = Network(args.project, ROOT)
    if not net.exists():
        raise SystemExit(f"no network for {args.project!r}")

    home = str(Path.home())
    touched = []
    for path in sorted(net.neuron_dir.glob("*.md")):
        before = path.read_text(encoding="utf-8")
        after = scrub(before, home)
        if after != before:
            touched.append(path.name)
            if not args.dry_run:
                path.write_text(after, encoding="utf-8")

    print(f"{len(touched)} neuron file(s) "
          f"{'would be' if args.dry_run else ''} scrubbed")
    for name in touched:
        print(f"  {name}")
    if touched and not args.dry_run:
        net.load()
        net.rebuild()
        print("derived files rebuilt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
