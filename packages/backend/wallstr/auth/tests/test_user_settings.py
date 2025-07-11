from wallstr.auth.models import UserModel
from wallstr.auth.schemas import UserSettings


async def test_empy_user_settings(alice: UserModel) -> None:
    assert isinstance(alice.settings, UserSettings)
    assert alice.settings.llm_model is None
