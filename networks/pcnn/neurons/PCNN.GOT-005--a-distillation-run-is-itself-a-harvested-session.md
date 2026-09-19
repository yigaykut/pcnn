@neuron PCNN.GOT-005
head: A distillation run is itself a harvested session, producing a self-referential delta whose recap is a mutation block
layer: GOT
project: pcnn
status: superseded
confidence: inferred
salience: 0.88
signals: distillation delta, empty delta, feedback loop, recap, self referential, session end hook
description: The distillation call runs as a Claude Code session whose working directory is the
  registered orchestrator directory, so the SessionEnd hook harvests the distillation run as an
  ordinary session. The resulting delta for 2026-09-17 carries zero file changes, zero commands
  and zero failures, one user instruction that is the distillation task prompt itself, and a
  recap that is the mutation block emitted for a different project. Such a delta describes the
  distiller, not the project, and its recap must not be read as evidence about the project being
  distilled.
rationale: Distilling a distillation delta would copy another project's neurons into the pcnn
  network and record the prompt text as if it were project work, so the shape has to be
  recognised before the content is trusted.
alternatives_rejected: treating the recap field as a project recap regardless of its content
anchors: hooks/session_end.py, pcnn/distill.py, pcnn/ingest.py
connected.PCNN.GOT-005 -> PCNN.DEC-001 : caused_by w=0.70
connected.PCNN.GOT-005 -> PCNN.ARC-002 : constrained_by w=0.80
connected.PCNN.GOT-005 -> PCNN.CON-005 : verified_by w=0.80
evidence: recap/session-dab5f42b-5451-426f-8072-19d89fa320d3
first_seen: 2026-09-17
last_touched: 2026-09-17
revision: 1
