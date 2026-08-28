# Scaffold Audit — Brex AI-Assisted Coding Interview

**Repo:** `fullstack-server-test/ai_assisted_coding_interview/` (git root; 3 commits, clean tree)
**Audited:** 2026-08-26, read-only. Cold start was *analyzed*, not executed — see §2 for why. **Plan added:** 2026-08-27 (Part 2).

## Verdict: **NEEDS WORK** (~2–3 h of scaffold work, then rehearsal — see Part 2)

> **Correction (2026-08-27):** the original estimate here said 30–45 min, which contradicted Part 2's own checklist. The blocking work (§Phase 1–2) is ~45 min; the full plan is 2–3 h, and the rehearsal reps that follow matter more than either.

The scaffold's *shape* is right — one table, one ORM model, REST + GraphQL, a React page that reads and writes through Apollo. But on this machine **none of the three apps can start** (no Node, no JVM, no Poetry), the Python backend **drops the database on every hot reload**, and there's **no CLAUDE.md / `.claude/settings.json`**. Fix those before the interview and pick *one* backend; don't start over.

**Recommendation: Python backend + Next.js frontend.** Fewer moving parts than Spring, faster restarts, and you already have `uv`. Delete `backend-kotlin/` from your working copy.

---

## 1. Inventory

| Piece | Stack | Entry point | Status |
|---|---|---|---|
| `backend-python/` | FastAPI 0.110, SQLAlchemy 2.0, Strawberry GraphQL, SQLite, Poetry | `src/app/main.py` → `poetry run uvicorn src.app.main:app --reload --port 8080` | Real, works on paper. No tests dir. |
| `backend-kotlin/` | Spring Boot 3.4, Kotlin 1.9, JPA, H2 in-mem, Gradle (JDK 17 toolchain) | `src/main/kotlin/brex/interview/Application.kt` → `./gradlew bootRun` | Real, duplicate of Python. 1 smoke test. |
| `frontend/` | Next.js 15 (App Router, turbo), React 19, Apollo Client 3, Tailwind 4, graphql-codegen, T3 env | `src/app/page.tsx` → `npm run dev` (port 3000) | Real. One component. No tests. |

Dependency files: `backend-python/pyproject.toml` + `poetry.lock`, `backend-kotlin/build.gradle.kts`, `frontend/package.json` + `package-lock.json`.

Domain: a single `messages` table (`id UUID, content VARCHAR(255) default 'Hello World', created_at`). Python's `Base` also adds `updated_at`. API surface = `latestMessages(limit)` query + `createMessage` mutation (no args), plus REST `GET/POST /api/messages`, `GET /api/messages/{id}`, `GET /api/messages/latest/`.

Empty/stubbed: `backend-python/tests/` (documented in README, doesn't exist), `frontend/tests/` and `frontend/src/types/` (documented, don't exist), `frontend/.env.example` (T3 boilerplate, zero variables), Kotlin `ApplicationTests.contextLoads()` (asserts nothing).

## 2. Cold start

**Result: 0 of 3 apps can start on this machine.** Not one command was runnable, so no timings.

| Requirement | On this Mac | Consequence |
|---|---|---|
| Node ≥18 + npm | **absent** (no `node`, no nvm/fnm/volta, checked login shell) | Frontend can't install or run |
| JDK 17 | **absent** (`/usr/bin/java` is the Apple stub: "Unable to locate a Java Runtime") | Kotlin can't build |
| Poetry | **absent** (`uv` 0.12.6 is present) | README install path fails |
| Python | 3.14.7 (homebrew) | Lockfile pins pydantic-core 2.33.1 (Apr 2025, pre-3.14). High chance of a Rust source build or failure. Use 3.12/3.13. |
| `fullstack-server-test/.venv` | exists, Python 3.14, **empty** (no packages) | A previous attempt stalled here |

Documented steps once the toolchain exists (README): Python = 3 steps (`poetry install`, `uvicorn …`, then frontend `npm install` + `npm run dev`) — realistically 4 shell commands across 2 terminals. Kotlin = `./gradlew build` (cold Gradle+deps download is typically 2–5 min) then `bootRun`.

Config gaps: no backend `.env`/`.env.example` at all (DB URL and CORS origin are hardcoded in `session.py`/`main.py`); frontend Apollo URI hardcoded to `http://localhost:8080/graphql` in `src/lib/apollo-client.ts`; `codegen.ts` needs a *running* backend on :8080 to regenerate types.

**Prep commands (run before the interview, verify once):**
```bash
brew install node                                   # frontend
cd fullstack-server-test/ai_assisted_coding_interview/backend-python
# convert pyproject.toml to [project] format first (Part 2 §D Phase 1), then:
uv venv --python 3.12 && uv sync
uv run uvicorn src.app.main:app --reload --port 8080
cd ../frontend && npm install && npm run dev
```

## 3. Vertical slice (Python path)

