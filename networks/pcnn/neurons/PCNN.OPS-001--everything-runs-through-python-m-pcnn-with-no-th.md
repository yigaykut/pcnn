@neuron PCNN.OPS-001
head: Everything runs through python -m pcnn with no third-party dependencies
layer: OPS
project: pcnn
status: active
confidence: verified
salience: 0.70
signals: cli, commands, entry-point, install, stdlib
description: The engine is Python 3 standard library only. Commands are init, status, validate,
  rebuild, query, context, harvest, distill, apply, audit, consolidate, render, demote and
  suggest. PCNN_HOME overrides the orchestrator root when the package is run from elsewhere,
  which is what the session hooks rely on.
anchors: pcnn/cli.py
connected.PCNN.OPS-001 -> PCNN.IMP-001 : depends_on w=0.45
connected.PCNN.OPS-001 -> PCNN.IMP-002 : depends_on w=0.45
evidence: P10
first_seen: 2026-09-17
last_touched: 2026-09-17
revision: 1
