@neuron INVEST.GOT-003
head: Dashboard HTML is verified by a Node smoke test with DOM stubs because browser screenshots freeze the renderer
layer: GOT
project: invest
status: active
confidence: verified
salience: 0.84
signals: dom stub, node, renderer frozen, screenshot timeout, smoke test, svg density
description: Visual verification of output/dashboard.html through the Chrome tooling repeatedly
  failed with script-injection and Page.captureScreenshot timeouts after the page was served on
  127.0.0.1. Verification instead extracts the inline script block, runs it under Node against a
  minimal document/localStorage stub, and asserts on the rendered row counts, categories and
  assistant answers; the payload is separately checked by parsing the const DATA literal out of
  the HTML.
rationale: The dashboard embeds dense inline SVG sparklines for dozens of tickers, which stalls
  the renderer long enough that every screenshot and scroll action times out, so browser-driven
  checking costs minutes and yields nothing.
anchors: output/dashboard.html, src/report.py
connected.INVEST.GOT-003 -> INVEST.ARC-001 : relates_to w=0.40
evidence: recap/session-1ba99976-dc23-4ebe-ae08-ad19f0ecfeb9
first_seen: 2026-09-17
last_touched: 2026-09-17
revision: 1
