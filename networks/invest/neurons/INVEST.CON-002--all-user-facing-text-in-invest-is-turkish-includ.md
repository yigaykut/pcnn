@neuron INVEST.CON-002
head: All user-facing text in invest is Turkish, including parameter names, docs and dashboard labels
layer: CON
project: invest
status: active
confidence: verified
salience: 0.95
signals: documentation language, labels, localisation, name_tr, turkce, turkish
description: Every parameter in config/weights.yaml carries a name_tr field,
  docs/PARAMETRELER.md explains all parameters in Turkish, and README.md plus the dashboard and
  watchlist HTML render their labels, risk levels and explanations in Turkish. Output files are
  written and read with explicit UTF-8 encoding, and generated HTML must carry a charset meta
  tag.
rationale: The user works in Turkish and asked for a detailed Turkish explanation file covering
  every parameter, so English-only additions would be unreadable to the sole intended reader.
anchors: config/weights.yaml, docs/PARAMETRELER.md, src/report.py
connected.INVEST.CON-002 -> INVEST.DAT-001 : constrained_by w=0.60
evidence: recap/session-1ba99976-dc23-4ebe-ae08-ad19f0ecfeb9
first_seen: 2026-09-17
last_touched: 2026-09-17
revision: 1
