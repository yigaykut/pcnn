@neuron INVEST.DEC-003
head: Factors whose data coverage is too thin are auto-disabled and the remaining weights renormalised
layer: DEC
project: invest
status: active
confidence: verified
salience: 0.87
signals: auto disable, diagnostics, sparse factor, weight renormalisation, wsb mentions
description: src/scoring.py detects factors available for too few tickers in a run, removes them
  from the calculation, renormalises the surviving weights so they still sum to the configured
  total, and reports the removals in diagnostics under auto_disabled, which the dashboard
  displays.
rationale: The user required that an over-restrictive parameter such as presence on the Reddit
  wallstreetbets chart be sacrificeable rather than silently eliminating most candidates.
alternatives_rejected: Hard-filtering on restrictive parameters, and scoring missing factors as
  zero, both of which penalise tickers for data absence rather than for weakness.
anchors: src/scoring.py, tests/test_scoring.py
connected.INVEST.DEC-003 -> INVEST.DAT-001 : depends_on w=0.70
evidence: recap/session-1ba99976-dc23-4ebe-ae08-ad19f0ecfeb9
first_seen: 2026-09-17
last_touched: 2026-09-17
revision: 1
