"""GraphQL schema — the active API surface.

Resolvers stay thin: unwrap arguments, call a service, return. No business
logic, no commits. `domain_errors` maps a DomainError onto a GraphQL error
carrying `extensions.code`.
"""

import logging
from collections.abc import Callable
from datetime import datetime
from functools import wraps
from typing import Any
from uuid import UUID

import strawberry
from fastapi import Depends
from graphql import GraphQLError
from sqlalchemy.orm import Session
from strawberry.types import ExecutionContext, Info

from ...database.session import get_db
from ...errors import DomainError
from ...services import messages as message_service

logger = logging.getLogger(__name__)


def domain_errors(resolver: Callable[..., Any]) -> Callable[..., Any]:
    """Surface DomainError as a client-visible error with a stable code."""

    @wraps(resolver)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return resolver(*args, **kwargs)
        except DomainError as exc:
            raise GraphQLError(exc.message, extensions={"code": exc.code}) from exc

    return wrapper


@strawberry.type
class Message:
    id: UUID
    content: str
    created_at: datetime


@strawberry.input
class CreateMessageInput:
    content: str


async def get_context(db: Session = Depends(get_db)) -> dict[str, Session]:
    return {"db": db}


@strawberry.type
class Query:
    @strawberry.field
    @domain_errors
    def latest_messages(self, info: Info, limit: int | None = 10) -> list[Message]:
        db: Session = info.context["db"]
        return message_service.list_latest(db, limit=limit or 10)


@strawberry.type
class Mutation:
    @strawberry.mutation
    @domain_errors
    def create_message(self, info: Info, input: CreateMessageInput) -> Message:
        db: Session = info.context["db"]
        return message_service.create_message(db, content=input.content)


def _domain_error_behind(error: GraphQLError) -> DomainError | None:
    """The DomainError behind a GraphQL error, if this was an expected failure."""
    cause: BaseException | None = error.original_error
    for _ in range(4):  # bounded: the chain is GraphQLError -> DomainError
        if isinstance(cause, DomainError):
            return cause
        if cause is None:
            return None
        cause = cause.__cause__
    return None


class Schema(strawberry.Schema):
    """A schema that does not log expected failures as if they were bugs.

    Strawberry logs every GraphQL error with a stack trace. A wrong password or
    an insufficient balance is a documented outcome, not a defect, and the login
    lock guarantees repeats — tracebacks for those would bury the real errors.
    Anything without a DomainError behind it keeps its full traceback.
    """

    def process_errors(
        self,
        errors: list[GraphQLError],
        execution_context: ExecutionContext | None = None,
    ) -> None:
        unexpected = []
        for error in errors:
            domain_error = _domain_error_behind(error)
            if domain_error is None:
                unexpected.append(error)
            else:
                logger.info("graphql: rejected with %s: %s", domain_error.code, error.message)
        if unexpected:
            super().process_errors(unexpected, execution_context)


schema = Schema(query=Query, mutation=Mutation)
