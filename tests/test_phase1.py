"""Tests for the deterministic parts of Phase 1.

The guard LLM itself is not unit-tested: LLM behavior is measured by the eval
harness (Phase 4). Here we test everything around it, including that a failing
guard blocks the turn instead of letting it through.
"""

import asyncio

import pytest
from fastapi.testclient import TestClient

from api.defense import pipeline
from api.defense.levels import get_level
from api.index import app
from api.llm.client import ChatTurn
from api.secrets import is_correct_guess

client = TestClient(app)


@pytest.fixture(autouse=True)
def secret_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Gives every test a known level-1 secret and role config."""
    monkeypatch.setenv("LEVEL_1_SECRET", "TESTWORD")
    for field, value in {
        "PROVIDER": "test",
        "MODEL": "test-model",
        "BASE_URL": "http://localhost",
        "API_KEY": "test-key",
    }.items():
        monkeypatch.setenv(f"DEFENDER_{field}", value)


def test_guess_ignores_case_and_spaces() -> None:
    """A correct guess counts however the player capitalizes or pads it."""
    assert is_correct_guess(1, "  testword ")


def test_wrong_guess_is_rejected() -> None:
    """A near miss must not pass."""
    assert not is_correct_guess(1, "testwords")


def test_guess_route_never_returns_the_secret() -> None:
    """The response body carries only the boolean."""
    response = client.post("/api/guess", json={"level": 1, "guess": "nope"})
    assert response.json() == {"correct": False}


def test_unknown_level_is_404() -> None:
    """Requests for a level that does not exist fail cleanly."""
    body = {"level": 99, "messages": [{"role": "user", "content": "hi"}]}
    assert client.post("/api/chat", json=body).status_code == 404


def test_chat_rejects_overlong_message() -> None:
    """The length cap protects the free LLM quota."""
    body = {"level": 1, "messages": [{"role": "user", "content": "x" * 1001}]}
    assert client.post("/api/chat", json=body).status_code == 422


def test_chat_requires_last_message_from_player() -> None:
    """The guard only answers the player, never continues its own turn."""
    body = {"level": 1, "messages": [{"role": "assistant", "content": "hi"}]}
    assert client.post("/api/chat", json=body).status_code == 422


def test_guard_failure_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    """If the LLM call raises, the turn is blocked with the in-world refusal."""

    async def boom(*_args: object, **_kwargs: object) -> None:
        raise TimeoutError("simulated outage")

    monkeypatch.setattr(pipeline, "complete", boom)
    level = get_level(1)
    assert level is not None

    result = asyncio.run(pipeline.run_turn(level, [ChatTurn(role="user", content="hi")]))

    assert result.blocked
    assert result.reply == pipeline.IN_WORLD_REFUSAL
    assert result.trace.layers[0].verdict == "block"
    # The refusal shown to the player must not hint at the cause.
    assert "TimeoutError" not in result.reply


def test_level_model_override_wins_over_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """DEFENDER_MODEL_LEVEL_<n> replaces the default model for that level only."""
    from api.llm.roles import load_role

    monkeypatch.setenv("DEFENDER_MODEL_LEVEL_1", "weak-model")
    assert load_role("DEFENDER", 1).model == "weak-model"
    assert load_role("DEFENDER", 2).model == "test-model"
    assert load_role("DEFENDER").model == "test-model"
