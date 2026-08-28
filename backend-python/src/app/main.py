import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from strawberry.fastapi import GraphQLRouter

from .api.graphql.schema import get_context, schema
from .api.rest import messages
from .config import settings
from .database.seed import seed_database
from .database.session import SessionLocal, engine
from .models.base import Base

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Create tables and seed on startup.

    NOTE: create_all() is CREATE TABLE IF NOT EXISTS — it does NOT add columns
    to tables that already exist. After changing a model, run `make reset-db`.
    Never add drop_all() here: with --reload it wipes your data on every save.
    """
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        inserted = seed_database(db)
        logger.info("startup: seeded %d rows", inserted)
    except Exception:
        logger.exception("startup: seeding failed")
    finally:
        db.close()

    yield


app = FastAPI(title="Brex Interview Playground", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=settings.cors_origin_regex or None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# REST API — supplied scaffold alternative, unused by the frontend.
app.include_router(messages.router, prefix="/api")

# GraphQL — the active path.
graphql_app = GraphQLRouter(schema, context_getter=get_context)
app.include_router(graphql_app, prefix="/graphql")
