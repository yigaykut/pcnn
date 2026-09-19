"""Zero-token updates: read what the session already said.

A session that just spent an hour in a codebase knows what it decided and is
already writing a closing message.  Asking it to end that message with a short
block in the mutation grammar costs a handful of output tokens it was spending
anyway.  Paying a *second* model to read the transcript and rediscover the same
decisions is buying the same knowledge twice, and the second copy is worse
because it is inferred from evidence rather than remembered.

So the default path has no model call in it at all:

    session writes  @pcnn ... @end   ->  hook parses it  ->  validator applies it

`distill.py` remains for the two cases this cannot cover: backfilling history
from transcripts written before any of this existed, and a session that ended
without reporting.  Both are opt-in.

The block is fenced rather than bare so it can never be confused with the output
of a distillation run, which is a bare mutation block.
"""

from __future__ import annotations

import re

OPEN = "@pcnn"
CLOSE = "@end"

_BLOCK_RE = re.compile(
    rf"^[ \t]*{re.escape(OPEN)}[ \t]*$\n(?P<body>.*?)^[ \t]*{re.escape(CLOSE)}[ \t]*$",
    re.S | re.M)

#: what a session is asked to append to its closing message
CONTRACT = """\
If this session established anything durable about the project - a decision and
why, a constraint, something that broke and what fixed it, a component that now
exists, an open thread - end your final message with a block like this:

@pcnn
@mutation upsert $DEC-1
head: <one complete claim, under 110 chars>
layer: DEC
project: {slug}
salience: 0.88
signals: three, or, four, retrieval, keys
description: <the whole fact, readable with nothing else loaded>
rationale: <why; required for DEC, CON and GOT>
anchors: src/thing.py:40-90
@mutation link $DEC-1 -> {example} : constrained_by w=0.80
@end

Layers: IDENT what the project is - DEC a choice and its reason - CON a must or
never rule - ARC a component or boundary - IMP a module and what it does - DAT a
schema, config key or format - OPS how to run, build or deploy - GOT what broke
and the fix - TODO an open thread - GLO a term this project uses specifically.

Edges: depends_on, implements, constrained_by, caused_by, refines, instance_of,
contradicts, supersedes, blocks, verified_by, mirrors, relates_to.

Use $LAYER-n for a neuron that does not exist yet; real ids are allocated for
you. Reference existing neurons by the ids in the map above. Write in English,
declaratively, no pronouns for the subject, no relative time. One fact per
neuron. Never restate something the map already holds - `@mutation touch <id>`
it instead.

If the session established nothing durable, write no block. An empty answer is
the right answer more often than not, and a block is never worth inventing.
"""


def extract(text: str) -> str | None:
    """Return the mutation body of the last `@pcnn ... @end` block, if any."""
    if not text or OPEN not in text:
        return None
    blocks = _BLOCK_RE.findall(text)
    if not blocks:
        return None
    body = blocks[-1].strip()
    return body or None


def contract_for(slug: str, example_id: str = "") -> str:
    """The instruction block, wired to one project."""
    return CONTRACT.format(
        slug=slug, example=example_id or f"{slug.upper()}.ARC-001")


def has_block(text: str) -> bool:
    return extract(text) is not None
