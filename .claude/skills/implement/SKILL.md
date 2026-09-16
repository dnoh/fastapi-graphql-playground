---
name: implement
description: Implement a plan step by step — build, test, inspect, compare, review, record evidence — and ask the human only at each checkpoint
argument-hint: "<design-doc-path> [step e.g. 1.2] [propose first]"
disable-model-invocation: true
---

Input: $ARGUMENTS — the design doc path (`docs/plans/<slug>.md`), which holds the
behaviour and decisions. The task file is `docs/impl/<slug>.md` — same file name,
sibling folder — and holds the exact contracts, the flows, each **step**'s block,
and progress. Steps are grouped into **checkpoints**: the agent verifies and
records evidence for every step, but asks the human only at the end of a
checkpoint. An optional step number (`1.2`) says where to start; the default is
the first unchecked step. Budget, as guidance: about two minutes to implement a
≤300-line step; verification, inspection, and the report are what remain.

This skill is project-agnostic. Commands and conventions come from the repo's
`CLAUDE.md` — in particular its **"Before you say done"** section, which is the
verification loop this skill runs. Read it first. Never guess a command: if
`CLAUDE.md` is silent, discover it from the Makefile, package scripts, CI config,
or README, and say where you found it.

**Shipping is outside this loop.** Never commit, push, or open a PR on the user's
behalf.

## State lives in the docs, not in your memory

You may be starting with no memory of earlier steps. Read both docs fresh
at the start of every step. Two marks carry state in the implementation doc:

- `[x]` on a step heading means **agent verification passed** — automated
  checks and whatever inspection was available — and the evidence is written in
  that step's Evidence field. It does not mean the human accepted it.
- `Accepted <date>` beside a checkpoint heading means the human answered
  "continue" at its gate. Pending human checks stay visible in the report until then.

**The working tree is shared with the user.** Before editing, look at
`git status` and `git diff` to identify their uncommitted changes; preserve them,
and keep this step's changes separable from them where possible. An
uncommitted tree is normal and does **not** mean the previous step is
unfinished.

**Blocked states — stop and say so, do not improvise:** the code contradicts a
checked-off step; a dependency the step needs is missing or cannot be
installed; a required verification step cannot run in this environment; the
step's files carry user edits that conflict with the planned change; the
design doc is still `Draft`. Each is a question for the user, not a guess.

## The loop — once per step; ask at the end of each checkpoint

1. **Read state.** The design doc's Overview and Goals, and its status line — if
   it still says `Draft`, say so and ask whether to proceed, because the human has not
   approved the design you are about to build. The task file's Contracts section
   and this step's block only. Then the current code the block names.
2. **Announce, then go.** In ≤5 lines: files touched, what changes, what tests
   prove it, rough size. Start immediately — the user reads it while you work and
   interrupts if the direction is wrong. **Exception:** if the invocation says
   "propose first", or the step is destructive (data loss, deleting a model,
   rewriting existing behaviour), present the plan and WAIT for approval.
3. **Implement.** The minimal, least-invasive change that satisfies this
   step's contracts. **Run steps concurrently when the task file says they are
   `Parallel with` each other** — dispatch one agent per step, each given its own
   step block plus the Contracts section, and each writing only the paths in its
   `Owns` list. Verify once after they all return, never inside a parallel agent:
   `make verify` contends for the database file and the generated schema. If two
   steps' `Owns` sets overlap, or a step has no `Owns` list, run them serially.
   **Agents never touch the task file or the design doc**: they return their
   results, and the orchestrator writes every Evidence field and flips every
   checkbox — two agents editing one file is the collision `Owns` exists to prevent. Follow `CLAUDE.md` and existing conventions over
   preference. Stay within ~500 changed lines including tests (plan targets 300;
   the rest is slack). Generated files and lockfiles don't count. If it won't fit,
   stop and propose a split.
4. **Test.** Write the tests in the step's Tests table, except where an
   existing test already proves the criterion — cite it instead. **Format first:**
   run the repo's formatters on the files this step created or changed
   (`CLAUDE.md` or the Makefile say which — a `make fmt` target if there is one).
   They are your own files, so this is on demand, not automatic; it turns a
   formatting-only failed round into nothing. **Format after a file's edits are
   finished, never between them**: formatters rewrap arguments and reorder
   classes, so a string anchor captured before formatting silently matches
   nothing afterwards. Never patch with a bare replace that cannot fail loudly. Then the "Before you say done"
   loop: use the repo's verification runner when it has one, run dependent
   checks in order, run independent checks concurrently only when they do not
   contend for shared state (a database file, a port), and capture each outcome.
   Include every conditional step whose trigger applies. Never weaken or delete
   a failing test to make it pass; report it.
