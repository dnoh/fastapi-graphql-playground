# CLAUDE.md

Conventions for working in this repo. Read this before adding a feature.

## Active path

**FastAPI + Strawberry GraphQL → SQLite**, consumed by **Next.js + Apollo**.
Run every command from the repo root.

**Out of scope — do not touch, do not extend:**

- `backend-python/src/app/api/rest/` and `backend-python/src/app/schemas/message.py` —
  a REST surface left over from the original scaffold. The frontend never calls it.
  It has a known route-ordering bug (`/{message_id}` shadows `/latest/`); leave it.

The API is GraphQL. If a task needs a new endpoint, it is a GraphQL field, not a route.

## Commands

| Command | What it does |
|---|---|
| `make dev` | both servers, one terminal (Ctrl-C stops both) |
| `make backend` | API only → <http://localhost:8080/graphql> |
| `make frontend` | UI only → <http://localhost:3000> |
| `make verify` | **the whole loop below in one command (~7s)** — codegen + lint-check + test + check + test-fe |
| `make test` | backend pytest suite |
| `make test-fe` | frontend Vitest suite |
| `make check` | frontend ESLint + Prettier + `tsc --noEmit` |
| `make lint` | ruff format + autofix (backend) — **on demand only, never automatic** |
| `make lint-check` | ruff read-only; rewrites nothing. Inside `verify`, and what CI runs |
| `make fmt` | `lint` + frontend Prettier — for files you just wrote, before `verify`; still on demand |
| `make schema` | export GraphQL SDL to `frontend/schema.graphql` |
| `make codegen` | `schema` + regenerate TS types (no running server needed) |
| `make reset-db` | drop the dev DB — **required after any model change** |
| `make stop` | force-free ports 8080 / 3000 |
| `make doctor` | verify/rebuild the backend venv |
| `make install` | first-time setup (uv sync + npm install) |

`dev`, `backend`, and `test` run `doctor` first, so a stale venv repairs itself.
Prefer these targets over raw `uv run` / `npm run` so the venv check always happens.

## Adding an entity — follow in order

1. **Model** — `backend-python/src/app/models/`, SQLAlchemy 2.0 typed `Mapped[]`.
   Inherit `Base` (`models/base.py`) for `id` / `created_at` / `updated_at`.
2. **Service** — `backend-python/src/app/services/<entity>.py`. Copy the shape of
   `services/messages.py`. All business rules, validation, and the `commit()` live here.
3. **GraphQL type + `Input`** — `backend-python/src/app/api/graphql/schema.py`.
4. **Resolver** — same file. Thin: unwrap args, call the service, return.
   Decorate with `@domain_errors`.
5. **Document** — `frontend/src/graphql/queries.ts` (`gql` template).
6. **`make codegen`** — regenerates `frontend/src/generated/graphql.ts`.
7. **Component** — `frontend/src/components/`, built on the generated hook.
   `components/ui/Feedback.tsx` already provides `Loading`, `ErrorBanner`, `errorCode`.
8. **Test** — `backend-python/tests/`. See `tests/test_messages.py` for both the
   HTTP-level and service-level patterns; `conftest.py` gives a temp-file SQLite DB per test.
9. **`make reset-db`** if step 1 changed an existing table.

## Conventions

**Money is integer minor units (cents).** Never floats, never `Decimal` columns —
SQLite has no real `NUMERIC`. Format for display in the frontend only.

**Never build SQL from strings.** SQLAlchemy `select()` / `Mapped` columns are
parameterized; `text()` with an f-string is not. There is no legitimate reason to
reach for the latter here.

**Every mutation takes a single `Input` type.**
`createMessage(input: CreateMessageInput!)` is the template. No loose argument lists.

**Services own the transaction boundary and are the only place that calls
`session.commit()`.** Resolvers never commit. For a multi-step operation (a transfer:
debit + credit + ledger row) do every write, then commit once.

**Expected failures raise `DomainError(message, code="...")`** from
`backend-python/src/app/errors.py`. The `@domain_errors` decorator maps it to a GraphQL
error carrying `extensions.code`, which the frontend branches on. Add a **new code**, not
a new exception class.

**Never add `Base.metadata.drop_all()`.** It used to run at import; combined with
`uvicorn --reload` it wiped the database on every file save. `main.py` now creates and
seeds inside a `lifespan` hook, and the seed is idempotent.

