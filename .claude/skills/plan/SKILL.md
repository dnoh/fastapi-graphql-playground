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

## Phase 1 — Explore (read-only)

Map the parts of the codebase this feature touches: existing models, services,
API patterns, test setup. Note what patterns already exist that this feature
should follow rather than reinvent — find the closest existing feature and use it
as the template. Then skim `checklist.md` (next to this file) once and note which
sections apply; most won't.

## Phase 2 — Clarify (stop and wait)

Ask via the **AskUserQuestion** tool, not prose — it renders selectable options
instead of a list the user has to answer by number. Ask only questions whose
answers change the design. If a reasonable senior engineer would just pick a
default, pick it and record it in the Trade-offs table instead of asking.
Do not write the doc until the user has answered. If the user's request already
answers everything, skip this phase.

## Phase 3 — Write the doc

Write to `docs/plans/<feature-slug>.md` using exactly this structure:

# <Feature>

## Original ask

Reproduce the requirements **verbatim** — the whole Requirements section of the
input file, or the inline text if there was no file — and cite the source path.
Never paraphrase: this is what `/review` checks the plan against, so a
requirement lost here is lost silently and permanently.

## Requirements

Functional requirements, then an explicit **Non-goals** list. Naming what you are
deliberately not building is a stronger signal than building it. If `CLAUDE.md`
has a deferred/out-of-scope list, start from it.

## Entities & Data Models

Fields, types, constraints, invariants. State per entity whether it is a new
table or a change to an existing one, and what that implies for the repo's
migration story (see `CLAUDE.md`).

## API & Interfaces

Signatures, input types, return types, error codes. These are contracts —
implementation must not silently diverge from them.

## Data Flow

Mermaid diagram of the request path. Skip it when the path is the repo's
standard one; draw it only when the feature departs from that.

## Trade-offs

| Decision | Rejected alternative | Why |
Every non-obvious choice goes here. This table is where senior judgment lives.

## Milestones

Sequential, and **ordered so that every milestone ends in something demoable** —
not merely compiling. Assume the work may be cut off at any milestone boundary:
whatever is finished must be a coherent thing you can show end-to-end, not a
half-built subsystem. Prefer a thin vertical slice first over a complete backend
with no frontend.

Each milestone must also end with the system coherent: tests passing, nothing
half-wired. For each:

- **Scope** — what changes, in terms of contracts, not step-by-step procedure
- **Done when** — observable success criteria
- **Tests** — happy path, edge cases specific to this domain (not generic
  null-checks), and regressions to guard if touching existing behavior
- **Est. size** — should read as a single reviewable PR: system coherent,
  main stays green, one sitting to review. Target ≤400 changed lines
  including tests; if it won't fit, split the milestone
- **Verification** — the exact commands that prove it, taken from `CLAUDE.md`.
  Include any conditional steps the repo needs (regenerate types, reset a dev
  DB, run a migration) and say what triggers each

## Rules

- Every milestone must be estimatable at ≤400 changed lines including tests.
  If a milestone exceeds this, split it — do not write it as one milestone
  with a note that it's large. Generated files, lockfiles, and migrations
  don't count toward the estimate; `CLAUDE.md` says which files are generated.
- Contracts, not choreography: never write "create file X then add method Y".
  The implementer decides procedure at implementation time.
- Prefer the minimal design that satisfies requirements. Flag any speculative
  generality in Trade-offs as rejected.
- If exploration reveals the feature conflicts with existing architecture,
  say so before writing the plan.
- Plan docs are committed, and so are requirements files. Do not write anywhere
  else under `docs/` — the rest is private scratch.
- Every numbered requirement in the ask must end up either in the contracts or
  explicitly under Non-goals. Dropping one silently is the failure mode this
  structure exists to prevent.