| Link | File | State |
|---|---|---|
| DB table | `backend-python/dummy.db` → `messages` (created by `Base.metadata.create_all` in `main.py:12-13`) | OK (SQLite, committed) |
| ORM model | `src/app/models/message.py` (`Message`), `models/base.py` (`Base` w/ timestamps) | OK; `created_at` redefined in subclass (harmless dup) |
| Seed | `src/app/database/seed.py` — inserts one "Hello World" | OK, runs at import in `main.py:16-22` |
| API | GraphQL `src/app/api/graphql/schema.py` (`latest_messages`, `create_message`); REST `src/app/api/rest/messages.py` | OK for GraphQL. **REST `/api/messages/latest` is broken** — route is `/latest/` and is declared *after* `/{message_id}`, so the README's URL 422s on UUID parse. |
| HTTP | `main.py` mounts `/api` and `/graphql`; CORS allows `http://localhost:3000` | OK |
| Frontend fetch | `frontend/src/lib/apollo-client.ts` → `src/app/providers.tsx` → `src/components/HelloWorldDashboard.tsx` uses `useQuery(GET_LATEST_MESSAGES)` from `src/graphql/queries.ts`, types from `src/generated/graphql.ts` | OK, renders list + "Create" button with refetch |

Chain is intact for GraphQL. One caveat: `generated/graphql.ts` was generated against the **Kotlin** schema (`createdAt: String!`, `[Message]!`), not Python's (`createdAt: DateTime!`, `[Message!]!`). Runtime is fine (Strawberry serializes DateTime as ISO string), but re-run `npm run codegen` against Python once so types stop lying.

Not verified live (toolchain absent); verified by reading every file in the chain.

## 4. Test loop

| | Runner | Tests | Command | Hot reload |
|---|---|---|---|---|
| Python | pytest in dev deps, **no `tests/` dir, no `httpx`** (required by FastAPI `TestClient`) | 0 | `poetry run pytest` → "no tests ran" | `uvicorn --reload` ✔ — **but see MUST FIX #2: reload wipes the DB** |
| Kotlin | JUnit 5 via Gradle | 1 (`contextLoads`, asserts nothing) | `./gradlew test` (~30–60 s warm) | Spring DevTools ✔ |
| Frontend | **none** (no vitest/jest/playwright) | 0 | — | `next dev --turbo` ✔ |

Nothing to run, so nothing measured. The interviewer will ask about Definition of Done; having *one* real API test you can extend is cheap credibility.

## 5. Liabilities (DELETE / simplify — less is better)

- **`backend-kotlin/`** — an entire duplicate backend. Pick one. Deleting it removes JDK/Gradle from the cold start and halves the "which one are you running?" confusion.
- **`main.py:12-13` `drop_all()/create_all()` at import** — combined with `--reload`, every save resets your data mid-demo. Replace with `create_all()` only (+ idempotent seed) or a `lifespan` hook.
- **`backend-python/dummy.db` committed** — generated binary in git; noisy diffs on every run. Ignore it.
- **`alembic` dependency** — declared, never configured (no `alembic.ini`, no `migrations/`). Either wire it (5 min) or drop it; don't leave it half-there.
- **`pydantic[email]`, `email-validator`, `python-dotenv`** — unused. `black`/`isort`/`mypy` — unused, no config beyond line-length; fine to keep but don't let them cost attention.
- **`frontend/src/generated/graphql.ts` committed** — generated file that drifts from whichever backend you run. Regenerate against Python and keep it (codegen needs a live server, so committing it is defensible) — but know it's stale today.
- **`frontend/src/env.js` + `@t3-oss/env-nextjs` + `zod`** — T3 env validation with zero variables. Bring it to life (`NEXT_PUBLIC_API_URL`) or delete `env.js` and the `next.config.js` import.
- **`frontend/README.md`** — create-t3-app boilerplate mentioning NextAuth/Prisma/Drizzle/tRPC that don't exist. Delete.
- **`prettier-plugin-tailwindcss`, ESLint `recommendedTypeChecked`+`stylisticTypeChecked`** — strict type-aware lint will nag under time pressure (`message: any` in `HelloWorldDashboard.tsx:88` already violates it). Keep prettier; consider relaxing lint to `recommended`.
- **Root `README.md` structure block** — describes `controller/`, `types/`, `tests/` dirs that don't exist. Rewrite after deleting Kotlin.
- **Python REST layer (`api/rest/messages.py`, `schemas/message.py`)** — a second API surface the frontend never calls. Either commit to it (and fix the `/latest` route) or delete it and go GraphQL-only. Two API styles = two conventions to explain.
- **`backend-kotlin/HELP.md`, `gradlew.bat`, `.gitattributes`** — go away with Kotlin.
- **`fullstack-server-test/.venv` (outside the git repo)** — empty 3.14 venv; delete and recreate with 3.12 inside `backend-python/`.

## 6. AI-readiness

- **No `CLAUDE.md`** anywhere (root, git root, or per-package).
- **No `.claude/` directory / `settings.json`** — nothing allowlisted; every `npm`, `uv`, `pytest`, `curl` will prompt.
- Both are scored directly under "AI Collaboration". Write a short `CLAUDE.md` (stack, run/test commands, API conventions, "Python backend only", where new features go) and allowlist `Bash(npm run *)`, `Bash(uv run *)`, `Bash(pytest*)`, `Bash(curl localhost*)`, `Bash(sqlite3 *)`.

## 7. Gaps you'd hit under time pressure

