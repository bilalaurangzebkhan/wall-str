import asyncio
from collections.abc import AsyncGenerator, Generator

import pytest
import pytest_asyncio
import structlog
from fastapi import Request
from fastapi.testclient import TestClient
from sqlalchemy import sql
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from wallstr.auth.models import UserModel
from wallstr.conf import settings
from wallstr.db import create_async_engine, create_session_maker, get_db_session
from wallstr.logging import configure_logging
from wallstr.models.base import BaseModel
from wallstr.server import app

logger = structlog.get_logger(__name__)


@pytest_asyncio.fixture(scope="session")
async def session_engine() -> AsyncGenerator[AsyncEngine]:
    engine = create_async_engine(settings.DATABASE_URL, "test")
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def configure(session_engine: AsyncEngine) -> AsyncGenerator[None]:
    async with session_engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)
    configure_logging(name="test")
    yield
    async with session_engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.drop_all)


@pytest_asyncio.fixture
async def engine() -> AsyncGenerator[AsyncEngine]:
    logger.debug(f"engine event_loop: {id(asyncio.get_event_loop())}")
    engine = create_async_engine(settings.DATABASE_URL, "test")
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(
    engine: AsyncEngine,
) -> AsyncGenerator[AsyncSession]:
    logger.debug(f"db_session event_loop: {id(asyncio.get_event_loop())}")
    session_maker = create_session_maker(engine)
    session = session_maker()

    yield session
    await session.close()


@pytest.fixture
def client() -> Generator[TestClient]:
    async def _get_db_session(request: Request) -> AsyncGenerator[AsyncSession]:
        """
        This function was created for future to rollback the transaction after each test.
        Requires more tunnings due to transaction isolation levels.

        await session.begin()
        yield session
        await session.rollback()
        """
        logger.debug(f"TestClient event_loop: {id(asyncio.get_event_loop())}")
        session_maker = request.state.session_maker
        session = session_maker()

        yield session
        await session.close()

    app.dependency_overrides[get_db_session] = _get_db_session
    with TestClient(app=app, base_url="http://testwallstr/") as client:
        yield client
    app.dependency_overrides.pop(get_db_session)


@pytest_asyncio.fixture
async def alice(db_session: AsyncSession) -> AsyncGenerator[UserModel]:
    async with db_session.begin():
        result = await db_session.execute(
            sql.insert(UserModel)
            .values(
                email="alice@example.com",
                password="password123",
                username="alice.fixture",
                fullname="Alice Fixture",
            )
            .returning(UserModel)
        )
        await db_session.commit()
        user = result.scalar_one()
    yield user

    async with db_session.begin():
        await db_session.execute(sql.delete(UserModel).filter_by(id=user.id))
