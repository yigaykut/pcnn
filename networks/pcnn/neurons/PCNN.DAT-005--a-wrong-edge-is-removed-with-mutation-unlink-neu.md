@neuron PCNN.DAT-005
head: A wrong edge is removed with @mutation unlink; neurons and weights stay permanent
layer: DAT
project: pcnn
status: superseded
confidence: stated
salience: 0.78
signals: correction, edge-removal, mistake, mutation-grammar, unlink
description: The mutation grammar carries @mutation unlink SRC -> DST : type, which drops one
  edge from a neuron and logs the removal. It refuses when no such edge exists. Every other
  operation in PCNN is additive because a fact that was true stays true, but an edge asserts a
  relationship between two facts and an assertion can simply be wrong.
rationale: The gap surfaced when a supersedes edge was written where refines was meant and there
  was no way to take it back, which would have left the graph permanently asserting that a live
  architecture neuron had been retired.
anchors: pcnn/distill.py, prompts/DISTILL_RECAP.md
connected.PCNN.DAT-005 -> PCNN.CON-002 : constrained_by w=0.85
connected.PCNN.DAT-005 -> PCNN.DEC-001 : refines w=0.80
evidence: recap/2026-09-17/zero-token
first_seen: 2026-09-17
last_touched: 2026-09-18
revision: 1
