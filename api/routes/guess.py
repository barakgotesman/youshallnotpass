"""Guess endpoint: the only place a password guess is checked, server-side."""

import asyncpg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from api import ratelimit
from api.db import queries
from api.defense.levels import get_level
from api.defense.versions import current_defense_version
from api.routes.limits import raise_if_refused
from api.secrets import is_correct_guess
from api.session import PlayerSession, current_session, db_connection

router = APIRouter()


class GuessRequest(BaseModel):
    """Body of ``POST /api/guess``.

    Attributes:
        level: Level the guess is for.
        guess: The password the player thinks they extracted.
    """

    level: int
    guess: str = Field(min_length=1, max_length=100)


class GuessResponse(BaseModel):
    """Body returned by ``POST /api/guess``.

    Mirrors ``web/src/types/guess.ts``.

    Attributes:
        correct: Whether the guess matched. Nothing else is revealed.
    """

    correct: bool


@router.post("/guess", response_model=GuessResponse)
async def guess(
    body: GuessRequest,
    session: PlayerSession = Depends(current_session),
    conn: asyncpg.Connection = Depends(db_connection),
) -> GuessResponse:
    """Checks a password guess.

    Args:
        body: Level and guess.
        session: The caller's anonymous session.
        conn: Request-scoped database connection.

    Returns:
        Whether the guess was correct.

    Raises:
        HTTPException: 404 if the level does not exist, 429 if the player is
            guessing too fast (a script could otherwise brute-force the word).
    """
    level = get_level(body.level)
    if level is None:
        raise HTTPException(status_code=404, detail="Unknown level")
    raise_if_refused(await ratelimit.check_guess(str(session.id), session.ip_hash))

    correct = is_correct_guess(level.id, body.guess)
    if correct:
        # Makes sure the level's database row exists before the progress row points at it.
        await current_defense_version(conn, level)
        if await queries.mark_cleared(conn, session.id, level.id):
            await queries.save_attack_from_session(conn, session.id, level.id)
    return GuessResponse(correct=correct)
