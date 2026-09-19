@neuron PCNN.CON-005
head: The pipeline never harvests its own sessions
layer: CON
project: pcnn
status: active
confidence: verified
salience: 0.98
pin: true
signals: feedback-loop, guard, pcnn-internal, runaway-cost, self-harvest, session-end
description: Two guards stop the distiller from feeding on its own output. First,
  distill.run_model sets PCNN_INTERNAL=1 on the headless claude -p call, and
  hooks/session_end.py exits immediately when that variable is present. Second,
  ingest.is_pipeline_output rejects any delta that changed no file, ran no command and whose
  closing message begins with @mutation, which catches a pipeline session the environment guard
  missed.
rationale: The headless model call runs as an ordinary Claude Code session in the registered
  orchestrator directory, so without a guard the SessionEnd hook harvests it, distils it, and
  that distillation is harvested in turn. The loop spends tokens without limit and writes the
  distiller's own prompt into the network as if it were a fact about the project. Seven such
  deltas accumulated on 2026-09-17 before the guards existed.
alternatives_rejected: unregistering the orchestrator so its sessions are ignored, which would
  also stop PCNN from recording its own development; matching on the session transcript path,
  which breaks as soon as the transcript location changes
anchors: hooks/session_end.py, pcnn/distill.py, pcnn/ingest.py
connected.PCNN.CON-005 -> PCNN.GOT-005 : caused_by w=1.00
connected.PCNN.CON-005 -> PCNN.ARC-002 : constrained_by w=0.95
evidence: recap/2026-09-17/loop
first_seen: 2026-09-17
last_touched: 2026-09-17
revision: 1