| Gap | Cost in interview | Pre-build? |
|---|---|---|
| **Migration workflow** — none; schema = `create_all` | Every new column requires deleting the DB or a `drop_all`. Acceptable for 50 min *if you say so out loud*. | Decide: "dev = `create_all` + reseed" and document it in CLAUDE.md. Skip Alembic. |
| **Seed data** — one row, hardcoded | New features need realistic rows to demo | Make `seed.py` idempotent and easy to extend (list of dicts) |
| **CORS** | Done for :3000 | No |
| **Error handling convention** — none (one raw `HTTPException`; GraphQL resolvers raise nothing) | Interviewer probes "what happens on bad input?" | Add one `NotFoundError` → GraphQL error / 404 pattern you can point to |
| **API response shape** — bare objects, no envelope; mutations take no input | Every feature needs an input type + return type; `createMessage` has no arguments to copy from | Add a `CreateMessageInput` and a `content` arg now so there's a template |
| **Frontend data-fetching pattern** — `useQuery` + `refetch`, `no-cache`, `any` cast | Works; `no-cache` avoids cache-normalization bugs, which is *good* for speed | Keep. Add one generic `<ErrorBanner>`/`<Loading>` so features don't re-invent |
| **ID type mismatch** — SQLAlchemy `Mapped[UUID]` on SQLite stores `CHAR(32)`; Strawberry emits `UUID` scalar | Fine; just don't be surprised by hyphen-less ids in sqlite3 | No |
| **`Base.updated_at`** exists in DB but not in API | Harmless | No |
| **Tests** — none runnable | DoD question | One `tests/test_api.py` with `TestClient` hitting `/graphql` |

---

## Findings ordered by impact on your first 10 minutes

### MUST FIX
1. **Install the toolchain** — no Node, no JDK, no Poetry on this Mac (`which node` → nothing). Nothing runs until `brew install node` and a 3.12 venv exist.
2. **`backend-python/src/app/main.py:12` `Base.metadata.drop_all()` at import** — with `--reload` your data is erased every time you save a file. Change to `create_all()` + idempotent seed.
3. **Choose one backend — but do _not_ delete the other.** ~~Delete `backend-kotlin/`~~ **Superseded (see Part 2 §A.2):** `backend-kotlin/` is 22 of 58 tracked files; deleting it is a large, unrelated diff against a scaffold that deliberately offers alternatives. Select Python, say so out loud, and tell your agent to ignore the Kotlin tree.
4. **Add `CLAUDE.md` + `.claude/settings.json` allowlist** — "AI Collaboration & Iteration" is explicitly scored and both are absent. Tool-specific (Claude Code), not a repo requirement; see Part 2 §D Phase 5.
5. **Python 3.14 + `poetry.lock`** — `pydantic-core 2.33.1` predates 3.14; use `uv venv --python 3.12`. The empty `fullstack-server-test/.venv` is evidence this already bit once.
6. **`backend-python/src/app/api/rest/messages.py:31` vs `:39`** — `/{message_id}` is registered before `/latest/`, so `/api/messages/latest` parses "latest" as a UUID and 422s. Real defect. **Revised priority:** the frontend is GraphQL-only, so this is a supplied-but-unused path — leave it and declare it out of scope, or fix the two-line ordering if you keep REST.

### SHOULD FIX
7. **Regenerate `frontend/src/generated/graphql.ts`** against the Python schema (`npm run codegen` with backend up) — currently Kotlin-shaped.
8. **Add a mutation with input** (`createMessage(content: String!)`) in `api/graphql/schema.py` + `queries.ts` so every feature has a copy-paste template.
9. **One real test** — `backend-python/tests/test_graphql.py` using `TestClient` (add `httpx` to dev deps).
10. **Make `seed.py` idempotent + richer** — current seed only runs because of `drop_all`.
11. **Wire `NEXT_PUBLIC_API_URL`** through `frontend/src/env.js` → `apollo-client.ts`, or delete `env.js`.
12. **Gitignore `backend-python/dummy.db`** — committed generated artifact.
13. **Rewrite root `README.md`** to the single stack + 3 commands; delete stale dir tree.
14. **Fix `message: any` at `HelloWorldDashboard.tsx:88`** — use the generated type; type-checked lint flags it.

### DELETE — **mostly superseded, see Part 2 §A**

Only these survive review:
- `fullstack-server-test/.venv` (empty, wrong Python — not tracked by git, safe)
- `alembic`, `python-dotenv`, `email-validator`, `pydantic[email]` — dropped as part of the `pyproject.toml` conversion, not as a deletion of supplied code. The REST layer keeps working (it needs only fastapi + pydantic + sqlalchemy).
- Untrack `backend-python/dummy.db` (`git rm --cached`) and gitignore `*.db*`

**Reversed — do NOT delete:**
- ~~`backend-kotlin/`~~ — 22 of 58 tracked files. Supplied alternative; declare scope instead.
- ~~`backend-python/src/app/api/rest/` + `schemas/`~~ — supplied alternative; unused by the frontend, harmless.
- ~~`.gitattributes`~~ — belongs to the Kotlin tree you're keeping.
- ~~`frontend/README.md`~~ — stale T3 boilerplate, but deleting supplied files to tidy is not worth the diff. Add a pointer line in the root README instead.
- ESLint relaxation: hold until rehearsal shows it actually costs you time.

---
---

# Part 2 — Prep Plan (revised 2026-08-27)

> **This is a revision.** The first draft was reviewed externally (Codex) and cut substantially. §G logs what changed and why. Four corrections were accepted outright; three trims were declined with reasons.

**Confirmed context:** you bring **your own prepped repo** to the interview, you'll drive it with **Claude Code**, and the DB stays **SQLite**.

