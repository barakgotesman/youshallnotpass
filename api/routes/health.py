"""Health endpoint: proves the API is up and reports basic configuration.

Used by the frontend hello-world and by deploy checks.
"""

import os
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    """Body returned by ``GET /api/health``.

    Mirrors ``web/src/types/health.ts``; change both together.

    Attributes:
        status: Always ``"ok"`` while the process is serving requests.
        database_configured: True if ``DATABASE_URL`` is set. This does not
            open a connection, so the health check stays fast and cannot fail
            just because the database is waking up.
    """

    status: Literal["ok"]
    database_configured: bool


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Reports that the API is alive.

    Returns:
        A ``HealthResponse`` with status and whether the database is configured.
    """
    return HealthResponse(
        status="ok",
        database_configured=bool(os.environ.get("DATABASE_URL")),
    )
