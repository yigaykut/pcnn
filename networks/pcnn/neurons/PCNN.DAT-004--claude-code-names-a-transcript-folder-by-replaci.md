@neuron PCNN.DAT-004
head: Claude Code names a transcript folder by replacing every non-alphanumeric character with a hyphen
layer: DAT
project: pcnn
status: active
confidence: stated
salience: 0.72
signals: naming, non-ascii, path-encoding, slug, transcript-folder
description: A working directory maps to its transcript folder by replacing every character that
  is not a letter or a digit with a hyphen. The drive colon, both path separators, the space and
  any non-ASCII letter all collapse the same way, so C:\\Users\\MSI\\OneDrive\\ Desktop\\project
  orchestrator is stored as C--Users-ME--OneDrive-Desktop-project- orchestrator. Matching a
  project to its transcripts requires the resolved path, not the one the registry happens to
  hold.
rationale: An earlier guess that only the colon and separators were replaced silently found zero
  sessions on a machine whose user name carries a Turkish dotted I.
anchors: pcnn/activity.py
evidence: self/2026-09-18/schedule
first_seen: 2026-09-18
last_touched: 2026-09-18
revision: 1
