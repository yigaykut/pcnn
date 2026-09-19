@neuron PCNN.OPS-004
head: The invest project is the second PCNN network, populated by distillation on 2026-09-17
layer: OPS
project: pcnn
status: superseded
confidence: stated
salience: 0.72
signals: invest, multi project, network population, onboarding, registry, second project
description: A network for the invest project exists alongside the pcnn network and was
  populated on 2026-09-17 by running the distillation step over the invest session transcript
  under C--Users-ME--OneDrive-Desktop-invest. That run emitted IDENT, ARC, DAT, DEC and CON
  neurons covering the invest pipeline, its weights configuration and its scoring rules, which
  exercises the harvest-then-distil path end to end on a project other than pcnn itself.
anchors: pcnn/distill.py, registry.json
connected.PCNN.OPS-004 -> PCNN.ARC-002 : instance_of w=0.70
connected.PCNN.OPS-004 -> PCNN.TODO-001 : supersedes w=1.00
evidence: recap/session-7a9e020c-46ee-4afe-9824-af8f301a81a0
first_seen: 2026-09-17
last_touched: 2026-09-17
revision: 1