5. **Inspect.** Exercise the real behaviour where tooling allows — start the app,
   send the request, load the page — not only the tests. Tests prove the contract;
   inspection catches wiring, layout, and persistence across a refresh.
6. **Compare.** Check what you built against the implementation doc's contracts
   and the design doc's intent. The approved contract wins: **fix the code to
   match it.** If the contract itself must change — the design was wrong, or
   reality disproved an assumption — stop and get approval via
   **AskUserQuestion** before editing either doc; then update both. A different
   but equivalent way of meeting the same contract is not a deviation — note it
   under Evidence. Never rewrite a requirement to fit what was built.
7. **Review.** Run `checklist.md` (beside this file) against the diff — only the
   sections whose *Applies when* holds. Every finding is a concrete miss with a
   file:line, not advice. Fix what is in this step's scope; report the rest.
8. **Re-verify.** Any fix in step 6 or 7 invalidates earlier results. Rerun the
   checks the fix could affect, plus every mandatory repository gate, after the
   **last** code change. Verification is the final thing that happens to the code.
9. **Persist evidence, then mark.** Write **five lines** into the step's
   Evidence field in the task file: verification result and test count · live
   checks passed · fixes applied (review or contract) · not covered · size vs
   plan. Not a copy of the report. Then flip `[ ]` to `[x]` there; when it is the
   checkpoint's last step, set that checkpoint's Status in the design doc's
   Delivery table. Evidence first, mark second — a fresh context must never see
   "done" without the proof beside it.
10. **Report — only at the end of a checkpoint.** If this step is not the last
    in its checkpoint: no report; announce the next step in one line and return
    to step 1. If it is: under ~20 lines, in the format below, covering every
    step in the checkpoint — one combined Tests table and the manual flows for
    the whole slice. The report is for the human at the gate; the Evidence field
    is for the next context.
11. **Ask — only at the end of a checkpoint.** After the report, via
    **AskUserQuestion**, exactly one question — continue to the next checkpoint,
    stop here, or reopen this one. Never proceed past a checkpoint without an
    answer. The user reviews the report and walks the manual tests before
    answering; that is the point of the gate. On "continue", write
    `Accepted <date>` beside the checkpoint heading and return to step 1. When
    the last checkpoint is accepted, report against the Goals' acceptance
    criteria in the design doc and stop.

    The docs hold all state, so the user may stop and resume in a fresh context at
    any gate. Recommend that only when it helps: after a long investigation,
    after accumulated failed attempts, or at a substantial task boundary.
    Otherwise, related steps in the same context keep useful knowledge of
    the code just touched — say so and offer to continue.

## Report format

**1. Verification** — one line when everything is green, naming what ran:
`reset-db ✅ (model added) · verify ✅ 39 tests · build ✅`. A table only if a
step failed or was skipped for a reason worth reading.

**2. Tests** — the tests **added or changed this step**, and what each
proves. The reviewer reads this instead of opening the test file. Regression
rows for untouched suites are one line: "accounts (14), messages (7) unchanged".

| Test | Asserts | Case |
|---|---|---|
| `test_overdraft_is_rejected` | `INSUFFICIENT_FUNDS`, balance unchanged, no ledger row | edge |

Case is `happy` / `edge` / `invariant` / `regression`. If a step criterion has
no test behind it, say so in its row.

**3. Manual test instructions** — what the user should do before answering the
gate. Always the happy path and at least one failure path. Rows are the ⬜
flows that need a human; what you exercised yourself in step 5 is one summary
line above the table ("exercised live: register, lookup, duplicate handle,
unknown number"), not rows.

| Flow | Steps | Expected | Verified |
|---|---|---|---|
| Overdraft | pick account → Debit → amount > balance → Post | inline error with code; balance unchanged | ✅ |

**4. Not covered** — what neither the tests nor the manual flows exercise, in one
bullet each, so the user knows exactly what they are trusting. Rows marked ⬜
above are pending human acceptance; list them here too.

Then at most 3 bullets: contract changes approved this checkpoint (and equivalent
implementation choices noted), review findings left open, and the change size if
it overran the estimate. Nothing else.

## Constraints

- No drive-by refactors outside step scope. Note them for the user.
- Never hand-edit generated files to make things line up — run the generator.
- Respect the repo's layer boundaries as `CLAUDE.md` states them.
- A step is never marked complete with a failing verification step.
