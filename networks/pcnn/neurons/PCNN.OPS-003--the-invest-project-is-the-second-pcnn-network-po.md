@neuron PCNN.OPS-003
head: The invest project is the second PCNN network, populated by distillation on 2026-09-17
layer: OPS
project: pcnn
status: active
confidence: verified
salience: 0.72
signals: invest, multi project, network population, onboarding, second project, stock screener
description: A network for the invest project exists alongside pcnn and was populated on
  2026-09-17 by running the distillation step over the invest session transcript at
  C--Users-ME--OneDrive-Desktop-invest\1ba99976-dc23-4ebe-ae08-ad19f0ecfeb9.jsonl. The run
  emitted IDENT, ARC, DAT, DEC and CON neurons covering the invest pipeline, its weights
  configuration and its scoring rules, which demonstrates the harvest-then-distil path end to
  end on a project other than pcnn itself.
anchors: pcnn/distill.py, registry.json
connected.PCNN.OPS-003 -> PCNN.ARC-002 : instance_of w=0.70
connected.PCNN.OPS-003 -> PCNN.OPS-004 : supersedes w=1.00
connected.PCNN.OPS-003 -> PCNN.TODO-001 : supersedes w=1.00
evidence: recap/session-dab5f42b-5451-426f-8072-19d89fa320d3
first_seen: 2026-09-17
last_touched: 2026-09-17
revision: 1
