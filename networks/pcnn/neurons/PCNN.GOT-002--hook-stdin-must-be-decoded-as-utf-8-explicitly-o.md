@neuron PCNN.GOT-002
head: Hook stdin must be decoded as UTF-8 explicitly or non-ASCII paths are mangled
layer: GOT
project: pcnn
status: active
confidence: verified
salience: 0.88
signals: codepage, encoding, hook-stdin, non-ascii-path, turkish, utf-8, windows
description: Reading a hook payload with sys.stdin.read() on Windows decodes it with the console
  codepage, which turned the orchestrator path <home>\... into a mangled string and made
  Registry.resolve_path return no project, so both hooks silently did nothing. Both hooks now
  read sys.stdin.buffer and decode UTF-8 with errors="replace".
rationale: Claude Code writes hook payloads as UTF-8 regardless of the console codepage, and the
  failure is silent - the hook exits 0 and logs that it found no project, which looks identical
  to a correctly ignored unregistered directory.
alternatives_rejected: setting PYTHONUTF8 in the hook command (does not travel with the
  repository and is easy to lose)
anchors: hooks/session_end.py, hooks/session_start.py
connected.PCNN.GOT-002 -> PCNN.ARC-002 : constrained_by w=0.85
evidence: recap/2026-09-17/build
first_seen: 2026-09-17
last_touched: 2026-09-17
revision: 1
