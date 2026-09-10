---
name: plan
description: Ask, investigate, and write a one-page mini design doc a human can read, plus a task file of contracts and steps — in about five minutes
argument-hint: "<requirements-file-path | feature description>"
effort: high
---

Feature to plan: $ARGUMENTS

You are responsible for planning an implementation before any code is changed.
Understand the requested product/feature, investigate the existing codebase, and
produce an implementation-ready design. **Do not implement code during this phase.**

**Input** is a path to `docs/requirements/<name>.md` — a title plus a `## Context`
section holding the ask verbatim as one numbered list — or an inline description,
which you first write into that shape from `_template.md`. **Output** is two files,
each written once:

| File | Reader | Budget |
|---|---|---|
| `docs/plans/<slug>.md` | the human — a **mini design doc** in the Google / Microsoft task-design-review shape | **800 words, diagrams excluded** — everything else counts: prose, tables, headers, status line. Per-section guides below sum to ~700. Diagrams are free but each must earn its place |
| `docs/impl/<slug>.md` | `/implement` — the task file: traceability, exact contracts, flow steps, step blocks, evidence. The human never reviews it | **~130 lines.** Only what feeds a check or a fresh-context resume |

**The design doc explains; the task file specifies.** Behaviour, goals, trade-offs,
and risks live in the design doc in plain sentences. Requirement traceability,
schemas, SDL, error codes, SQL, limits, and tests live in the task file. Neither
restates the other. A design doc is not an implementation manual: if it mostly
says *how* without *why* and *what else was considered*, it has failed. The task
file may elaborate a design-doc decision; it may never introduce behaviour the
design doc does not show. Once approved, both are what `/implement` builds to; a
material change needs the user's approval before either changes. Everything repo-specific — stack,
commands, layout, conventions, domain rules — comes from `CLAUDE.md`. Read it
first. If it is silent on a command, discover it from the Makefile, package
scripts, CI config, or README rather than guessing.

**Budget, as guidance:** about five minutes to ask, investigate, and write both
files. Time goes to checks and contracts, never to prose nobody consumes.

**Stopping rule.** Planning is complete when the behaviour and every consequential
decision are settled, and each step has a clear starting point and a
verification path. It does **not** eliminate every lookup during implementation:
finding the right helper or deciding how to organise a function is ordinary
implementation work. When the rule is met, write the files and stop.


## Process

1. **Understand the request.** Read the ask and `CLAUDE.md`. The user/product
   problem; the desired behaviour in concrete terms; acceptance criteria; explicit
   non-goals. Every numbered item in the ask is traced in the task file's
   Traceability table — none may silently vanish; the design doc's Goals cite the
   item numbers in passing, never as a table.
2. **Resolve ambiguity now, in proportion to its consequence.** The questions are
   almost always about the ask, not the code, so ask before investigating and
   design on answered ground. Separate **Known facts**, **Assumptions**, **Open
   questions**; answer from `CLAUDE.md` and the requirements what they can answer;
   then sort what remains:

   | Ask the user before proceeding | Choose a reasonable default and disclose it |
   |---|---|
   | ambiguous user-visible behaviour | internal function or file organisation |
   | two requirements in conflict | following an existing repository convention |
   | data loss or an incompatible contract | a reversible implementation detail |
   | new infrastructure, a new dependency, or meaningful cost | equivalent ways to implement the same contract |
   | access rules that cannot be inferred | minor presentation choices |
   | prototype vs production, when the ask is silent | |

   The left column goes to the user via **AskUserQuestion** — up to four per
   round, and further rounds when answers raise new left-column questions. The
   right column is decided and recorded as default rows in the design doc's
   Alternatives table; the user overrides at approval. If investigation or
   drafting later surfaces a new left-column question, ask before finalising.
3. **Investigate the repository — in one pass.** Read, in a single call, the
   files `CLAUDE.md` names as templates to copy plus the files the ask touches:
   models, services, API, tests, the UI component it replaces or extends. Trace
   current behaviour from those; then stop. Determine the patterns to reuse and
   cite files and symbols inline, in the step that touches them, not in a
   separate section. Do not propose a new abstraction until you understand the
   existing ones. Skim `../implement/checklist.md` once and note which sections
   apply. Anything you still want to know at this point is a lookup the
   implementer makes in seconds; do not plan it.
