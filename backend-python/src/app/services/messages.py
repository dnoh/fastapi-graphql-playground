"""Message business logic.

Rules for this layer (see CLAUDE.md):
  - All business rules and validation live here, never in a resolver.
  - This is the ONLY place that calls session.commit() — it owns the
    transaction boundary. For a multi-step operation (e.g. a transfer:
    debit + credit + ledger row) do all the writes, then commit ONCE.
  - Raise DomainError with a stable code for expected failures.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..errors import DomainError
from ..models.message import Message

MAX_CONTENT_LENGTH = 255
MAX_PAGE_SIZE = 100


def list_latest(db: Session, limit: int = 10) -> list[Message]:
    """Most recent messages first. `limit` is clamped, never trusted."""
    limit = max(1, min(limit, MAX_PAGE_SIZE))
    stmt = select(Message).order_by(Message.created_at.desc()).limit(limit)
    return list(db.scalars(stmt))


def create_message(db: Session, content: str) -> Message:
    content = (content or "").strip()
    if not content:
        raise DomainError("Message content must not be empty", code="VALIDATION_ERROR")
    if len(content) > MAX_CONTENT_LENGTH:
        raise DomainError(
            f"Message content must be {MAX_CONTENT_LENGTH} characters or fewer",
            code="VALIDATION_ERROR",
        )

    message = Message(content=content)
    db.add(message)
    db.commit()  # transaction boundary
    db.refresh(message)
    return message
