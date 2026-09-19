@neuron PCNN.CON-006
head: The pipeline's own spending is capped and measured, never assumed
layer: CON
project: pcnn
status: active
confidence: verified
salience: 0.96
pin: true
signals: budget, cost-control, daily-limit, haiku, ledger, token-cost
description: Every model call is charged against a daily ceiling of 30 calls across all
  projects, held in .budget.json and raised with PCNN_DAILY_CALLS. When the ceiling is reached
  the pipeline stops and says so, and the undistilled deltas wait on disk. Harvest costs nothing
  because no model runs in it, a day that changed no file and hit no failure is skipped without
  a call, and pcnn cost prints what has actually been charged.
rationale: PCNN exists to spend fewer tokens than re-deriving context does, so a system that
  could spend without limit defeats its own purpose. The self-distillation loop of 2026-09-17
  proved that an unbounded pipeline exhausts a usage limit in minutes.
alternatives_rejected: trusting the guards alone with no ceiling behind them
anchors: pcnn/budget.py, pcnn/cli.py
connected.PCNN.CON-006 -> PCNN.IDENT-001 : caused_by w=0.95
connected.PCNN.CON-006 -> PCNN.CON-005 : refines w=0.80
evidence: recap/2026-09-17/cost
first_seen: 2026-09-17
last_touched: 2026-09-17
revision: 1
