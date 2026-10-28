"""Chat endpoint: one player message goes through the level's defense pipeline."""

import logging
from typing import Literal

import asyncpg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from api import ratelimit
from api.db import queries
from api.defense.levels import LevelConfig, get_level
from api.defense.pipeline import TurnResult, run_turn
from api.defense.versions import current_defense_version
from api.llm.client import ChatTurn
from api.routes.limits import raise_if_refused
from api.session import PlayerSession, current_session, db_connection

logger = logging.getLogger(__name__)

router = APIRouter()

# Caps keep one request from burning a large share of the free LLM quota.
MAX_MESSAGE_CHARS = 1000
MAX_HISTORY_MESSAGES = 20


class ChatMessage(BaseModel):
    """One message of the visible conversation.

    Attributes:
        role: ``"user"`` for the player, ``"assistant"`` for the guard.
        content: Message text, length-limited.
    """

    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=MAX_MESSAGE_CHARS)


class ChatRequest(BaseModel):
    """Body of ``POST /api/chat``.

    Attributes:
        level: Level being played.
        messages: Conversation so far, ending with the player's new message.
            The client holds the history; it can only forge its own chat, and
            the system prompt (with the secret) is added on the server.
    """

    level: int
    messages: list[ChatMessage] = Field(min_length=1, max_length=MAX_HISTORY_MESSAGES)


class ChatResponse(BaseModel):
    """Body returned by ``POST /api/chat``.

    Mirrors ``web/src/types/chat.ts``. Deliberately has no trace or block
    reason: the client must not learn which layer stopped a message.

    Attributes:
        reply: The guard's reply, or an in-world refusal.
        blocked: True if the turn was stopped by the pipeline.
    """

    reply: str
    blocked: bool


@router.post("/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    session: PlayerSession = Depends(current_session),
    conn: asyncpg.Connection = Depends(db_connection),
) -> ChatResponse:
    """Runs the player's message through the level's pipeline.

    Args:
        body: Level and conversation history.
        session: The caller's anonymous session.
        conn: Request-scoped database connection.

    Returns:
        The guard's reply and whether the turn was blocked.

    Raises:
        HTTPException: 404 if the level does not exist, 422 if the last
            message is not from the player, 429 if the player is over a limit
            or the daily budget is spent.
    """
    level = get_level(body.level)
    if level is None:
        raise HTTPException(status_code=404, detail="Unknown level")
    if body.messages[-1].role != "user":
        raise HTTPException(status_code=422, detail="Last message must be from the player")

    # Limits run before the LLM call: a refused request must cost no quota.
    raise_if_refused(await ratelimit.check_chat(str(session.id), session.ip_hash))

    history = [ChatTurn(role=m.role, content=m.content) for m in body.messages]
    result = await run_turn(level, history)
    await _record_attempt(conn, session, level, body.messages[-1].content, result)
    return ChatResponse(reply=result.reply, blocked=result.blocked)


async def _record_attempt(
    conn: asyncpg.Connection,
    session: PlayerSession,
    level: LevelConfig,
    user_message: str,
    result: TurnResult,
) -> None:
    """Saves the turn and its trace without ever failing the player's request.

    The player already has their answer; losing one analytics row is better
    than showing an error for a reply the guard did give. The failure is logged.

    Args:
        conn: Request-scoped database connection.
        session: The caller's session.
        level: Level played.
        user_message: The player's message.
        result: What the pipeline produced.
    """
    try:
        version_id = await current_defense_version(conn, level)
        await queries.save_attempt(
            conn,
            session.id,
            level.id,
            version_id,
            user_message,
            None if result.blocked else result.reply,
            result.trace.model_dump_json(),
        )
    except Exception:  # noqa: BLE001 - persistence must not break the game
        logger.exception("could not save attempt")
