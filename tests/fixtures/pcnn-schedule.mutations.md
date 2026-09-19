@mutation upsert $DEC-1
head: The nightly pass runs only on days a session was actually opened
layer: DEC
project: pcnn
salience: 0.88
signals: nightly, activity-gate, transcript-mtime, quiet-day, scheduled-task
description: scripts/nightly.py asks pcnn.activity.anything_happened before doing any work
  and stands down when the answer is no. The signal is the Claude Code transcript itself: a
  file under the transcript root whose modification time falls on the day in question, and
  whose folder name matches a registered project. A session that opened and changed nothing
  still counts, because the question is whether a session happened rather than whether it
  was productive. The --force switch overrides the gate.
rationale: Running on a day nobody worked rewrites four HTML files to say exactly what they
  said yesterday and writes a log line that means nothing, which makes the log harder to
  read on the days it matters.
alternatives_rejected: gating on whether a recap was written, which misses a session that
  opened and changed nothing
anchors: pcnn/activity.py, scripts/nightly.py
evidence: self/2026-09-18/schedule
first_seen: 2026-09-18

@mutation upsert $DAT-1
head: Claude Code names a transcript folder by replacing every non-alphanumeric character with a hyphen
layer: DAT
project: pcnn
salience: 0.72
signals: transcript-folder, slug, naming, non-ascii, path-encoding
description: A working directory maps to its transcript folder by replacing every character
  that is not a letter or a digit with a hyphen. The drive colon, both path separators, the
  space and any non-ASCII letter all collapse the same way, so C:\\Users\\Renee\\OneDrive\\
  Desktop\\project orchestrator is stored as C--Users-Renee-OneDrive-Desktop-project-
  orchestrator. Matching a project to its transcripts requires the resolved path, not the
  one the registry happens to hold.
rationale: An earlier guess that only the colon and separators were replaced silently found
  zero sessions on a machine whose user name carries a Turkish dotted I.
anchors: pcnn/activity.py
evidence: self/2026-09-18/schedule
first_seen: 2026-09-18

@mutation upsert $OPS-1
head: The nightly run ends with one Windows toast and leaves nothing resident
layer: OPS
project: pcnn
salience: 0.70
signals: notification, toast, winrt, powershell, scheduled-task, residency
description: scripts/notify.ps1 hands a toast to the shell through the WinRT notification
  API, which needs nothing installed, and exits. Clicking the toast opens output/
  network.html through protocol activation. The whole nightly pass measured six seconds
  end to end and left no process behind, so nothing occupies memory between runs. A toast
  that cannot be shown, because notifications are off or Focus Assist is on, is swallowed
  rather than allowed to fail the run.
anchors: pcnn/cli.py, scripts/notify.ps1, scripts/nightly.py
evidence: self/2026-09-18/schedule
first_seen: 2026-09-18

@mutation link $DEC-1 -> PCNN.DEC-005 : refines w=0.85
@mutation link $DEC-1 -> $DAT-1 : depends_on w=0.90
@mutation link $OPS-1 -> $DEC-1 : implements w=0.75
@mutation link $OPS-1 -> PCNN.DEC-009 : refines w=0.70
