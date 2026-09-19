@neuron PCNN.GOT-009
head: The SessionEnd hook wrote a self-report into a Network it had never loaded
layer: GOT
project: pcnn
status: active
confidence: stated
salience: 0.90
signals: derived-files, empty-network, hook, init, load, map-wipe
description: hooks/session_end.py called Network.init(), which only creates directories, and
  then applied the session's self-report against it. With no neurons in memory every link to an
  existing neuron was rejected as unknown, and the rebuild that followed wrote a MAP.md
  containing one neuron over a map of thirty-seven. The neuron files on disk were untouched, so
  a single rebuild restored everything.
rationale: Nothing was lost because neurons are the source of truth and MAP.md, INVARIANTS and
  graph.json are derived from them, which is the reason they are kept apart. The fix is
  two-sided: the hook now loads before applying, and Network.rebuild re-reads the directory
  whenever it holds more neurons than the instance does, so no caller can overwrite a map with a
  stale view of it again.
alternatives_rejected: fixing only the hook, which would leave the same trap for the next caller
  that forgets
anchors: hooks/session_end.py, pcnn/store.py
connected.PCNN.GOT-009 -> PCNN.ARC-002 : constrained_by w=0.85
connected.PCNN.GOT-009 -> PCNN.CON-002 : verified_by w=0.70
evidence: self/2026-09-17/hook-run
first_seen: 2026-09-17
last_touched: 2026-09-17
revision: 1
