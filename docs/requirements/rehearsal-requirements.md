# Accounts & transactions (rehearsal)

> Committed on purpose: `docs/requirements/` is the plan pipeline's input, and
> this is the published example prompt used to rehearse it. On the day, copy
> `_template.md` to `docs/requirements/<name>.md`, fill it from the real prompt,
> and commit that too — it is a legitimate artifact of how you worked.
>
> Rehearse with: `/plan docs/requirements/rehearsal-requirements.md`

A small, correct full-stack app for monetary transactions and account balances.

## Context

> Build a small but correct full-stack web application that supports basic monetary
> transactions and account balances. Evaluated on correctness and judgment, not on
> breadth or styling — the scenario is deliberately small so the money-correctness
> decisions stand out.

**Requirements**

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

**Constraints**

7. **Not building:** authentication or authorization (explicitly not required);
   cross-account transfers (out of scope — single-leg postings only); multi-currency
   or FX (one currency per account); double-entry ledger unless it falls out cheaply.
8. **Time:** 50 minutes.
9. **Demo:** every milestone independently demoable; work may stop after any one.
