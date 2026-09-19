@neuron INVEST.CON-001
head: The in-dashboard assistant must stay free and offline, answering only from data embedded in the page
layer: CON
project: invest
status: active
confidence: verified
salience: 0.96
signals: assistant, chat, free, intent engine, no api, offline, ucretsiz
description: src/assistant_ui.py emits a chat panel into section IV of output/dashboard.html
  that resolves questions about tickers and parameters with a client-side intent engine over the
  computed data already serialised into the page. No paid language-model service may be called,
  and no network request is made at answer time.
rationale: The user requested the chat feature with the explicit condition that it be free, so
  any design that calls a hosted model API violates the requirement regardless of quality gain.
anchors: src/assistant_ui.py, src/report.py
connected.INVEST.CON-001 -> INVEST.IDENT-001 : constrained_by w=0.60
evidence: recap/session-1ba99976-dc23-4ebe-ae08-ad19f0ecfeb9
first_seen: 2026-09-17
last_touched: 2026-09-17
revision: 1
