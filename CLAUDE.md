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
| `make test` | backend pytest suite |
| `make check` | frontend lint + `tsc --noEmit` |
| `make lint` | ruff format + autofix (backend) — **on demand only, never automatic** |
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

The verification loop, in order, from the repo root. `/implement` runs exactly this.

1. `make reset-db` — **only if a model changed.** `create_all()` is
   `CREATE TABLE IF NOT EXISTS`; without this you get `no such column`.
2. `make codegen` — **only if the GraphQL schema changed.** Regenerates
   `frontend/schema.graphql` and `frontend/src/generated/graphql.ts`. Skipping it is the
   top way a change reports green while the frontend is broken: backend tests pass on
   the new schema while the UI is still on the old types.
3. `make test` — backend suite.
4. `make check` — frontend lint + `tsc --noEmit`. Not optional: it is the only thing
   that type-checks the generated hooks against the components.

**Generated files** (never hand-edit; don't count toward change-size budgets):
`frontend/schema.graphql`, `frontend/src/generated/graphql.ts`.

**Layer boundaries:** services own the transaction boundary and are the only place
that commits; resolvers unwrap args, call a service, return. Expected failures are
`DomainError(msg, code=...)`, surfaced as `extensions.code`.

**Templates to copy:** `services/messages.py` (service), `api/graphql/schema.py`
(type + input + resolver), `tests/test_messages.py` (HTTP-level and service-level tests).

## Active domain rules

Domain rule-sets live in `.claude/domains/` and are switched on per feature with an
import line below. A domain recurs — every money feature gets the same money rules —
so add or remove an import; never rewrite rules inline here.

@.claude/domains/money.md

## Deferred by choice — say it, don't build it

Each of these is a considered omission. Name the trade-off; do not implement it unasked:

- **Auth** — no users/sessions in the MVP. Out of scope, deliberately.
- **Migrations** — `create_all` + reseed in dev; Alembic in production.
- Domain-specific deferrals (row locking, ledger design, …) live in the active
  domain file, not here.
- Also deferred: cursor pagination, structured logging, observability, frontend tests,
  Docker.

## Workflow skills

`/plan <feature>` → `/implement <plan-doc> <n>` → `/review <plan-doc>`.

The skills are project-agnostic and reusable; **this file is the only place that
knows the stack, and `.claude/domains/` is the only place that knows the domain.** They read "Before you say done" for the verification loop and
this file's conventions for layer rules.

`/plan` writes contracts and milestones to `docs/plans/<slug>.md` (committed; the
rest of `docs/` is private scratch). `/implement` does **one** milestone per
invocation — announces its intent, proceeds, stops when verified; add "propose first"
to get a blocking approval gate. `/review` fans out four fresh-context subagents:
plan-correctness, design, safety, and the general `checklist.md` that ships with the
skill. Milestones are planned at ≤400 changed lines and implemented with a ceiling of
~500; generated files don't count.

**Model per phase.** Skills cannot pin a model, so switch with `/model` between phases:
Fable for `/plan` (fast, and a plan is cheap to redo), Opus for `/implement` and the
demo. `/review` pins its own subagents to Opus regardless of the session model, so it
needs no switch.

## Deliberately not included

Alembic, auth, cursor pagination, structured logging, Postgres, Docker, frontend tests.
Don't add them speculatively.
