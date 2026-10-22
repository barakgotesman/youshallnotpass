"""Runs one chat turn through a level's defense pipeline.

Level 1 has a single step: the guard LLM with a (naive) system prompt. Later
phases add input layers before it and output layers after it.
"""

from pydantic import BaseModel

from api.defense.base import LayerResult, PipelineTrace
from api.defense.levels import LevelConfig
from api.llm.client import ChatTurn, complete
from api.llm.roles import load_role
from api.prompts import load_prompt
from api.secrets import get_secret

# The guard's character is one fixed file for every level. Changing it means
# a new persona version and a changelog entry, never a per-level setting.
PERSONA_VERSION = "v1"

# What the player sees when a guard layer fails. In-world on purpose: a raw
# error would reveal our infrastructure, and it must read the same whatever
# the cause.
IN_WORLD_REFUSAL = "The guard narrows his eyes and says nothing. Perhaps try again later."


class TurnResult(BaseModel):
    """What the pipeline hands back to the route.

    Attributes:
        reply: Text to show the player.
        blocked: True if the turn was stopped instead of answered normally.
        trace: Full per-layer record. Internal; never sent to the client.
    """

    reply: str
    blocked: bool
    trace: PipelineTrace


async def run_turn(level: LevelConfig, history: list[ChatTurn]) -> TurnResult:
    """Runs the guard for one turn.

    Fail closed: if the guard call errors or times out, the turn is blocked
    with the in-world refusal. Availability is traded for safety, which is the
    right trade for a system whose whole job is keeping a secret.

    Args:
        level: The level being played.
        history: Conversation so far, ending with the player's new message.

    Returns:
        The reply to show, whether it was blocked, and the trace.
    """
    trace = PipelineTrace()
    # Character first, then this level's security rules: the persona is the
    # same for the whole game, so only the rules part differs per level.
    persona = load_prompt("persona", PERSONA_VERSION)
    rules = load_prompt("defender", level.defender_prompt, secret=get_secret(level.id))
    system_prompt = f"{persona}\n{rules}"
    messages = [ChatTurn(role="system", content=system_prompt), *history]

    try:
        result = await complete(load_role("DEFENDER", level.id), messages, level.defender_temperature)
    except Exception as exc:  # noqa: BLE001 - any failure must fail closed
        trace.layers.append(
            LayerResult(layer="guard", verdict="block", reason=f"guard failed: {type(exc).__name__}")
        )
        return TurnResult(reply=IN_WORLD_REFUSAL, blocked=True, trace=trace)

    trace.layers.append(
        LayerResult(
            layer="guard",
            verdict="allow",
            reason="guard replied",
            latency_ms=result.latency_ms,
            tokens_in=result.tokens_in,
            tokens_out=result.tokens_out,
        )
    )
    return TurnResult(reply=result.text, blocked=False, trace=trace)
