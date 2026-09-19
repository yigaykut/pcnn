@neuron PCNN.DEC-005
head: The view ships one dark surface with pigments validated against true black
layer: DEC
project: pcnn
status: active
confidence: verified
salience: 0.87
signals: brass, contrast-validation, dark-only, iris, palette, true-black, verdigris
description: The surface is #000000 rather than a tinted near-black, and the three family hues
  are brass #b4862f, verdigris #27a08c and iris #8e79ef. The triad was run through the
  colour-vision validator against that surface: worst all-pairs CVD delta E 11.3 and worst
  normal-vision delta E 17.0, both clear of their floors. There is no light theme and no theme
  toggle.
rationale: A second theme would need its own validated steps and doubles the surface the design
  has to hold together, for a page that is read as an instrument rather than as a document.
alternatives_rejected: gold #d4af37 and #c9a227, both above the dark-mode lightness band; a
  four-hue palette adding violet, magenta, red or yellow, each of which failed all-pairs
  separation
anchors: pcnn/templates/network.html.tmpl
connected.PCNN.DEC-005 -> PCNN.DEC-002 : refines w=0.80
evidence: recap/2026-09-17/design
first_seen: 2026-09-17
last_touched: 2026-09-17
revision: 1
