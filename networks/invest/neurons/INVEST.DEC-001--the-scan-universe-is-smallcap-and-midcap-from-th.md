@neuron INVEST.DEC-001
head: The scan universe is smallcap and midcap from the Nasdaq screener API, not S&P 500 or Nasdaq-100
layer: DEC
project: invest
status: active
confidence: verified
salience: 0.90
signals: evren, index constituents, nasdaq screener, small cap, ticker list, universe
description: src/universe.py builds the default scan universe from the Nasdaq screener endpoint
  https://api.nasdaq.com/api/screener/stocks?tableonly=true&limit=10000&offset=0&exchange=<EX>
  across NASDAQ, NYSE and AMEX, bucketed by market cap into smallcap and midcap sources, giving
  roughly 7000 tickers before filtering. The canonical scan is --universe smallcap,midcap,wsb.
rationale: Index membership selects for companies that already completed their growth; scanning
  the S&P 500 returned only high-priced, topped-out names, which is the opposite of the stated
  goal of finding future-promising stocks.
alternatives_rejected: S&P 500 and Nasdaq-100 constituent lists scraped from Wikipedia, which
  remain available as the sp500 and nasdaq100 sources but are no longer the default.
anchors: config/weights.yaml, src/universe.py
connected.INVEST.DEC-001 -> INVEST.GOT-002 : constrained_by w=0.60
connected.INVEST.DEC-001 -> INVEST.IDENT-001 : implements w=0.85
evidence: recap/session-1ba99976-dc23-4ebe-ae08-ad19f0ecfeb9
first_seen: 2026-09-17
last_touched: 2026-09-17
revision: 1
