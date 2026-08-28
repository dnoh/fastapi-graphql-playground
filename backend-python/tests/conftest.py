"""Test fixtures.

Design notes (deliberate, and worth being able to explain):

  - Each test gets its own temp-FILE SQLite database, not `:memory:`.
    TestClient serves requests from a threadpool, and an in-memory SQLite
    database is per-connection — so a threaded test would silently talk to a
    different, empty database unless you wire up StaticPool. A temp file
    sidesteps that entirely and costs ~1ms.

  - Tables are created per test and the file is thrown away after, so tests
    are fully isolated. We do NOT use a rollback-per-test fixture: the service
    layer commits (it owns the transaction boundary), which would defeat it.

  - TestClient is built WITHOUT a `with` block on purpose. Entering the context
    manager runs the app's lifespan, which would create and seed the real
    ./app.db. We only need request routing, not startup.
"""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.database.session import get_db
from app.main import app
from app.models.base import Base


@pytest.fixture
def engine(tmp_path) -> Iterator[Engine]:
    eng = create_engine(
        f"sqlite:///{tmp_path / 'test.db'}",
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(eng, "connect")
    def _enable_foreign_keys(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=eng)
    yield eng
    eng.dispose()


@pytest.fixture
def session_factory(engine: Engine):
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)


@pytest.fixture
def db(session_factory) -> Iterator[Session]:
    """A session for arranging test data directly."""
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(session_factory) -> Iterator[TestClient]:
    """HTTP client wired to the per-test database."""

    def override_get_db() -> Iterator[Session]:
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def graphql(client: TestClient):
    """POST a GraphQL document and return the parsed JSON body."""

    def _post(query: str, variables: dict | None = None) -> dict:
        response = client.post("/graphql", json={"query": query, "variables": variables or {}})
        assert response.status_code == 200, response.text
        return response.json()

    return _post
