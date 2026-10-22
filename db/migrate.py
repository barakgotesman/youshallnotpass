"""Minimal SQL migration runner.

Applies every ``db/migrations/*.sql`` file in filename order, once each, and
records applied names in ``schema_migrations``. We use plain SQL files and ~30
lines of runner on purpose: the schema stays readable, and there is no ORM
magic to learn.

Usage:
    python -m db.migrate
"""

import asyncio
from pathlib import Path

from dotenv import load_dotenv

from api.db.connection import connect

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


async def migrate() -> None:
    """Applies all pending migrations, each inside its own transaction.

    A transaction per file means a failing migration leaves the database
    exactly as it was before that file, so it is safe to fix and re-run.

    Raises:
        RuntimeError: If ``DATABASE_URL`` is not set.
    """
    conn = await connect()
    try:
        await conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations ("
            "name text PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now())"
        )
        applied = {r["name"] for r in await conn.fetch("SELECT name FROM schema_migrations")}
        for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
            if path.name in applied:
                continue
            async with conn.transaction():
                await conn.execute(path.read_text(encoding="utf-8"))
                await conn.execute("INSERT INTO schema_migrations (name) VALUES ($1)", path.name)
            print(f"applied {path.name}")
    finally:
        await conn.close()


if __name__ == "__main__":
    load_dotenv()
    asyncio.run(migrate())
