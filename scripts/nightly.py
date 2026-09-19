#!/usr/bin/env python3
"""The nightly pass: distil what is pending, then consolidate every network.

Run by the Windows scheduled task that `install-nightly.ps1` registers, or by
hand. Writes its own log so a failed run leaves evidence rather than silence.

Order matters: distillation adds neurons, consolidation cleans up after it.
Doing it the other way round would leave the day's duplicates until tomorrow.
"""

from __future__ import annotations

import argparse
import io
import sys
import traceback
from contextlib import redirect_stdout
from datetime import datetime, timezone
from pathlib import Path

HOME = Path(__file__).resolve().parent.parent
LOG = Path(__file__).resolve().parent / "nightly.log"

sys.path.insert(0, str(HOME))


def log(message: str) -> None:
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    line = f"{stamp} {message}"
    print(line)
    try:
        with LOG.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except OSError:
        pass


def step(name: str, argv: list[str]) -> int:
    """Run one CLI command, capturing its output into the log."""
    from pcnn.cli import main as cli_main

    log(f"--- {name}: pcnn {' '.join(argv)}")
    buffer = io.StringIO()
    try:
        with redirect_stdout(buffer):
            code = cli_main(argv)
    except SystemExit as exc:
        code = int(exc.code or 0)
    except Exception:  # noqa: BLE001 - one bad step must not skip the rest
        log(f"{name} raised:\n{traceback.format_exc()}")
        return 1
    for line in buffer.getvalue().splitlines():
        log(f"    {line}")
    return code


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--distill", action="store_true",
                    help="also pay a model to read days no session reported on")
    ap.add_argument("--force", action="store_true",
                    help="run even on a day no session was opened")
    ap.add_argument("--quiet", action="store_true",
                    help="do the work without showing a notification")
    args = ap.parse_args()

    from pcnn import activity
    if not (args.force or activity.anything_happened()):
        log("no session was opened today; nothing to consolidate, standing down")
        return 0

    log(f"nightly start (PCNN_HOME={HOME})")
    worst = 0
    if args.distill:
        worst |= step("distill", ["distill", "--all"])
    worst |= step("consolidate", ["consolidate", "--all"])
    worst |= step("audit", ["audit", "--all"])
    if not args.quiet:
        step("notify", ["notify"])
    log(f"nightly done (exit {worst})")
    return worst


if __name__ == "__main__":
    raise SystemExit(main())
