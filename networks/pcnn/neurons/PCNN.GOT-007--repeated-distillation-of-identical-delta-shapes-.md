@neuron PCNN.GOT-007
head: Repeated distillation of identical delta shapes mints duplicate neurons because upsert allocates a fresh id
layer: GOT
project: pcnn
status: superseded
confidence: inferred
salience: 0.82
signals: dedup, duplicate, id allocation, near-identical neuron, placeholder, upsert
description: A $LAYER-n upsert always allocates a new id, so a delta shape that recurs across
  runs yields a fresh neuron stating the same fact each time rather than converging on one. The
  pcnn network on 2026-09-17 carries two such pairs: PCNN.GOT-005 and PCNN.GOT-006 both state
  that a distillation run is itself a harvested session producing a self-referential delta, and
  PCNN.OPS-003 and PCNN.OPS-004 both state that the invest project is the second PCNN network
  populated by distillation on 2026-09-17. Duplicates split activation between two entries and
  inflate MAP.md; resolution is a supersede edge from one to the other, never a deletion.
rationale: Distillation has no way to recognise that a proposed neuron restates an existing one,
  so the instruction to touch rather than re-record is the only dedup mechanism, and it fails
  exactly when a delta recurs in near-identical form.
alternatives_rejected: deleting the redundant neuron; rewriting one of the pair to absorb the
  other
anchors: pcnn/distill.py, pcnn/store.py
connected.PCNN.GOT-007 -> PCNN.DEC-001 : caused_by w=0.90
connected.PCNN.GOT-007 -> PCNN.CON-002 : constrained_by w=0.70
connected.PCNN.GOT-007 -> PCNN.GOT-006 : refines w=0.70
evidence: recap/session-243ebd4e-5074-4a80-8165-4e25b55b3ee0
first_seen: 2026-09-17
last_touched: 2026-09-17
revision: 1
