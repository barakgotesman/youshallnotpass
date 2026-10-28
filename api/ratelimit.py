"""Rate limiting and quota protection, backed by Upstash Redis.

Free-tier LLM limits belong to the provider account, not to a player, so one
script could drain the whole game's quota. Three kinds of counters stop that:
per session, per IP, and a global daily budget for the defender LLM.

Counters are fixed windows: a key per (scope, id, window length, window number)
that Redis increments and expires by itself. Fixed windows can allow a short
burst at a window boundary; that is an accepted trade for being trivial to read
and needing no Lua scripts.

Fail closed: if Redis is configured but errors, the request is refused as
"vault closed". Local development without Upstash configured runs unlimited.
"""

import logging
import os
import time
from typing import Literal, Protocol

import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)

SECONDS_PER_MINUTE = 60
SECONDS_PER_DAY = 86_400

Reason = Literal["ok", "slow_down", "vault_closed"]

# (scope, identity, window_seconds, max_hits)
Limit = tuple[str, str, int, int]


class Decision(BaseModel):
    """Whether a request may proceed.

    Attributes:
        allowed: True if the request may continue.
        reason: ``"slow_down"`` when this player is over a personal limit,
            ``"vault_closed"`` when the shared daily budget is spent or the
            limiter itself is unavailable.
        retry_after: Seconds until the blocking window resets (0 if allowed).
    """

    allowed: bool
    reason: Reason = "ok"
    retry_after: int = 0


class CounterStore(Protocol):
    """Anything that can atomically increment expiring counters."""

    async def incr_many(self, keys: list[tuple[str, int]]) -> list[int]:
        """Increments each counter and returns the new values.

        Args:
            keys: ``(key, ttl_seconds)`` pairs. The TTL is applied when the
                counter is first created.

        Returns:
            The counter values after incrementing, in the same order.
        """
        ...


class UpstashStore:
    """Counter store using Upstash's REST API (works from serverless functions)."""

    def __init__(self, url: str, token: str) -> None:
        """Creates the store.

        Args:
            url: ``UPSTASH_REDIS_REST_URL``.
            token: ``UPSTASH_REDIS_REST_TOKEN``.
        """
        self._url = url.rstrip("/")
        self._token = token

    async def incr_many(self, keys: list[tuple[str, int]]) -> list[int]:
        """Increments counters in one round trip using Upstash's pipeline endpoint.

        Args:
            keys: ``(key, ttl_seconds)`` pairs.

        Returns:
            New counter values, in order.

        Raises:
            httpx.HTTPError: On any network or HTTP failure.
        """
        commands: list[list[str | int]] = []
        for key, ttl in keys:
            commands.append(["INCR", key])
            # NX: only set the expiry on the first hit, so later hits cannot extend the window.
            commands.append(["EXPIRE", key, ttl, "NX"])
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.post(
                f"{self._url}/pipeline",
                headers={"Authorization": f"Bearer {self._token}"},
                json=commands,
            )
            response.raise_for_status()
        results = response.json()
        # Results alternate INCR, EXPIRE; keep the INCR values.
        return [int(results[i]["result"]) for i in range(0, len(results), 2)]


def _int_env(name: str, default: int) -> int:
    """Reads an integer env var with a default.

    Args:
        name: Variable name.
        default: Value when unset or empty.

    Returns:
        The configured integer.
    """
    raw = os.environ.get(name, "")
    return int(raw) if raw else default


def default_store() -> CounterStore | None:
    """Builds the Upstash store from env, or None when it is not configured.

    Returns:
        The store, or None to run without limits (local development).
    """
    url = os.environ.get("UPSTASH_REDIS_REST_URL", "")
    token = os.environ.get("UPSTASH_REDIS_REST_TOKEN", "")
    if not url or not token:
        return None
    return UpstashStore(url, token)


