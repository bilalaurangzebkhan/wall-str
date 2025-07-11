from collections.abc import AsyncGenerator

from fastapi import Request
from pydantic import SecretStr
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine as _create_async_engine

from wallstr.conf import settings

type AsyncSessionMaker = async_sessionmaker[AsyncSession]


def create_async_engine(url: SecretStr, application_name: str) -> AsyncEngine:
    return _create_async_engine(
        url.get_secret_value(),
        echo=settings.DEBUG_SQL,
        connect_args={"server_settings": {"application_name": application_name}},
    )


def create_session_maker(engine: AsyncEngine) -> AsyncSessionMaker:
    return async_sessionmaker(
        engine,
        expire_on_commit=False,
        autobegin=False,
        autoflush=False,
    )


async def get_db_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    session_maker = request.state.session_maker
    async with session_maker() as session:
        yield session
