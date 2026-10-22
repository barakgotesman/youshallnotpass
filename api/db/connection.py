"""Neon Postgres connection helper.

Serverless functions are short-lived, so we open a connection per use instead
of keeping a long-lived pool. Neon's pooled connection string (PgBouncer) is
what makes this cheap; use it for ``DATABASE_URL``.
"""

import os

import asyncpg


async def connect() -> asyncpg.Connection:
    """Opens a new connection to Neon using ``DATABASE_URL``.

    Returns:
        An open asyncpg connection. The caller must close it.

    Raises:
        RuntimeError: If ``DATABASE_URL`` is not set.
    """
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set; see .env.example")
    return await asyncpg.connect(url)
