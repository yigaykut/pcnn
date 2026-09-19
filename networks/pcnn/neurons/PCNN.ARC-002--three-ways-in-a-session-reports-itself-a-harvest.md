@neuron PCNN.ARC-002
head: Three ways in - a session reports itself, a harvest records it, a model reads it only if asked
layer: ARC
project: pcnn
status: active
confidence: verified
salience: 0.92
signals: distill, harvest, hooks, pipeline, self-report, session-end, two-stage, zero-token
description: Stage A parses the Claude Code session transcript with no model involved and writes
  a raw delta listing files changed, commands run, verbatim user instructions and failures. The
  normal update path then costs nothing further: the session fenced what it learned between
  @pcnn and @end in its closing message, and the SessionEnd hook validates that block and writes
  the neurons. Stage B, a headless model call that reads the delta and infers the same facts,
  remains available for backfilling old transcripts and for a session that ended without
  reporting, but it is off by default in both the nightly task and the session hook. Stage A is
  free and cannot hallucinate; Stage B is the only step that costs tokens and the only step that
  can be wrong.
rationale: Splitting the pipeline means a failed or skipped distillation still leaves the
  session fully recorded on disk, so nothing is ever unrecoverable. Putting the self-report
  ahead of distillation means the usual case never pays a model at all, because the session that
  did the work is the cheapest and most reliable witness to it.
alternatives_rejected: distilling every harvested day by default, which paid a model to
  rediscover what the session already knew
anchors: hooks/session_end.py, hooks/session_start.py, pcnn/distill.py, pcnn/ingest.py, pcnn/reap.py
connected.PCNN.ARC-002 -> PCNN.CON-002 : constrained_by w=0.90
connected.PCNN.ARC-002 -> PCNN.DEC-001 : implements w=0.85
evidence: P5, recap/2026-09-17/zero-token
first_seen: 2026-09-17
last_touched: 2026-09-17
revision: 2
