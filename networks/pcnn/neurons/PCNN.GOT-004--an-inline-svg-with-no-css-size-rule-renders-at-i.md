@neuron PCNN.GOT-004
head: An inline SVG with no CSS size rule renders at its default size and wrecks the layout
layer: GOT
project: pcnn
status: active
confidence: verified
salience: 0.82
signals: css-sizing, glyph, inline-svg, layout-bug, legend
description: The same svgGlyph helper fed both the filter chips and the legend, but only .chip
  .glyph carried width and height, so every legend glyph rendered at the browser default SVG
  size and expanded the panel to the full height of the page. The size rule is now on the .mark
  class itself rather than on one of its call sites.
rationale: An inline SVG has no intrinsic size to fall back on, so a shared helper must carry
  its own dimensions instead of relying on whichever context happens to style it.
anchors: pcnn/templates/network.html.tmpl
connected.PCNN.GOT-004 -> PCNN.IMP-002 : constrained_by w=0.60
evidence: recap/2026-09-17/design
first_seen: 2026-09-17
last_touched: 2026-09-17
revision: 1
