@neuron PCNN.DEC-004
head: Weight is drawn as distance from the core, not as node size
layer: DEC
project: pcnn
status: active
confidence: verified
salience: 0.90
signals: radial-layout, rings, sacred-geometry, salience-encoding, visual-language
description: The HTML view is a radial field whose concentric rings are weight bands. Radius
  follows weight rank rather than weight value, so every shell fills evenly even though the
  network is top-heavy, while the order stays exact: nearer the core is always heavier. Ring
  captions report the real weight at each boundary. Angle is assigned by golden-angle
  phyllotaxis over rank order, and the edge springs are weak enough only to bend a neuron
  towards its neighbours, so the same network always draws the same picture.
rationale: The single promise the system makes is that weight never decays, so the view puts
  weight in the one channel that cannot be skimmed past. Mapping weight value directly to radius
  emptied the outer shells, and letting forces choose the angle pulled every neuron towards
  whichever hub it was tied to until the field collapsed into one clump and stopped reading as a
  network at all.
alternatives_rejected: free force-directed placement with size alone carrying salience; a linear
  weight-to-radius map; force-negotiated angles
anchors: pcnn/render.py, pcnn/templates/network.html.tmpl
connected.PCNN.DEC-004 -> PCNN.CON-001 : caused_by w=0.90
connected.PCNN.DEC-004 -> PCNN.IMP-002 : constrained_by w=0.85
evidence: recap/2026-09-17/design
first_seen: 2026-09-17
last_touched: 2026-09-17
revision: 1
