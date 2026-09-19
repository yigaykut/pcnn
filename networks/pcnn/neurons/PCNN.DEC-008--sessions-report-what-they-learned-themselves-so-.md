@neuron PCNN.DEC-008
head: Sessions report what they learned themselves, so the normal path makes no model call
layer: DEC
project: pcnn
status: active
confidence: verified
salience: 0.95
pin: true
signals: contract, cost, pcnn-block, self-report, session-end, zero-token
description: The SessionStart hook injects a contract asking the session to end its closing
  message with a fenced block in the mutation grammar, between @pcnn and @end. The SessionEnd
  hook extracts that block with pcnn.reap, validates it and writes the neurons. No model runs at
  any point in the update path, and the nightly consolidation, audit and render are plain
  Python. Distillation still exists for backfilling old transcripts and for a session that ended
  without reporting, but it is off by default in both the nightly task and the session hook,
  gated behind PCNN_AUTODISTILL.
rationale: A session that has just spent an hour in a codebase already knows what it decided and
  is already writing a closing message, so the marginal cost of ten more lines is nothing.
  Paying a second model to read the transcript and rediscover those decisions buys the same
  knowledge twice, and the second copy is worse because it is inferred from evidence rather than
  remembered.
alternatives_rejected: a distillation call per project-day, which cost about 7000 input tokens
  each even after the prompt was cut by 68 percent; a nightly batch call, which has the same
  problem at a coarser grain
anchors: hooks/session_end.py, hooks/session_start.py, pcnn/reap.py
connected.PCNN.DEC-008 -> PCNN.IDENT-001 : caused_by w=0.85
connected.PCNN.DEC-008 -> PCNN.CON-006 : implements w=0.95
connected.PCNN.DEC-008 -> PCNN.ARC-002 : refines w=0.85
evidence: recap/2026-09-17/zero-token
first_seen: 2026-09-17
last_touched: 2026-09-17
revision: 1
