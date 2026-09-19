@mutation upsert $CON-1
head: The pipeline never harvests its own sessions
layer: CON
project: pcnn
status: active
confidence: verified
salience: 0.98
pin: true
signals: feedback-loop, pcnn-internal, self-harvest, runaway-cost, guard, session-end
description: Two guards stop the distiller from feeding on its own output. First,
  distill.run_model sets PCNN_INTERNAL=1 on the headless claude -p call, and
  hooks/session_end.py exits immediately when that variable is present. Second,
  ingest.is_pipeline_output rejects any delta that changed no file, ran no command and
  whose closing message begins with @mutation, which catches a pipeline session the
  environment guard missed.
rationale: The headless model call runs as an ordinary Claude Code session in the
  registered orchestrator directory, so without a guard the SessionEnd hook harvests it,
  distils it, and that distillation is harvested in turn. The loop spends tokens without
  limit and writes the distiller's own prompt into the network as if it were a fact about
  the project. Seven such deltas accumulated on 2026-09-17 before the guards existed.
alternatives_rejected: unregistering the orchestrator so its sessions are ignored, which
  would also stop PCNN from recording its own development; matching on the session
  transcript path, which breaks as soon as the transcript location changes
anchors: pcnn/distill.py, pcnn/ingest.py, hooks/session_end.py
evidence: recap/2026-09-17/loop
first_seen: 2026-09-17

@mutation upsert $OPS-1
head: pcnn distill takes --limit so a first run on a backlog is not one model call per day
layer: OPS
project: pcnn
status: active
confidence: verified
salience: 0.74
signals: distill, limit, backlog, cost-control, cli
description: pcnn distill processes every pending delta by default, which on a freshly
  harvested project is one model call per calendar day of history. The invest backlog was
  22 deltas on first harvest. --limit N stops after N deltas and reports how many remain;
  the nightly job leaves it unset on purpose.
anchors: pcnn/cli.py
evidence: recap/2026-09-17/loop
first_seen: 2026-09-17

@mutation link $CON-1 -> PCNN.GOT-005 : caused_by w=1.00
@mutation link $CON-1 -> PCNN.ARC-002 : constrained_by w=0.95
@mutation link $OPS-1 -> PCNN.ARC-002 : constrained_by w=0.70
@mutation link PCNN.GOT-005 -> $CON-1 : verified_by w=0.80
