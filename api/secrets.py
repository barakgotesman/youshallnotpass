"""Server-only access to level secrets.

The secret is read from the environment and injected into the defender prompt
on the server. No route returns it, and nothing here logs it.
"""

import hmac
import os


def get_secret(level_id: int) -> str:
    """Returns the active secret for a level.

    Args:
        level_id: Level number.

    Returns:
        The secret string.

    Raises:
        RuntimeError: If ``LEVEL_<n>_SECRET`` is not set.
    """
    name = f"LEVEL_{level_id}_SECRET"
    value = os.environ.get(name, "")
    if not value:
        raise RuntimeError(f"{name} is not set; see .env.example")
    return value


def is_correct_guess(level_id: int, guess: str) -> bool:
    """Checks a player's password guess.

    Comparison ignores case and surrounding spaces so "lantern " counts, and
    uses a constant-time compare so response timing cannot leak how many
    leading characters were right.

    Args:
        level_id: Level the guess is for.
        guess: The player's guess.

    Returns:
        True if the guess matches the secret.
    """
    expected = get_secret(level_id).strip().casefold()
    return hmac.compare_digest(guess.strip().casefold().encode(), expected.encode())