4. **Recognise the domain; label the inference, not the domain.** Match the ask
   against the table below. It lists **failure modes to check**, not rules to
   apply: adopt one only when the ask, an existing repository contract, or a
   correctness property the feature cannot do without supports it. If `CLAUDE.md`
   imports a rules file for the domain, that file is authoritative. An adopted rule
   the ask never stated becomes an inferred `I` row in Non-functional requirements
   with its reason, and from there a constraint in the data model, a step in the
   flow, and an `edge` or `invariant` test where it applies. The inference is
   always visible; the domain label is not — the reader sees "a debit may not take
   the balance below zero (I1)", never the word "money". Check both a primary
   domain and any cross-cutting one.

   | Tells in the ask | Domain | Failure modes to check |
   |---|---|---|
   | transfer, balance, wallet, payment, refund, credits | money | balance driven negative where the product forbids it; a movement committed in two halves; a retry applied twice; a movement with no record |
   | stock, cart, checkout, quantity, seats, tickets | inventory | overselling under concurrent checkout; a hold that never releases; a count updated by read-then-write |
   | appointment, slot, calendar, room, shift | scheduling | double-booking — fixed slots need uniqueness, arbitrary intervals need an overlap check that is itself protected against concurrent bookings; naive time zones |
   | status, lifecycle, approval, workflow, cancel | state machine | an illegal transition; transitions defined in several places; a transition applied twice; no record of who changed state |
   | store, organization, workspace, "each X sees only" | multi-tenant | a query that forgets the tenant filter; scoping only in the UI; guessable cross-tenant ids |
   | profile, email, address, mask, conceal | PII | storing more than needed; exposing it in an unauthorised view, a log, or a URL; deletion that does not delete |
   | send, notify, webhook, email, retry | delivery | duplicate sends on retry; an external call inside a DB transaction; a commit whose delivery was lost — outbox or reconciliation when the contract needs it |

   A plain CRUD ask matches no row; design it as CRUD. "Create order" is CRUD until
   it has quantity, payment, a status, or a store — then check those rows.
5. **Determine constraints and cross-cutting concerns.** Existing API/contracts
   that must stay compatible; data-model and migration implications; concurrency
   and idempotency; security and privacy; performance; failure behaviour; rollout
   or feature-flag needs.

   **The default is production-grade.** Auth and authorization, structured
   logging, metrics and observability, PII handling, migrations, and failure
   handling are held to industry standard. Each gets a row in the **Cross-cutting**
   table with exactly one disposition and the reason:

   | Disposition | Meaning |
   |---|---|
   | Existing | the repo's current infrastructure already covers it — cite what; never rebuild it |
   | Build | this change needs additional work to meet the standard |
   | Not applicable | the concern does not arise for this change — say why in one clause |
   | Deferred | relevant, and explicitly outside this delivery — cite the ask item that defers it |

   Only the ask can defer — by naming the concern out of scope, or by calling the
   work a prototype or MVP. Even then, apply judgment: "prototype" does not waive
   access control over real private data, and a small feature does not need new
   metrics infrastructure to count as production-grade. Every concern stays
   visible whatever its disposition — but in the design doc, group them on four
   lines by disposition (`Build: authz, logging, PII · Existing: migrations ·
   Not applicable: performance · Deferred (item 4): authentication, metrics`).
   Do not force a table for concerns the feature does not touch. Label accurately:
   `create_all` plus a dev reset is *schema initialisation on disposable data*, not
   a migration strategy; a concern you bounded (page sizes, indexes) is *bounded*,
   not "not applicable".

   **Checks the design must answer before it is done** — each is a past miss:
   - A per-operation bound does not bound the accumulated value. If the wire type has
     a ceiling (GraphQL `Int`), every credit is conditional on that ceiling, not documented.
   - Wherever idempotency keys exist, the **client retry contract** is part of the
     design: reuse the key after a timeout or uncertain result, mint a new key for a new
     intent, and say whether a rejected request reserves its key.
   - Concurrency names how a write transaction is **acquired** (`BEGIN IMMEDIATE` on
     SQLite, `SELECT … FOR UPDATE` on Postgres), how busy/lock failures are bounded, and
     is proven by a **threaded test against the engine actually in use**. "The engine
     serialises writers" is not a design.
   - Any explicit transaction statement (`BEGIN IMMEDIATE`, `SET TRANSACTION`, a
     manual `BEGIN`) says **what transaction state the session is in when it runs**.
     SQLAlchemy opens a transaction on the first SELECT and keeps it open, so a
     request-context lookup that runs before the service leaves one open, and a
     second BEGIN fails. Say which of: the context ends its read with a rollback,
     or the driver runs with `isolation_level=None` and a begin event emits the
     statement, or the service uses its own session.
   - Simulated inputs — funding that mints money, seeded identities — are labelled
     simulated, with who may invoke them and the cap.
   - Conservation is stated precisely: which operations preserve the sum, which change
     it by exactly their amount, and that each balance reconciles to its own ledger.
