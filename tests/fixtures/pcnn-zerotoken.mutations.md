@mutation upsert $DEC-1
head: Sessions report what they learned themselves, so the normal path makes no model call
layer: DEC
project: pcnn
status: active
confidence: verified
salience: 0.95
pin: true
signals: zero-token, self-report, pcnn-block, session-end, cost, contract
description: The SessionStart hook injects a contract asking the session to end its closing
  message with a fenced block in the mutation grammar, between @pcnn and @end. The
  SessionEnd hook extracts that block with pcnn.reap, validates it and writes the neurons.
  No model runs at any point in the update path, and the nightly consolidation, audit and
  render are plain Python. Distillation still exists for backfilling old transcripts and
  for a session that ended without reporting, but it is off by default in both the nightly
  task and the session hook, gated behind PCNN_AUTODISTILL.
rationale: A session that has just spent an hour in a codebase already knows what it
  decided and is already writing a closing message, so the marginal cost of ten more lines
  is nothing. Paying a second model to read the transcript and rediscover those decisions
  buys the same knowledge twice, and the second copy is worse because it is inferred from
  evidence rather than remembered.
alternatives_rejected: a distillation call per project-day, which cost about 7000 input
  tokens each even after the prompt was cut by 68 percent; a nightly batch call, which has
  the same problem at a coarser grain
anchors: pcnn/reap.py, hooks/session_end.py, hooks/session_start.py
evidence: recap/2026-09-17/zero-token
first_seen: 2026-09-17

@mutation upsert $DAT-1
head: A self-report is fenced between @pcnn and @end so it cannot be confused with distiller output
layer: DAT
project: pcnn
status: active
confidence: verified
salience: 0.80
signals: pcnn-fence, block-delimiter, grammar, self-report, disambiguation
description: A session reports inside @pcnn and @end. A distillation run emits a bare
  mutation block with no fence. ingest.is_pipeline_output treats a fenced block as a real
  session reporting and a bare one as the pipeline talking to itself, which keeps the
  self-report path and the loop guard from colliding. Only the last block in a message is
  read, so a session that revises its report supersedes its own earlier draft.
anchors: pcnn/reap.py, pcnn/ingest.py
evidence: recap/2026-09-17/zero-token
first_seen: 2026-09-17

@mutation link $DEC-1 -> PCNN.ARC-002 : supersedes w=0.60
@mutation link $DEC-1 -> PCNN.CON-006 : implements w=0.95
@mutation link $DEC-1 -> PCNN.IDENT-001 : caused_by w=0.85
@mutation link $DAT-1 -> $DEC-1 : implements w=0.90
@mutation link $DAT-1 -> PCNN.CON-005 : constrained_by w=0.85
@mutation touch PCNN.DEC-006
