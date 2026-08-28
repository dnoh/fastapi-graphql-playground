# Domain rules: money

Applies to any feature that stores or moves monetary value — balances, transfers,
payments, refunds, ledgers. Activated by an `@.claude/domains/money.md` line in
`CLAUDE.md`. Remove that line for features that don't touch money.

These are correctness rules, not style. Each one changes what gets *built*;
general good practice lives in `.claude/skills/review/checklist.md`.

## Rules

- **Integer minor units (cents). No floating-point arithmetic on money, ever** —
  not in Python, not in SQL, not in the browser. `0.1 + 0.2 != 0.3`. Divide only
  for display.
- **One commit per operation.** A transfer is debit + credit (+ ledger row) and then
  a single `commit()` in the service. Never commit between the legs — a crash there
  destroys money.
- **Read and write the balance in the same transaction.** "Is there enough?" and the
  debit must happen inside one service call; split across two transactions it's a race.
- **Invariants in the database, not only in Python.** `CHECK (balance >= 0)`,
  `UNIQUE(idempotency_key)`, FKs on. App validation is the friendly message; the
  constraint is what holds.
- **Idempotency is a `UNIQUE` column, not an app-level check.** A retried request
  returns the original result; it never double-charges.
- **Mind the integer ceiling.** GraphQL `Int` is 32-bit — integer cents cap near
  $21M. Fine for a demo; say so rather than discover it. A real system uses a
  `BigInt`/string scalar.
- **Every movement leaves an audit trail** — who, what, when, and the resulting
  balance. Money that moved without a record didn't happen, legally.

## Deferred by choice — say it, don't build it

- **Row locking** — SQLite serializes writers, so the code is correct here. On
  Postgres: `SELECT … FOR UPDATE` on the source account, or an optimistic
  `version` column.
- **Concurrency test** — a two-thread contention test belongs in CI against Postgres.
- **Ledger vs. balance column** — know the trade-off, pick the simpler one on purpose.
- **Multi-currency, FX, rounding on splits** — single currency in the MVP; name it
  as a non-goal.
