"""Loads versioned prompt files from ``prompts/``.

Prompts are never written inline in code: they are files with a version in the
name, so a defense version can point at an exact, immutable prompt.
"""

from pathlib import Path

# prompts/ sits at the repo root, one level above this package.
PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


def load_prompt(role: str, version: str, **variables: str) -> str:
    """Reads ``prompts/<role>/<version>.md`` and fills ``{{NAME}}`` placeholders.

    Args:
        role: Prompt folder, e.g. ``"defender"``.
        version: File stem, e.g. ``"v1"``.
        **variables: Placeholder values, keyed by lowercase name. ``secret="X"``
            replaces ``{{SECRET}}``.

    Returns:
        The prompt text with placeholders replaced.

    Raises:
        FileNotFoundError: If that prompt version does not exist.
    """
    text = (PROMPTS_DIR / role / f"{version}.md").read_text(encoding="utf-8")
    for name, value in variables.items():
        text = text.replace("{{" + name.upper() + "}}", value)
    return text
