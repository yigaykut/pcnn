@neuron PCNN.DEC-007
head: Running pcnn with no arguments prints the dashboard and costs nothing
layer: DEC
project: pcnn
status: active
confidence: verified
salience: 0.86
signals: cli, dashboard, ergonomics, no-args, one-command
description: python -m pcnn with no subcommand reports every project's fact count, how many days
  are waiting, whether anything needs a look, how many model calls today has spent against the
  ceiling, and the path to the rendered view. It is read-only and makes no model call. Every
  other command remains available but none is needed day to day, because the hooks and the
  nightly task do the work.
rationale: A context system that requires a remembered sequence of commands is a system that
  stops being used, and the whole point is that the human does not maintain it.
alternatives_rejected: requiring pcnn status, pcnn audit and pcnn render to be run separately to
  learn the same things
anchors: pcnn/cli.py
connected.PCNN.DEC-007 -> PCNN.OPS-001 : refines w=0.75
evidence: recap/2026-09-17/cost
first_seen: 2026-09-17
last_touched: 2026-09-17
revision: 1
