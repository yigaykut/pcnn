@neuron PCNN.DAT-002
head: A self-report is fenced between @pcnn and @end so it cannot be confused with distiller output
layer: DAT
project: pcnn
status: active
confidence: verified
salience: 0.80
signals: block-delimiter, disambiguation, grammar, pcnn-fence, self-report
description: A session reports inside @pcnn and @end. A distillation run emits a bare mutation
  block with no fence. ingest.is_pipeline_output treats a fenced block as a real session
  reporting and a bare one as the pipeline talking to itself, which keeps the self-report path
  and the loop guard from colliding. Only the last block in a message is read, so a session that
  revises its report supersedes its own earlier draft.
anchors: pcnn/ingest.py, pcnn/reap.py
connected.PCNN.DAT-002 -> PCNN.CON-005 : constrained_by w=0.85
connected.PCNN.DAT-002 -> PCNN.DEC-008 : implements w=0.90
evidence: recap/2026-09-17/zero-token
first_seen: 2026-09-17
last_touched: 2026-09-17
revision: 1
