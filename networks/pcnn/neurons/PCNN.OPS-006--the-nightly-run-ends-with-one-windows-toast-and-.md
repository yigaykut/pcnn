@neuron PCNN.OPS-006
head: The nightly run ends with one Windows toast and leaves nothing resident
layer: OPS
project: pcnn
status: active
confidence: stated
salience: 0.70
signals: notification, powershell, residency, scheduled-task, toast, winrt
description: scripts/notify.ps1 hands a toast to the shell through the WinRT notification API,
  which needs nothing installed, and exits. Clicking the toast opens output/ network.html
  through protocol activation. The whole nightly pass measured six seconds end to end and left
  no process behind, so nothing occupies memory between runs. A toast that cannot be shown,
  because notifications are off or Focus Assist is on, is swallowed rather than allowed to fail
  the run.
anchors: pcnn/cli.py, scripts/nightly.py, scripts/notify.ps1
connected.PCNN.OPS-006 -> PCNN.DEC-009 : implements w=0.75
connected.PCNN.OPS-006 -> PCNN.DEC-009 : refines w=0.70
evidence: self/2026-09-18/schedule
first_seen: 2026-09-18
last_touched: 2026-09-18
revision: 1