**`create_all()` is `CREATE TABLE IF NOT EXISTS`** — it does *not* add columns to an
existing table. Change a model ⇒ `make reset-db`. There are no migrations; that is a
deliberate omission for a dev-scale app, not an oversight.

**Never hand-edit `frontend/src/generated/graphql.ts`.** Run `make codegen`.
It reads the committed SDL in `frontend/schema.graphql`, so no server needs to be up.
`codegen.ts` sets `strictScalars`, so a new custom scalar fails the build until you add it
to the `scalars:` map — do that rather than letting it become `any`.

**Config comes from env, not literals.** Backend: `src/app/config.py`
(`DATABASE_URL`, `CORS_ORIGINS`). Frontend: `src/env.js` (`NEXT_PUBLIC_API_URL`), which
is zod-validated — add new variables to both `client`/`server` and `runtimeEnv`.

**Ports.** Next.js silently hops to :3001 when :3000 is busy; CORS already allows any
`localhost` port, so that keeps working. `make stop` frees both.

## Before you say done

Run `make verify` from the repo root. It is steps 2-4 below plus `make lint-check`,
in one command, and CI runs that same target — so local green and CI green mean the
same thing. Step 1 is yours to judge: `verify` never drops your database.

`/implement` runs exactly this.

1. `make reset-db` — **only if a model changed.** `create_all()` is
   `CREATE TABLE IF NOT EXISTS`; without this you get `no such column`.
2. `make codegen` — **only if the GraphQL schema changed.** Regenerates
   `frontend/schema.graphql` and `frontend/src/generated/graphql.ts`. Skipping it is the
   top way a change reports green while the frontend is broken: backend tests pass on
   the new schema while the UI is still on the old types.
3. `make test` — backend suite.
4. `make check` — frontend ESLint, Prettier, and `tsc --noEmit`. Not optional: it is
   the only thing that type-checks the generated hooks against the components.

If `make check` fails on formatting alone, `cd frontend && npm run format:write`
fixes it. If `make lint-check` fails, `make lint` fixes it. Neither is a code defect.

**Generated files** (never hand-edit; don't count toward change-size budgets):
`frontend/schema.graphql`, `frontend/src/generated/graphql.ts`.

**Layer boundaries:** services own the transaction boundary and are the only place
that commits; resolvers unwrap args, call a service, return. Expected failures are
`DomainError(msg, code=...)`, surfaced as `extensions.code`.

**Templates to copy:** `services/messages.py` (service), `api/graphql/schema.py`
(type + input + resolver), `tests/test_messages.py` (HTTP-level and service-level tests).

## Stack gotchas — read before writing code, not after a failed `verify`

Each of these cost a debugging cycle once. They are properties of this stack, not
mistakes anyone reasons their way to.

**SQLAlchemy orders INSERTs by relationship, not by foreign key.** A child row whose
model has no `relationship()` can be inserted before its parent, and the FK fails.
Either declare the relationship, or `db.flush()` the parent first — still one
transaction, because flush is not a commit.

**Uvicorn configures only its own loggers.** `logger.info(...)` from `app.*` goes
nowhere until something calls `logging.basicConfig`. `main.py` does; do not remove it,
or every audit line silently vanishes while the code looks correct.

**Strawberry logs every GraphQL error as an ERROR with a stack trace**, including
expected `DomainError`s. `api/graphql/schema.py` subclasses `strawberry.Schema` and
overrides `process_errors` so expected failures log one line and real bugs keep their
traceback. A wrong password must not print a stack trace.

**SQLite discards `tzinfo` and returns naive datetimes.** `DateTime(timezone=True)`
does not change this. Comparing a value read from the database against
`datetime.now(UTC)` raises `TypeError`. Store naive UTC and compare with
a small `utcnow_naive()` helper. Put the offset back at the API boundary
(an `_as_utc` helper), because a bare timestamp is parsed as *local* time by the browser.

**`BEGIN IMMEDIATE` fails inside an open transaction.** SQLAlchemy opens one on the
first SELECT and keeps it open, and the request context has already read the session
cookie. the money write helper rolls back immediately before its BEGIN;
that rollback is the guarantee, not the one in `get_context`.

**The default SQLite pool caps at 15 connections** (QueuePool, size 5 + overflow 10).
A test fanning out wider queues on the *pool* instead of on SQLite's write lock, so it
proves nothing. Concurrency tests build their own engine with `poolclass=NullPool`.

**Generated GraphQL enums are TypeScript enums, not strings.** `movement.kind ===
"FUND"` is an ESLint error. Import the generated enum and compare against its member.

## Active domain rules

Domain rule-sets live in `.claude/domains/` and are switched on per feature with an
import line below. A domain recurs — every money feature gets the same money rules —
so add or remove an import; never rewrite rules inline here.

@.claude/domains/money.md

## Not in the scaffold — the plan decides, production-grade by default

The scaffold ships without auth, structured logging, metrics/observability,
migrations, cursor pagination, or Docker. That is a statement about
the *scaffold*, not a rule for features. When planning a feature:

- **Default: hold them to industry standard.** Auth and authorization, logging,
  metrics and observability, PII handling, migrations, failure handling — each gets a
  row in the plan's Cross-cutting table with one disposition: **Existing** (the repo
  already covers it — cite what, never rebuild), **Build**, **Not applicable** (say
  why), or **Deferred**.
