@neuron PCNN.IMP-001
head: Retrieval is spreading activation over the graph, returning the path that matched
layer: IMP
project: pcnn
status: active
confidence: verified
salience: 0.72
signals: hops, query, ranking, retrieval, seeds, spreading-activation
description: Query terms seed neurons through signals, head, anchors and id matches with
  activation equal to their salience, then activation propagates along edges for up to three
  hops at 0.6 decay per hop and 0.8 for traversing an edge backwards. Results above the cutoff
  are ranked and returned with the activation path, so a neuron no query term touched can still
  surface because a decision two hops away depends on it.
anchors: pcnn/query.py
connected.PCNN.IMP-001 -> PCNN.CON-001 : constrained_by w=0.70
connected.PCNN.IMP-001 -> PCNN.ARC-001 : depends_on w=0.75
evidence: P8
first_seen: 2026-09-17
last_touched: 2026-09-17
revision: 1
