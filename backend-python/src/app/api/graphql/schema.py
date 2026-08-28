"""GraphQL schema — the active API surface.

Resolvers stay thin: unwrap arguments, call a service, return. No business
logic, no commits. `domain_errors` maps a DomainError onto a GraphQL error
carrying `extensions.code`.
"""

from collections.abc import Callable
from datetime import datetime
from functools import wraps
from typing import Any
from uuid import UUID

import strawberry
from fastapi import Depends
from graphql import GraphQLError
from sqlalchemy.orm import Session
from strawberry.types import Info

from ...database.session import get_db
from ...errors import DomainError
from ...services import messages as message_service


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


schema = strawberry.Schema(query=Query, mutation=Mutation)
