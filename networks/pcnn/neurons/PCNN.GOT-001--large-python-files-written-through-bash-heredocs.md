@neuron PCNN.GOT-001
head: Large Python files written through bash heredocs get mangled; use the Write tool
layer: GOT
project: pcnn
status: active
confidence: verified
salience: 0.84
signals: bash, file-creation, heredoc, quoting, windows, write-tool
description: Creating pcnn/schema.py with a quoted bash heredoc failed with "unexpected EOF
  while looking for matching quote" on Git Bash under Windows, despite the terminator being
  correct. Writing the same content with the Write tool succeeded immediately.
rationale: Shell quoting over a multi-hundred-line payload containing apostrophes and regex
  escapes is fragile enough that retrying it costs more than switching tools.
anchors: pcnn/schema.py
connected.PCNN.GOT-001 -> PCNN.OPS-001 : relates_to w=0.30
evidence: P11
first_seen: 2026-09-17
last_touched: 2026-09-17
revision: 1
