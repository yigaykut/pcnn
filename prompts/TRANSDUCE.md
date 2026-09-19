# PASS 2 - intake to network (transduction)

Converts the free-form intake document from pass 1 into PCNN mutations. Run this
in a session at the orchestrator root, with the intake file in context.

Success is measured, not assumed: every intake paragraph id must appear in at
least one neuron's `evidence:`. `python -m pcnn audit <slug>` prints the
coverage percentage and lists the paragraphs nothing cited.

---

## TASK

Read `networks/<slug>/intake/<date>.md` and emit a mutation block that captures
**every** paragraph in it.

Emit only the mutation block. No prose, no code fences.

## Method

1. **Pass over the intake once, assigning each paragraph a layer.** Do not write
   anything yet. A paragraph that carries two facts gets split across two
   neurons; a fact stated across three paragraphs becomes one neuron citing all
   three.
2. **Write the high layers first**: `IDENT`, then `CON`, then `DEC`. These anchor
   everything else and later neurons will link back to them.
3. **Then the structural layers**: `ARC`, `IMP`, `DAT`, `OPS`.
4. **Then `GOT`, `TODO`, `GLO`.**
5. **Then the edges.** Every neuron needs at least one. Work through the list and
   ask, for each: what does this depend on, what constrains it, what decision
   caused it, what does it implement?
6. **Check coverage before answering.** List every paragraph id from the intake
   and confirm each appears in some `evidence:` field. Cite the ones you decided
   were not worth a neuron on the nearest related neuron rather than dropping
   them — an uncited paragraph is an unexplained gap.

## Layers, grammar and style

Identical to `DISTILL_RECAP.md` sections 2, 3 and 5 — read that file for the
layer table, the edge vocabulary, the writing rules and the mutation grammar.

Two differences apply to transduction:

- **Evidence is paragraph ids**, not a recap path: `evidence: P4, P17`.
- **Confidence tracks the intake's own hedging.** A fact the intake states
  outright is `verified`; a fact the intake says it inferred from the code is
  `inferred`; a fact the intake attributes to a comment or commit message without
  confirming it is `stated`. Do not upgrade confidence to make the network look
  more certain than it is.

## Salience within a layer

The floor is the minimum, not the answer. Raise a neuron above its floor when:

- the project would be misunderstood without it (+0.05 to +0.10)
- it is the reason several other facts exist (+0.05)
- getting it wrong caused real damage before (`GOT`, +0.05)

Set `pin: true` only for facts that must be in front of every future session —
typically the identity neuron and two to five hard constraints. More than about
eight pinned neurons in a project means nothing is pinned.

## Common transduction failures

- **Merging distinct facts** to keep the neuron count down. The count is not a
  budget. Two facts, two neurons.
- **Writing topic labels as heads.** `head` is a claim with a verb in it.
- **Dropping the "why".** An intake paragraph that explains a reason becomes the
  `rationale` of a `DEC` or `CON` neuron, not a sentence appended to a
  description.
- **Leaving new neurons unlinked.** Unlinked means unreachable by retrieval.
- **Paraphrasing commands or identifiers.** Copy them exactly.

## After the mutations are applied

```
python -m pcnn apply <slug> --file <mutations.md> --cause intake/<date>
python -m pcnn audit <slug>
```

If coverage is below 95%, re-run this prompt scoped to the uncited paragraphs
only, so the existing neurons are not rewritten.
