---
name: implement
description: Implement one milestone from a plan doc, with announce-then-go and a verification loop
argument-hint: "<plan-doc-path> <milestone-number> [propose first]"
disable-model-invocation: true
---

Input: $ARGUMENTS (plan doc path and milestone number, e.g. "docs/plans/transfers.md 2")

This skill is project-agnostic. All repo-specific commands and conventions come
from the repo's `CLAUDE.md` — in particular its **"Before you say done"** section,
which is the verification loop this skill runs. Read it first; never guess a
command.

## Hard rule: one milestone per invocation

Implement only the named milestone, then stop. Do not continue to the next
milestone even if it seems easy. The user reviews, then re-invokes for the next one.

Committing between milestones is optional — do not assume it happened, and never
commit on the user's behalf. Under time pressure the user may also skip `/clear`
between milestones; that is fine, keep going with the context you have.

## Steps

1. **Read state.** The plan doc is the source of truth for progress — its milestone
   checkboxes say what is done, because the user may not be committing. Read the
   contracts and this milestone, then the current code it touches. `git log` and
   `git status` are supplementary hints only; an uncommitted tree does NOT mean the
   previous milestone is unfinished. Only stop if the *code* contradicts a checked-off
   milestone.
2. **Announce, then go.** State in ≤5 lines: files touched, what's added or modified,
   what tests will prove it, rough size. Then start working immediately — do not wait
   for approval. The user reads it while you work and interrupts if the direction is
   wrong, which is cheaper than a round trip on every milestone.

   **Exception:** if the invocation says "propose first", or the milestone is
   destructive (data loss, deleting a model, rewriting existing behavior), present
   the plan and WAIT for explicit approval before editing.
3. **Implement.** Minimal, least-invasive change that satisfies the milestone's
   contracts. Follow `CLAUDE.md` and existing codebase conventions over personal
   preference. Stay within ~500 changed lines including tests (plan targets 400; the
   extra is slack for estimation error). Generated files and lockfiles don't count.
   If it won't fit, stop and propose a split.
4. **Verify.** Run the repo's "Before you say done" loop from `CLAUDE.md`, in the
   order it gives, including every conditional step whose trigger applies (a schema
   change, a model change, a migration). Then check each "done when" criterion from
   the plan doc and report pass/fail **per criterion**, not just "tests pass".
5. **Close out.** Check off the milestone in the plan doc. If implementation
   forced any deviation from the doc's contracts, update the doc and flag the
   change loudly — silent divergence is the failure mode.

## Constraints

- Never weaken or delete a failing test to make it pass; report it instead.
- No drive-by refactors outside milestone scope. Note them for the user.
- Never hand-edit generated files to make things line up — run the generator.
  `CLAUDE.md` says which files are generated and how.
- Respect the repo's layer boundaries as `CLAUDE.md` states them (where the
  transaction boundary lives, what a handler may and may not do).
