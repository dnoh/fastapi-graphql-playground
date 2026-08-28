"""Development seed data.

Idempotent on purpose: it runs on every boot, so it must never duplicate rows.
Add new rows by extending the list — keep it small and realistic.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.message import Message

SEED_MESSAGES: list[dict] = [
    {"content": "Hello World"},
    {"content": "Second message"},
    {"content": "Third message"},
]


def seed_database(db: Session) -> int:
    """Insert seed rows if the table is empty. Returns the number inserted."""
    already_seeded = db.scalar(select(Message).limit(1)) is not None
    if already_seeded:
        return 0

    db.add_all([Message(**row) for row in SEED_MESSAGES])
    db.commit()
    return len(SEED_MESSAGES)
