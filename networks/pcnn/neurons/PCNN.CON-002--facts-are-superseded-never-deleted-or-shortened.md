@neuron PCNN.CON-002
head: Facts are superseded, never deleted or shortened
layer: CON
project: pcnn
status: active
confidence: verified
salience: 1.00
pin: true
signals: deletion, immutability, retired, shrink-guard, supersede
description: A fact that changes gets status superseded plus a supersedes edge from its
  replacement, and stays on disk and on the canvas drawn hollow. A rewrite that drops more than
  40 percent of an existing description, or drops an existing rationale, is rejected into
  quarantine rather than applied. INVARIANTS.md carries a RETIRED section so a later session
  cannot rediscover and re-adopt an abandoned approach.
rationale: Summarisation is the failure mode PCNN exists to prevent, so the storage layer has to
  make information loss structurally impossible rather than merely discouraged.
alternatives_rejected: rewriting neurons in place; deleting obsolete neurons
anchors: pcnn/distill.py, pcnn/store.py
connected.PCNN.CON-002 -> PCNN.IDENT-001 : caused_by w=0.90
evidence: P2, P3
first_seen: 2026-09-17
last_touched: 2026-09-17
revision: 1
