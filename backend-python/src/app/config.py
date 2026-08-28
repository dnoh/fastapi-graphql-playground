"""Application settings, sourced from the environment.

Every externally-configurable value lives here — no hardcoded URLs elsewhere.
Override any field with an env var of the same name (case-insensitive), e.g.
`DATABASE_URL=postgresql+psycopg://... uv run uvicorn app.main:app`.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # SQLite by default: zero setup. Swap to Postgres by setting DATABASE_URL.
    database_url: str = "sqlite:///./app.db"

    # Browser origins allowed to call this API.
    cors_origins: list[str] = ["http://localhost:3000"]

    # Next.js silently hops to :3001, :3002, ... when :3000 is taken. Matching
    # any localhost port keeps the app working instead of failing with an
    # opaque CORS error. Set CORS_ORIGIN_REGEX="" to disable.
    cors_origin_regex: str = r"http://localhost:\d+"


settings = Settings()
