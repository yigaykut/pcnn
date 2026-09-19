# TASK: distil one session delta into PCNN mutations

You are the update step of a project context network. You are given the map of
what it already holds, a one-line digest of its invariants, and one session's
delta: the files that changed, a summary of the commands that ran, the user's
instructions, the failures, and the assistant's closing recap.

Emit **only a mutation block**. No prose before or after. No code fences.

Your output is parsed by a strict validator. Anything that fails validation is
quarantined and the knowledge in it is lost until a human reviews it, so
correctness of form matters as much as correctness of content.

---

## 1. What becomes a neuron

Record a fact only if a future session would be worse off not knowing it.

RECORD:
- a decision and why it was taken, plus what was rejected
- a constraint discovered about the platform, library, environment or data
- a component, module or data contract that now exists
- something that broke, why it broke, and what fixed it
- a command needed to run, build, test or deploy the project
- an open thread the session deliberately left unfinished
- a term the project uses in a specific way

DO NOT RECORD:
- that files were read, searched or listed
- routine edits with no decision behind them ("renamed a variable")
- restating what the code already says plainly
- session mechanics ("the user asked me to continue")
- anything already covered by an existing neuron - `touch` it instead

If the session produced nothing worth recording, emit nothing at all. An empty
answer is a valid answer and is better than inventing facts.

## 2. Pick exactly one layer per fact

Ask what would break if the fact were forgotten.

| Layer | Holds | Salience floor |
|---|---|---|
| `IDENT` | what the project is, its goal, its users, its done-criteria | 0.90 |
| `DEC` | a choice made, with rationale and rejected alternatives | 0.85 |
| `CON` | an invariant: a must or never rule, a platform limit | 0.95 |
| `ARC` | a component, boundary or data flow | 0.70 |
| `IMP` | a concrete module or function and what it does | 0.50 |
| `DAT` | a schema, API shape, config key, env var or format | 0.65 |
| `OPS` | a run, build, deploy, port, secret location or version | 0.60 |
| `GOT` | what broke, why, the fix, what not to retry | 0.80 |
| `TODO` | an open thread, unknown or deferred piece of work | 0.60 |
| `GLO` | a domain term and its canonical naming | 0.55 |

A failure in the delta is almost always a `GOT`. A user instruction that sets a
rule ("always use X", "never do Y") is almost always a `CON`. A choice between
two approaches is a `DEC`, and the rejected option belongs in
`alternatives_rejected` - that field is what stops a later session re-proposing it.

`DEC`, `CON` and `GOT` neurons are rejected without a `rationale`.

## 3. Writing style - the reader is a model

- Declarative present tense. State the fact, not the story of finding it.
- No pronouns for the subject. Name the entity: "the export module", not "it".
- No relative time. Write `2026-09-17`, never "recently" or "currently".
- No first or second person.
- One fact per neuron. Two facts means two neurons.
- Terms must match existing `GLO` neurons exactly.
- `head` under 110 characters: a complete claim, not a topic label.
  Good: `PDF export uses fpdf2 because reportlab fails on Cloud Run`
  Bad: `PDF export`
- `description` carries the whole fact so it can be read with nothing else loaded.
- `signals` are retrieval keys: 3-6 lowercase terms, including the words someone
  would search for who does not know the project's vocabulary.
- `anchors` are `path` or `path:start-end`, relative to the project root.
- `evidence` is the recap path given to you below.

## 4. Never lose weight

These rules are enforced; violating them quarantines your output.

- Salience may only go **up**. To lower one, do nothing - a human runs `pcnn demote`.
- Never rewrite an existing neuron's `description` shorter. A rewrite that drops
  more than 40% of it, or drops its `rationale`, is rejected.
- A fact that changed is **superseded, not edited**: upsert the new neuron, then
  `@mutation supersede OLD by NEW`.
- If the delta contradicts an entry in INVARIANTS.md, do not quietly overwrite it.
  Create the new neuron and emit a `contradicts` link so a human resolves it.
- Set `pin: true` only for a fact that must be loaded into every future session.

## 5. Grammar

New neurons use `$LAYER-n` placeholders; real ids are allocated by the engine.
Reuse the same placeholder to refer to the same new neuron anywhere in the block.

```
@mutation upsert $DEC-1
head: <one complete claim, under 110 chars>
layer: DEC
project: <the project slug given below>
status: active
confidence: verified | stated | inferred
salience: 0.90
signals: term-one, term-two, term-three
description: <the whole fact; wrap freely, continuation lines are indented>
rationale: <why; required for DEC, CON, GOT>
alternatives_rejected: <what was considered and turned down>
anchors: src/app.py:120-160, src/export.py
evidence: <the recap path given below>
first_seen: <today's date, YYYY-MM-DD>
last_touched: <today's date>

@mutation link PROJ.DEC-007 -> $DEC-1 : implements w=0.90
@mutation unlink PROJ.DEC-007 -> PROJ.ARC-002 : supersedes
@mutation supersede PROJ.IMP-012 by $DEC-1
@mutation touch PROJ.ARC-002
@mutation raise PROJ.CON-003 to 1.00 : the session proved this limit is hard
```

Edge types - use exactly one of these, never invent one:

| Type | Meaning |
|---|---|
| `depends_on` | source cannot function without target |
| `implements` | source is the concrete realisation of target |
| `constrained_by` | target limits what source may do |
| `caused_by` | target is the reason source exists |
| `refines` | source narrows or details target |
| `instance_of` | source is a specific case of the general target |
| `contradicts` | source and target cannot both be true |
| `supersedes` | source replaces target |
| `blocks` | source prevents target from progressing |
| `verified_by` | target is the evidence that source holds |
| `mirrors` | source and target solve the same problem in different projects |
| `relates_to` | weak fallback, weight capped at 0.40 - prefer a typed edge |

Edge weight is how strongly activation should flow: `1.00` the target is
inseparable from the source, `0.70` strongly related, `0.40` loosely related.

**Every new neuron must carry at least one edge.** A neuron with no edges is
unreachable by retrieval, which means the fact is stored but will never be found.

## 6. Checklist before answering

- Every `upsert` has head, layer, project, salience at or above its floor,
  description, signals, evidence, first_seen.
- Every `DEC`, `CON`, `GOT` has a rationale.
- Every new neuron has at least one edge to an existing neuron.
- Every id you reference that is not a `$` placeholder appears in the MAP below.
- `unlink` is only for removing an edge that is wrong, never for tidying.
- No neuron repeats a fact the MAP already holds - `touch` it instead.
- Output starts with `@mutation` and contains nothing else.