**Target — the one sentence that governs every decision below:**
> Boot reliably → make one vertical change fast → test it → *explain* the transactional/idempotency design you'd add when the prompt actually calls for transfers.

Not: pre-build transfer infrastructure. An over-built scaffold reads as pattern-matching rather than designing, and it inverts the Definition-of-Done signal you're being scored on.

## A. Decisions

| # | Decision | Status | Reason |
|---|---|---|---|
| 1 | Keep the scaffold; clean it up | unchanged | Shape is right; rebuild risk > payoff |
| 2 | **Python/FastAPI is the *active* path; `backend-kotlin/` stays untouched** | **REVERSED** | 22 of 58 tracked files. The scaffold deliberately offers alternatives; deleting one is a large unrelated diff. Say "I selected Python + GraphQL; I left the provided alternatives untouched." Tell Claude to ignore the tree via `CLAUDE.md`. |
| 3 | **GraphQL is the *active* path; REST layer stays untouched, unused** | **REVERSED** | Same reasoning. The `/latest` ordering bug (`messages.py:31` before `:39`) is real but out of scope — name it if asked. |
| 4 | SQLite for dev/test/interview | unchanged | Zero boot risk; transactions, `CHECK`, `UNIQUE` idempotency keys all work. Row locking gets narrated, not demoed. |
| 5 | Postgres / Docker deferred entirely | unchanged | Only revisit if a rehearsal genuinely wants to *demo* `with_for_update()`. |
| 6 | `uv` + `pyproject.toml [project]` + `uv.lock`; `uv sync` / `uv run` only | clarified | Do **not** mix with ad-hoc `uv pip install -e .` — convert once, then one reproducible path. |
| 7 | Python 3.12 | unchanged | Pinned deps lack 3.14 wheels; the empty `.venv` is evidence it already failed. |
| 8 | `ruff` for lint + format, run on demand | unchanged | One tool replacing black + isort. |
| 9 | `pydantic-settings` for `DATABASE_URL` / `CORS_ORIGINS` | unchanged | Typed, env-driven, no hardcoded URLs. |
| 10 | `create_all()` + idempotent seed in a `lifespan` hook; no `drop_all()` | unchanged | Fixes the reload-wipes-data footgun. |
| 11 | **Explicit `make reset-db`; schema changes require a reset, not `create_all`** | **CORRECTED** | `create_all()` is `CREATE TABLE IF NOT EXISTS` — it does **not** add columns to existing tables. The original DoD wording implied otherwise and was false. |
| 12 | SQLite pragmas: `foreign_keys=ON` (app + tests), `journal_mode=WAL` (app only) | refined | FKs are **off** by default in SQLite. WAL helps the app; irrelevant to tests. |
| 13 | Thin `services/` module — business logic and `commit()` live there, never in resolvers | **kept (declined trim)** | ~10 lines, and it is exactly where a transfer's transaction boundary goes. Declined the "no service layer" trim; **dropped** the Unit-of-Work abstraction, which *was* over-build. |
| 14 | **One** `DomainError` with a `code`, surfaced in GraphQL `extensions` | **kept, narrowed (declined trim)** | ~15 lines. "Insufficient funds" is the single most likely unhappy path in a transfer prompt. **Dropped** the `NotFound`/`Conflict`/… taxonomy. |
| 15 | Mutations take `Input` types (`createMessage(input: CreateMessageInput!)`) | unchanged | The copy-paste template for every feature. |
| 16 | Money = integer minor units | unchanged | Correctness; SQLite has no real `NUMERIC`. |
| 17 | **Tests: temp *file* SQLite per test + `create_all` per test** | **CORRECTED** | The original "in-memory + rollback per test" is deceptively complex: `TestClient` crosses threads (in-memory needs `StaticPool` + `check_same_thread=False`), and a service layer that commits defeats a naive rollback fixture. File-backed is more reliable and easier to narrate. |
| 18 | **`codegen.ts` must map custom scalars** (`DateTime`→`string`, `UUID`→`string`) | **NEW** | Currently no `scalars` config. Regenerating against Strawberry introduces `DateTime`/`UUID`, which codegen silently emits as `any` — quietly destroying the type safety that justifies codegen at all. |
| 19 | No frontend test runner | unchanged | Unused in 50 min; declare deferred. |
| 20 | Makefile of **aliases** (`test`, `reset-db`, `backend`, `frontend`, `codegen`, `lint`) | narrowed | Zero deps; provides the `reset-db` command. **Dropped** `make dev` (the concurrent process manager) — that was the part worth cutting. |
| 21 | `CLAUDE.md` with a numbered new-entity checklist + `.claude/settings.json` allowlist | unchanged | "AI Collaboration & Iteration" is explicitly scored. Optional one-line `AGENTS.md` pointer for portability. |
| 22 | **No `PostToolUse` ruff auto-fix hook** | **REVERSED** | A hook that rewrites files after every agent edit muddies your diff and can surprise you mid-demo. Run `make lint` on demand. |
| 23 | Root `README.md` gets an "ACTIVE PATH" note at the top | narrowed | **Dropped** the full rewrite — don't restructure supplied docs, just point at what you chose. |
| 24 | Deferred: Alembic, Postgres, Docker, request-id/structured logging, `/feature` skill, UoW, FE test tooling, MCP DB servers, multi-agent workflows | expanded | None of these improve the first ten minutes enough to justify setup + verification cost. All become §E talking points. |
| 25 | 2–3 timed 50-min rehearsals; fold every stall back into the scaffold or `CLAUDE.md` | **promoted to the centerpiece** | With the build trimmed, this *is* the prep. |