- **Only the ask can defer** — by naming the concern out of scope, or by calling the
  work a prototype/MVP; the row cites the item number. Judgment still applies:
  "prototype" does not waive access control over real private data.
- **Ask when the ask is silent.** No mention of prototype vs production ⇒ `/plan`
  asks before writing; it never assumes either way.
- Domain-specific deferrals (row locking on SQLite, ledger design, …) live in the
  active domain file, not here.

## Workflow skills

`/plan <requirements-file>` → `/implement <design-doc>`, which builds one
checkpoint at a time and asks before each next one.

The skills are project-agnostic and reusable; **this file is the only place that
knows the stack, and `.claude/domains/` is the only place that knows the domain.**
They read "Before you say done" for the verification loop and this file's
conventions for layer rules.

**Input:** `docs/requirements/<name>.md` — a title plus the verbatim ask as one
numbered list, nothing else; start from `_template.md`. Your decisions become
Alternatives rows in the design doc, your questions are resolved in `/plan`'s
ambiguity step, and a rule the prompt forgot (overdraw, precision, idempotency)
becomes an inferred `I` row in the task file's Traceability table — never a new
section in the requirements file.

**Output: two docs per feature, in two folders.** `docs/plans/<slug>.md` is the
**design doc for the human** — a 2-minute read (≤800 words, diagrams excluded) with
a status/date header: Overview · Goals · Non-goals · Design · Alternatives ·
Cross-cutting · Risks · Delivery. No Open Questions section (the doc is not written
while one is open) and no SDL, SQL, or error tables (it explains; the task file
specifies). It is the only thing the human reviews. `docs/impl/<slug>.md` is the
**task file for the agent** — Traceability, the Contracts (entity tables, the SDL,
error codes, limits), the flow steps, and an Implementation Plan of `## Checkpoint N`
headings holding `### Step N.M — [ ]` blocks (Owns, Parallel with, Tests,
Verification, and an Evidence field of five lines that `/implement` fills); about
130 lines, written and read in silence, never linked from the design doc. Same file
name in both folders. Contracts live in the task file; the design doc explains them.
Budgets, as guidance: about five minutes to plan, about two to implement a ≤300-line
step.

**`/implement`** builds every step of a checkpoint in one pass: implement → test →
inspect → compare against the docs → review the diff with `checklist.md` → record
Evidence and mark each step → one report at the checkpoint gate (tests table, manual
test instructions, and what is *not* covered) → **ask** whether to continue. It never
proceeds past a gate without an answer, and never commits; shipping happens outside
the loop. Add "propose first" to gate before any code is written. A checkpoint is a
vertical slice — API *and* UI — that demos on its own. Steps are planned at ≤300
changed lines and implemented with a ceiling of ~500; generated files don't count.

**Model per phase.** Skills cannot pin a model, so switch with `/model` between
phases: Fable for `/plan` (fast, and a plan is cheap to redo), Opus for
`/implement` and the demo.

## Deliberately not included

Alembic, auth, cursor pagination, structured logging, Postgres, and Docker
are absent from the *scaffold*. Do not add them to the scaffold speculatively; a
feature plan adds whichever its Cross-cutting table decides — see "Not in the
scaffold" above.

Also **no Python type checker and no coverage**, and the first one is a real decision
rather than laziness: mypy and ty both flag the resolvers in `api/graphql/schema.py`
for returning SQLAlchemy models where the annotation promises Strawberry types. That
is the pattern every new entity copies, so a checker costs one error and one
conversion layer per resolver. Turn it on only after changing the pattern.
