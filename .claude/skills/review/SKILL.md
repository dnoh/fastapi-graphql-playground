---
name: review
description: Parallel fresh-context subagent review of the current diff against the plan and a general engineering checklist
argument-hint: "<plan-doc-path> [git-range]"
---

Scope: $ARGUMENTS (plan doc path; optionally a git range — default: diff vs main)

This skill is project-agnostic. Repo conventions come from `CLAUDE.md`; the
general engineering checklist is `checklist.md` next to this file.

Launch four subagents with the **Agent** tool, all in a **single message** so they
actually run concurrently — separate messages run them serially and you lose the
point of the fan-out.

Use `subagent_type: "general-purpose"` and `model: "opus"` — review is judgment
work and is worth the stronger model even when the session is on something faster.
**Never `"fork"`** — a fork inherits this
session's full conversation history, which is exactly what this skill exists to
avoid. Each subagent gets ONLY: the diff, the plan doc path, the path to
`CLAUDE.md`, and its brief below. Fresh eyes are the point.

**Reviewer 1 — Correctness against the plan.** Does the diff implement the
milestone's contracts and success criteria exactly? Any silent divergence from
documented interfaces, data models, or error codes? Are the doc's listed tests
actually present and meaningful? If `CLAUDE.md` names generated files or a
migration step, were they actually regenerated / run — or is the diff green only
on one side?

**Reviewer 2 — Design.** KISS/SOLID/YAGNI applied concretely: abstractions with a
single implementation, duplicated logic, responsibilities in the wrong layer,
dead code, speculative flexibility nothing uses. Judge against the conventions in
`CLAUDE.md`, not generic taste.

**Reviewer 3 — Safety.** Error handling and input validation at boundaries,
transaction correctness and atomicity, race conditions, backward compatibility
with existing callers and stored data. Expected failures should surface through
the repo's error convention, not leak raw exceptions.

**Reviewer 4 — Checklist.** Read `checklist.md`. For each section, decide whether
it applies to this diff at all; skip the ones that don't. For the ones that do,
check each item and report **only concrete misses with a file:line** — never
"consider adding…" boilerplate. An item that applies and is handled is silence.

## Output

Merge and dedupe findings. Rank: BLOCKER / SHOULD FIX / NIT. Each finding
needs file:line and a one-line rationale. Report only — do not fix anything
without the user's go-ahead. If reviewers disagree, present both views
rather than averaging them.

## When to use something else

This skill's unique value is Reviewers 1 and 4 — a diff checked *against a plan's
contracts* and against a standing checklist. Reviewers 2 and 3 overlap the
built-in `/code-review`, which has better tooling for those lanes (verification
pass, inline PR comments, `--fix`). With no plan doc in play, prefer
`/code-review high`.
