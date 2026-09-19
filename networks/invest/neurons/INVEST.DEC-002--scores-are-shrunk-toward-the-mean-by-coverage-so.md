@neuron INVEST.DEC-002
head: Scores are shrunk toward the mean by coverage so thin-data tickers cannot top the ranking
layer: DEC
project: invest
status: active
confidence: verified
salience: 0.90
signals: coverage, low confidence, missing data, ranking bias, regional banks, shrinkage
description: src/scoring.py multiplies each ticker's weighted score by a coverage-based
  shrinkage term and drops any ticker whose coverage falls below a configured floor entirely, in
  addition to flagging low_confidence below min_coverage_for_confidence (0.60). A market
  capitalisation ceiling filter was added at the same time.
rationale: Without shrinkage, tickers with almost no data (small regional banks such as RZC,
  AMTB, AMAL, OBK) scored highest because the weights of their missing factors were renormalised
  away, turning absent data into an advantage and concentrating the top of the ranking in one
  sector.
alternatives_rejected: Relying only on the low_confidence flag and leaving thin-data tickers in
  the ranking for the reader to discount.
anchors: config/weights.yaml, src/scoring.py, tests/test_scoring.py
connected.INVEST.DEC-002 -> INVEST.GLO-001 : depends_on w=0.80
connected.INVEST.DEC-002 -> INVEST.DEC-003 : refines w=0.70
evidence: recap/session-1ba99976-dc23-4ebe-ae08-ad19f0ecfeb9
first_seen: 2026-09-17
last_touched: 2026-09-17
revision: 1
