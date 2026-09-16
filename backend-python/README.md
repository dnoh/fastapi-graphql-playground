# backend-python

The FastAPI + Strawberry GraphQL service over SQLite. Everything is driven from the
**repo root** with `make`; there is nothing to run from this folder directly.

| | |
|---|---|
| Run | `make backend` (or `make dev` for both servers) → <http://localhost:8080/graphql> |
| Test | `make test` |
| Format / lint | `make lint` (rewrites) · `make lint-check` (read-only, what CI runs) |
| Export SDL | `make schema` |

Tooling is **uv** (environment and dependencies, `pyproject.toml` + `uv.lock`) and
**ruff** (format and lint). There is no type checker by design; see "Deliberately not
included" in the root [README](../README.md), and the conventions and layer rules in
[CLAUDE.md](../CLAUDE.md).

`src/app/api/rest/` is left over from the original scaffold. The frontend never calls
it, and it is not extended.