def _window_key(scope: str, ident: str, window_s: int, now: float) -> tuple[str, int]:
    """Builds the counter key for the current window and its remaining seconds.

    Args:
        scope: What is being limited, e.g. ``"chat:session"``.
        ident: Session id, IP hash, or role name.
        window_s: Window length in seconds.
        now: Current epoch time.

    Returns:
        ``(key, seconds_left_in_window)``.
    """
    bucket = int(now // window_s)
    left = window_s - int(now % window_s)
    return f"rl:{scope}:{ident}:{window_s}:{bucket}", left


async def _check(store: CounterStore | None, limits: list[Limit], now: float) -> Decision:
    """Increments counters and compares them with their limits.

    Args:
        store: Counter store, or None to allow everything.
        limits: The limits to enforce.
        now: Current epoch time.

    Returns:
        Allowed, or ``slow_down`` with the longest wait among exceeded limits.
    """
    if store is None:
        return Decision(allowed=True)
    keyed = [_window_key(scope, ident, window, now) for scope, ident, window, _ in limits]
    counts = await store.incr_many([(key, window) for (key, _), (_, _, window, _) in zip(keyed, limits)])
    waits = [left for (_, left), count, (_, _, _, cap) in zip(keyed, counts, limits) if count > cap]
    if waits:
        return Decision(allowed=False, reason="slow_down", retry_after=max(waits))
    return Decision(allowed=True)


async def check_chat(
    session_id: str,
    ip_hash: str,
    store: CounterStore | None = None,
    now: float | None = None,
) -> Decision:
    """Decides whether a chat message may reach the guard LLM.

    Personal limits are checked first and the global budget only afterwards, so
    a spammer who is already blocked cannot burn everyone's shared budget.

    Args:
        session_id: The player's session id.
        ip_hash: Hashed client IP.
        store: Counter store; defaults to Upstash from env. Injectable for tests.
        now: Current epoch time; injectable for tests.

    Returns:
        The decision. ``vault_closed`` if the daily budget is spent or Redis
        failed (fail closed).
    """
    store = store if store is not None else default_store()
    now = time.time() if now is None else now
    personal: list[Limit] = [
        ("chat:session", session_id, SECONDS_PER_MINUTE, _int_env("RATE_CHAT_PER_MIN_SESSION", 8)),
        ("chat:session", session_id, SECONDS_PER_DAY, _int_env("RATE_CHAT_PER_DAY_SESSION", 150)),
        ("chat:ip", ip_hash, SECONDS_PER_MINUTE, _int_env("RATE_CHAT_PER_MIN_IP", 20)),
        ("chat:ip", ip_hash, SECONDS_PER_DAY, _int_env("RATE_CHAT_PER_DAY_IP", 400)),
    ]
    budget: list[Limit] = [
        ("budget", "DEFENDER", SECONDS_PER_DAY, _int_env("DAILY_BUDGET_DEFENDER", 10_000))
    ]
    try:
        decision = await _check(store, personal, now)
        if not decision.allowed:
            return decision
        spent = await _check(store, budget, now)
    except Exception:  # noqa: BLE001 - limiter trouble must fail closed
        logger.exception("rate limiter unavailable; closing the vault")
        return Decision(allowed=False, reason="vault_closed", retry_after=60)
    if not spent.allowed:
        return Decision(allowed=False, reason="vault_closed", retry_after=spent.retry_after)
    return decision


async def check_guess(
    session_id: str,
    ip_hash: str,
    store: CounterStore | None = None,
    now: float | None = None,
) -> Decision:
    """Decides whether a password guess may be checked.

    Guesses cost no LLM quota, but unlimited guesses would let a script
    brute-force the password, so they get personal limits (no global budget).

    Args:
        session_id: The player's session id.
        ip_hash: Hashed client IP.
        store: Counter store; defaults to Upstash from env. Injectable for tests.
        now: Current epoch time; injectable for tests.

    Returns:
        The decision.
    """
    store = store if store is not None else default_store()
    now = time.time() if now is None else now
    limits: list[Limit] = [
        ("guess:session", session_id, SECONDS_PER_MINUTE, _int_env("RATE_GUESS_PER_MIN_SESSION", 10)),
        ("guess:ip", ip_hash, SECONDS_PER_MINUTE, _int_env("RATE_GUESS_PER_MIN_IP", 30)),
    ]
    try:
        return await _check(store, limits, now)
    except Exception:  # noqa: BLE001 - limiter trouble must fail closed
        logger.exception("rate limiter unavailable; refusing guess")
        return Decision(allowed=False, reason="vault_closed", retry_after=60)
