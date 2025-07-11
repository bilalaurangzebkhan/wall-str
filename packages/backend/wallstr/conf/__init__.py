from enum import Enum
from pathlib import Path
from typing import Literal, cast

import tomllib
from pydantic import HttpUrl, SecretStr, ValidationInfo, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from wallstr.conf.llm_models import SUPPORTED_LLM_MODELS_TYPES, ModelsConfig


def get_version() -> str:
    with open(Path(__file__).parent.parent.parent / "pyproject.toml", "rb") as f:
        data = tomllib.load(f)
        return cast(str, data["tool"]["poetry"]["version"])


class Env(str, Enum):
    dev = "dev"
    prod = "prod"
    test = "test"


class JWTSettings(BaseSettings):
    issuer: str = "https://github.com/limanAI/wallstr"
    algorithm: Literal["HS512"] = "HS512"
    access_token_expire_minutes: int = 60
    access_token_renewal_leeway_days: int = 3
    refresh_token_expire_days: int = 7


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_nested_delimiter="__", case_sensitive=True, extra="ignore"
    )

    VERSION: str = get_version()
    ENV: Env = Env.dev
    DEBUG: bool = False
    DEBUG_SQL: bool = False

    # Required
    SECRET_KEY: SecretStr
    DATABASE_URL: SecretStr
    RABBITMQ_URL: SecretStr
    REDIS_URL: SecretStr
    STORAGE_URL: HttpUrl
    STORAGE_BUCKET: str
    STORAGE_ACCESS_KEY: SecretStr
    STORAGE_SECRET_KEY: SecretStr
    OLLAMA_URL: SecretStr
    OPENAI_API_KEY: SecretStr

    # Optional
    WEAVIATE_API_URL: SecretStr | None = None
    WEAVIATE_GRPC_URL: SecretStr | None = None
    SENTRY_DSN: SecretStr | None = None
    LOGFIRE_TOKEN: SecretStr | None = None

    # LLM platforms
    DEEPSEEK_API_KEY: SecretStr | None = None
    GOOGLE_API_KEY: SecretStr | None = None
    REPLICATE_API_KEY: SecretStr | None = None
    # LLM models
    MODELS: ModelsConfig = ModelsConfig()

    CORS_ALLOW_ORIGINS: list[str] = []

    # JWT
    JWT: JWTSettings = JWTSettings()

    @field_validator(
        "SECRET_KEY",
        "DATABASE_URL",
        "RABBITMQ_URL",
        "REDIS_URL",
        "STORAGE_URL",
        "STORAGE_BUCKET",
        "STORAGE_ACCESS_KEY",
        "STORAGE_SECRET_KEY",
        "OLLAMA_URL",
        "OPENAI_API_KEY",
        mode="before",
    )
    @classmethod
    def check_not_empty(cls, value: str, info: ValidationInfo) -> str:
        if not value.strip():
            raise ValueError(f"{info.field_name} cannot be empty")
        return value


# https://github.com/pydantic/pydantic/issues/3753
settings = Settings.model_validate({})


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="CFG__",
        env_nested_delimiter="__",
        case_sensitive=True,
        extra="ignore",
    )

    AUTH_ALLOW_SIGNUP: bool = True

    @computed_field  # type: ignore[misc]
    @property
    def AUTH_PROVIDERS(self) -> list[str]:
        return []

    @computed_field  # type: ignore[misc]
    @property
    def LLM_MODELS(self) -> list[SUPPORTED_LLM_MODELS_TYPES]:
        return settings.MODELS.get_enabled_models


# https://github.com/pydantic/pydantic/issues/3753
config = Config.model_validate({})

if not config.LLM_MODELS:
    raise Exception(
        "Application isn't configured with any LLM models, please provide MODELS__ env variables"
    )
