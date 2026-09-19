@neuron PCNN.GOT-003
head: One Claude Code session can span weeks, so a raw delta must be split per calendar day
layer: GOT
project: pcnn
status: active
confidence: verified
salience: 0.89
signals: cursor, day-split, delta-size, incremental-harvest, prompt-size, session-length
description: The invest transcript covers 2026-08-11 to 2026-09-17 in a single session and
  produced a 2 MB delta with 496 instructions and 2695 commands, far too large to use as a
  distillation prompt. Harvesting now buckets records by calendar day, folds repeated commands
  into one entry with a repeat count, caps each list per day, and records a line cursor per
  transcript so a re-fired SessionEnd hook never re-emits a day already written.
rationale: Delta size is bounded by the day rather than by the session, which both fits a prompt
  and matches how the network is meant to be read - what changed on which day.
alternatives_rejected: one delta per session (unbounded); truncating the newest records (drops
  exactly the conclusions worth keeping)
anchors: pcnn/ingest.py
connected.PCNN.GOT-003 -> PCNN.CON-002 : caused_by w=0.55
connected.PCNN.GOT-003 -> PCNN.ARC-002 : constrained_by w=0.90
evidence: recap/2026-09-17/build
first_seen: 2026-09-17
last_touched: 2026-09-17
revision: 1
