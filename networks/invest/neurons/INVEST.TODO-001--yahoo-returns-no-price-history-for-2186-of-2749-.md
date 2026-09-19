@neuron INVEST.TODO-001
head: Yahoo returns no price history for 2186 of 2749 emerging-universe tickers and the cause is unresolved
layer: TODO
project: invest
status: active
confidence: verified
salience: 0.78
signals: 2186, coverage gap, missing data, universe shrink, unresolved, yahoo history
description: A full smallcap and midcap scan of 2781 tickers scored only 429 of them.
  Investigation established that 2186 of 2749 tickers have no price history at all, leaving
  effective coverage near 563 stocks, and that the one-million-dollar daily liquidity filter is
  not the cause. Whether the missing tickers are delisted, carry symbols Yahoo spells
  differently, or are lost to fetch throttling remains undetermined as of 2026-08-11. A related
  fix is needed in diagnostics, which stored only the first 50 dropped examples and therefore
  concealed the scale of the gap.
anchors: output/diagnostics.json, src/providers/yahoo.py, src/universe.py
connected.INVEST.TODO-001 -> INVEST.IDENT-001 : blocks w=0.70
connected.INVEST.TODO-001 -> INVEST.DEC-001 : caused_by w=0.80
evidence: recap/session-1ba99976-dc23-4ebe-ae08-ad19f0ecfeb9
first_seen: 2026-09-17
last_touched: 2026-09-17
revision: 1
