@neuron PCNN.DEC-006
head: Distillation runs on haiku and is fed a summarised delta, not the raw one
layer: DEC
project: pcnn
status: active
confidence: verified
salience: 0.92
signals: commands, cost, haiku, model-choice, prompt-size, slim-delta
description: distill.slim_delta builds a prompt-sized view of a delta: shell commands become
  bucket counts plus the twenty most repeated, truncated to 120 characters; instructions and
  failures are capped; files read are dropped entirely. The invariants arrive as one line per
  neuron instead of in full, so prompt cost stays flat as a network grows. Measured on one real
  day of the invest project, the prompt fell from 25,363 to 7,322 input tokens, and the model is
  haiku rather than a frontier model.
rationale: Verbatim shell commands were 67 percent of the payload and the least useful signal in
  it, because what a session decided lives in its closing recap, its file changes and its
  failures. Distillation is structured extraction against a closed grammar with a validator
  behind it, which a frontier model does no better and charges roughly ten times as much for.
alternatives_rejected: sending the raw delta; trimming the delta on disk, which would destroy
  the evidence the neuron is audited against
anchors: pcnn/distill.py
connected.PCNN.DEC-006 -> PCNN.ARC-002 : constrained_by w=0.85
connected.PCNN.DEC-006 -> PCNN.CON-002 : constrained_by w=0.90
connected.PCNN.DEC-006 -> PCNN.CON-006 : implements w=0.90
evidence: recap/2026-09-17/cost
first_seen: 2026-09-17
last_touched: 2026-09-17
revision: 1
