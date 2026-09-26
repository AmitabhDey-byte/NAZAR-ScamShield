from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    pass


# Neon and other hosted PostgreSQL providers commonly include libpq query
# parameters such as ``sslmode`` and ``channel_binding`` in their connection
# URLs.  Those parameters are understood by psycopg (used by Alembic), but
# asyncpg does not accept them as keyword arguments.  Remove them from the
# async URL and translate the common ``sslmode=require`` setting to asyncpg's
# ``ssl=True`` option.
def _async_engine_config() -> tuple[object, dict[str, object]]:
    url = make_url(settings.async_database_url)
    connect_args: dict[str, object] = {}

    sslmode = url.query.get("sslmode")
    if sslmode:
        url = url.difference_update_query(["sslmode"])
        if sslmode not in {"disable", "allow", "prefer"}:
            connect_args["ssl"] = True

    # asyncpg negotiates channel binding itself and has no channel_binding
    # connect() keyword, so this libpq-only query parameter must be removed.
    if "channel_binding" in url.query:
        url = url.difference_update_query(["channel_binding"])

    return url, connect_args


_async_url, _async_connect_args = _async_engine_config()
engine = create_async_engine(
    _async_url,
    pool_pre_ping=True,
    echo=False,
    connect_args=_async_connect_args,
)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


async def init_db() -> None:
    from app import models  # noqa: F401

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
