@neuron PCNN.GOT-008
head: Re-distilling the same delta mints duplicate neurons because placeholder ids cannot match existing ones
layer: GOT
project: pcnn
status: active
confidence: inferred
salience: 0.84
signals: deduplication, duplicate neurons, idempotence, placeholder id, rerun, upsert
description: Distilling the same raw delta twice produced two near-identical neuron pairs in the
  pcnn network - PCNN.GOT-005 and PCNN.GOT-006 both stating that a distillation run is itself
  harvested, and PCNN.OPS-003 and PCNN.OPS-004 carrying an identical head about the invest
  project. The cause is that an upsert naming a $LAYER-n placeholder always allocates a fresh
  id, so the engine has no key by which to recognise that the same fact already exists;
  re-running distillation over an unchanged day therefore grows the graph instead of touching
  it. Resolution is a supersede edge from the fuller neuron to the thinner one, never deletion.
rationale: The placeholder mechanism that keeps the model from inventing ids also strips it of
  any way to address an existing neuron it is about to restate, so idempotence has to come from
  head or description matching at upsert time or from a consolidation pass, not from the model's
  own output.
alternatives_rejected: deleting the duplicate neuron; letting the model guess a concrete id
  instead of a placeholder, which PCNN.DEC-001 forbids
anchors: pcnn/distill.py, pcnn/schema.py, pcnn/store.py
connected.PCNN.GOT-008 -> PCNN.DEC-001 : caused_by w=0.80
connected.PCNN.GOT-008 -> PCNN.DAT-001 : constrained_by w=0.70
connected.PCNN.GOT-008 -> PCNN.GOT-006 : refines w=0.60
connected.PCNN.GOT-008 -> PCNN.GOT-007 : supersedes w=1.00
evidence: recap/session-7be63a0e-2d25-4765-b5a2-345a527e3db8
first_seen: 2026-09-17
last_touched: 2026-09-17
revision: 1
