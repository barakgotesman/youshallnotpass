"""Resolves which defense version is currently deployed for a level."""

import asyncpg

from api.db import queries
from api.defense.levels import LevelConfig
from api.defense.pipeline import PERSONA_VERSION
from api.llm.roles import load_role


async def current_defense_version(conn: asyncpg.Connection, level: LevelConfig) -> int:
    """Finds (or registers) the defense version row for what is running now.

    The version is derived from the live config (prompt versions and model
    names) rather than stored by hand, so it cannot drift from reality: change
    a prompt or a model and the next turn is automatically a new version.

    Args:
        conn: Open connection.
        level: The level being played.

    Returns:
        The defense version id.
    """
    prompt_versions = {"persona": PERSONA_VERSION, "defender": level.defender_prompt}
    models = {"defender": load_role("DEFENDER", level.id).model}
    return await queries.ensure_defense_version(conn, level, prompt_versions, models)
