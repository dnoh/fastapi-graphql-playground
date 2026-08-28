# Accounts & Transactions

A single-currency ledger: open an account, post credits/debits, read the balance with its history.

## Requirements

| # | Ask | Decision |
|---|---|---|
| R1 | Create accounts | `createAccount` → account number, balance 0 |
| R2 | Post debit/credit against an account | `postTransaction` |
| R3 | Retrieve accounts + balance + transaction list | `accounts`, `account`, `Account.transactions` |
| R4 | UI: create, log in, submit, view balance + recent | `/` — picker + account view |
| C1 | SQLite | existing engine, unchanged |
| C2 | Conceal PII | email never returned; name masked on read |
| C3 | Non-negative, ≤2 decimal places | `Decimal` parse at the boundary |
| C4 | Prevent negative balances | conditional `UPDATE` + DB `CHECK` |
| C5 | README section: setup, API, assumptions | appended below existing contents |
| C6 | Never float | integer cents end to end |
| C7 | Single currency | `currency` fixed at `USD` |
| C8 | Cross-account transfers | **Non-goal** |
| C9 | No auth | **Non-goal** — "login" = client-side account selection |
| C10 | Correctness over breadth | governs every row above |
| C11 | GraphQL over REST | GraphQL only; REST scaffold untouched |

**Also non-goals** (from `CLAUDE.md`): migrations, row locking, cursor pagination, structured logging, frontend tests, Docker, multi-currency/FX, editing or reversing a transaction, card processing — R4's "credit or debit card" is read as credit/debit *transactions*.

## Entities & Data Models

Both new tables. No migrations — `make reset-db` after each.

**`accounts`**

| Column | Type | Constraints |
|---|---|---|
| `id` | UUID | PK |
| `account_number` | String(10) | NOT NULL, UNIQUE — the only public identifier |
| `owner_name` / `owner_email` | String(100) / String(255) | NOT NULL, PII |
| `currency` | String(3) | NOT NULL, default `USD` |
| `balance_cents` | Integer | NOT NULL, default 0, `CHECK (>= 0)` |

Why: balance is denormalized for O(1) reads and so the overdraw check can be one conditional `UPDATE`. **Invariant:** `balance_cents == Σ credits − Σ debits`.

**`transactions`**

| Column | Type | Constraints |
|---|---|---|
| `id` | UUID | PK |
| `account_id` | UUID | FK → `accounts.id`, indexed |
| `kind` | CREDIT / DEBIT | NOT NULL |
| `amount_cents` | Integer | NOT NULL, `CHECK (> 0)` — always positive; `kind` carries direction |
| `balance_after_cents` | Integer | NOT NULL — the audit trail |
| `description` | String(255) | nullable |
| `idempotency_key` | String(64) | nullable, `UNIQUE (account_id, key)` |

Why: append-only. To undo a transaction, post its opposite.

## API & Interfaces

```graphql
type Account { id: UUID!  accountNumber: String!  ownerNameMasked: String!
               currency: String!  balanceCents: Int!  createdAt: DateTime!
               transactions(limit: Int = 20): [Transaction!]! }
type Transaction { id: UUID!  kind: TransactionKind!  amountCents: Int!
                   balanceAfterCents: Int!  description: String  createdAt: DateTime! }

input CreateAccountInput  { ownerName: String!, ownerEmail: String! }
input PostTransactionInput { accountNumber: String!, kind: TransactionKind!,
                             amount: String!, description: String, idempotencyKey: String }

accounts(limit: Int = 50): [Account!]!    account(accountNumber: String!): Account!
createAccount(input:): Account!           postTransaction(input:): Transaction!
```

| Choice | Why |
|---|---|
| `amount` is a decimal **string** | C3 is phrased in decimal places; `Decimal("0.29").scaleb(2)` is exactly 29, `float` gives 28.999… |
| `ownerNameMasked`, no email field | PII leak becomes a schema error, not a review catch |
| `Int` cents, not a BigInt scalar | caps at ~$21.4M; rejected at the boundary, documented |

| Error code | When |
|---|---|
| `VALIDATION_ERROR` | bad name/email; amount not a positive decimal with ≤2 places; over the ceiling |
| `NOT_FOUND` | unknown `accountNumber` |
| `INSUFFICIENT_FUNDS` | debit rejected by the guarded `UPDATE` |
| `IDEMPOTENCY_CONFLICT` | key reused with a different amount or kind |

## Data Flow

Queries follow the repo's standard resolver → service → session path. Only `postTransaction` departs from it:

