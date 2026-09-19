@neuron INVEST.OPS-001
head: The canonical scan is python run.py --universe smallcap,midcap,wsb --top 45 --workers 8
layer: OPS
project: invest
status: active
confidence: verified
salience: 0.72
signals: cache, cli, http server, run command, scan, test command
description: A full scan runs as python run.py --universe smallcap,midcap,wsb --top 45 --workers
  8 and takes roughly an hour, so running it in the background is normal. Stale data is cleared
  with python run.py clear-cache, optionally scoped by --namespace (for example yahoo_bench).
  Watchlist commands are python run.py watch add TICKER [--price P] [--note N], watch list, and
  watch update [--use-cache]. Tests run as python tests/test_scoring.py. Generated HTML is
  inspected by serving output/ with python -m http.server <port> --bind 127.0.0.1. Yahoo fetch
  noise is suppressed by piping through grep -v "HTTP Error".
anchors: run.py, tests/test_scoring.py
connected.INVEST.OPS-001 -> INVEST.ARC-001 : implements w=0.75
evidence: recap/session-1ba99976-dc23-4ebe-ae08-ad19f0ecfeb9
first_seen: 2026-09-17
last_touched: 2026-09-17
revision: 1
