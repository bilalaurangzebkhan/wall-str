from typing import Generic, TypeVar

from pydantic import BaseModel, computed_field

from wallstr.conf.llm_models import SUPPORTED_LLM_MODELS_TYPES

T = TypeVar("T")


class Paginated(BaseModel, Generic[T]):
    items: list[T]
    cursor: int | None


class SSE(BaseModel):
    @computed_field
    def type(self) -> str:
        raise NotImplementedError("Subclasses must define a `type` field.")


class AuthConfig(BaseModel):
    allow_signup: bool
    providers: list[str]


class ConfigResponse(BaseModel):
    name: str = "Wallstr"
    version: str
    auth: AuthConfig
    llm_models: list[SUPPORTED_LLM_MODELS_TYPES]
