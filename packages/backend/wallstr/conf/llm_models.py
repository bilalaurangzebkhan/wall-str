from typing import Literal
from urllib.parse import parse_qs, urlparse

from pydantic import SecretStr, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ModelConfig(BaseSettings):
    # Tokens per minute
    TPM: int = -1

    # Tokens per day
    TPD: int = -1

    # Requests per minute
    RPM: int = -1


# fmt: off
TClaude35Sonnet = Literal["claude-3.5-sonnet"]
TDeepSeek       = Literal["deepseek"]
TDeepSeekR1     = Literal["deepseek-r1"]
TGemini2        = Literal["gemini-2.0-flash"]
TGemma3_27b     = Literal["gemma-3-27b"]
TGpt4o          = Literal["gpt-4o"]
TGpt4oMini      = Literal["gpt-4o-mini"]
TLlama31_405b   = Literal["llama3.1-405b"]
TLlama3_70b     = Literal["llama3-70b"]
# fmt: on

SUPPORTED_LLM_MODELS_TYPES = (
    TClaude35Sonnet
    | TDeepSeek
    | TDeepSeekR1
    | TGemini2
    | TGemma3_27b
    | TGpt4o
    | TGpt4oMini
    | TLlama31_405b
    | TLlama3_70b
)


class Claude35SonnetConfig(ModelConfig):
    NAME: TClaude35Sonnet = "claude-3.5-sonnet"
    PROVIDER: Literal["REPLICATE"]
    REPLICATE_API_KEY: SecretStr | None = None

    context_window: int = 200_000


class Gemma3_27bConfig(ModelConfig):
    NAME: TGemma3_27b = "gemma-3-27b"
    PROVIDER: Literal["REPLICATE"]
    REPLICATE_API_KEY: SecretStr | None = None

    context_window: int = 128_000


class Gemini2Config(ModelConfig):
    NAME: TGemini2 = "gemini-2.0-flash"
    PROVIDER: Literal["GOOGLE"]
    GOOGLE_API_KEY: SecretStr | None = None

    context_window: int = 1_048_576


class DeepSeekConfig(ModelConfig):
    """
    https://github.com/deepseek-ai/DeepSeek-V3
    """

    NAME: TDeepSeek = "deepseek"
    PROVIDER: Literal["DEEPSEEK"]
    DEEPSEEK_API_KEY: SecretStr | None = None

    context_window: int = 128_000


class DeepSeekR1Config(ModelConfig):
    """
    https://github.com/deepseek-ai/DeepSeek-R1
    """

    NAME: TDeepSeekR1 = "deepseek-r1"
    PROVIDER: Literal["DEEPSEEK", "REPLICATE"]
    REPLICATE_API_KEY: SecretStr | None = None
    DEEPSEEK_API_KEY: SecretStr | None = None

    context_window: int = 128_000


class OpenAIModelConfig(ModelConfig):
    NAME: TGpt4o | TGpt4oMini
    PROVIDER: Literal["OPENAI", "AZURE"]
    AZURE_API_URL: str | None = None
    AZURE_API_KEY: SecretStr | None = None
    OPENAI_API_KEY: SecretStr | None = None

    @computed_field  # type: ignore[misc]
    @property
    def AZURE_API_VERSION(self) -> str:
        if not self.AZURE_API_URL:
            raise ValueError(f"Missing Azure API URL for model {self.NAME}")
        parsed_url = urlparse(self.AZURE_API_URL)

        if not parsed_url.query:
            raise ValueError(
                f"Missing query parameters in Azure API URL {self.AZURE_API_URL}"
            )
        api_version = parse_qs(str(parsed_url.query)).get("api-version", [])[0]
        if not api_version:
            raise ValueError(
                f"Missing api-version in Azure API URL {self.AZURE_API_URL}"
            )
        return str(api_version)


class Gpt4oConfig(OpenAIModelConfig):
    """
    https://platform.openai.com/docs/models/gpt-4o
    """

    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
    )
    NAME: TGpt4o | TGpt4oMini = "gpt-4o"

    TPM: int = 450_000
    TPD: int = 1_350_000
    RPM: int = 5_000

    context_window: int = 128_000


class Gpt4oMiniConfig(OpenAIModelConfig):
    """
    https://platform.openai.com/docs/models/gpt-4o-mini
    """

    NAME: TGpt4o | TGpt4oMini = "gpt-4o-mini"

    TPM: int = 2_000_000
    TPD: int = 20_000_000
    RPM: int = 5_000

    context_window: int = 128_000


class Llama3_70bConfig(ModelConfig):
    NAME: TLlama3_70b = "llama3-70b"
    PROVIDER: Literal["REPLICATE"]
    REPLICATE_API_KEY: SecretStr | None = None

    context_window: int = 8_000


class Llama31_405bConfig(ModelConfig):
    NAME: TLlama31_405b = "llama3.1-405b"
    PROVIDER: Literal["REPLICATE"]
    REPLICATE_API_KEY: SecretStr | None = None

    # context_window: int = 128_000
    # by some reasons Replicate version doesn't accept more than 4096 tokens
    context_window: int = 4_096


class ModelsConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_prefix="MODELS",
        case_sensitive=True,
        extra="ignore",
    )
    CLAUDE_35_SONNET: Claude35SonnetConfig | None = None
    DEEPSEEK: DeepSeekConfig | None = None
    DEEPSEEK_R1: DeepSeekR1Config | None = None
    GEMINI_2: Gemini2Config | None = None
    GEMMA_3_27B: Gemma3_27bConfig | None = None
    GPT_4O: Gpt4oConfig | None = None
    GPT_4O_MINI: Gpt4oMiniConfig | None = None
    LLAMA3_70B: Llama3_70bConfig | None = None
    LLAMA31_405B: Llama31_405bConfig | None = None

    @computed_field  # type: ignore[misc]
    @property
    def get_enabled_models(self) -> list[SUPPORTED_LLM_MODELS_TYPES]:
        enabled_models = []
        for model in self.__dict__.values():
            if model and model.NAME:
                enabled_models.append(model.NAME)
        return enabled_models
