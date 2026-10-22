"""Shared types for the defense pipeline.

Every layer reports a ``LayerResult`` in the same shape, and the pipeline
collects them into a ``PipelineTrace``. That uniform trace is what later phases
save to the database and what the eval harness measures.
"""

from typing import Literal

from pydantic import BaseModel, Field


class LayerResult(BaseModel):
    """The outcome of one layer for one turn.

    Attributes:
        layer: Layer name, e.g. ``"guard"``.
        verdict: ``"allow"`` lets the turn continue, ``"block"`` stops it.
        reason: Why, for internal use only. It must never be sent to the
            client: telling players which layer blocked them teaches them how
            to get around it.
        latency_ms: Time this layer took.
        tokens_in: LLM prompt tokens used (0 for deterministic layers).
        tokens_out: LLM completion tokens used (0 for deterministic layers).
    """

    layer: str
    verdict: Literal["allow", "block"]
    reason: str
    latency_ms: int = 0
    tokens_in: int = 0
    tokens_out: int = 0


class PipelineTrace(BaseModel):
    """Ordered record of every layer that ran during one turn.

    Attributes:
        layers: Results in execution order.
    """

    layers: list[LayerResult] = Field(default_factory=list)
