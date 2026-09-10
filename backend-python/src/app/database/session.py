from collections.abc import Generator

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from ..config import settings

_is_sqlite = settings.database_url.startswith("sqlite")

engine = create_engine(
    settings.database_url,
    connect_args=(
        {
            # FastAPI serves requests from a threadpool, so the connection must
            # be usable from more than the thread that created it.
            "check_same_thread": False,
            # Bound how long a writer waits for the single write lock instead of
            # failing immediately with "database is locked".
            "timeout": settings.sqlite_busy_timeout_s,
        }
        if _is_sqlite
        else {}
    ),
)


@event.listens_for(Engine, "connect")
def _set_sqlite_pragmas(dbapi_connection, connection_record):
    """SQLite ships with foreign keys DISABLED. Turn them on for every connection.

    WAL lets readers proceed while a write is in flight. Both are no-ops on
    other backends, so this listener guards on the dialect via duck-typing.
    """
    if not _is_sqlite:
        return
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
