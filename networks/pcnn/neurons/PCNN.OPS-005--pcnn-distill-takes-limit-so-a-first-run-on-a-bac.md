@neuron PCNN.OPS-005
head: pcnn distill takes --limit so a first run on a backlog is not one model call per day
layer: OPS
project: pcnn
status: active
confidence: verified
salience: 0.74
signals: backlog, cli, cost-control, distill, limit
description: pcnn distill processes every pending delta by default, which on a freshly harvested
  project is one model call per calendar day of history. The invest backlog was 22 deltas on
  first harvest. --limit N stops after N deltas and reports how many remain; the nightly job
  leaves it unset on purpose.
anchors: pcnn/cli.py
connected.PCNN.OPS-005 -> PCNN.ARC-002 : constrained_by w=0.70
evidence: recap/2026-09-17/loop
first_seen: 2026-09-17
last_touched: 2026-09-17
revision: 1
