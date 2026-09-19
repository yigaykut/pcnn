@mutation upsert $IDENT-1
head: PCNN is a retrieval system that keeps project context readable by AI across sessions
layer: IDENT
project: pcnn
status: active
confidence: verified
salience: 0.95
pin: true
signals: pcnn, project-context-neural-network, purpose, retrieval, context-loss
description: PCNN stores every durable fact about a software project as an atomic neuron
  with a fixed schema, typed weighted edges to other neurons, and immutable evidence. The
  primary consumer is a language model resuming work on the project; the human-facing HTML
  view is a rendering of the same data. PCNN spans several projects at once and links
  equivalent solutions across them.
rationale: Context earned inside one Claude Code session dies with that session, so
  decisions, rejected alternatives and platform gotchas get re-derived or silently
  contradicted in the next one.
anchors: README.md, pcnn/schema.py
evidence: P1
first_seen: 2026-09-17

@mutation upsert $CON-1
head: Salience never decreases automatically; only an explicit human demote lowers it
layer: CON
project: pcnn
status: active
confidence: verified
salience: 1.00
pin: true
signals: salience, weight, decay, demote, floor, never-lose-weight
description: Every automated path - distillation, consolidation, touch boosts - may raise
  a neuron's salience and may never lower it. Lowering requires the pcnn demote command,
  which refuses without a written reason and refuses to go below the layer floor. There is
  no recency decay anywhere in the engine; last_touched feeds the timeline view only.
rationale: Recency decay is the standard design and it is precisely how old context gets
  lost: a decision taken on day one must not fade because nobody touched it for a month.
alternatives_rejected: exponential recency decay on salience; automatic pruning of
  low-traffic neurons
anchors: pcnn/weights.py, pcnn/schema.py
evidence: P2
first_seen: 2026-09-17

@mutation upsert $CON-2
head: Facts are superseded, never deleted or shortened
layer: CON
project: pcnn
status: active
confidence: verified
salience: 1.00
pin: true
signals: supersede, immutability, deletion, shrink-guard, retired
description: A fact that changes gets status superseded plus a supersedes edge from its
  replacement, and stays on disk and on the canvas drawn hollow. A rewrite that drops more
  than 40 percent of an existing description, or drops an existing rationale, is rejected
  into quarantine rather than applied. INVARIANTS.md carries a RETIRED section so a later
  session cannot rediscover and re-adopt an abandoned approach.
rationale: Summarisation is the failure mode PCNN exists to prevent, so the storage layer
  has to make information loss structurally impossible rather than merely discouraged.
alternatives_rejected: rewriting neurons in place; deleting obsolete neurons
anchors: pcnn/distill.py, pcnn/store.py
evidence: P2, P3
first_seen: 2026-09-17

@mutation upsert $ARC-1
head: Three read tiers - MAP.md to navigate, neurons to read, evidence to audit
layer: ARC
project: pcnn
status: active
confidence: verified
salience: 0.90
pin: true
signals: read-tiers, map, l0, l1, l2, token-budget, navigation
description: L0 is MAP.md, one line per neuron, loaded every session. L1 is
  neurons/<id>--<slug>.md, the canonical fact in full, opened on demand. L2 is the evidence
  and recap material, read only when auditing. The tiers exist so token cost falls without
  any knowledge being compressed away.
anchors: pcnn/store.py
evidence: P4
first_seen: 2026-09-17

@mutation upsert $ARC-2
head: Two-stage update - deterministic harvest at session end, model distillation after
layer: ARC
project: pcnn
status: active
confidence: verified
salience: 0.90
signals: pipeline, session-end, harvest, distill, two-stage, hooks
description: Stage A parses the Claude Code session transcript with no model involved and
  writes a raw delta listing files changed, commands run, verbatim user instructions and
  failures. Stage B feeds that delta plus MAP.md and INVARIANTS.md to a headless claude -p
  call which returns a mutation block. Stage A is free and cannot hallucinate; Stage B is
  the only step that costs tokens and the only step that can be wrong.
