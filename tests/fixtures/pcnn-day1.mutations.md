@mutation upsert $GOT-1
head: Hook stdin must be decoded as UTF-8 explicitly or non-ASCII paths are mangled
layer: GOT
project: pcnn
status: active
confidence: verified
salience: 0.88
signals: hook-stdin, utf-8, encoding, windows, codepage, non-ascii-path, turkish
description: Reading a hook payload with sys.stdin.read() on Windows decodes it with the
  console codepage, which mangled an orchestrator path whose home directory carries a
  non-ASCII letter and made Registry.resolve_path return no project, so both hooks
  silently did nothing. Both hooks now read sys.stdin.buffer and decode UTF-8 with errors="replace".
rationale: Claude Code writes hook payloads as UTF-8 regardless of the console codepage,
  and the failure is silent - the hook exits 0 and logs that it found no project, which
  looks identical to a correctly ignored unregistered directory.
alternatives_rejected: setting PYTHONUTF8 in the hook command (does not travel with the
  repository and is easy to lose)
anchors: hooks/session_end.py, hooks/session_start.py
evidence: recap/2026-09-17/build
first_seen: 2026-09-17

@mutation upsert $GOT-2
head: One Claude Code session can span weeks, so a raw delta must be split per calendar day
layer: GOT
project: pcnn
status: active
confidence: verified
salience: 0.85
signals: session-length, delta-size, day-split, prompt-size, cursor, incremental-harvest
description: The invest transcript covers 2026-08-11 to 2026-09-17 in a single session and
  produced a 2 MB delta with 496 instructions and 2695 commands, far too large to use as a
  distillation prompt. Harvesting now buckets records by calendar day, folds repeated
  commands into one entry with a repeat count, caps each list per day, and records a line
  cursor per transcript so a re-fired SessionEnd hook never re-emits a day already written.
rationale: Delta size is bounded by the day rather than by the session, which both fits a
  prompt and matches how the network is meant to be read - what changed on which day.
alternatives_rejected: one delta per session (unbounded); truncating the newest records
  (drops exactly the conclusions worth keeping)
anchors: pcnn/ingest.py
evidence: recap/2026-09-17/build
first_seen: 2026-09-17

@mutation upsert $DEC-1
head: Nightly consolidation runs as a Windows scheduled task, not a cloud routine
layer: DEC
project: pcnn
status: active
confidence: verified
salience: 0.86
signals: nightly, scheduled-task, cron, consolidation, local-execution
description: scripts/nightly.py runs pcnn distill, consolidate and audit across every
  network, registered by scripts/install-nightly.ps1 as a daily Windows scheduled task at
  23:30. The -NoDistill switch skips the model call so the free half can run on its own.
rationale: A scheduled cloud agent executes remotely and cannot reach the networks, the
  session transcripts or the rendered HTML, all of which are on this machine.
alternatives_rejected: a scheduled cloud agent via the schedule skill; a /loop session,
  which only lasts as long as the session does
anchors: scripts/nightly.py, scripts/install-nightly.ps1
evidence: recap/2026-09-17/build
first_seen: 2026-09-17

@mutation upsert $CON-1
head: The xprj scope is never registered with a filesystem path
layer: CON
project: pcnn
status: active
confidence: verified
salience: 0.95
signals: xprj, cross-project, registry, resolve-path, scope
description: networks/xprj holds cross-project neurons and has no source directory. Giving
  it a registry path made Registry.resolve_path attribute any unregistered directory under
  that path to the cross-project network, so xprj is kept out of registry.json entirely and
  added to --all targets explicitly by pcnn.cli._targets.
rationale: resolve_path does longest-prefix matching, so a broad registered path silently
  captures every project below it that is not itself registered.
alternatives_rejected: registering xprj against the Desktop directory
anchors: pcnn/cli.py, registry.json
evidence: recap/2026-09-17/build
first_seen: 2026-09-17

@mutation upsert $OPS-1
head: Both hooks are registered in the user settings file in exec form
layer: OPS
project: pcnn
status: active
confidence: verified
salience: 0.72
signals: settings-json, hook-registration, exec-form, args, install
description: SessionStart and SessionEnd entries in the Claude Code user settings file use
  command "python" with the script path in args, so the path is spawned directly instead of
  being parsed by a shell. Removing the two entries from that file disables the whole
  automatic update pipeline without touching the repository.
anchors: README.md
evidence: recap/2026-09-17/build
first_seen: 2026-09-17

@mutation link $GOT-1 -> PCNN.ARC-002 : constrained_by w=0.85
@mutation link $GOT-2 -> PCNN.ARC-002 : constrained_by w=0.90
@mutation link $DEC-1 -> PCNN.ARC-002 : implements w=0.75
@mutation link $CON-1 -> PCNN.DAT-001 : constrained_by w=0.70
@mutation link $OPS-1 -> PCNN.ARC-002 : implements w=0.80
@mutation link $OPS-1 -> PCNN.OPS-001 : depends_on w=0.60
@mutation link $GOT-2 -> PCNN.CON-002 : caused_by w=0.55
@mutation touch PCNN.ARC-002
@mutation touch PCNN.GOT-001
