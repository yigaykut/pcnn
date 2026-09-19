# PASS 1 - project intake (recall first, format later)

Paste this into a Claude Code session opened **in the project you want to
onboard**. It produces a free-form intake document. Pass 2 (`TRANSDUCE.md`)
converts that document into the network's schema.

The two passes are separate on purpose. Asking for deep recall and strict
formatting at the same time costs recall: facts get dropped because they are
awkward to format. Here, nothing is dropped — formatting is not your problem yet.

---

## TASK

Read this project thoroughly and write everything a future session would need to
know about it, as a numbered intake document.

### How to read the project

1. Start with the entry points: README, package manifest, main module, config.
2. Follow the data: where input enters, how it is transformed, where it leaves.
3. Read the code that looks strange. Unusual code almost always encodes a
   constraint someone discovered the hard way — that is the most valuable
   material in the whole exercise.
4. Read the git log if there is one, especially reverts and commits whose message
   explains a *why*.
5. Check for tests, CI config, deploy scripts, environment files, and note what
   they reveal about how the project is actually run.
6. Note what is missing or half-finished as carefully as what is complete.

### What to write down

Cover all of these, and say explicitly when a category is empty:

- **Identity** — what the project does, who or what uses it, what "working"
  means for it.
- **Decisions** — every choice visible in the code or history, with the reason if
  you can find it, and what was evidently rejected. Mark the reason as inferred
  when you are reading it off the code rather than a stated explanation.
- **Constraints** — must and never rules: platform limits, library quirks, data
  assumptions, conventions the code holds to without saying so.
- **Architecture** — components, boundaries, what calls what, where state lives.
- **Implementation** — the modules and functions that matter, and what each is for.
- **Data contracts** — schemas, API shapes, file formats, config keys, env vars.
- **Operations** — how to run, build, test and deploy it; ports; where secrets
  live; pinned versions.
- **Gotchas** — anything that looks like a workaround, a retry, a pinned version,
  a `# don't change this` comment, or a bug fix. Say what would break without it.
- **Open threads** — TODOs, stubs, commented-out code, known-broken paths.
- **Glossary** — terms this project uses in a specific way.

### Format

Plain Markdown. Number every paragraph with a bracketed id on its own line start:

```
[P1] The project is a daily stock screening pipeline. It pulls quotes, scores
them against weighted parameters and writes a static HTML dashboard.

[P2] Scoring weights live in config/weights.yaml. Changing a weight changes the
output ranking without any code change, which is why the file is separate.
```

Rules:
- One fact per paragraph. If a paragraph contains two facts, split it.
- Ids are sequential and never reused; pass 2 cites them as evidence.
- State uncertainty inline: "inferred from the code, not stated anywhere".
- Write in English, declaratively, no pronouns for the subject, no relative time.
- Quote exact identifiers, paths, commands and version numbers. Do not paraphrase
  a command — a paraphrased command is a command that will not run.
- Length is not a virtue, but omission is the one failure that cannot be repaired
  later. When unsure whether something matters, include it.

### Output

Write the document to:

    <orchestrator>/networks/<project-slug>/intake/<YYYY-MM-DD>.md

Then report the paragraph count and list the categories that came back empty.
