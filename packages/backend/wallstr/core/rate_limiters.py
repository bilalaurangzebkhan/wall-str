import asyncio
import time
from collections import deque
from collections.abc import Sequence
from datetime import datetime, timedelta
from typing import TypedDict, overload

import structlog
from langchain_core.messages import BaseMessage
from langchain_core.prompt_values import PromptValue
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from tiktoken import encoding_for_model

from wallstr.conf.llm_models import SUPPORTED_LLM_MODELS_TYPES
from wallstr.core.llm import LLMModel, estimate_input_tokens

logger = structlog.get_logger()


class Request(TypedDict):
    tokens: int
    requests: int
    created_at: datetime


# Add distributed Redis rate-limiter
class RateLimiter:
    def __init__(
        self, model: str, *, key: str, tpm: int | None = None, rpm: int | None = None
    ) -> None:
        self.model = model
        self.key = key
        self.tpm = tpm
        self.rpm = rpm

        self.tpm_capacity = tpm or float("inf")
        self.rpm_capacity = rpm or float("inf")

        self.dequeue: deque[Request] = deque()
        self.lock = asyncio.Lock()
        self.tick = 0.1
        self.locked_at: None | float = None

    @overload
    async def acquire(self, llm: LLMModel, input_: PromptValue) -> None: ...

    @overload
    async def acquire(self, llm: LLMModel, input_: int) -> None: ...

    @overload
    async def acquire(
        self,
        llm: LLMModel,
        input_: Sequence[BaseMessage],
    ) -> None: ...

    # https://cookbook.openai.com/examples/how_to_count_tokens_with_tiktoken
    async def acquire(
        self,
        llm: LLMModel,
        input_: int | PromptValue | Sequence[BaseMessage],
    ) -> None:
        if self.model == "noop":
            return

        if not isinstance(llm, (ChatOpenAI, AzureChatOpenAI)):
            """
            Rate limiter is implemented only for OpenAI models
            """
            return

        if not llm.model_name:
            raise ValueError(f"Model name is not set for {llm}")

        tokens_per_message = 3
        if isinstance(input_, PromptValue):
            enc = encoding_for_model(llm.model_name)
            tokens = len(enc.encode(input_.to_string()))
            messages = len(input_.to_messages())
        elif isinstance(input_, int):
            tokens = input_
            messages = 1
        elif isinstance(input_, list):
            tokens = estimate_input_tokens(llm, input_)
            messages = len(input_)
        else:
            raise ValueError(f"Unknown input type {input_}")
        tokens += tokens_per_message * messages
        while not await self._consume(tokens, requests=1):
            await asyncio.sleep(self.tick)

    async def _consume(self, tokens: int, requests: int) -> bool:
        async with self.lock:
            now = datetime.now()
            if self.tpm_capacity >= tokens and self.rpm_capacity >= requests:
                if self.locked_at is not None:
                    logger.trace(
                        f"RateLimiter unlocked in {time.perf_counter() - self.locked_at:.3f}s"
                    )
                    self.locked_at = None
                logger.trace(
                    f"Consume {tokens} tokens from {self.tpm_capacity}, {self.rpm_capacity} requests"
                )
                self.dequeue.append(
                    Request(tokens=tokens, requests=requests, created_at=now)
                )
                self.tpm_capacity -= tokens
                self.rpm_capacity -= requests
                return True
            # free capacity
            while len(self.dequeue) and (
                now - self.dequeue[0]["created_at"]
            ) > timedelta(minutes=1.5):
                logger.warn(f"dequeu[0] {self.dequeue[0]}")
                slot = self.dequeue.popleft()
                logger.warn(f"slot {slot}")
                self.tpm_capacity += slot["tokens"]
                self.rpm_capacity += slot["requests"]
        if self.locked_at is None:
            logger.trace("RateLimiter locked")
            self.locked_at = time.perf_counter()
        return False


TIERS = {
    "gpt-4o-mini": {
        "tier1": {
            "tpm": 100_000,
            "rpm": 500,
        },
        "tier2": {
            "tpm": 2_000_000,
            "rpm": 5000,
        },
    },
    "gpt-4o": {
        "tier1": {
            "tpm": 100_000,
            "rpm": 500,
        },
        "tier2": {
            "tpm": 450_000,
            "rpm": 5000,
        },
    },
    "llama3-70b": {},
}


gpt4o_mini_rate_limiter = RateLimiter(
    model="gpt-4o-mini",
    key="main",
    tpm=TIERS["gpt-4o-mini"]["tier2"]["tpm"],
    rpm=TIERS["gpt-4o-mini"]["tier2"]["tpm"],
)
gpt4o_rate_limiter = RateLimiter(
    model="gpt-4o",
    key="main",
    tpm=TIERS["gpt-4o"]["tier2"]["tpm"],
    rpm=TIERS["gpt-4o"]["tier2"]["tpm"],
)
llama3_70b_rate_limiter = RateLimiter(
    model="llama3-70b",
    key="main",
)
gemini_2_0_rate_limiter = RateLimiter(
    model="gemini-2.0-flash",
    key="main",
)
noop_rate_limiter = RateLimiter(
    model="noop",
    key="main",
)


def get_rate_limiter(model: SUPPORTED_LLM_MODELS_TYPES) -> RateLimiter:
    if model == "gpt-4o-mini":
        return gpt4o_mini_rate_limiter
    if model == "gpt-4o":
        return gpt4o_rate_limiter
    if model == "llama3-70b":
        return llama3_70b_rate_limiter
    if model == "gemini-2.0-flash":
        return gemini_2_0_rate_limiter

    return noop_rate_limiter
