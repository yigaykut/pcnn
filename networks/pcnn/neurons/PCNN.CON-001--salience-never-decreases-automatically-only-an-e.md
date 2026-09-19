@neuron PCNN.CON-001
head: Salience never decreases automatically; only an explicit human demote lowers it
layer: CON
project: pcnn
status: active
confidence: verified
salience: 1.00
pin: true
signals: decay, demote, floor, never-lose-weight, salience, weight
description: Every automated path - distillation, consolidation, touch boosts - may raise a
  neuron's salience and may never lower it. Lowering requires the pcnn demote command, which
  refuses without a written reason and refuses to go below the layer floor. There is no recency
  decay anywhere in the engine; last_touched feeds the timeline view only.
rationale: Recency decay is the standard design and it is precisely how old context gets lost: a
  decision taken on day one must not fade because nobody touched it for a month.
alternatives_rejected: exponential recency decay on salience; automatic pruning of low-traffic
  neurons
anchors: pcnn/schema.py, pcnn/weights.py
connected.PCNN.CON-001 -> PCNN.IDENT-001 : caused_by w=0.90
evidence: P2
first_seen: 2026-09-17
last_touched: 2026-09-17
revision: 1
