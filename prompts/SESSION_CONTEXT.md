# Making a live session use the network

Two ways to deliver this. Use the first; keep the second for sessions that run
without hooks.

## A. Automatic (preferred)

`hooks/session_start.py` injects the invariants, the map and these rules into
every session opened inside a registered project. Nothing to paste. Setup is in
the README under "Wiring the hooks".

## B. Manual - paste this into the session

Replace `<SLUG>` with the project slug and `<ORCHESTRATOR>` with the absolute
path to this repository. Everything from the line below down is the prompt.

---

```
This project has a context network at <ORCHESTRATOR>/networks/<SLUG>/.
It holds what previous sessions established about this codebase: decisions and
why they were taken, constraints, what broke before, and what is still open.
Treat it as established fact about this project, not as suggestion.

Load it now, in this order:
1. Read <ORCHESTRATOR>/networks/<SLUG>/INVARIANTS.md in full. These must not be
   contradicted.
2. Read <ORCHESTRATOR>/networks/<SLUG>/MAP.md. It is an index: one line per
   neuron, formatted as
   `id | layer | salience | flags | head | outgoing edges | code anchors`.
   Do not read the individual neuron files yet.

Then follow these rules for the rest of the session:

- Before any architectural change, any new dependency, or any rewrite of an
  existing component, consult the map for neurons covering that area and open the
  ones that apply: <ORCHESTRATOR>/networks/<SLUG>/neurons/<id>--*.md
- Before concluding that something does not exist in this project, or that a
  thing has never been tried, run:
      python -m pcnn query <SLUG> "<the question in plain words>"
  from <ORCHESTRATOR>. It retrieves by spreading activation across the graph and
  surfaces neurons that no keyword search would have matched. Reading the map top
  to bottom is not a substitute.
- Never contradict an entry in INVARIANTS.md silently. If the task genuinely
  requires going against one, say so explicitly, name the neuron id, explain why,
  and let the user decide.
- The RETIRED section of INVARIANTS.md lists approaches that were tried and
  abandoned. Do not re-propose one of them without addressing why it was dropped.
- Salience is how much weight a fact carries. A high-salience neuron outranks
  your own inference about the codebase. If the code appears to contradict a
  pinned neuron, that is a finding worth raising, not a reason to ignore the
  neuron.
- When this session establishes something new - a decision, a constraint, a
  gotcha, a component, an open thread - state it plainly in your final message,
  including the reason. That message is harvested into the network automatically
  at session end, and a reason you do not write down is a reason that is lost.
```

---

## C. Per-project CLAUDE.md snippet

For a permanent rule, append this to the project's own `CLAUDE.md`. It is the
same contract in short form, for the cases where the full block is too much.

```markdown
## Context network

This project's durable context lives at `<ORCHESTRATOR>/networks/<SLUG>/`.

- `INVARIANTS.md` - decisions, constraints and gotchas that must not be
  contradicted. Read it before changing architecture.
- `MAP.md` - one-line index of every known fact.
- `neurons/<id>--*.md` - the full fact, its rationale and its evidence.

Before concluding something does not exist here, run
`python -m pcnn query <SLUG> "<question>"` from `<ORCHESTRATOR>`.

State new decisions, constraints and gotchas explicitly in your final message -
they are harvested into the network at session end.
```

## D. The visual view

`<ORCHESTRATOR>/output/<SLUG>.html` is the human view of the same data, rebuilt
on every update. It is not a substitute for the map in a session: it is for
seeing the shape of the project, tracing how a decision reaches a file
(shift-click two nodes), and spotting decay through the health badges.
