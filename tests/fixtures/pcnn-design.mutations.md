@mutation upsert $DEC-1
head: Weight is drawn as distance from the core, not as node size
layer: DEC
project: pcnn
status: active
confidence: verified
salience: 0.90
signals: radial-layout, salience-encoding, rings, sacred-geometry, visual-language
description: The HTML view is a radial field whose concentric rings are weight bands.
  Radius follows weight rank rather than weight value, so every shell fills evenly even
  though the network is top-heavy, while the order stays exact: nearer the core is always
  heavier. Ring captions report the real weight at each boundary. Angle is assigned by
  golden-angle phyllotaxis over rank order, and the edge springs are weak enough only to
  bend a neuron towards its neighbours, so the same network always draws the same picture.
rationale: The single promise the system makes is that weight never decays, so the view
  puts weight in the one channel that cannot be skimmed past. Mapping weight value
  directly to radius emptied the outer shells, and letting forces choose the angle pulled
  every neuron towards whichever hub it was tied to until the field collapsed into one
  clump and stopped reading as a network at all.
alternatives_rejected: free force-directed placement with size alone carrying salience;
  a linear weight-to-radius map; force-negotiated angles
anchors: pcnn/templates/network.html.tmpl, pcnn/render.py
evidence: recap/2026-09-17/design
first_seen: 2026-09-17

@mutation upsert $DEC-2
head: The view ships one dark surface with pigments validated against true black
layer: DEC
project: pcnn
status: active
confidence: verified
salience: 0.87
signals: palette, dark-only, true-black, brass, verdigris, iris, contrast-validation
description: The surface is #000000 rather than a tinted near-black, and the three family
  hues are brass #b4862f, verdigris #27a08c and iris #8e79ef. The triad was run through
  the colour-vision validator against that surface: worst all-pairs CVD delta E 11.3 and
  worst normal-vision delta E 17.0, both clear of their floors. There is no light theme
  and no theme toggle.
rationale: A second theme would need its own validated steps and doubles the surface the
  design has to hold together, for a page that is read as an instrument rather than as a
  document.
alternatives_rejected: gold #d4af37 and #c9a227, both above the dark-mode lightness band;
  a four-hue palette adding violet, magenta, red or yellow, each of which failed
  all-pairs separation
anchors: pcnn/templates/network.html.tmpl
evidence: recap/2026-09-17/design
first_seen: 2026-09-17

@mutation upsert $CON-1
head: The rendered view loads no font, script or stylesheet over the network
layer: CON
project: pcnn
status: active
confidence: verified
salience: 0.95
signals: offline, webfont, cdn, self-contained, typography, font-stack
description: Typography uses a font stack of faces already present on the machine:
  Constantia and Palatino Linotype for reading, Century Gothic for controls, each with
  documented fallbacks. No webfont is fetched and no font is embedded.
rationale: The output has to open from disk years from now with no network, which a
  Google Fonts link silently breaks and an embedded font pays for in file size on every
  render.
alternatives_rejected: Cormorant Garamond and Jost from Google Fonts; base64-embedding
  both families into every rendered page
anchors: pcnn/templates/network.html.tmpl
evidence: recap/2026-09-17/design
first_seen: 2026-09-17

@mutation upsert $GOT-1
head: An inline SVG with no CSS size rule renders at its default size and wrecks the layout
layer: GOT
project: pcnn
status: active
confidence: verified
salience: 0.82
signals: inline-svg, css-sizing, legend, layout-bug, glyph
description: The same svgGlyph helper fed both the filter chips and the legend, but only
  .chip .glyph carried width and height, so every legend glyph rendered at the browser
  default SVG size and expanded the panel to the full height of the page. The size rule
  is now on the .mark class itself rather than on one of its call sites.
rationale: An inline SVG has no intrinsic size to fall back on, so a shared helper must
  carry its own dimensions instead of relying on whichever context happens to style it.
anchors: pcnn/templates/network.html.tmpl
evidence: recap/2026-09-17/design
first_seen: 2026-09-17

@mutation link $DEC-1 -> PCNN.IMP-002 : constrained_by w=0.85
@mutation link $DEC-1 -> PCNN.CON-001 : caused_by w=0.90
@mutation link $DEC-2 -> PCNN.DEC-002 : refines w=0.80
@mutation link $CON-1 -> PCNN.IMP-002 : constrained_by w=0.90
@mutation link $GOT-1 -> PCNN.IMP-002 : constrained_by w=0.60
@mutation link PCNN.IMP-002 -> $DEC-1 : implements w=0.90
@mutation touch PCNN.IMP-002
@mutation touch PCNN.DEC-002
