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
| Node | ≥ 20.9 | `brew install node` |

You do **not** need Python preinstalled — `uv` reads `requires-python` and downloads
CPython 3.12 itself.

## Commands

`make help` lists everything.

| Command | What it does |
|---|---|
| `make dev` | both servers in one terminal |
| `make backend` / `make frontend` | one at a time, in separate terminals |
| `make stop` | force-free ports 8080 / 3000 |
| `make test` | backend test suite |
| `make lint` | format + autofix the backend (ruff) |
| `make check` | frontend lint + typecheck |
| `make schema` | export the GraphQL SDL to `frontend/schema.graphql` |
| `make codegen` | regenerate TS types from the SDL (no running server needed) |
| `make reset-db` | drop the dev database — **required after any model change** |
| `make doctor` | verify the backend venv, rebuilding it if stale (runs automatically before `dev`/`backend`/`test`) |

## Layout

```
backend-python/
  src/app/
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

## Deliberately not included

Alembic migrations, authentication, cursor pagination, structured logging, Postgres,
Docker, and frontend tests. Each is a considered omission for a small, fast-moving
app — not an oversight.
