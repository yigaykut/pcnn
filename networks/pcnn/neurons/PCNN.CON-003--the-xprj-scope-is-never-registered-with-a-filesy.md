@neuron PCNN.CON-003
head: The xprj scope is never registered with a filesystem path
layer: CON
project: pcnn
status: active
confidence: verified
salience: 0.95
signals: cross-project, registry, resolve-path, scope, xprj
description: networks/xprj holds cross-project neurons and has no source directory. Giving it a
  registry path made Registry.resolve_path attribute any unregistered directory under that path
  to the cross-project network, so xprj is kept out of registry.json entirely and added to --all
  targets explicitly by pcnn.cli._targets.
rationale: resolve_path does longest-prefix matching, so a broad registered path silently
  captures every project below it that is not itself registered.
alternatives_rejected: registering xprj against the Desktop directory
anchors: pcnn/cli.py, registry.json
connected.PCNN.CON-003 -> PCNN.DAT-001 : constrained_by w=0.70
evidence: recap/2026-09-17/build
first_seen: 2026-09-17
last_touched: 2026-09-17
revision: 1
