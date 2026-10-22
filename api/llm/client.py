"""Provider-agnostic LLM client.

Groq, Mistral and Gemini all expose the same "OpenAI-compatible" HTTP API, so a
single wrapper around the OpenAI SDK talks to all of them; only ``base_url`` and
the key change per role.
"""

import time
from typing import Literal

from openai import AsyncOpenAI
from pydantic import BaseModel

from api.llm.roles import RoleConfig

# Hard ceiling per call. Guard layers must fail closed, and a hung request is a
# failure like any other, so we never wait longer than this.
REQUEST_TIMEOUT_SECONDS = 20.0

# The SDK retries 429 (rate limit) and transient 5xx errors with exponential
# backoff. If these retries are exhausted the exception propagates and the
# pipeline fails closed.
MAX_RETRIES = 3

# Room for the model's hidden reasoning plus the visible answer. Reasoning
# models spend tokens thinking first; too small a cap leaves an empty answer.
MAX_COMPLETION_TOKENS = 1500


class ChatTurn(BaseModel):
    """One message in an LLM conversation.

    Attributes:
        role: Who said it.
        content: The message text.
    """

    role: Literal["system", "user", "assistant"]
    content: str


class LLMResult(BaseModel):
    """What one LLM call returns, with the numbers the eval harness needs.

    Attributes:
        text: The model's visible answer (empty string if it produced none).
        tokens_in: Prompt tokens billed.
        tokens_out: Completion tokens billed (includes hidden reasoning).
        latency_ms: Wall-clock time of the call, including retries.
    """

    text: str
    tokens_in: int
    tokens_out: int
    latency_ms: int


async def complete(role: RoleConfig, messages: list[ChatTurn], temperature: float) -> LLMResult:
    """Sends a conversation to the role's model and returns its answer.

    Args:
        role: Provider/model settings for this call.
        messages: Full conversation, system prompt first.
        temperature: Sampling temperature. Use 0 for classifier and judge so
            their verdicts are as repeatable as possible.

    Returns:
        The answer text plus token counts and latency.

    Raises:
        openai.OpenAIError: On auth, rate-limit (after retries), timeout or
            server errors. Callers on a guard path must treat this as "block".
    """
    # `async with` closes the underlying HTTP connection when the call ends.
    # Serverless requests are short-lived, so one client per call is simplest
    # and must not leave sockets open behind it.
    async with AsyncOpenAI(
        base_url=role.base_url,
        api_key=role.api_key,
        timeout=REQUEST_TIMEOUT_SECONDS,
        max_retries=MAX_RETRIES,
    ) as client:
        started = time.perf_counter()
        response = await client.chat.completions.create(
            model=role.model,
            messages=[m.model_dump() for m in messages],
            temperature=temperature,
            max_completion_tokens=MAX_COMPLETION_TOKENS,
        )
    latency_ms = int((time.perf_counter() - started) * 1000)
    usage = response.usage
    return LLMResult(
        text=response.choices[0].message.content or "",
        tokens_in=usage.prompt_tokens if usage else 0,
        tokens_out=usage.completion_tokens if usage else 0,
        latency_ms=latency_ms,
    )
