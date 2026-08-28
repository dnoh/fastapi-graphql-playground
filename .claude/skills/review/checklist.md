# Engineering checklist

General, project-agnostic. Used by `/review` (Reviewer 4) and skimmed once by
`/plan`. Each section starts with an **Applies when** line — if it doesn't apply
to the change under review, skip the whole section. Domain-specific rules
(money, healthcare, etc.) belong in the repo's `CLAUDE.md`, not here.

The bar for every item: a concrete miss with a file:line. Not advice.

## 1. Data integrity
Applies when: the change writes to a store.
- Invariants enforced in the database (`NOT NULL`, `UNIQUE`, `CHECK`, FKs), not
  only in application code. App validation is the friendly message; the
  constraint is what holds.
- A multi-step write is one transaction — nothing commits between the steps.
- Read-then-write on the same row happens in one transaction (no check-then-act
  race across two).
- Existing stored data still loads after a schema change (new columns nullable
  or defaulted; no silent reinterpretation of old rows).
- No floating-point storage or arithmetic for exact quantities (money, counts,
  units). Integers or decimal types.
- IDs are not guessable where enumeration would leak information.
- Deletions: soft-delete vs hard-delete chosen deliberately; cascades explicit.

## 2. API design
Applies when: the change adds or modifies an externally callable interface.
- Inputs are a named type/object, not a growing positional argument list.
- Errors carry a stable machine-readable code; clients never string-match a
  message.
- Mutating operations are idempotent where a retry is plausible (network,
  mobile, queues) — via a client-supplied key with a uniqueness constraint.
- List endpoints bound their result size (a max page size, cursor or offset).
- Backward compatible: existing callers keep working; removed fields are
  deprecated first, not deleted.
- Nullability is intentional: a field is optional because it can genuinely be
  absent, not because it was easier.
- Timestamps are timezone-aware (UTC in storage, explicit offset on the wire).

## 3. Input validation & injection
Applies when: the change accepts untrusted input.
- Validate at the boundary (type, range, length, format); trust nothing past it.
- Queries are parameterized — never built by string formatting. Same for shell
  commands, file paths, and templates.
- Output is encoded for its destination (HTML, URL, SQL, shell) — don't rely on
  input sanitization alone.
- Size limits on request bodies, uploads, list lengths, and string fields.
- Path traversal: user-supplied file names never reach the filesystem unmapped.

## 4. Authentication & authorization
Applies when: the change exposes an operation or data that not everyone should
reach. If the project has declared auth out of scope, confirm it's named as a
non-goal and stop here.
- Every operation checks *who* (authn) and *whether they may* (authz) — on the
  server, never only in the UI.
- Authorization is by ownership or role on the object, not just "logged in".
- Secrets and tokens are never logged, never in URLs, never in the repo.
- Sensitive operations re-check state server-side (don't trust client-supplied
  balances, prices, roles).
- Rate limiting or abuse controls on anything that costs money, sends messages,
  or can enumerate.

## 5. Concurrency
Applies when: two requests could touch the same row or resource at once.
- Contended updates use row locks, optimistic versioning, or atomic
  `UPDATE … WHERE` — not read-modify-write in application memory.
- Uniqueness is enforced by a constraint, not by a "check if exists" query.
- Background or async work is idempotent and safe to retry.
- No shared mutable state across requests in a multi-worker server.

## 6. Error handling & failure modes
Applies when: the change can fail partway through.
- Expected failures (validation, not-found, conflict) are distinct from bugs
  (5xx); the former are user-visible with a code, the latter are logged with
  a stack trace.
- Partial failure leaves the system consistent (transaction rolled back, no
  half-written state, no orphaned side effects).
- External calls (HTTP, queue, email) have a timeout and a decision about what
  happens when they fail — and are not inside a database transaction.
- Retries have a bound and, where relevant, backoff.
- Errors don't leak internals (stack traces, SQL, file paths) to clients.

## 7. Observability
Applies when: the change adds behavior someone will need to debug in production.
- Log at the boundary of each significant operation with enough context to
  correlate (request or entity id), without PII or secrets.
- Failures are logged once, at the layer that handles them — not at every
  layer they pass through.
- Anything with a business consequence (money moved, permissions changed,
  records deleted) leaves an audit trail with who/what/when.

## 8. Testing
Applies when: always.
- Tests exist for the happy path, each documented error code, and the edge
  cases specific to this domain — not just null checks.
- Tests assert observable behavior (response, stored state), not
  implementation details (which method was called).
- A test that was changed to pass was changed for a reason stated in the diff.
- Tests are deterministic: no wall-clock dependence, no ordering dependence,
  no shared state between tests.
- If the change touches existing behavior, a regression test guards it.

## 9. Configuration & operability
Applies when: the change introduces something environment-dependent.
- URLs, credentials, feature flags, and limits come from config/env with a
  safe default — no literals in code.
- A new required config value fails loudly at startup, not on first use.
- Dev/test defaults can't accidentally be used in production (and vice versa).

## 10. Scope discipline
Applies when: always.
- Nothing in the diff is speculative — every abstraction has a concrete second
  use today, or it's a plain function.
- No drive-by refactors or unrelated formatting changes mixed in.
- Anything deliberately deferred is written down as a non-goal, not silently
  skipped.