6. **Design the solution.** The smallest coherent implementation that satisfies the
   requirements. Prefer existing abstractions, incremental changes, simple designs,
   reversible changes. Avoid unrelated refactors, speculative abstractions,
   duplicated logic, premature generalisation. For each meaningful decision, name
   the alternative and why the chosen one wins. A new package, service, or piece of
   infrastructure is such a decision — it appears with the existing tool it beats,
   or it does not happen.
7. **Describe the flow — only where it is not the standard path.** Numbered
   steps, one per line, with the error code each step can raise and which layers
   change. This goes in the task file; the design doc carries only the behaviour
   it implements, in sentences. A feature with no non-standard flow has no flow section.
8. **Produce checkpoints and steps.** A **checkpoint** is a vertical slice the
   user can use end to end — API *and* UI — and the only place the human is asked
   to review; aim for about three (access · funding and history · transfers is the
   shape for a money feature). Each checkpoint creates the tables it needs — a dev
   reset between checkpoints is free, so never front-load schema for later work.
   Inside a checkpoint, **steps** are the agent's units: coherent, independently
   verifiable, **≤300 changed lines** so each implements in about two minutes.
   **Split for concurrency wherever the contract allows it.** The SDL and the error
   codes are fixed before any code is written, so the server side and the client side
   of one checkpoint are independent work — give them separate steps with disjoint
   `Owns` sets and mark them `Parallel with` each other. Serial writing is the
   dominant cost of a large feature, and this is the only thing that removes it
   (generated files and lockfiles don't count; `CLAUDE.md` says which). Split
   steps on behaviour, risk, or dependency boundaries, never on line count alone;
   a step that cannot be split cleanly may run over with the reason stated. The
   agent verifies and records evidence for every step but asks only at the end of
   a checkpoint. When scope clearly exceeds the budget, propose a smaller useful
   slice or give a revised estimate — requirement count is not a complexity measure.
9. **Define verification per step.** The tests that prove it (unit, integration,
   edge, regression, and the threaded contention test where money moves), the
   exact typecheck/lint/build commands from `CLAUDE.md` with what triggers each
   conditional one, and the manual checks automation cannot reach — those belong
   to the checkpoint. All of it lives in the step block, nowhere else.
10. **Resolve risks; list only what remains.** For each risky assumption,
    regression surface, concurrency or failure mode, first ask: *would the
    production-standard choice remove it?* If yes, that choice is the default —
    an HttpOnly, SameSite cookie instead of a token in browser storage; a
    database CHECK instead of an app-only bound; a login attempt limit instead
    of a "rate limiting" non-goal; a test that guards an assumption instead of
    a sentence about it. "Prototype" does not lower this
    bar. If the production choice changes user-visible behaviour, cost, or
    scope, it is a **left-column question in step 2** with the production option
    recommended — never a Risks bullet the reviewer discovers later. What
    reaches the Risks section is only what no choice in this feature can remove
    (SQLite serialises writers; simulated funding mints money), each with its
    mitigation or the test that guards it. A Risks bullet that a design change
    could delete is a design defect.
11. **Completion criteria.** An explicit checklist for "the feature is complete",
    in the design doc.

## The design doc — `docs/plans/<slug>.md`

A **mini design doc**: the shape Google uses for a 1–3 page doc and Microsoft's
task design review — context, goals and non-goals, the design with its trade-offs,
alternatives, cross-cutting concerns, risks, open questions. Written for a human
who has not seen the code and will not open the task file. Do not link or mention
the task file; `/implement` finds `docs/impl/<slug>.md` by the shared file name.

```
# <Feature>
Status: Draft · Date: <YYYY-MM-DD> · Ask: docs/requirements/<name>.md

## Overview            ≤70 words. 2–4 sentences: the problem, who has it, what this delivers, and the one
                       constraint that shapes the design. Assumptions in one more sentence.
## Goals               ≤90 words. bullets — what the user can do afterwards, each with its acceptance
                       criterion in plain words; cite ask items in parentheses "(item 2)".
                       Every capability a Delivery checkpoint promises has a Goal bullet —
                       funding included when it exists
## Non-goals           ≤40 words. bullets — things that could reasonably be goals but are chosen not to be,
                       each with its reason ("prototype", "single currency"). Never a phrase that
                       reads as negating a built goal: if you build password login, the non-goal
                       is "SSO, refresh tokens, password recovery", not "auth infrastructure"
## Design              model paragraph ≤70 words; ≤40 words under each diagram; bullets ≤100.
                       One paragraph for the model. Then, for **each major flow** — every
                       user-facing operation that touches the store (sign-in, funding, transfer;
                       not a plain read) — one titled Mermaid sequence diagram of its
                       **successful path** with the transaction boundary marked, followed by at
                       most two sentences of what it guarantees. Then one bullet list, "Retries
                       and correctness": every failure behaviour and guarantee, one sentence
                       each — always including the client contract (one key per intent, reused
                       after a timeout) and the conservation statement. Branching, conflict recovery, and tests stay in the task file.
                       No schemas, no SDL, no SQL, no column lists, no error-code tables,
                       no file inventory.
## Alternatives considered   ≤80 words. table: Chosen | Instead of | Trade-off — 3–5 rows, the real
                       reason; no dates. Every answer the user gave in step 2 (identity,
                       funding, wire format, access) is a row, before any implementation trade-off
## Cross-cutting concerns    ≤50 words. four lines: Build · Existing · Bounded · Deferred (with the ask item)
## Risks               ≤50 words. residual risks only — see step 10. 2–3 bullets, each with its mitigation or its owner
## Delivery            ≤40 words. table: # | Checkpoint | You can then… | Status — the human gates only
```

There is no Open Questions section: the doc is not written while one is open
(step 2 and the stopping rule), so the section would always read "None".

**Readability rules — the last doc broke every one of these:**
- Sentences, not fragments. No `·`-chained lists inside a line, no "C2, C5, C7" id
  soup, no bold-label-colon sentences ("**Fund.** A user…"). Say "Retrying a
  request is safe" and put the item numbers in the task file.
- Backticks only for a name the reader must recognise in the UI or API
  (`transfer`, `me`); never for concepts, columns, constants, or SQL.
- One idea per sentence; a paragraph is three to five sentences; a section is at
  most two paragraphs.
- Numbers live in the task file's Limits unless they change what the user sees.
- Read it back as the reviewer: if a sentence needs the schema to make sense, it
  belongs in the task file.
- **Each diagram shows one flow's successful path only, and truthfully.** Failures are bullets,
  not `alt` branches — an `alt` block does not stop a Mermaid sequence, so branching
  diagrams lie. **Exactly three lanes, always named `Client`, `Server`, `Database`** —
  not Browser, not GraphQL API, not SQLite, and never a lane per internal layer;
  resolver and service are the Server lane. If engine behaviour matters (a
  SQLite write lock), say it in a note, not a lane name. Arrows
  carry plain words ("debit the sender if the balance covers it"), never SQL. On a
  successful path the idempotency step reads "confirm the key is unused" — never
  "return the earlier X if the key was used", which describes the replay path.
  Responses travel the path they take (the store never answers the browser). Mark
  where the transaction begins and commits with notes. Where a fast-path check is
  not the guarantee, the bullets say where the guarantee lives.
- Goals promise what the design delivers: "most recent movements, up to a limit",
  not "every movement", when paging is a non-goal. No absolute claims ("X is the
  production answer"); state the actual risk and what needs review.
- The what-is-new / what-is-extended inventory is task-file content, not design.

Write it to the one-page aim in one pass, in the same response as the task file.
**Draft to the per-section guides, then measure the total once.** The guides in
the template sum to about 700 words; write each section to its number as you go,
and the first draft lands inside the band without a trim phase. Headers, the
status line, and table pipes cost about 85 words, which the slack covers. Do not
draft to the shape of a previous plan.

Then measure once, the total only: `sed '/^```mermaid/,/^```/d' FILE | wc -w` for
the design doc, `wc -l FILE` for the task file. Never measure section by section.
**The numbers are a band, not a target:** a design doc under 800 words is done and
must not be trimmed; a task file under 200 lines is done when its entity tables
and SDL are what fill it. Only above that do you act, and the action is
**deleting whole items with targeted edits in one pass** — a bullet, an
Alternatives row, a Risk, starting with the section furthest over its guide —
never shortening sentences (40 words a pass) and never re-emitting the whole
file (a minute per pass, and the diagrams come out identical). Never delete a
diagram, a user decision, the client retry contract, the conservation statement,
or the token-storage risk when a token exists. One measure after the edits, then
stop.

The status line flips to `Approved` when the user accepts the doc; `/implement`
treats a Draft as not yet reviewed and says so.

## The task file — `docs/impl/<slug>.md`

Exactly this, and nothing else. It holds what `/implement` needs that the design
doc does not: the contracts, the flows, the per-step work, and durable progress.

```
# <Feature> — task file
Design: docs/plans/<slug>.md

# Traceability
table: Ask item | Requirement (verbatim, short) | Where it is met (contract / step / test) — every
numbered ask item and every inferred I-row with its one-clause why; consolidated rows may cite
several items; nothing from the ask is absent

# Contracts
entities — one table each: column | type | constraints (named CHECK / UNIQUE / FK), + the invariant
API — the GraphQL SDL block, exactly as it will be exported
errors — table: Code | Raised when
limits — the constants (caps, ceilings, TTLs, page sizes) with their values

# Data / Control Flow
<flow name>(input)
1. step                                   [ERROR_CODE]
…

# Implementation Plan
## Checkpoint 1 — <name>                  human gate at the end; `Accepted <date>` written here
### Step 1.1 — [ ] <name>
- Outcome:                  one line — what works afterward
- Owns:                     every file this step creates or edits, as paths. Two steps that can
                            run at once must share no path. This is the contract that makes
                            fan-out safe, so it is exhaustive or the step runs alone
- Parallel with:            the sibling steps whose Owns sets are disjoint from this one, or
                            `none`. Backend and frontend split cleanly once the SDL is pinned,
                            because the contract is written before either side is built. A
                            frontend step running parallel to its backend step cannot wait for
                            `make codegen` (it derives the SDL from Python that does not exist
                            yet): it writes the Contracts SDL to `frontend/schema.graphql` and
                            runs `npm run codegen` itself; the closing `make verify` proves the
                            backend emits the identical SDL. Say so in the step's Contracts line
- Touchpoints:              existing files, symbols, and patterns to copy or extend
- Contracts:                which of the Contracts above this step implements; anything step-local —
                            never "create file X then add method Y"
- Tests:                    table: Test | Asserts | Case (happy / edge / invariant / regression)
- Verification:             the repo's formatter then its single verification target (here
                            `make fmt` → `make verify`), plus the conditional steps CLAUDE.md
                            names with what triggers each (`make reset-db` on a model change,
                            `make codegen` on a schema change) — never the individual commands
                            the target already runs. Manual checks on the checkpoint's last step only
- Evidence:                 left empty by /plan; /implement fills five lines before marking
### Step 1.2 — [ ] …
## Checkpoint 2 — …
```

No repeated rationale, no pseudocode, no line-by-line editing instructions.

The `[ ]` on each step heading is progress state; `/implement` flips it to `[x]`
when its own verification has passed — human acceptance is recorded on the
checkpoint heading at the gate. Every step's Tests table has at least one `edge`
row per error code it introduces. It has a `regression` row for each existing
behaviour the step touches, citing the existing test when one already proves it —
an existing test that covers a criterion satisfies it, no new test is invented to
fill the table, and a brand-new component that touches nothing existing says
"none affected". Case vocabulary is the one `/implement` reports in.

Each step block is self-contained: `/implement` reads the Contracts section, the
design doc's Design section, and its own block — nothing else. Completeness is the
bar, not length — a block that makes the implementer re-derive a decision has failed.

## Rules

- **The design-doc budget is the rule everything else serves.** Over a cap means
  cut; never append a note apologising for length.
- Say each thing once. The ask lives in the requirements file: reference it, never
  restate it. Explanation lives in the design doc, specification in the task file;
  neither copies the other. Rationale is a clause, not a paragraph — and a reason,
  not a date.
- Contracts, not choreography. Minimal design; speculative generality is a rejected
  Alternative.
- If investigation reveals a conflict with existing architecture, say so before
  writing.
- Write only under `docs/requirements/`, `docs/plans/`, and `docs/impl/`.
- **Do not run this skill inside the harness's plan mode.** It forces the design
  doc to be written twice — once into the harness's plan file for approval, once
  for real. The approval gate is the design doc's `Status` line.
- Self-review as a senior before finishing: read the design doc top to bottom in
  under two minutes, once — and ask whether a reviewer who has never seen the code
  could say what the feature does, and why it is built this way, from the Design and
  Alternatives sections alone. Then check every step block
  names its tests and its commands — and stop. The stopping rule above is the definition of done for
  this skill.
