@neuron INVEST.GLO-001
head: "kapsama" is the share of total factor weight a ticker actually has data for
layer: GLO
project: invest
status: active
confidence: verified
salience: 0.60
signals: coverage, etki puani, glossary, kapsama, low confidence, terminology
description: In invest, "kapsama" (coverage) names the fraction of the total configured factor
  weight for which a ticker has usable data, exported as the coverage field and shown as a
  percentage. A ticker below min_coverage_for_confidence is marked low_confidence, rendered in
  Turkish as "dusuk guven". The weighted sum itself is called "etki puani" (impact score) in
  Turkish and total_score in the JSON export.
anchors: config/weights.yaml, output/llm_export.json, src/scoring.py
connected.INVEST.GLO-001 -> INVEST.ARC-001 : relates_to w=0.40
evidence: recap/session-1ba99976-dc23-4ebe-ae08-ad19f0ecfeb9
first_seen: 2026-09-17
last_touched: 2026-09-17
revision: 1
