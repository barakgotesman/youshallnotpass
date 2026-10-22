"""Chat endpoint: one player message goes through the level's defense pipeline."""

from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.defense.levels import get_level
from api.defense.pipeline import run_turn
from api.llm.client import ChatTurn

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
async def chat(body: ChatRequest) -> ChatResponse:
    """Runs the player's message through the level's pipeline.

    Args:
        body: Level and conversation history.

    Returns:
        The guard's reply and whether the turn was blocked.

    Raises:
        HTTPException: 404 if the level does not exist, 422 if the last
            message is not from the player.
    """
    level = get_level(body.level)
    if level is None:
        raise HTTPException(status_code=404, detail="Unknown level")
    if body.messages[-1].role != "user":
        raise HTTPException(status_code=422, detail="Last message must be from the player")

    history = [ChatTurn(role=m.role, content=m.content) for m in body.messages]
    result = await run_turn(level, history)
    return ChatResponse(reply=result.reply, blocked=result.blocked)
