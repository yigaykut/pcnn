@neuron PCNN.ARC-001
head: Three read tiers - MAP.md to navigate, neurons to read, evidence to audit
layer: ARC
project: pcnn
status: active
confidence: verified
salience: 0.90
pin: true
signals: l0, l1, l2, map, navigation, read-tiers, token-budget
description: L0 is MAP.md, one line per neuron, loaded every session. L1 is
  neurons/<id>--<slug>.md, the canonical fact in full, opened on demand. L2 is the evidence and
  recap material, read only when auditing. The tiers exist so token cost falls without any
  knowledge being compressed away.
anchors: pcnn/store.py
connected.PCNN.ARC-001 -> PCNN.IDENT-001 : implements w=0.80
evidence: P4
first_seen: 2026-09-17
last_touched: 2026-09-17
revision: 1
