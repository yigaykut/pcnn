@neuron PCNN.IDENT-001
head: PCNN is a retrieval system that keeps project context readable by AI across sessions
layer: IDENT
project: pcnn
status: active
confidence: verified
salience: 0.95
pin: true
signals: context-loss, pcnn, project-context-neural-network, purpose, retrieval
description: PCNN stores every durable fact about a software project as an atomic neuron with a
  fixed schema, typed weighted edges to other neurons, and immutable evidence. The primary
  consumer is a language model resuming work on the project; the human-facing HTML view is a
  rendering of the same data. PCNN spans several projects at once and links equivalent solutions
  across them.
rationale: Context earned inside one Claude Code session dies with that session, so decisions,
  rejected alternatives and platform gotchas get re-derived or silently contradicted in the next
  one.
anchors: README.md, pcnn/schema.py
evidence: P1
first_seen: 2026-09-17
last_touched: 2026-09-17
revision: 1
