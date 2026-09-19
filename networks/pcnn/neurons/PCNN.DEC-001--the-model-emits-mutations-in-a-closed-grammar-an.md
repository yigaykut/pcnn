@neuron PCNN.DEC-001
head: The model emits mutations in a closed grammar and never writes neuron files directly
layer: DEC
project: pcnn
status: active
confidence: verified
salience: 0.98
signals: mutation-grammar, placeholder-ids, quarantine, upsert, validation
description: Distillation output is parsed as mutation operations - upsert, link, supersede,
  touch, raise - each validated against the schema before anything is written. New neurons use
  $LAYER-n placeholders because the model cannot know which ids are free; the engine allocates
  real ids and substitutes them. Rejected mutations are written to quarantine/ with the reason
  and surfaced as a badge in the HTML.
rationale: A model writing storage files directly can corrupt the graph in ways nothing detects;
  a closed grammar with a validator in front makes every bad write visible.
alternatives_rejected: letting the model edit neurons/*.md directly; free-form JSON output
anchors: pcnn/distill.py
connected.PCNN.DEC-001 -> PCNN.IDENT-001 : caused_by w=0.60
connected.PCNN.DEC-001 -> PCNN.CON-002 : constrained_by w=0.95
evidence: P6
first_seen: 2026-09-17
last_touched: 2026-09-17
revision: 1
