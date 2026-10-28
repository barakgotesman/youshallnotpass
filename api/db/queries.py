"""Database queries used by the API.

Plain SQL in clearly named functions. Every function takes the request's
connection so one request pays for one connection.
"""

import json
from uuid import UUID

import asyncpg

from api.defense.levels import LevelConfig


async def session_exists(conn: asyncpg.Connection, session_id: UUID) -> bool:
    """Checks whether a session id is known.

    Args:
        conn: Open connection.
        session_id: Id from the cookie.

    Returns:
        True if the session exists.
    """
    return await conn.fetchval("SELECT EXISTS (SELECT 1 FROM sessions WHERE id = $1)", session_id)


async def create_session(conn: asyncpg.Connection, ip_hash: str) -> UUID:
    """Creates an anonymous session.

    Args:
        conn: Open connection.
        ip_hash: Salted hash of the client IP.

    Returns:
        The new session id.
    """
    return await conn.fetchval("INSERT INTO sessions (ip_hash) VALUES ($1) RETURNING id", ip_hash)


async def ensure_defense_version(
    conn: asyncpg.Connection,
    level: LevelConfig,
    prompt_versions: dict[str, str],
    models: dict[str, str],
) -> int:
    """Finds or creates the defense version row for what is currently deployed.

    Attempts and attacks point at this row, so a later eval can say exactly
    which prompts and models a given attack faced. The ``levels`` row is
    created on first use because the level list lives in code.

    Args:
        conn: Open connection.
        level: The level being played.
        prompt_versions: Prompt version per role, e.g. ``{"defender": "v1"}``.
        models: Model per role.

    Returns:
        The defense version id.
    """
    await conn.execute(
        "INSERT INTO levels (id, name, pipeline_config) VALUES ($1, $2, $3::jsonb) "
        "ON CONFLICT (id) DO NOTHING",
        level.id,
        level.name,
        level.model_dump_json(),
    )
    prompts_json = json.dumps(prompt_versions)
    models_json = json.dumps(models)
    # Race-safe thanks to the unique index: concurrent first requests both
    # insert-or-ignore, then both read the one surviving row.
    await conn.execute(
        "INSERT INTO defense_versions (level_id, prompt_versions, models) "
        "VALUES ($1, $2::jsonb, $3::jsonb) ON CONFLICT DO NOTHING",
        level.id,
        prompts_json,
        models_json,
    )
    return await conn.fetchval(
        "SELECT id FROM defense_versions "
        "WHERE level_id = $1 AND prompt_versions = $2::jsonb AND models = $3::jsonb",
        level.id,
        prompts_json,
        models_json,
    )


async def save_attempt(
    conn: asyncpg.Connection,
    session_id: UUID,
    level_id: int,
    defense_version_id: int,
    user_message: str,
    model_response: str | None,
    pipeline_trace: str,
) -> None:
    """Stores one chat turn with its full pipeline trace.

    Args:
        conn: Open connection.
        session_id: The player's session.
        level_id: Level played.
        defense_version_id: Defense the turn faced.
        user_message: The player's message.
        model_response: The guard's reply, or None if the turn was blocked.
        pipeline_trace: The trace as a JSON string.
    """
    await conn.execute(
        "INSERT INTO attempts "
        "(session_id, level_id, defense_version_id, user_message, model_response, pipeline_trace) "
        "VALUES ($1, $2, $3, $4, $5, $6::jsonb)",
        session_id,
        level_id,
        defense_version_id,
        user_message,
        model_response,
        pipeline_trace,
    )


async def cleared_levels(conn: asyncpg.Connection, session_id: UUID) -> list[int]:
    """Lists the levels a player has beaten.

    Args:
        conn: Open connection.
        session_id: The player's session.

    Returns:
        Level ids, ascending.
    """
    rows = await conn.fetch(
        "SELECT level_id FROM session_progress WHERE session_id = $1 ORDER BY level_id", session_id
    )
    return [row["level_id"] for row in rows]


async def mark_cleared(conn: asyncpg.Connection, session_id: UUID, level_id: int) -> bool:
    """Records that a player beat a level.

    Args:
        conn: Open connection.
        session_id: The player's session.
        level_id: Level beaten. Its ``levels`` row must exist (the player
            guessing without ever chatting is handled by the caller).

    Returns:
        True if this is the first clear, False if it was already recorded.
    """
    inserted = await conn.fetchval(
        "INSERT INTO session_progress (session_id, level_id) VALUES ($1, $2) "
        "ON CONFLICT DO NOTHING RETURNING 1",
        session_id,
        level_id,
    )
    return inserted is not None


async def save_attack_from_session(conn: asyncpg.Connection, session_id: UUID, level_id: int) -> None:
    """Saves the conversation that led to a clear as an attack record.

    The conversation is rebuilt from the player's stored, answered attempts
    (blocked turns have no guard reply and are left out). It is not yet in the
    regression suite: curation and dedup come with the attack-intelligence phase.

    Args:
        conn: Open connection.
        session_id: The player's session.
        level_id: Level just beaten.
    """
    rows = await conn.fetch(
        "SELECT defense_version_id, user_message, model_response FROM attempts "
        "WHERE session_id = $1 AND level_id = $2 AND model_response IS NOT NULL ORDER BY id",
        session_id,
        level_id,
    )
    if not rows:
        return
    conversation: list[dict[str, str]] = []
    for row in rows:
        conversation.append({"role": "user", "content": row["user_message"]})
        conversation.append({"role": "assistant", "content": row["model_response"]})
    await conn.execute(
        "INSERT INTO attacks (level_id, defense_version_id, conversation) VALUES ($1, $2, $3::jsonb)",
        level_id,
        rows[-1]["defense_version_id"],
        json.dumps(conversation),
    )
