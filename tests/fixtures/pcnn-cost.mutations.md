@mutation upsert $CON-1
head: The pipeline's own spending is capped and measured, never assumed
layer: CON
project: pcnn
status: active
confidence: verified
salience: 0.96
pin: true
signals: budget, token-cost, daily-limit, haiku, cost-control, ledger
description: Every model call is charged against a daily ceiling of 30 calls across all
  projects, held in .budget.json and raised with PCNN_DAILY_CALLS. When the ceiling is
  reached the pipeline stops and says so, and the undistilled deltas wait on disk. Harvest
  costs nothing because no model runs in it, a day that changed no file and hit no failure
  is skipped without a call, and pcnn cost prints what has actually been charged.
rationale: PCNN exists to spend fewer tokens than re-deriving context does, so a system
  that could spend without limit defeats its own purpose. The self-distillation loop of
  2026-09-17 proved that an unbounded pipeline exhausts a usage limit in minutes.
alternatives_rejected: trusting the guards alone with no ceiling behind them
anchors: pcnn/budget.py, pcnn/cli.py
evidence: recap/2026-09-17/cost
first_seen: 2026-09-17

@mutation upsert $DEC-1
head: Distillation runs on haiku and is fed a summarised delta, not the raw one
layer: DEC
project: pcnn
status: active
confidence: verified
salience: 0.90
signals: haiku, model-choice, prompt-size, slim-delta, commands, cost
description: distill.slim_delta builds a prompt-sized view of a delta: shell commands
  become bucket counts plus the twenty most repeated, truncated to 120 characters;
  instructions and failures are capped; files read are dropped entirely. The invariants
  arrive as one line per neuron instead of in full, so prompt cost stays flat as a network
  grows. Measured on one real day of the invest project, the prompt fell from 25,363 to
  7,322 input tokens, and the model is haiku rather than a frontier model.
rationale: Verbatim shell commands were 67 percent of the payload and the least useful
  signal in it, because what a session decided lives in its closing recap, its file changes
  and its failures. Distillation is structured extraction against a closed grammar with a
  validator behind it, which a frontier model does no better and charges roughly ten times
  as much for.
alternatives_rejected: sending the raw delta; trimming the delta on disk, which would
  destroy the evidence the neuron is audited against
anchors: pcnn/distill.py
evidence: recap/2026-09-17/cost
first_seen: 2026-09-17

@mutation upsert $DEC-2
head: Running pcnn with no arguments prints the dashboard and costs nothing
layer: DEC
project: pcnn
status: active
confidence: verified
salience: 0.86
signals: cli, dashboard, no-args, ergonomics, one-command
description: python -m pcnn with no subcommand reports every project's fact count, how many
  days are waiting, whether anything needs a look, how many model calls today has spent
  against the ceiling, and the path to the rendered view. It is read-only and makes no
  model call. Every other command remains available but none is needed day to day, because
  the hooks and the nightly task do the work.
rationale: A context system that requires a remembered sequence of commands is a system
  that stops being used, and the whole point is that the human does not maintain it.
alternatives_rejected: requiring pcnn status, pcnn audit and pcnn render to be run
  separately to learn the same things
anchors: pcnn/cli.py
evidence: recap/2026-09-17/cost
first_seen: 2026-09-17

@mutation link $CON-1 -> PCNN.IDENT-001 : caused_by w=0.95
@mutation link $CON-1 -> PCNN.CON-005 : refines w=0.80
@mutation link $DEC-1 -> $CON-1 : implements w=0.90
@mutation link $DEC-1 -> PCNN.ARC-002 : constrained_by w=0.85
@mutation link $DEC-1 -> PCNN.CON-002 : constrained_by w=0.90
@mutation link $DEC-2 -> PCNN.OPS-001 : refines w=0.75
@mutation touch PCNN.ARC-002
