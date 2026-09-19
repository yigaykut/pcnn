@neuron INVEST.GOT-002
head: Wikipedia index scraping needs lxml installed, and Nasdaq-100 tables must be located by column name
layer: GOT
project: invest
status: active
confidence: verified
salience: 0.82
signals: lxml, nasdaq-100, read_html, scraping, table parsing, wikipedia
description: pandas.read_html raises an import error until lxml is installed, which is why lxml
  is listed in requirements.txt. The Nasdaq-100 Wikipedia page additionally returns several
  tables whose index shifts, so src/universe.py fetches the page with a Mozilla User-Agent,
  wraps the HTML in io.StringIO and selects the table that has a Ticker or Symbol column rather
  than a fixed position.
rationale: A missing optional parser dependency and a positional table index both fail silently
  as an empty universe, which looks like a scoring bug rather than a fetch bug.
anchors: requirements.txt, src/universe.py
evidence: recap/session-1ba99976-dc23-4ebe-ae08-ad19f0ecfeb9
first_seen: 2026-09-17
last_touched: 2026-09-17
revision: 1
