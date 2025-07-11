import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from wallstr.auth.services import UserService


@pytest.fixture(scope="function")
def user_svc(db_session: AsyncSession) -> UserService:
    return UserService(db_session)
