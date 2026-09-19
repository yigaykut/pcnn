@neuron PCNN.GOT-010
head: A self-report can be written well before a session's last three messages
layer: GOT
project: pcnn
status: active
confidence: stated
salience: 0.86
signals: last-three, recap-window, scan, self-report, tail
description: The recap field holds only the final three assistant messages of a day, so a block
  written before a long tail of follow-up work falls out of it. Harvesting now scans every
  assistant message of the day for a fenced block and stores the last one in the delta's
  self_report field, which the hook reads before falling back to the recap.
rationale: The failure is silent in exactly the wrong way: the session reports correctly, the
  hook finds nothing, and the day looks like one where nothing was learned. It was caught by
  running the real hook against this session's own transcript rather than a fixture.
anchors: pcnn/ingest.py, pcnn/reap.py
connected.PCNN.GOT-010 -> PCNN.DEC-008 : constrained_by w=0.90
connected.PCNN.GOT-010 -> PCNN.DAT-002 : refines w=0.75
evidence: self/2026-09-17/hook-run
first_seen: 2026-09-17
last_touched: 2026-09-17
revision: 1
