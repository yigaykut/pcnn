@neuron PCNN.DEC-002
head: Eleven layers share three validated hues, distinguished by node shape
layer: DEC
project: pcnn
status: active
confidence: verified
salience: 0.90
signals: categorical, colour-vision, composite-encoding, legend, palette, shapes
description: The eleven neuron layers are grouped into three families - intent, structure,
  experience - each carrying one of the three hues that clear the all-pairs colour-vision floor
  in both light and dark mode. The specific layer is carried by node shape: circle, square,
  diamond, triangle or hexagon. Every layer appears in the legend with both its hue and its
  shape, and node labels are drawn on the canvas.
rationale: A categorical palette may not be cycled or extended with generated hues; testing
  showed only three of the documented hues clear the all-pairs separation floor, so the
  remaining distinction has to be carried by a second visual channel.
alternatives_rejected: eleven distinct hues; four hues including violet, magenta, red or yellow,
  all of which failed the dark-mode separation check
anchors: pcnn/render.py, pcnn/templates/network.html.tmpl
connected.PCNN.DEC-002 -> PCNN.IMP-002 : constrained_by w=0.50
evidence: P7
first_seen: 2026-09-17
last_touched: 2026-09-17
revision: 1
