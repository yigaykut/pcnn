@neuron PCNN.CON-004
head: The rendered view loads no font, script or stylesheet over the network
layer: CON
project: pcnn
status: active
confidence: verified
salience: 0.95
signals: cdn, font-stack, offline, self-contained, typography, webfont
description: Typography uses a font stack of faces already present on the machine: Constantia
  and Palatino Linotype for reading, Century Gothic for controls, each with documented
  fallbacks. No webfont is fetched and no font is embedded.
rationale: The output has to open from disk years from now with no network, which a Google Fonts
  link silently breaks and an embedded font pays for in file size on every render.
alternatives_rejected: Cormorant Garamond and Jost from Google Fonts; base64-embedding both
  families into every rendered page
anchors: pcnn/templates/network.html.tmpl
connected.PCNN.CON-004 -> PCNN.IMP-002 : constrained_by w=0.90
evidence: recap/2026-09-17/design
first_seen: 2026-09-17
last_touched: 2026-09-17
revision: 1