rationale: Splitting the pipeline means a failed or skipped distillation still leaves the
  session fully recorded on disk, so nothing is ever unrecoverable.
anchors: pcnn/ingest.py, pcnn/distill.py, hooks/session_end.py
evidence: P5
first_seen: 2026-09-17

@mutation upsert $DEC-1
head: The model emits mutations in a closed grammar and never writes neuron files directly
layer: DEC
project: pcnn
status: active
confidence: verified
salience: 0.92
signals: mutation-grammar, quarantine, validation, upsert, placeholder-ids
description: Distillation output is parsed as mutation operations - upsert, link,
  supersede, touch, raise - each validated against the schema before anything is written.
  New neurons use $LAYER-n placeholders because the model cannot know which ids are free;
  the engine allocates real ids and substitutes them. Rejected mutations are written to
  quarantine/ with the reason and surfaced as a badge in the HTML.
rationale: A model writing storage files directly can corrupt the graph in ways nothing
  detects; a closed grammar with a validator in front makes every bad write visible.
alternatives_rejected: letting the model edit neurons/*.md directly; free-form JSON output
anchors: pcnn/distill.py
evidence: P6
first_seen: 2026-09-17

@mutation upsert $DEC-2
head: Eleven layers share three validated hues, distinguished by node shape
layer: DEC
project: pcnn
status: active
confidence: verified
salience: 0.88
signals: palette, colour-vision, categorical, composite-encoding, shapes, legend
description: The eleven neuron layers are grouped into three families - intent, structure,
  experience - each carrying one of the three hues that clear the all-pairs colour-vision
  floor in both light and dark mode. The specific layer is carried by node shape: circle,
  square, diamond, triangle or hexagon. Every layer appears in the legend with both its hue
  and its shape, and node labels are drawn on the canvas.
rationale: A categorical palette may not be cycled or extended with generated hues; testing
  showed only three of the documented hues clear the all-pairs separation floor, so the
  remaining distinction has to be carried by a second visual channel.
alternatives_rejected: eleven distinct hues; four hues including violet, magenta, red or
  yellow, all of which failed the dark-mode separation check
anchors: pcnn/render.py, pcnn/templates/network.html.tmpl
evidence: P7
first_seen: 2026-09-17

@mutation upsert $IMP-1
head: Retrieval is spreading activation over the graph, returning the path that matched
layer: IMP
project: pcnn
status: active
confidence: verified
salience: 0.72
signals: query, spreading-activation, retrieval, hops, seeds, ranking
description: Query terms seed neurons through signals, head, anchors and id matches with
  activation equal to their salience, then activation propagates along edges for up to
  three hops at 0.6 decay per hop and 0.8 for traversing an edge backwards. Results above
  the cutoff are ranked and returned with the activation path, so a neuron no query term
  touched can still surface because a decision two hops away depends on it.
anchors: pcnn/query.py
evidence: P8
first_seen: 2026-09-17

@mutation upsert $IMP-2
head: The HTML view is a single self-contained file with a hand-written force layout
layer: IMP
project: pcnn
status: active
confidence: verified
salience: 0.66
signals: html, canvas, force-directed, offline, renderer, output
description: pcnn/render.py injects a JSON payload into pcnn/templates/network.html.tmpl,
  which carries its own simulation, canvas renderer, filters, table view, timeline and path
  finder. No CDN, no build step and no vendored library, so the output still opens from
  disk years later.
anchors: pcnn/render.py, pcnn/templates/network.html.tmpl
evidence: P7
first_seen: 2026-09-17

@mutation upsert $DAT-1
head: Neuron ids are SCOPE.LAYER-NNN and are never reused, even after a merge
layer: DAT
project: pcnn
status: active
confidence: verified
salience: 0.75
signals: neuron-id, scope, identifier, next-id, changelog
description: A neuron id is the uppercased project slug, a dot, the three or four letter
  layer code, a hyphen and a zero-padded number, for example PCNN.DEC-002. Allocation scans
  both the live neurons and the changelog so an id belonging to a merged or superseded
  neuron is never handed out again.
anchors: pcnn/schema.py, pcnn/store.py
evidence: P9
first_seen: 2026-09-17

@mutation upsert $OPS-1
head: Everything runs through python -m pcnn with no third-party dependencies
layer: OPS
project: pcnn
status: active
confidence: verified
salience: 0.70
signals: cli, commands, stdlib, entry-point, install
description: The engine is Python 3 standard library only. Commands are init, status,
  validate, rebuild, query, context, harvest, distill, apply, audit, consolidate, render,
  demote and suggest. PCNN_HOME overrides the orchestrator root when the package is run
  from elsewhere, which is what the session hooks rely on.
anchors: pcnn/cli.py
evidence: P10
first_seen: 2026-09-17

@mutation upsert $GOT-1
head: Large Python files written through bash heredocs get mangled; use the Write tool
layer: GOT
project: pcnn
status: active
confidence: verified
salience: 0.82
signals: heredoc, bash, write-tool, file-creation, quoting, windows
description: Creating pcnn/schema.py with a quoted bash heredoc failed with "unexpected EOF
  while looking for matching quote" on Git Bash under Windows, despite the terminator being
  correct. Writing the same content with the Write tool succeeded immediately.
rationale: Shell quoting over a multi-hundred-line payload containing apostrophes and regex
  escapes is fragile enough that retrying it costs more than switching tools.
anchors: pcnn/schema.py
evidence: P11
first_seen: 2026-09-17

@mutation upsert $GLO-1
head: Neuron, salience, signals, anchors, evidence and layer have fixed meanings
layer: GLO
project: pcnn
status: active
confidence: verified
salience: 0.60
signals: glossary, terminology, vocabulary, definitions
description: A neuron is one atomic fact. Salience is its stored importance from 0 to 1.
  Signals are curated retrieval keys used to seed a query. Anchors are file or file:line
  references into the project being described. Evidence records where the fact came from, a
  recap path or an intake paragraph id. A layer is the single category a fact belongs to.
anchors: pcnn/schema.py
evidence: P1
first_seen: 2026-09-17

@mutation upsert $TODO-1
head: No project other than pcnn itself has been onboarded yet
layer: TODO
project: pcnn
status: active
confidence: verified
salience: 0.70
signals: onboarding, backlog, invest, kriptografi, next-steps
description: The registry holds only the pcnn project. The invest project is the intended
  first real onboarding because it has the largest transcript history and a public GitHub
  remote, which exercises both ingestion volume and the rule that real project context stays
  out of the public repository. kriptografi follows.
evidence: P12
first_seen: 2026-09-17

@mutation link $ARC-2 -> $CON-2 : constrained_by w=0.90
@mutation link $ARC-2 -> $DEC-1 : implements w=0.85
@mutation link $DEC-1 -> $CON-2 : constrained_by w=0.95
@mutation link $DEC-1 -> $IDENT-1 : caused_by w=0.60
@mutation link $CON-1 -> $IDENT-1 : caused_by w=0.90
@mutation link $CON-2 -> $IDENT-1 : caused_by w=0.90
@mutation link $ARC-1 -> $IDENT-1 : implements w=0.80
@mutation link $IMP-1 -> $ARC-1 : depends_on w=0.75
@mutation link $IMP-2 -> $DEC-2 : implements w=0.90
@mutation link $DEC-2 -> $IMP-2 : constrained_by w=0.50
@mutation link $DAT-1 -> $CON-2 : constrained_by w=0.80
@mutation link $OPS-1 -> $IMP-1 : depends_on w=0.45
@mutation link $OPS-1 -> $IMP-2 : depends_on w=0.45
@mutation link $GLO-1 -> $DAT-1 : refines w=0.55
@mutation link $GOT-1 -> $OPS-1 : relates_to w=0.30
@mutation link $TODO-1 -> $ARC-2 : blocks w=0.40
@mutation link $IMP-1 -> $CON-1 : constrained_by w=0.70
