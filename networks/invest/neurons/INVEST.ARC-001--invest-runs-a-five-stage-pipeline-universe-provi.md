@neuron INVEST.ARC-001
head: invest runs a five-stage pipeline: universe -> providers -> factors -> scoring -> report
layer: ARC
project: invest
status: active
confidence: verified
salience: 0.80
signals: architecture, boru hatti, data flow, modules, pipeline, stages
description: The invest pipeline has five stages, each owning one module. src/universe.py builds
  the ticker list from named sources (sp500, nasdaq100, smallcap, midcap, wsb). src/providers/
  fetches raw data (yahoo.py for price history and fundamentals, reddit_wsb.py for mention
  counts, cache.py for an on-disk namespaced cache). src/factors.py computes one raw value per
  parameter per ticker. src/scoring.py normalises, weights, applies penalties and filters, and
  produces the ranking. src/report.py renders output/dashboard.html plus output/ranking.csv,
  output/llm_export.json and output/diagnostics.json. run.py is the CLI entry point that drives
  all five stages.
anchors: run.py, src/factors.py, src/providers/, src/report.py, src/scoring.py, src/universe.py
connected.INVEST.ARC-001 -> INVEST.DEC-001 : constrained_by w=0.70
connected.INVEST.ARC-001 -> INVEST.GOT-001 : constrained_by w=0.85
connected.INVEST.ARC-001 -> INVEST.IDENT-001 : implements w=0.90
evidence: recap/session-1ba99976-dc23-4ebe-ae08-ad19f0ecfeb9
first_seen: 2026-09-17
last_touched: 2026-09-17
revision: 1
