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
- **The overdraw check happens INSIDE the write, never as a read-then-write.**
  A conditional update — `UPDATE accounts SET balance = balance - :amt WHERE id = :id
  AND balance >= :amt`, then reject when `rowcount == 0` — or an explicit row lock.
  Reading the balance, checking it in Python, then writing is a lost update: two
  concurrent debits both read the old balance and both pass. Being inside one
  transaction is necessary but NOT sufficient — under Postgres `READ COMMITTED` the
  naive version still races. Be able to say why.
- **Parse money from strings with `Decimal`, never `float`.** `float("0.29") * 100`
  is `28.999...`; `Decimal("0.29").scaleb(2)` is exactly `29`. Reject more than two
  decimal places and any negative amount at the boundary, and pin it with a unit test.
- **Balance is denormalized; state its invariant explicitly.**
  `balance == Σ(credits) − Σ(debits)`, and prove it in a test that posts several
  transactions and recomputes. A derived value nobody checks drifts.
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
