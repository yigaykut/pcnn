@neuron PCNN.OPS-002
head: Both hooks are registered in the user settings file in exec form
layer: OPS
project: pcnn
status: active
confidence: verified
salience: 0.72
signals: args, exec-form, hook-registration, install, settings-json
description: SessionStart and SessionEnd entries in the Claude Code user settings file use
  command "python" with the script path in args, so the path is spawned directly instead of
  being parsed by a shell. Removing the two entries from that file disables the whole automatic
  update pipeline without touching the repository.
anchors: README.md
connected.PCNN.OPS-002 -> PCNN.OPS-001 : depends_on w=0.60
connected.PCNN.OPS-002 -> PCNN.ARC-002 : implements w=0.80
evidence: recap/2026-09-17/build
first_seen: 2026-09-17
last_touched: 2026-09-17
revision: 1
