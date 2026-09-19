@neuron PCNN.DEC-009
head: The nightly pass runs only on days a session was actually opened
layer: DEC
project: pcnn
status: active
confidence: stated
salience: 0.88
signals: activity-gate, nightly, quiet-day, scheduled-task, transcript-mtime
description: scripts/nightly.py asks pcnn.activity.anything_happened before doing any work and
  stands down when the answer is no. The signal is the Claude Code transcript itself: a file
  under the transcript root whose modification time falls on the day in question, and whose
  folder name matches a registered project. A session that opened and changed nothing still
  counts, because the question is whether a session happened rather than whether it was
  productive. The --force switch overrides the gate.
rationale: Running on a day nobody worked rewrites four HTML files to say exactly what they said
  yesterday and writes a log line that means nothing, which makes the log harder to read on the
  days it matters.
alternatives_rejected: gating on whether a recap was written, which misses a session that opened
  and changed nothing
anchors: pcnn/activity.py, scripts/nightly.py
connected.PCNN.DEC-009 -> PCNN.DAT-004 : depends_on w=0.90
connected.PCNN.DEC-009 -> PCNN.DEC-005 : refines w=0.85
evidence: self/2026-09-18/schedule
first_seen: 2026-09-18
last_touched: 2026-09-18
revision: 1