## B. Stack

| Layer | Choice |
|---|---|
| Runtime / pkg | Python 3.12, `uv`, `pyproject.toml [project]`, `uv.lock` |
| API | FastAPI + Strawberry GraphQL (active path; REST left in place, unused) |
| ORM / DB | SQLAlchemy 2.0 typed `Mapped[]`; SQLite — WAL, FKs on; `DATABASE_URL` env switch |
| Config | `pydantic-settings` |
| Lint / test | `ruff` (on demand); `pytest` + `httpx` |
| Frontend | Next.js 15 App Router, React 19, Apollo Client 3, Tailwind 4, graphql-codegen **with scalar mapping** |
| Orchestration | Makefile aliases |

## C. Dependencies

**System:** `brew install node`. (`uv` 0.12.6 and `sqlite3` already present.)

**Backend runtime**
```
fastapi                      # API
uvicorn[standard]            # server; uvloop/httptools/watchfiles → fast reload
strawberry-graphql[fastapi]  # GraphQL
sqlalchemy                   # ORM
pydantic                     # also keeps the supplied REST layer importable
pydantic-settings            # env config (replaces python-dotenv)
```
**Backend dev**
```
pytest, httpx                # httpx is required by TestClient — currently missing
ruff                         # lint + format
```
**Not installed:** alembic, python-dotenv, email-validator, `pydantic[email]` (all unused).
**Frontend:** `npm install` as-is; no additions.

## D. Execution checklist

### Phase 1 — Boot reliably ✅ **DONE 2026-08-27**
- [x] `brew install node` — node **26.7.0** / npm 11.19.0 (was already present by the time this ran; absent at audit time on 26 Aug)
- [x] `rm -rf fullstack-server-test/.venv` (empty, Python 3.14, untracked)
- [x] Convert `backend-python/pyproject.toml` to `[project]`; `uv venv --python 3.12` (**1.5 s**); `uv sync` (**1.0 s**); `poetry.lock` removed → `uv.lock`
- [x] Added the 7 missing `__init__.py` files; import path is now `app.main:app`, not `src.app.main:app`
- [x] `git rm --cached backend-python/dummy.db`; gitignored `*.db*`; DB is now `backend-python/app.db`
- [x] `npm install` — **18 s**, exit 0; `:3000` returns 200
- [x] **Measured cold start (deps already installed): backend ready 0.5 s, frontend ready 2.0 s**

### Phase 2 — Fix the footguns ✅ **DONE 2026-08-27**
- [x] `src/app/config.py` — new `Settings(BaseSettings)`: `database_url`, `cors_origins`
- [x] `database/session.py` — engine from settings; `connect` listener sets `PRAGMA foreign_keys=ON` + `journal_mode=WAL`, guarded so it no-ops on non-SQLite
- [x] `main.py` — **`drop_all()` deleted**; `lifespan` runs `create_all()` + idempotent seed; CORS from settings
- [x] `database/seed.py` — 3 rows as dicts, inserts only when the table is empty
- [x] `models/message.py` — no longer redefines `created_at` (inherited from `Base`)
- [x] `ruff` clean (`B008` ignored — `Depends()` in defaults is the FastAPI idiom)

**Verified:**
- `foreign_keys = 1`, `journal_mode = wal` on the app's own connections (the `sqlite3` CLI shows `foreign_keys=0` because it is a *per-connection* pragma — check via the engine, not the CLI)
- GraphQL query returns the 3 seeded rows; `createMessage` mutation returns a new row
- **Footgun fixed:** created a 4th row, restarted the server, still 4 rows. Seed did not duplicate.
- CORS preflight from `:3000` → `:8080` returns 200 with the correct `access-control-allow-origin`

### Phase 3 — Vertical-slice templates ✅ **DONE 2026-08-27**
- [x] `src/app/services/messages.py` — `list_latest`, `create_message`; the only place that commits
- [x] `src/app/errors.py` — one `DomainError(message, code)`; a `@domain_errors` resolver decorator maps it to a GraphQL error with `extensions.code`
- [x] `CreateMessageInput(content: String!)` + `createMessage(input:)`
- [x] `tests/conftest.py` — temp-**file** SQLite per test, `create_all` per test, `get_db` override, `TestClient` built **without** a `with` block (a `with` runs the lifespan and would create/seed the real `app.db`)
- [x] `tests/test_messages.py` — **7 tests**, incl. the error-`code` assertion and a service-level test with no HTTP
- [x] `Makefile` at the repo root — `dev`, `backend`, `frontend`, `test`, `lint`, `check`, `schema`, `codegen`, `reset-db`, `install`, `help`
- [x] **`make test` green: 7 passed in 0.06 s, zero warnings**

**Pulled forward from Phase 4 out of necessity** (the required `input` argument broke the old no-arg frontend mutation, so leaving it would have meant a knowingly-broken app):
- [x] `codegen.ts` — `scalars: { DateTime: 'string', UUID: 'string' }` + `strictScalars: true`. Verified: `DateTime`/`UUID` now generate as `string`, not `any`.
- [x] **`make schema`** exports the SDL to `frontend/schema.graphql`; `codegen.ts` reads that file instead of the live endpoint.
- [x] `queries.ts` + new `MessagesPanel.tsx` (replaces `HelloWorldDashboard.tsx`) using generated hooks — no `any` anywhere; `components/ui/Feedback.tsx` holds `Loading`, `ErrorBanner`, `errorCode`.
- [x] `npx tsc --noEmit` clean.

