@neuron INVEST.DAT-001
head: config/weights.yaml is the single source of truth for factors, weights, penalties and filters
layer: DAT
project: invest
status: active
confidence: verified
salience: 0.80
signals: config, factor definition, parameters, schema, weights, yaml
description: config/weights.yaml holds a factors list where each entry carries id, weight,
  category (technical, emergence, potential, quality, analyst, valuation, momentum, risk,
  sentiment, growth), norm (the normalisation method), and name_tr (the Turkish display name).
  The same file holds a penalties list of id/points/name_tr entries, a filters block, and
  scoring keys including min_coverage_for_confidence (0.60). Both README.md and
  docs/PARAMETRELER.md are generated and cross-checked against this file, so adding a factor
  without updating the config breaks the docs consistency check.
anchors: README.md, config/weights.yaml, docs/PARAMETRELER.md
connected.INVEST.DAT-001 -> INVEST.ARC-001 : refines w=0.80
evidence: recap/session-1ba99976-dc23-4ebe-ae08-ad19f0ecfeb9
first_seen: 2026-09-17
last_touched: 2026-09-17
revision: 1
