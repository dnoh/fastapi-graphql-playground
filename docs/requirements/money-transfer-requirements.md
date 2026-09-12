# Peer-to-peer money transfer

A prototype where users hold an account, send money to each other, and see history and balance.

## Context

We are building a peer to peer money-transfer product prototype. Users should be able to hold an account, send money to another user, view transfer history, and see an accurate balance.

Requirements:
1. Users can hold and register for an account
2. Users should be able to send money to another user
3. Users should be able to view transfer history and see an accurate balance represented in the smallest currency unit for example, cents/

Constraints:
Information can be stored in SQLlite or In Memory for the prototype. The prototype should preserve money safely across crashes, retries, and concurrent requests. Correct money semantics. No overdrafts, no duplicat debits, and no state where the sender is debited whiule the reviever is not credited. Idempotent transfer requests. Scalable for concurrent transfers as well as fauilure recovery and auditablility.