> **Blocker found and worked around:** codegen against the live endpoint fails with
> `Syntax Error: Unexpected Name "DIRECTIVE_DEFINITION"`. graphql-core (Python) advertises
> `@deprecated` on the `DIRECTIVE_DEFINITION` location, which **graphql-js 16.10 cannot parse**.
> Exporting Strawberry's SDL sidesteps it (built-in directives are omitted) — and as a bonus
> `make codegen` no longer needs a running server.

**Still open in Phase 4:** `NEXT_PUBLIC_API_URL` through `env.js` (Apollo URL is still hardcoded), the optional ESLint relaxation, and one known nit — `createdAt` serializes without a timezone offset (SQLAlchemy `DateTime` drops tzinfo on SQLite), so `new Date()` in the browser reads it as local time. Display-only; fix with `DateTime(timezone=True)` if it bothers you.

### Phase 3b — Repo self-containment ✅ **DONE 2026-08-27**

Goal: clone the private repo on any machine and run with zero overhead.

- [x] **`Makefile` moved into the repo root** (`ai_assisted_coding_interview/`) with repo-relative paths — it was outside the git repo and would never have been pushed
- [x] **`.vscode/{settings,extensions}.json` moved in and un-ignored** (`.vscode/*` + `!settings.json` + `!extensions.json`), so a fresh clone gets the right interpreter and extension prompts automatically
- [x] `README.md` rewritten: quick start, prerequisites, commands, architecture, add-a-feature recipe, conventions, troubleshooting. Deleted `frontend/README.md` (T3 boilerplate)
- [x] `frontend/package.json` — `engines.node >= 20.9` so a wrong runtime fails loudly
- [x] `make stop` added — force-frees :8080/:3000
- [x] **Verified with a simulated fresh clone** (74 tracked files rsynced to a clean dir, no `.venv`/`node_modules`/`*.db`): `make install` **7.7 s** → `make test` 7 passed → both servers boot → DB auto-seeds → mutation works → frontend 200

**Three real bugs found and fixed by that test:**
1. `make dev` piped both servers through `sed` for `[be]`/`[fe]` prefixes — `sed` block-buffers on a non-TTY and **swallowed all server output**. Pipes removed; `exec` added so signals reach the real processes. Verified via a PTY that logs now appear.
2. Ctrl-C could leave orphaned servers. Added `make stop` as a guaranteed escape hatch; verified `SIGINT` to the process group now kills both.
3. **Next.js silently hops to :3001 when :3000 is taken**, and CORS only allowed :3000 — the app would break with an opaque CORS error. Added `cors_origin_regex` matching any `localhost` port. Verified: :3000 ✓, :3001 ✓, `evil.example.com` blocked.

**Also hit:** the backend venv broke with `ModuleNotFoundError: No module named 'app'`. Cause: `~/.local/share/uv/python/cpython-3.12-...` is a **symlink** to `cpython-3.12.14-...`; the venv referenced the symlink path for `lib-dynload` while the interpreter resolved to the versioned path, so `site.py` bailed and never processed any `.pth` file (including the editable install). Recovery is `rm -rf .venv && uv sync` — **0.16 s**. Documented in the README troubleshooting table.

### Phase 3c — Single-stack cleanup ✅ **DONE 2026-08-27** *(user decision)*

- [x] **Deleted `backend-kotlin/`** (22 tracked files) and `.gitattributes` (existed only for `gradlew`/`*.bat`/`*.jar`)
- [x] Removed the 28-line Kotlin/Gradle/Spring block from `.gitignore`, keeping the IntelliJ entries
- [x] `README.md` rewritten for a single stack — quick start, prerequisites, commands, layout, add-a-feature recipe, conventions, troubleshooting
- [x] `eslint.config.js` now ignores `src/generated/**` — `make check` was failing on the *generated* file
- [x] Verified: zero remaining kotlin/gradle/spring references; `make test` 7 passed; `make check` clean; both servers boot; payload down to **0.9 MB / 51 files**

> **Decision A.2 reversed again, deliberately.** The review's objection (a large diff against a
> scaffold that intentionally offers alternatives) applies to a PR *against Brex's repo*. This is
> now the user's own private repo, so the objection largely evaporates and a single-stack tree is
> easier to explain. The REST layer under `api/rest/` was kept.

### ⚠️ Environment finding — iCloud is breaking the virtualenv

The backend venv broke **twice** with `ModuleNotFoundError: No module named 'app'`, each time
after heavy file activity in the tree.

**Cause: `~/Documents` is iCloud-synced.** Confirmed by the `com.apple.file-provider-domain-id`
xattr on `~/Documents`, a `Documents` folder under `~/Library/Mobile Documents/com~apple~CloudDocs/`,
and `brctl status` showing an active sync at the time of the failures. The earlier duplicate
`_editable_impl_brex_interview_backend 2.pth` is iCloud's conflict-rename signature. iCloud is
syncing `.venv` and `node_modules` file-by-file and occasionally corrupting the editable install.

