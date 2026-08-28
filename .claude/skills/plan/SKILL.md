---
name: plan
description: Research the codebase and produce a plan doc with contracts and milestones for a feature
argument-hint: "<requirements-file-path | feature description>"
effort: high
---

Feature to plan: $ARGUMENTS

**Input** is either a path to a requirements file (normally under
`docs/requirements/`) or an inline description. If it is a path, read that file
first and treat it as the authoritative ask. **Output** always goes to
`docs/plans/<feature-slug>.md` — input and output never share a folder.

This skill is project-agnostic. Everything repo-specific — stack, commands, file
layout, conventions, domain rules — comes from the repo's `CLAUDE.md`. Read it
first and treat it as authoritative; never assume a stack or a command.

## The budget: a 2-minute read

**Hard cap: 140 lines, of which ≤400 words are prose** — text outside tables and
code blocks. Tables are line-cheap and scan fast; paragraphs are what make a doc
unreadable, so budget those specifically. The verbatim appendix doesn't count.

A plan an engineer will not finish reading is a plan nobody checked. This is the
single most important rule in this file — if the doc is over budget, cut it; do
not append a note apologising for length.

- **Tables and bullets carry the content.** Prose only where a table cannot.
- **One idea per line.** Short sentences. No paragraph longer than 3 lines.
- **Never say the same thing twice.** The most common bloat is restating the ask
  in your own words after quoting it. Quote once, in the appendix, and reference it.
- Rationale is a **clause, not a paragraph** — "…because SQLite has no NUMERIC".

## Phase 1 — Explore (read-only)

Map the parts of the codebase this feature touches: existing models, services,
API patterns, test setup. Find the closest existing feature and use it as the
template rather than reinventing. Skim `checklist.md` (next to this file) once
and note which sections apply; most won't.

## Phase 2 — Clarify (stop and wait)

Ask via the **AskUserQuestion** tool, not prose. Ask only questions whose answers
change the design. If a reasonable senior engineer would just pick a default,
pick it and record it in Trade-offs instead of asking. Do not write the doc until
the user has answered. Skip this phase if the request already answers everything.

## Phase 3 — Write the doc

Write to `docs/plans/<feature-slug>.md` using exactly this structure and order.

### `# <Feature>`

One line: what this builds, for whom.

### `## Requirements`

A traceability table — this replaces restating the ask in prose:

| # | Requirement | Decision |
|---|---|---|
| R1 | Create accounts | Build — `createAccount` |
| C8 | Cross-account transfers | **Non-goal** |

Every numbered item from the ask gets a row. Every row is either built or an
explicit non-goal. A silently dropped requirement is the failure this table
exists to prevent. Add a short **Non-goals** bullet list under it for
deferrals that came from `CLAUDE.md` rather than the ask.

### `## Entities & Data Models`

One table per entity: column, type, constraints. Then **one line** per entity
saying why it is shaped that way, and one line stating any invariant. Say whether
each is a new table or a change to an existing one, and what that means for the
repo's migration story.

### `## API & Interfaces`

The contract, as a signature block plus an error-code table. Add a **Why** column
or a one-line note for any non-obvious choice (why a string and not an int, why
this is nested rather than top-level). Implementation must not silently diverge
from what is written here.

### `## Data Flow`

**Numbered steps, one per line, for each flow that is not the repo's standard
path.** This is the section engineers actually use, so be concrete:

```
postTransaction(input)
1. parse amount → Decimal → cents      [VALIDATION_ERROR]
2. look up account by number           [NOT_FOUND]
3. if idempotency key seen → return original
4. UPDATE … WHERE balance >= amt RETURNING   [INSUFFICIENT_FUNDS if 0 rows]
5. INSERT ledger row
6. COMMIT (once)
```

Add a mermaid diagram only if the step list genuinely needs one. Skip the whole
section for flows that follow the repo's standard path — say so in one line.

### `## Trade-offs`

| Decision | Rejected | Why | Open? |
|---|---|---|---|

The **Open?** column marks rows you want the engineer to push back on — mark the
genuinely contestable ones, not everything. This table is where senior judgment
lives; keep the Why to one clause.

### `## Milestones`

A summary table first:

| # | Milestone | Demoable when | Size |
|---|---|---|---|

Then, per milestone, a short block: **Scope** (contracts, not procedure),
**Done when** (observable criteria as bullets), **Tests** (a bullet list of
cases — the implementer turns these into the test table), **Verification** (the
exact commands from `CLAUDE.md`, with what triggers each conditional step).

Order so **every milestone ends in something demoable** end-to-end — assume the
work is cut off at any boundary. Prefer a thin vertical slice first over a
complete backend with no frontend.

### `## Appendix — the ask, verbatim`

The requirements reproduced **verbatim** in a fenced block, with the source path.
Never paraphrase: `/review` checks the plan against this. It goes last because it
is reference material, not reading material.

## Rules

- **Respect the 120-line budget.** Everything else is subordinate to it.
- Every milestone ≤400 changed lines including tests. If it won't fit, split it —
  never write one large milestone with a note that it's large. Generated files
  and lockfiles don't count; `CLAUDE.md` says which files are generated.
- Contracts, not choreography: never "create file X then add method Y".
- Prefer the minimal design. Flag speculative generality in Trade-offs as rejected.
- If exploration reveals a conflict with existing architecture, say so before
  writing the plan.
- Only `docs/requirements/` and `docs/plans/` are committed; the rest of `docs/`
  is private scratch. Do not write elsewhere.
