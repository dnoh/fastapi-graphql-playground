"""Integration tests for the message API.

One test per resolver plus one per failure mode. Copy this shape for every new
entity: happy-path query, happy-path mutation, and the error code.
"""

import pytest

from app.errors import DomainError
from app.models.message import Message
from app.services import messages as message_service

LATEST = """
query Latest($limit: Int) {
  latestMessages(limit: $limit) { id content createdAt }
}
"""

CREATE = """
mutation Create($input: CreateMessageInput!) {
  createMessage(input: $input) { id content createdAt }
}
"""


def test_latest_messages_returns_newest_first(db, graphql):
    for content in ["first", "second", "third"]:
        message_service.create_message(db, content=content)

    body = graphql(LATEST, {"limit": 10})

    assert "errors" not in body, body
    contents = [m["content"] for m in body["data"]["latestMessages"]]
    assert contents == ["third", "second", "first"]


def test_latest_messages_is_empty_on_a_fresh_database(graphql):
    body = graphql(LATEST, {"limit": 10})
    assert body["data"]["latestMessages"] == []


def test_create_message_persists_and_returns_it(db, graphql):
    body = graphql(CREATE, {"input": {"content": "hello from a test"}})

    assert "errors" not in body, body
    assert body["data"]["createMessage"]["content"] == "hello from a test"
    assert db.query(Message).count() == 1


def test_create_message_rejects_blank_content_with_a_stable_code(graphql):
    body = graphql(CREATE, {"input": {"content": "   "}})

    assert body["data"] is None or body["data"].get("createMessage") is None
    assert body["errors"][0]["extensions"]["code"] == "VALIDATION_ERROR"


def test_create_message_rejects_overlong_content(graphql):
    body = graphql(CREATE, {"input": {"content": "x" * 256}})
    assert body["errors"][0]["extensions"]["code"] == "VALIDATION_ERROR"


def test_service_raises_domain_error_directly(db):
    """The service is usable without HTTP — errors are domain-level, not web-level."""
    with pytest.raises(DomainError) as exc_info:
        message_service.create_message(db, content="")
    assert exc_info.value.code == "VALIDATION_ERROR"


def test_list_latest_clamps_an_absurd_limit(db):
    message_service.create_message(db, content="only one")
    assert len(message_service.list_latest(db, limit=10_000)) == 1
