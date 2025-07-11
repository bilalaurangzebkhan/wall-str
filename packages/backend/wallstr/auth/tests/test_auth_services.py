import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from wallstr.auth.models import UserModel
from wallstr.auth.services import AuthService, UserService


@pytest.fixture
def auth_svc(db_session: AsyncSession) -> AuthService:
    return AuthService(db_session)


@pytest.mark.asyncio
async def test_get_user_by_email(user_svc: UserService, alice: UserModel) -> None:
    email = "alice@example.com"

    result = await user_svc.get_user_by_email(email)
    assert result == alice
