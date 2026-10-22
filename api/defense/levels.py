"""Level definitions: which defender prompt and settings each level uses.

Each level is a configuration that adds one layer on top of the previous one.
Only level 1 exists so far; later phases append entries here.
"""

from pydantic import BaseModel


class LevelConfig(BaseModel):
    """Pipeline configuration for one level.

    Attributes:
        id: Level number, 1-based.
        name: Display name.
        defender_prompt: Version of ``prompts/defender/`` to use (the
            level's security rules).
        defender_temperature: Sampling temperature for the guard. Higher means
            more varied (and more easily tricked) replies.
    """

    id: int
    name: str
    defender_prompt: str
    defender_temperature: float


LEVELS: dict[int, LevelConfig] = {
    1: LevelConfig(
        id=1,
        name="The Gate",
        defender_prompt="v1",
        defender_temperature=0.7,
    ),
}


def get_level(level_id: int) -> LevelConfig | None:
    """Looks up a level.

    Args:
        level_id: Level number from the request.

    Returns:
        The level's config, or None if no such level exists.
    """
    return LEVELS.get(level_id)
