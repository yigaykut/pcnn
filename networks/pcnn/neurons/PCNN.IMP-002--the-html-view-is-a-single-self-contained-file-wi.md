@neuron PCNN.IMP-002
head: The HTML view is a single self-contained file with a hand-written force layout
layer: IMP
project: pcnn
status: active
confidence: verified
salience: 0.66
signals: canvas, force-directed, html, offline, output, renderer
description: pcnn/render.py injects a JSON payload into pcnn/templates/network.html.tmpl, which
  carries its own simulation, canvas renderer, filters, table view, timeline and path finder. No
  CDN, no build step and no vendored library, so the output still opens from disk years later.
anchors: pcnn/render.py, pcnn/templates/network.html.tmpl
connected.PCNN.IMP-002 -> PCNN.DEC-002 : implements w=0.90
connected.PCNN.IMP-002 -> PCNN.DEC-004 : implements w=0.90
evidence: P7
first_seen: 2026-09-17
last_touched: 2026-09-17
revision: 1
