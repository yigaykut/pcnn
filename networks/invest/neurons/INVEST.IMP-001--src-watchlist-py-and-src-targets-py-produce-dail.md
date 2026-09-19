@neuron INVEST.IMP-001
head: src/watchlist.py and src/targets.py produce daily targets, stops and risk levels for held tickers
layer: IMP
project: invest
status: active
confidence: verified
salience: 0.65
signals: izleme listesi, position tracking, price target, sell signal, stop loss, watchlist
description: src/watchlist.py stores selected tickers with an optional entry price and note, and
  on update recomputes for each one the current price, profit and loss against the entry price,
  a short term and a long term price target with the method that produced it, stop levels, and a
  Turkish risk level. src/targets.py holds the target and stop calculations, and
  src/report_watch.py renders output/watchlist.html. The dashboard carries an add-to-list button
  per row.
anchors: src/report_watch.py, src/targets.py, src/watchlist.py
connected.INVEST.IMP-001 -> INVEST.IDENT-001 : implements w=0.70
evidence: recap/session-1ba99976-dc23-4ebe-ae08-ad19f0ecfeb9
first_seen: 2026-09-17
last_touched: 2026-09-17
revision: 1
