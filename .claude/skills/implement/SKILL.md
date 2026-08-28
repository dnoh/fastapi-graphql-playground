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
   change, a model change, a migration). **Chain the whole loop into one shell
   invocation** (`a && b && c && d`) rather than one call per step — the round
   trips are most of the wall-clock cost of this skill. Only re-run a step
   individually when it fails.
5. **Report.** Tables, not paragraphs. See "Report format" below.
6. **Close out.** Check off the milestone in the plan doc. If implementation
   forced any deviation from the doc's contracts, update the doc and flag the
   change loudly — silent divergence is the failure mode.

## Report format

Keep the whole report under ~30 lines. Three tables and nothing else. No
narrative summary of what you did — the tables say it.

**1. Verification loop** — one row per step, with whether its trigger applied:

| Step | Trigger | Result |
|---|---|---|
| `make reset-db` | model added | ✅ |

**2. Tests** — every test added this milestone, and what it proves. This is the
table the reviewer reads instead of opening the test file:

| Test | Asserts | Case type |
|---|---|---|
| `test_overdraft_is_rejected` | `INSUFFICIENT_FUNDS`, balance unchanged, no ledger row | edge |
| `test_balance_equals_credits_minus_debits` | denormalized balance == recomputed ledger | invariant |

Mark each `happy` / `edge` / `invariant` / `regression`. If a "done when"
criterion has no test behind it, say so in that row.

**3. Manual test flows** — what a human should click through before the next
milestone, because automated tests do not cover it. Always include at least the
happy path and one failure path:

| Flow | Steps | Expected |
|---|---|---|
| Overdraft | pick account → Debit → amount > balance → Post | inline error + code; balance unchanged |

Run these yourself where the tooling allows, and mark each row ✅ verified or
⬜ needs a human. Do not walk a flow in a browser that a test already covers
end-to-end — the manual pass is for what tests cannot see (layout, wiring,
persistence across refresh).

After the tables, at most 3 bullets: deviations from the plan's contracts,
anything left out, and the change size if it overran the estimate. Nothing else.

## Constraints

- Never weaken or delete a failing test to make it pass; report it instead.
- No drive-by refactors outside milestone scope. Note them for the user.
- Never hand-edit generated files to make things line up — run the generator.
  `CLAUDE.md` says which files are generated and how.
- Respect the repo's layer boundaries as `CLAUDE.md` states them (where the
  transaction boundary lives, what a handler may and may not do).
