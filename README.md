# FastAPI GraphQL Playground

A small full-stack app: **FastAPI + Strawberry GraphQL** backend, **Next.js + Apollo**
frontend, **SQLite** database. Built to add features fast without fighting setup.

## Quick start

```bash
make install     # one time — backend deps (uv) + frontend deps (npm)
make dev         # both servers; Ctrl-C stops both
```

| | |
|---|---|
| UI | <http://localhost:3000> |
| GraphQL + GraphiQL | <http://localhost:8080/graphql> |

The database is created and seeded automatically on first start. There is no `.env`
to write — the defaults work.

> **Where you clone matters.** Do not put this in an iCloud-synced folder
> (`~/Documents` or `~/Desktop` when "Desktop & Documents" sync is on). iCloud
> syncs `.venv` and `node_modules` file-by-file and can rename files on conflict
> (`_editable_impl_... 2.pth`), which intermittently breaks the virtualenv.
> Clone to something local like `~/code/` instead.

### Prerequisites

| Tool | Version | Install |
|---|---|---|
| [uv](https://docs.astral.sh/uv/) | ≥ 0.5 | `brew install uv` |
| Node | ≥ 20.9 (CI pins `.nvmrc`) | `brew install node` |

You do **not** need Python preinstalled — `uv` reads `requires-python` and downloads
CPython 3.12 itself.

## Commands

`make help` lists everything.

| Command | What it does |
|---|---|
| `make dev` | both servers in one terminal |
| `make backend` / `make frontend` | one at a time, in separate terminals |
| `make stop` | force-free ports 8080 / 3000 |
| `make verify` | **run this before you call anything done** — the whole loop, ~5s |
| `make test` | backend test suite |
| `make test-fe` | frontend Vitest suite |
| `make lint` | format + autofix the backend (ruff) — rewrites files, on demand only |
| `make lint-check` | the same checks read-only, rewriting nothing — what CI runs |
| `make fmt` | `lint` + frontend Prettier — for files you just wrote, before `verify` |
| `make check` | frontend ESLint + Prettier + `tsc --noEmit` |
| `make schema` | export the GraphQL SDL to `frontend/schema.graphql` |
| `make codegen` | regenerate TS types from the SDL (no running server needed) |
| `make reset-db` | drop the dev database — **required after any model change** |
| `make doctor` | verify the backend venv, rebuilding it if stale (runs automatically before `dev`/`backend`/`test`) |

## Verifying a change

```bash
make verify      # codegen + backend lint/tests + frontend lint/format/types
```

One command, about five seconds, and it is the same command CI runs. It exists
because the loop has an ordering trap: a schema change that skips `make codegen`
leaves the backend tests passing against the new schema while the UI still
compiles against the old types. Everything reports green and the app is broken.

`make reset-db` is deliberately **not** part of it. That target drops data, and
you only need it after a model change. Run it yourself, then re-run `verify`.

CI ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)) runs `make verify`
plus two things too slow or too stateful for the inner loop:

- `next build`, which catches server/client boundary errors `tsc --noEmit` cannot see.
- a check that `schema.graphql` and `src/generated/graphql.ts` are committed and
  current, so a schema change can never merge with stale generated types.

There is a liveness probe at <http://localhost:8080/health>. It is the one route
that is not GraphQL, on purpose: a health check that needs the GraphQL layer to
answer cannot tell you the GraphQL layer is down.

## Layout

```
backend-python/
  src/app/
    main.py            app wiring, lifespan seed, /health probe
    config.py          settings from env (DATABASE_URL, CORS_ORIGINS)
    errors.py          DomainError(message, code)
    models/            SQLAlchemy models
    services/          business logic — the ONLY place that commits
    api/graphql/       types, inputs, resolvers
    api/rest/          unused REST routes kept from the scaffold
    database/          engine, session, seed
  tests/               pytest + httpx integration tests
frontend/
  schema.graphql       exported SDL (source for codegen)
  src/generated/       typed hooks — generated, do not edit
  src/graphql/         GraphQL documents
  src/components/      UI
```

The API is **GraphQL**. `api/rest/` is left over from the original scaffold and is
not used by the frontend.

## Adding a feature

1. Add the model in `models/`.
2. Put the logic in `services/` — raise `DomainError(msg, code="...")` for expected
   failures. This is where the transaction boundary lives.
3. Add the GraphQL type, `Input`, and resolver in `api/graphql/schema.py`. Resolvers
   stay thin: unwrap args, call the service, return.
4. Add the document to `frontend/src/graphql/queries.ts`.
5. `make codegen`
6. Build the component against the generated hook.
7. Add a test in `backend-python/tests/`.
8. `make reset-db` if you changed a model.

## Conventions

- **Money is stored as integer minor units** (cents), never floats.
- Every mutation takes a single `Input` type.
- Services own the transaction boundary — resolvers never call `commit()`.
- Errors carry a stable `extensions.code` the frontend can branch on.
- `create_all()` does **not** alter existing tables. Change a model → `make reset-db`.
- SQLite runs with `foreign_keys=ON` and WAL.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `ModuleNotFoundError: No module named 'app'` | Stale venv. `make doctor` repairs it (and runs automatically before `dev`/`backend`/`test`). Manually: `cd backend-python && rm -rf .venv && uv sync`. If it keeps recurring, you are probably on an iCloud-synced path — see the note above. |
| Frontend started on :3001 | Port 3000 was busy. It still works — CORS allows any `localhost` port. `make stop` frees them. |
| Something still listening after Ctrl-C | `make stop` |
| "no such column" after adding a model field | `make reset-db` |
| Types stale after a schema change | `make codegen` |
| `make check` fails only on formatting | `cd frontend && npm run format:write` |
| `make lint-check` fails | `make lint` (it rewrites; `lint-check` only reports) |

## Deliberately not included

Alembic migrations, authentication, cursor pagination, structured logging, Postgres,
Docker, and frontend tests are absent from the **scaffold**. That is not a rule for
features: a feature plan defaults to building these to industry standard, and waives
one only when the requirements say so or call the work a prototype.

**A Python type checker is also omitted, and that one needs a reason.** mypy and
ty both flag exactly the same two lines: the resolvers in `api/graphql/schema.py`
return SQLAlchemy models where the annotation promises Strawberry types. That code
is correct — Strawberry resolves fields by attribute access — but it is the pattern
every new entity copies, so turning a checker on means a fresh error per resolver
and a conversion layer to write for each one. Add the checker only if you first
change the pattern. Coverage is skipped for a related reason: a number nobody has
time to act on is not a signal.
