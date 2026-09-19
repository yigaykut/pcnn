@neuron PCNN.GOT-006
head: A distillation run is itself harvested, yielding a self-referential delta whose recap is a mutation block
layer: GOT
project: pcnn
status: active
confidence: verified
salience: 0.92
signals: distillation delta, empty delta, feedback loop, recap, self referential, session end hook
description: The distillation step runs as a Claude Code session whose working directory is the
  registered orchestrator directory, so the SessionEnd hook harvests the distillation run itself
  as an ordinary session. The delta produced this way carries zero file changes, zero commands,
  zero reads and zero failures, exactly one user instruction which is the distillation task
  prompt verbatim, and a recap field that is the mutation block emitted for whichever project
  was being distilled. Such a delta describes the distiller, not the project it names, and its
  instruction text must never be recorded as project work.
rationale: Distilling a distillation delta at face value copies another project's neurons into
  the pcnn network and stores the prompt template as if it were a session decision, so the shape
  - one instruction, empty change lists, a recap starting with @mutation - has to be recognised
  before the content is trusted.
alternatives_rejected: reading the recap field as a project recap regardless of its content;
  treating the distillation prompt as a user instruction that sets project rules
anchors: hooks/session_end.py, pcnn/distill.py, pcnn/ingest.py
connected.PCNN.GOT-006 -> PCNN.DEC-001 : caused_by w=0.70
connected.PCNN.GOT-006 -> PCNN.ARC-002 : constrained_by w=0.80
connected.PCNN.GOT-006 -> PCNN.GOT-003 : refines w=0.60
connected.PCNN.GOT-006 -> PCNN.GOT-005 : supersedes w=1.00
evidence: recap/session-7a9e020c-46ee-4afe-9824-af8f301a81a0
first_seen: 2026-09-17
last_touched: 2026-09-17
revision: 1
