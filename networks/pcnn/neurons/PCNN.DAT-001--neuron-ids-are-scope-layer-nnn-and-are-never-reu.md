@neuron PCNN.DAT-001
head: Neuron ids are SCOPE.LAYER-NNN and are never reused, even after a merge
layer: DAT
project: pcnn
status: active
confidence: verified
salience: 0.75
signals: changelog, identifier, neuron-id, next-id, scope
description: A neuron id is the uppercased project slug, a dot, the three or four letter layer
  code, a hyphen and a zero-padded number, for example PCNN.DEC-002. Allocation scans both the
  live neurons and the changelog so an id belonging to a merged or superseded neuron is never
  handed out again.
anchors: pcnn/schema.py, pcnn/store.py
connected.PCNN.DAT-001 -> PCNN.CON-002 : constrained_by w=0.80
evidence: P9
first_seen: 2026-09-17
last_touched: 2026-09-17
revision: 1
