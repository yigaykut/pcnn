@neuron PCNN.DEC-003
head: Nightly consolidation runs as a Windows scheduled task, not a cloud routine
layer: DEC
project: pcnn
status: active
confidence: verified
salience: 0.86
signals: consolidation, cron, local-execution, nightly, scheduled-task
description: scripts/nightly.py runs pcnn distill, consolidate and audit across every network,
  registered by scripts/install-nightly.ps1 as a daily Windows scheduled task at 23:30. The
  -NoDistill switch skips the model call so the free half can run on its own.
rationale: A scheduled cloud agent executes remotely and cannot reach the networks, the session
  transcripts or the rendered HTML, all of which are on this machine.
alternatives_rejected: a scheduled cloud agent via the schedule skill; a /loop session, which
  only lasts as long as the session does
anchors: scripts/install-nightly.ps1, scripts/nightly.py
connected.PCNN.DEC-003 -> PCNN.ARC-002 : implements w=0.75
evidence: recap/2026-09-17/build
first_seen: 2026-09-17
last_touched: 2026-09-17
revision: 1