**Mitigations applied:**
- `make doctor` verifies the venv and silently rebuilds it (~1 s) if `import app` fails; `dev`,
  `backend`, and `test` all depend on it. Verified by deleting the `.pth` and re-running.
- README warns against cloning into an iCloud-synced path.

**Done:** the working copy moved to `~/code/brex-interview-scaffold`; the `~/Documents`
tree was deleted (Phase 5b).

### Phase 4 — Frontend ✅ **DONE 2026-08-27**
- [x] `codegen.ts` — `scalars: { DateTime: 'string', UUID: 'string' }` + `strictScalars: true` *(done in Phase 3)*
- [x] `src/env.js` + `.env.example` + `lib/apollo-client.ts` — `NEXT_PUBLIC_API_URL`
- [x] `make codegen` (SDL-based, no running server needed); result committed *(done in Phase 3)*
- [x] `HelloWorldDashboard.tsx` replaced by `MessagesPanel.tsx` — generated types, no `any`, content input wired to `createMessage(input:)` *(done in Phase 3)*
- [x] `components/ui/Feedback.tsx` — `Loading`, `ErrorBanner`, `errorCode` *(done in Phase 3)*
- [x] `make check` clean (`next lint` + `tsc --noEmit`)

**`NEXT_PUBLIC_API_URL` — as wired:**
- Holds the **full GraphQL endpoint**, not a base URL — a direct swap for the literal that
  was in `apollo-client.ts`, nothing to concatenate.
- `z.string().url().default("http://localhost:8080/graphql")` in `env.js`, so a fresh clone
  still needs **no `.env`** — the README's "There is no `.env` to write" promise survives.
- `.env.example` rewritten from T3 boilerplate to document the one real (optional) variable.

**Verified three ways** (`node --input-type=module -e 'import {env} from "./src/env.js"'`):
| Input | Result |
|---|---|
| no env var | `http://localhost:8080/graphql` (zod default) |
| `NEXT_PUBLIC_API_URL=http://localhost:9999/graphql` | `http://localhost:9999/graphql` |
| `NEXT_PUBLIC_API_URL=not-a-url` | `❌ Invalid environment variables … 'Invalid url'` |

Also confirmed the override reaches the **browser** bundle, not just Node: with the var set,
the served chunk contains `XT_PUBLIC_API_URL: ("TURBOPACK compile-time value",
"http://localhost:9999/graphql")`. With it unset the string is absent and zod's `.default()`
supplies the value at runtime — which is why `localhost:8080/graphql` appears in the bundle
either way (it is the `.default()` literal in the schema, not the resolved `uri`).

**Deferred, unchanged:** the optional ESLint relaxation (audit §5) — hold until a rehearsal
shows it actually costs time. And the `createdAt` timezone nit (SQLAlchemy `DateTime` drops
tzinfo on SQLite, so the browser reads it as local time); display-only.

