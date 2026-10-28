"""Progress endpoint: which levels this player has beaten."""

import asyncpg
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from api.db import queries
from api.session import PlayerSession, current_session, db_connection

router = APIRouter()


class ProgressResponse(BaseModel):
    """Body returned by ``GET /api/progress``.

    Mirrors ``web/src/types/progress.ts``.

    Attributes:
        cleared_levels: Ids of the levels the player has beaten.
    """

    cleared_levels: list[int]


@router.get("/progress", response_model=ProgressResponse)
async def progress(
    session: PlayerSession = Depends(current_session),
    conn: asyncpg.Connection = Depends(db_connection),
) -> ProgressResponse:
    """Returns the player's cleared levels so a reload keeps their progress.

    Args:
        session: The caller's anonymous session.
        conn: Request-scoped database connection.

    Returns:
        The cleared level ids.
    """
    return ProgressResponse(cleared_levels=await queries.cleared_levels(conn, session.id))
