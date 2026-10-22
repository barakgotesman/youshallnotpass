"""LLM role configuration, read from environment variables.

The game uses several LLM "roles" (defender, classifier, judge). Each role is
configured only through env vars, so swapping a model or provider never needs a
code change: edit ``.env`` (or Vercel's env settings) and restart.
"""

import os
from typing import Literal

from pydantic import BaseModel

Role = Literal["DEFENDER", "CLASSIFIER", "JUDGE"]


class RoleConfig(BaseModel):
    """Connection settings for one LLM role.

    Attributes:
        provider: Human-readable provider name (e.g. ``"groq"``). Used for logs
            and traces only; the actual routing is done by ``base_url``.
        model: Model identifier as the provider names it.
        base_url: OpenAI-compatible endpoint of the provider.
        api_key: Secret key. Never log or return this.
    """

    provider: str
    model: str
    base_url: str
    api_key: str


def load_role(role: Role) -> RoleConfig:
    """Builds a role's config from ``{ROLE}_PROVIDER/_MODEL/_BASE_URL/_API_KEY``.

    Args:
        role: Which role to load.

    Returns:
        The validated configuration for that role.

    Raises:
        RuntimeError: If any of the four env vars is missing or empty. We fail
            loudly at call time instead of guessing a default model, because a
            silently wrong model would corrupt eval results.
    """
    values: dict[str, str] = {}
    for field in ("provider", "model", "base_url", "api_key"):
        name = f"{role}_{field.upper()}"
        value = os.environ.get(name, "")
        if not value:
            raise RuntimeError(f"{name} is not set; see .env.example")
        values[field] = value
    return RoleConfig(**values)
