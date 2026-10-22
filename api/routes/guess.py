"""Guess endpoint: the only place a password guess is checked, server-side."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.defense.levels import get_level
from api.secrets import is_correct_guess

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
async def guess(body: GuessRequest) -> GuessResponse:
    """Checks a password guess.

    Args:
        body: Level and guess.

    Returns:
        Whether the guess was correct.

    Raises:
        HTTPException: 404 if the level does not exist.
    """
    if get_level(body.level) is None:
        raise HTTPException(status_code=404, detail="Unknown level")
    return GuessResponse(correct=is_correct_guess(body.level, body.guess))
