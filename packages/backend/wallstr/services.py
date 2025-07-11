import inspect
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated, Self

import structlog
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from wallstr.db import get_db_session

logger = structlog.get_logger()


class BaseService:
    def __init__(self, db_session: AsyncSession) -> None:
        self.db = db_session

    @classmethod
    async def inject_svc(
        cls, db: Annotated[AsyncSession, Depends(get_db_session)]
    ) -> Self:
        """
        Works only in FastAPI environment because requires Request
        """
        return cls(db)

    # Subtransactions
    # https://docs.sqlalchemy.org/en/20/changelog/migration_20.html#session-subtransaction-behavior-removed
    # https://github.com/sqlalchemy/sqlalchemy/discussions/12140
    @asynccontextmanager
    async def tx(self) -> AsyncGenerator[None, None]:
        stack = inspect.stack(0)[:-3]
        from_ = stack[2]
        if self.db.in_transaction():
            logger.trace(f"Already in tx from {from_.function}")
            yield
            return
        async with self.db.begin():
            logger.trace(f"tx starts from {from_.function}")
            yield
        logger.trace(f"tx commits from {from_.function}")