### Phase 5 — AI tooling ✅ **DONE 2026-08-27**
- [x] `CLAUDE.md` at the repo root (committed — it is the scored artifact):
  - Active path: Python + Strawberry GraphQL + Next.js/Apollo. **Ignore `src/app/api/rest/`
    and `schemas/message.py`** — supplied alternative, unused by the frontend, out of scope,
    with its known `/latest/` route-ordering bug named so nobody "fixes" it.
    *(The audit's "ignore `backend-kotlin/`" is moot — Phase 3c deleted that tree.)*
  - Full command table from `make help`, plus the note that `dev`/`backend`/`test` already
    run `doctor` first, so a stale venv repairs itself.
  - **New-entity checklist**, each step anchored to the real file it lands in:
    model → service → GraphQL type + `Input` → resolver → `queries.ts` → `make codegen` →
    component → test → `make reset-db` if a model changed.
  - Conventions: integer minor units; one `Input` per mutation; services own the transaction
    boundary and are the only place that commits; `DomainError` + a **new code, not a new
    class**; never re-add `drop_all`; `create_all` doesn't alter tables ⇒ `make reset-db`;
    never hand-edit `generated/graphql.ts`; `strictScalars` needs a `scalars:` entry for any
    new scalar; config from `config.py` / `env.js`, never literals.
- [x] `.claude/settings.json` — allows `Bash(make *)`, `Bash(uv run *)`, `Bash(npm run *)`,
  `Bash(curl localhost*)`, `Bash(sqlite3 *)`. **No hooks** (decision A.22 — a `PostToolUse`
  ruff auto-fix muddies the diff and can surprise you mid-demo; `make lint` stays on demand).
  - **Also added: `"defaultMode": "acceptEdits"`.** `~/.claude/settings.json` sets
    `defaultMode: "plan"` globally, and project settings take precedence — without this
    override the allowlist would have bought nothing until you manually left plan mode at
    minute zero. Scoped to this repo only.
- [x] ~~Root `README.md` — prepend an "ACTIVE PATH" note~~ **Not needed.** Phase 3c already
  rewrote the README for the single stack: it opens with the stack, and its Layout section
  already flags `api/rest/` as unused. The note would duplicate what is there.

**Verified:** `make test` 7 passed · `make check` clean · `make dev` boots both servers,
GraphQL returns the seeded rows with the right CORS header, `createMessage` succeeds, an
empty-content mutation still returns `extensions.code = VALIDATION_ERROR`, frontend 200,
and no `frontend/.env` was created.

### Phase 5b — Retire the old working copy ✅ **DONE 2026-08-27**

Deleted `~/Documents/Code/interview_prep_2026/brex/ai-assisted-coding` (**611 MB**, almost
all `.venv` + `node_modules`) — the iCloud-synced path blamed for the venv corruption above.
Redundancy confirmed before deleting:

- Old repo (`fullstack-server-test/ai_assisted_coding_interview`): clean tree, no stashes, no
  extra local branches, HEAD `e471383` — an **ancestor** of the new repo's `ea1b7b1`, which
  `git ls-remote` confirms is already on GitHub.
- `diff -rq` of the two source trees (excluding `node_modules`/`.venv`/`.git`/caches/DBs)
  differed in exactly **2 files** — `.gitignore` and `frontend/package-lock.json` — both
  accounted for by `ea1b7b1`, which the old copy predates.
- `docs/scaffold-audit.md` byte-identical in both locations.
- `fullstack-server-test-personal/` was empty (0 B); the sibling `.venv` was the empty
  Python 3.14 one from audit §2.
- Re-added the `upstream` remote the old clone had
  (`github.com/brexhq/ai_assisted_coding_interview`), the only thing it carried that the new
  repo lacked.

**Note:** `docs/` is gitignored (deliberate — prep notes stay off GitHub), so this file now
exists in exactly one place: `~/code/brex-interview-scaffold/docs/`. `~/code` is not
iCloud-synced, so it is safe from the sync corruption — but it is also not backed up.

### Phase 6 — Rehearsal *(this is the actual prep)*
- [ ] **Run A:** accounts + balances → transfer with idempotency key → transfer history → insufficient-funds UI
- [ ] **Run B:** points earn / redeem / expire → leaderboard → admin adjustment with audit log
- [ ] Each run timed at 50 min. Afterwards, log every stall and fix it **in the scaffold or `CLAUDE.md`** — never in memory
- [ ] Rehearse the boring path too: backend boot, frontend boot, one mutation, `make codegen`, `make test`, `make reset-db`

## E. Deliberately deferred — narrate, don't build

Say these out loud when relevant; each is a point, not a gap:

- **Migrations** — "Dev is `create_all` + reseed; a column change means `make reset-db`. Production would be Alembic."
- **Row locking** — "SQLite serializes writers, so this is correct here. On Postgres I'd `SELECT … FOR UPDATE` the source account, or use an optimistic `version` column."
- **Concurrency test** — "I'd add a two-thread contention test against Postgres in CI."
- **Idempotency** — "`UNIQUE(idempotency_key)` on the transfer table; a retry returns the original result instead of double-charging."
- **Invariants in the DB** — `CHECK (balance >= 0)`, FKs on — "not just validated in Python."
- **Ledger vs. balance column** — know the trade-off; pick the simpler one *deliberately* and say why.
- **`Int` is 32-bit in GraphQL** — integer cents caps around $21M; a real system uses a `BigInt`/string scalar.
- Also deferred: auth, cursor pagination, request-id/structured logging, observability, frontend tests, Docker.

## F. Definition-of-Done script *(corrected)*

> "In 50 minutes I ship: a schema change applied by resetting and reseeding the dev database, a typed GraphQL API with input types and stable error codes, UI wired through generated hooks, and one integration test per resolver. I'm deliberately deferring Alembic migrations — `create_all` doesn't alter existing tables, so a column change here means an explicit DB reset, which is fine for dev and not for production. Also deferred: auth, cursor pagination, structured logging, and Postgres row locking — SQLite serializes writers so this is correct locally, and I'd add `with_for_update()` plus a contention test in CI."

## G. Review log — first draft → this revision

**Accepted (the review was right):**
1. `create_all()` does not migrate existing tables — the original DoD sentence was **false**. Corrected in §F.
2. The "in-memory SQLite + rollback per test" fixture is genuinely fragile with `TestClient` threading and a committing service layer. Switched to temp-file DB per test (§A.17).
3. Deleting `backend-kotlin/` (22 of 58 tracked files) and the REST layer is a large unrelated diff against a scaffold that intentionally offers alternatives. Reversed (§A.2, §A.3).
4. The `≈30–45 min` verdict contradicted the multi-hour plan beneath it. Corrected in Part 1.
5. Don't mix `uv pip install -e .` with `uv sync`; don't auto-run `ruff --fix` on every agent edit. Both applied.
6. Missed entirely by the first draft: **codegen maps unmapped custom scalars to `any`** — added as §A.18. Verified: `codegen.ts` has no `scalars` config today.

**Declined, with reasons:**
1. *"Defer the service layer."* Kept a ~10-line `services/` module — it's where a transfer's transaction boundary lives and it's the API-design signal. Dropped the Unit-of-Work abstraction, which *was* over-build.
2. *"Defer generic domain-error plumbing."* Kept exactly **one** `DomainError` + `code` (~15 lines) because insufficient-funds is the likeliest unhappy path. Dropped the error taxonomy.
3. *"Defer the `make dev` process manager."* Makefile *aliases* aren't a process manager, cost nothing, and supply the `reset-db` command the review itself asked for. Dropped only the concurrent `make dev` target.

**Contested framing:** `CLAUDE.md` is tool-specific, but "AI Collaboration & Iteration" is an explicitly scored criterion, so a conventions file is how you score it — kept, with an optional `AGENTS.md` pointer for portability.
