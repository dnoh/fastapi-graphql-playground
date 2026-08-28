# REHEARSAL ONLY — example prompt, not committed

> Private scratch (`docs/` is gitignored). This is the **published example**
> prompt, used to rehearse. Do not commit it.
>
> On the day: `cp docs/requirements/_template.md docs/requirements/<name>.md`,
> fill it from the real prompt, and commit that one — it is a legitimate
> artifact of how you worked.
>
> Rehearse with: `/plan docs/rehearsal-requirements.md`

## Requirements

Verbatim ask:

> Build a small but correct full-stack web application that supports basic monetary
> transactions and account balances. Evaluated on correctness and judgment, not on
> breadth or styling — the scenario is deliberately small so the money-correctness
> decisions stand out.

1. **Backend API** — REST *or* GraphQL (pick one, justify it) that can:
   create accounts; post a transaction (credit or debit) against an account;
   retrieve accounts with current balance, and a list of transactions.
2. **Persistence** — in-memory or a lightweight database, both acceptable.
3. **Frontend** — one page: create an account, submit a credit or debit,
   view current balance plus recent transactions.
4. **Validation & business rules** — non-negative amounts with at most 2 decimal
   places, required fields, unknown account and unknown transaction type rejected;
   **reject any debit that would drive an account below zero**.
5. **Tests** — happy paths and error cases (overdraw, malformed amount, unknown
   account), plus a unit test pinning money precision (e.g. `0.29` parses exactly).
6. **README** — setup/run instructions, API summary, stated assumptions.

## Constraints

- **Not building:** authentication or authorization (explicitly not required);
  cross-account transfers (out of scope — single-leg postings only); multi-currency
  or FX (one currency per account); double-entry ledger unless it falls out cheaply.
- **Time:** 50 minutes.
- **Demo:** every milestone independently demoable; work may stop after any one.

## Decisions

- **GraphQL**, not REST — the scaffold's typed schema plus codegen means the UI is
  type-checked against the API, which is a correctness argument, not a taste one.
- **SQLite**, not in-memory — in-memory is allowed, but a real DB lets the overdraw
  check be a conditional `UPDATE` and lets `CHECK (balance >= 0)` hold the invariant.
- **Denormalized `balance_cents` column** on the account, with the invariant
  `balance == Σ(credits) − Σ(debits)` asserted in a test — not a balance recomputed
  from the ledger on every read.
- **Amounts cross the API as decimal strings**, parsed to integer cents with
  `Decimal`. Never `Float`, and not `Int` at the boundary — `Int` is 32-bit.

## Ask the interviewer

1. In-memory acceptable for the final submission, or should I show a real
   persistence path?
2. Single-leg postings, or true double-entry transfers between two accounts?
3. What error shape/status do you expect on overdraw vs. malformed amount?
4. How should I split time between UI and backend/tests?