```
postTransaction(input)
1. parse amount → Decimal → integer cents        [VALIDATION_ERROR]
2. validate description ≤255, key ≤64            [VALIDATION_ERROR]
3. look up account by number                     [NOT_FOUND]
4. if key already used on this account → return original, or [IDEMPOTENCY_CONFLICT]
5. UPDATE accounts SET balance = balance ∓ amt
     WHERE id = ? AND balance >= amt   (credit: AND balance <= MAX - amt)
     RETURNING balance                            [0 rows → INSUFFICIENT_FUNDS]
6. INSERT ledger row, balance_after = the RETURNING value
7. COMMIT — once, covering steps 5 and 6
   (IntegrityError → rollback both, return the concurrent winner's row)
```

Step 5 is the whole design: the balance check is *in the WHERE clause*. Read-then-write is a lost update — two concurrent debits both read the old balance and both pass. This stays correct on Postgres `READ COMMITTED`.

## Trade-offs

| Decision | Rejected | Why | Open? |
|---|---|---|---|
| "Login" = pick an account | PIN on the account | C9 forbids auth; a PIN is fake security | |
| Store PII, mask on read | store none / return all | C2 needs something concealed; the UI needs a greeting | |
| Reject zero amounts | allow 0 per literal "non-negative" | moves nothing, pollutes the ledger | **yes** |
| Denormalized balance + `balance_after` | derive via `SUM()` | O(1) reads; enables the one-statement guard | **yes** |
| Idempotency key optional, per-account | global UNIQUE; silent replay | one client's key can't collide with another account's | |
| `/` becomes the bank UI | keep `/` as messages, add `/bank` | the feature is the demo; scaffold moves to `/messages` | |
| No `initialDeposit` on create | accept an opening balance | a credit does the same job and stays on the ledger | |

## Milestones

| # | Milestone | Demoable when | Size |
|---|---|---|---|
| M1 — [ ] | Accounts end-to-end | create + list accounts in the browser, name masked | ~330 |
| M2 — [ ] | Transactions backend | credit/debit/overdraft/replay in GraphiQL | ~380 |
| M3 — [ ] | Account UI + README | full R4 flow in the browser | ~300 |

**M1** `Account` model + service (`create_account`, `list_accounts`, `get_by_number`, `mask_name`), GraphQL type + `createAccount` + `accounts`/`account`, `AccountPicker`, `lib/money.ts`; messages move to `/messages`.
*Tests:* masked name · no PII anywhere in the serialized response · newest-first · `NOT_FOUND` · `VALIDATION_ERROR` on blank name and bad email · distinct account numbers · limit clamped.

**M2** `Transaction` model, `parse_amount_cents`, `post_transaction`, `list_for_account`, GraphQL enum + type + `postTransaction` + nested `Account.transactions`; seeded through the service so the balance can't lie.
*Tests:* parse table (`0.29`→29; reject `1.005`, `-1`, `0`, `NaN`, `Infinity`, ceiling) · overdraft leaves balance *and* ledger untouched · exact-balance debit · `NOT_FOUND` · replay vs conflict · balance invariant recomputed from the ledger · both DB `CHECK`s forced through the ORM.

**M3** `GET_ACCOUNT`/`POST_TRANSACTION`, `AccountView`, `BankPanel` (selection + `localStorage`), README section.
*Tests:* none new — frontend tests are deferred; `make check` type-checks the generated hooks against the components.

*Verify (all):* `make reset-db && make codegen && make test && make check` — `reset-db` only on a model change, `codegen` only on a schema change.

## Appendix — the ask, verbatim

Source: `docs/requirements/money-transfer-requirements.md`

```
## Requirements

1. Create accounts
2. Post a transaction (debit or credit) againist an account
3. Retrieve accounts (with current balance) and a list of transactions
4. User can create an account, login to account, submit credit or debit card transactions, and view their current balance plus recent transactions via UI.

## Constraints

1. Utilize SQLlite as a lightweightDB
2. Conceal sensitive information (PII)
3. Validate inputs (non-negative amounts with up to 2 decimal places)
4. Prevent negative balances (reject any debit that would drive an account below zero)
5. Update the readme with a section below the existing contents with setup/run instructions, API summary, and any assumptions
6. Never store money as a floating point number
7. Single currency per account is acceptable. 
8. Cross account transfers are out of scope.
9. No authentication and authorization is required
10. Optimize for correctness and clarity over breadth
11. Use GraphQL over Rest
```
