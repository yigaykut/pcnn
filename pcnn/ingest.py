"""Stage A - deterministic harvest of a Claude Code session transcript.

No model runs here.  This step is pure parsing so that it is free, instant and
incapable of hallucinating: whatever actually happened in the session is
recorded verbatim, and only the *interpretation* of it (Stage B, `distill.py`)
costs tokens.  If distillation never runs, the raw delta is still on disk and
nothing is lost.

Two properties that real transcripts force:

**Split by day.**  A Claude Code session is not a day - the transcripts here span
five weeks and 2700 commands.  One delta that size is useless as a distillation
prompt, so records are bucketed by calendar day and each day gets its own raw
delta.  That also matches how the network is meant to be read: what changed on
which day.

**Incremental.**  The SessionEnd hook fires every time a long-running session
ends, and re-parsing from line zero would re-emit days already harvested.  A
cursor per transcript records how far the last harvest got.

Transcripts live at `~/.claude/projects/<slug>/<session-id>.jsonl`, one JSON
object per line.  The shapes this reads are:

  {"type":"user","message":{"content": "..."} , "cwd":..., "gitBranch":...}
  {"type":"assistant","message":{"content":[{"type":"tool_use","name":"Edit",...}]}}
  {"type":"user","message":{"content":[{"type":"tool_result","is_error":true,...}]}}
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

#: tools whose invocation means the working tree changed
WRITE_TOOLS = {"Edit", "Write", "NotebookEdit", "MultiEdit"}
READ_TOOLS = {"Read", "Grep", "Glob"}
SHELL_TOOLS = {"Bash", "PowerShell"}

MAX_INSTRUCTION_CHARS = 2000
MAX_RECAP_CHARS = 8000
MAX_ERROR_CHARS = 500

#: per-day caps, so one busy day cannot produce a prompt nothing can read.
#: Counts are always reported in full even when the lists are truncated.
MAX_INSTRUCTIONS = 60
MAX_COMMANDS = 120
MAX_FAILURES = 40
MAX_FILE_CHANGES = 200
MAX_READS = 60

CURSOR_NAME = ".cursor.json"

#: first line of prompts/DISTILL_RECAP.md, used to recognise a session
#: that PCNN itself started
DISTILL_PROMPT_MARKER = "TASK: distil one session delta"

_COMMAND_BUCKETS = (
    ("test", re.compile(r"\b(pytest|unittest|jest|vitest|go test|cargo test|npm t(est)?\b)")),
    ("build", re.compile(r"\b(make|cmake|npm run build|tsc|webpack|vite build|cargo build)\b")),
    ("deploy", re.compile(r"\b(gcloud|docker|kubectl|terraform|vercel|fly deploy|heroku|"
                          r"serverless|aws)\b")),
    ("install", re.compile(r"\b(pip install|npm i(nstall)?\b|yarn add|poetry add|apt-get|choco)\b")),
    ("vcs", re.compile(r"^\s*git\b")),
    ("run", re.compile(r"\b(python|node|streamlit|uvicorn|flask|dotnet run)\b")),
)


def bucket_command(cmd: str) -> str:
    for name, pattern in _COMMAND_BUCKETS:
        if pattern.search(cmd):
            return name
    return "other"


@dataclass
class Delta:
    """One project-day of work, as facts rather than interpretation."""
    day: str = ""
    session_id: str = ""
    transcript: str = ""
    project: str = ""
    cwd: str = ""
    git_branch: str = ""
    started: str = ""
    ended: str = ""
    cli_version: str = ""
    user_instructions: list[dict] = field(default_factory=list)
    file_changes: list[dict] = field(default_factory=list)
    files_read: list[str] = field(default_factory=list)
    commands: list[dict] = field(default_factory=list)
    failures: list[dict] = field(default_factory=list)
    skills_used: list[str] = field(default_factory=list)
    recap: str = ""
    #: the last fenced @pcnn block anywhere in the day, not just in the recap
    self_report: str = ""
    counts: dict = field(default_factory=dict)
    truncated: dict = field(default_factory=dict)
    #: assistant text blocks for this day, kept only to pick the closing recap
    _texts: list[str] = field(default_factory=list, repr=False)

    def is_empty(self) -> bool:
        return not (self.file_changes or self.commands or self.user_instructions)

    def to_dict(self) -> dict:
        return {
            "kind": "pcnn.raw-delta",
            "version": 2,
            "day": self.day,
            "session_id": self.session_id,
            "transcript": self.transcript,
            "project": self.project,
            "cwd": self.cwd,
            "git_branch": self.git_branch,
            "started": self.started,
            "ended": self.ended,
            "cli_version": self.cli_version,
            "user_instructions": self.user_instructions,
            "file_changes": self.file_changes,
            "files_read": self.files_read,
            "commands": self.commands,
            "failures": self.failures,
            "skills_used": self.skills_used,
            "recap": self.recap,
            "self_report": self.self_report,
            "counts": self.counts,
            "truncated": self.truncated,
        }


def _clip(text: str, limit: int) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n... [clipped, {len(text) - limit} more chars]"


def _stringify(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(
            b.get("text", "") if isinstance(b, dict) else str(b) for b in content)
    return str(content)


def _dedupe(items: list[str]) -> list[str]:
    seen, out = set(), []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


# --------------------------------------------------------------------------
# Parsing
# --------------------------------------------------------------------------

def parse_transcript(path: str | Path, *, start_line: int = 0,
                     max_lines: int = 2_000_000) -> tuple[list[Delta], int]:
    """Walk a session jsonl and return (one delta per calendar day, lines read).

    Never raises on malformed lines: a transcript that is being written while it
    is read will have a torn final line, and that must not cost a whole harvest.
    """
    path = Path(path)
    days: dict[str, Delta] = {}
    tool_calls: dict[str, dict] = {}
    meta = {"session_id": "", "cwd": "", "branch": "", "version": ""}
    lineno = 0

    def day_delta(ts: str) -> Delta:
        key = (ts or "")[:10] or "undated"
        d = days.get(key)
        if d is None:
            d = Delta(day=key, transcript=str(path))
            days[key] = d
        return d

    with path.open("r", encoding="utf-8", errors="replace") as fh:
        for lineno, line in enumerate(fh, 1):
            if lineno <= start_line:
                continue
            if lineno - start_line > max_lines:
                break
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(rec, dict):
                continue

            meta["session_id"] = rec.get("sessionId") or rec.get("session_id") \
                or meta["session_id"]
            meta["cwd"] = rec.get("cwd") or meta["cwd"]
            meta["branch"] = rec.get("gitBranch") or meta["branch"]
            meta["version"] = rec.get("version") or meta["version"]

            ts = rec.get("timestamp", "")
            rtype = rec.get("type")
            if rtype not in ("user", "assistant") or not ts:
                continue

            d = day_delta(ts)
            d.started = d.started or ts
            d.ended = ts

            message = rec.get("message") or {}
            content = message.get("content")
            sidechain = bool(rec.get("isSidechain"))

            if rtype == "user":
                if isinstance(content, str):
                    if rec.get("isMeta") or sidechain:
                        continue
                    text = content.strip()
                    if text:
                        d.user_instructions.append(
                            {"ts": ts, "text": _clip(text, MAX_INSTRUCTION_CHARS)})
                elif isinstance(content, list):
                    for block in content:
                        if not isinstance(block, dict):
                            continue
                        if block.get("type") == "tool_result" and block.get("is_error"):
                            call = tool_calls.get(block.get("tool_use_id", ""), {})
                            d.failures.append({
                                "ts": ts,
                                "tool": call.get("name", "?"),
                                "target": call.get("target", ""),
                                "error": _clip(_stringify(block.get("content")),
                                               MAX_ERROR_CHARS),
                            })

            elif rtype == "assistant" and isinstance(content, list):
                for block in content:
                    if not isinstance(block, dict):
                        continue
                    if block.get("type") == "text" and not sidechain:
                        text = block.get("text", "").strip()
                        if text:
                            d._texts.append(text)
                    elif block.get("type") == "tool_use":
                        _record_tool_use(d, block, tool_calls, ts)

    for d in days.values():
        d.session_id = meta["session_id"]
        d.cwd = meta["cwd"]
        d.git_branch = meta["branch"]
        d.cli_version = meta["version"]
        _finalise(d)

    return [days[k] for k in sorted(days)], lineno


def _record_tool_use(d: Delta, block: dict, tool_calls: dict, ts: str) -> None:
    name = block.get("name", "")
    args = block.get("input") or {}
    call_id = block.get("id", "")
    target = ""

    if name in WRITE_TOOLS:
        target = str(args.get("file_path") or args.get("notebook_path") or "")
        entry = {"ts": ts, "path": target, "tool": name,
                 "op": "create" if name == "Write" else "edit"}
        if name == "Write":
            entry["bytes"] = len(str(args.get("content", "")))
        else:
            entry["bytes_removed"] = len(str(args.get("old_string", "")))
            entry["bytes_added"] = len(str(args.get("new_string", "")))
        d.file_changes.append(entry)

    elif name in SHELL_TOOLS:
        cmd = str(args.get("command", "")).strip()
        target = cmd[:120]
        if cmd:
            d.commands.append({"ts": ts, "tool": name, "command": _clip(cmd, 500),
                               "bucket": bucket_command(cmd),
                               "description": str(args.get("description", ""))})

    elif name in READ_TOOLS:
        p = args.get("file_path") or args.get("path") or args.get("pattern")
        if p:
            target = str(p)
            d.files_read.append(target)

    elif name == "Skill":
        skill = str(args.get("skill", ""))
        if skill and skill not in d.skills_used:
            d.skills_used.append(skill)

    if call_id:
        tool_calls[call_id] = {"name": name, "target": target}


def _finalise(d: Delta) -> None:
    """Aggregate, cap and count.  Counts stay truthful even when lists are cut."""
    changed_paths = [c["path"] for c in d.file_changes]
    d.counts = {
        "instructions": len(d.user_instructions),
        "file_changes": len(d.file_changes),
        "files_touched": len(set(changed_paths)),
        "commands": len(d.commands),
        "failures": len(d.failures),
        "reads": len(set(d.files_read)),
    }

    # commands repeat heavily (the same test run forty times); fold duplicates
    folded: dict[str, dict] = {}
    for c in d.commands:
        key = c["command"]
        if key in folded:
            folded[key]["repeats"] += 1
            folded[key]["ts"] = c["ts"]
        else:
            folded[key] = {**c, "repeats": 1}
    commands = sorted(folded.values(), key=lambda c: (-c["repeats"], c["ts"]))
    d.counts["unique_commands"] = len(commands)

    # file changes fold to one entry per path, carrying the edit count and churn
    per_file: dict[str, dict] = {}
    for c in d.file_changes:
        e = per_file.setdefault(c["path"], {"path": c["path"], "edits": 0,
                                            "created": False, "churn": 0})
        e["edits"] += 1
        e["created"] = e["created"] or c["op"] == "create"
        e["churn"] += c.get("bytes", 0) + c.get("bytes_added", 0)
    files = sorted(per_file.values(), key=lambda f: -f["churn"])

    d.truncated = {}
    for name, seq, cap in (("user_instructions", d.user_instructions, MAX_INSTRUCTIONS),
                           ("failures", d.failures, MAX_FAILURES)):
        if len(seq) > cap:
            d.truncated[name] = len(seq) - cap
    if len(commands) > MAX_COMMANDS:
        d.truncated["commands"] = len(commands) - MAX_COMMANDS
    if len(files) > MAX_FILE_CHANGES:
        d.truncated["file_changes"] = len(files) - MAX_FILE_CHANGES

    # keep the *last* instructions and failures: the end of a day is where the
    # conclusions are, and the earlier ones were already harvested on their day
    d.user_instructions = d.user_instructions[-MAX_INSTRUCTIONS:]
    d.failures = d.failures[-MAX_FAILURES:]
    d.commands = commands[:MAX_COMMANDS]
    d.file_changes = files[:MAX_FILE_CHANGES]
    d.files_read = _dedupe(d.files_read)[:MAX_READS]
    d.recap = _clip("\n\n".join(d._texts[-3:]), MAX_RECAP_CHARS)
    # A self-report can be written before the session's last three messages - a
    # long tail of follow-up work pushes it out of the recap window - so the
    # whole day is scanned for it rather than only the end of it.
    from . import reap
    for text in reversed(d._texts):
        found = reap.extract(text)
        if found:
            d.self_report = found
            break
    d._texts = []


# --------------------------------------------------------------------------
# Cursors and writing
# --------------------------------------------------------------------------

def _cursor_path(network_dir: Path) -> Path:
    return network_dir / "recaps" / CURSOR_NAME


def _cursor_key(transcript: str | Path) -> str:
    """One key per file, whatever spelling the caller used.

    The CLI is given a path with forward slashes and the SessionEnd hook is
    given the same file with backslashes.  Keyed on the raw string those are two
    different transcripts, so the hook found no cursor and re-read from line one,
    duplicating every day it had already harvested.
    """
    return os.path.normcase(os.path.abspath(str(transcript)))


def _normalised(data: dict) -> dict:
    """Fold any keys written before normalisation, keeping the furthest read."""
    out: dict = {}
    for raw, value in data.items():
        key = _cursor_key(raw)
        lines = int(value.get("lines", 0)) if isinstance(value, dict) else 0
        if lines > int(out.get(key, {}).get("lines", 0)):
            out[key] = {"lines": lines}
    return out


def read_cursor(network_dir: Path, transcript: str) -> int:
    path = _cursor_path(network_dir)
    if not path.exists():
        return 0
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return 0
    return int(_normalised(data).get(_cursor_key(transcript), {}).get("lines", 0))


def write_cursor(network_dir: Path, transcript: str, lines: int) -> None:
    path = _cursor_path(network_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {}
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            data = {}
    data = _normalised(data)
    data[_cursor_key(transcript)] = {"lines": lines}
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")


def is_pipeline_output(delta: Delta) -> bool:
    """True when a delta is PCNN's own distillation run rather than project work.

    The `PCNN_INTERNAL` guard in the SessionEnd hook is the primary defence, but
    it only covers sessions this machine started.  A delta that changed no file,
    ran no command and whose closing message is a mutation block is the
    distiller looking at itself, and must never be fed back in.
    """
    from . import reap
    if delta.self_report or reap.has_block(delta.recap):
        return False          # a fenced self-report is a real session reporting
    if delta.file_changes or delta.commands:
        return False
    if delta.recap.lstrip().startswith("@mutation"):
        return True
    # the distillation prompt is the only instruction such a session ever gets,
    # and it identifies itself on its first line; matching the instruction is
    # sturdier than matching the answer, which may be an error message instead
    first = (delta.user_instructions[0]["text"] if delta.user_instructions else "")
    return DISTILL_PROMPT_MARKER in first[:400]


def harvest(transcript: str | Path, project: str, network_dir: Path,
            *, session_id: str = "", incremental: bool = True) -> list[Path]:
    """Parse a transcript and write one raw delta per day under `recaps/<day>/`.

    Returns the written paths.  A day that only read files produces nothing -
    reading is not a fact about the project.
    """
    transcript = str(transcript)
    start = read_cursor(network_dir, transcript) if incremental else 0
    deltas, lines_read = parse_transcript(transcript, start_line=start)

    written: list[Path] = []
    for delta in deltas:
        if delta.is_empty() or is_pipeline_output(delta):
            continue
        delta.project = project
        if session_id:
            delta.session_id = session_id or delta.session_id
        out_dir = network_dir / "recaps" / delta.day
        out_dir.mkdir(parents=True, exist_ok=True)
        stem = delta.session_id or Path(transcript).stem
        # the harvested line range is part of the name, so re-harvesting the same
        # range overwrites itself identically while a later range never collides
        out = out_dir / f"{stem}-L{start + 1:06d}-{lines_read:06d}.raw.json"
        out.write_text(json.dumps(delta.to_dict(), indent=2, ensure_ascii=False) + "\n",
                       encoding="utf-8")
        written.append(out)

    if incremental:
        write_cursor(network_dir, transcript, lines_read)
    return written


def pending(network_dir: Path) -> list[Path]:
    """Raw deltas that have not been distilled yet."""
    recaps = network_dir / "recaps"
    if not recaps.is_dir():
        return []
    return [raw for raw in sorted(recaps.glob("*/*.raw.json"))
            if not applied_marker(raw).exists()]


def applied_marker(raw: Path) -> Path:
    return raw.with_suffix("").with_suffix(".applied.json")


def mark_applied(raw: Path, result: dict) -> Path:
    marker = applied_marker(raw)
    marker.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n",
                      encoding="utf-8")
    return marker
