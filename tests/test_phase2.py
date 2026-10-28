"""Tests for Phase 2: sessions, attempt persistence, and rate limiting."""

import asyncio

import pytest
from fastapi.testclient import TestClient

from api import ratelimit
from api.defense import pipeline
from api.defense.base import LayerResult, PipelineTrace
from api.index import app
from api.session import COOKIE_NAME, hash_ip
from tests.conftest import FakeDb


class MemoryStore:
    """In-memory counter store with the same contract as Upstash."""

    def __init__(self) -> None:
        self.counts: dict[str, int] = {}

    async def incr_many(self, keys: list[tuple[str, int]]) -> list[int]:
        for key, _ttl in keys:
            self.counts[key] = self.counts.get(key, 0) + 1
        return [self.counts[key] for key, _ttl in keys]


class BrokenStore:
    """A store whose backend is down."""

    async def incr_many(self, keys: list[tuple[str, int]]) -> list[int]:
        raise ConnectionError("redis down")


@pytest.fixture
def guard_reply(monkeypatch: pytest.MonkeyPatch) -> None:
    """Replaces the LLM guard with a canned answer."""

    async def fake_run_turn(*_args: object) -> pipeline.TurnResult:
        trace = PipelineTrace(layers=[LayerResult(layer="guard", verdict="allow", reason="ok")])
        return pipeline.TurnResult(reply="Go away.", blocked=False, trace=trace)

    monkeypatch.setattr("api.routes.chat.run_turn", fake_run_turn)
    monkeypatch.setenv("LEVEL_1_SECRET", "TESTWORD")
    for field, value in {"PROVIDER": "t", "MODEL": "m", "BASE_URL": "http://x", "API_KEY": "k"}.items():
        monkeypatch.setenv(f"DEFENDER_{field}", value)


CHAT_BODY = {"level": 1, "messages": [{"role": "user", "content": "hello"}]}


def test_first_request_sets_an_httponly_session_cookie(guard_reply: None) -> None:
    """A new player gets a cookie the page's scripts cannot read."""
    client = TestClient(app)
    response = client.post("/api/chat", json=CHAT_BODY)
    assert response.status_code == 200
    assert "httponly" in response.headers["set-cookie"].lower()
    assert COOKIE_NAME in client.cookies


def test_returning_player_keeps_their_session(guard_reply: None, fake_db: FakeDb) -> None:
    """The second request reuses the session instead of creating another."""
    client = TestClient(app)
    client.post("/api/chat", json=CHAT_BODY)
    client.post("/api/chat", json=CHAT_BODY)
    assert len(fake_db.sessions) == 1


def test_garbage_cookie_gets_a_fresh_session(guard_reply: None, fake_db: FakeDb) -> None:
    """A forged or malformed cookie must not cause an error."""
    client = TestClient(app, cookies={COOKIE_NAME: "not-a-uuid"})
    assert client.post("/api/chat", json=CHAT_BODY).status_code == 200
    assert len(fake_db.sessions) == 1


def test_attempt_is_saved_with_its_trace(guard_reply: None, fake_db: FakeDb) -> None:
    """Every turn lands in attempts with the pipeline trace attached."""
    TestClient(app).post("/api/chat", json=CHAT_BODY)
    assert len(fake_db.attempts) == 1
    saved = fake_db.attempts[0]
    assert saved["message"] == "hello"
    assert saved["reply"] == "Go away."
    assert '"layer":"guard"' in saved["trace"]


def test_saving_failure_does_not_break_the_reply(
    guard_reply: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The player still gets their answer if the analytics write fails."""

    async def boom(*_args: object) -> None:
        raise RuntimeError("db down")

    monkeypatch.setattr("api.routes.chat.queries.save_attempt", boom)
    response = TestClient(app).post("/api/chat", json=CHAT_BODY)
    assert response.status_code == 200
    assert response.json()["reply"] == "Go away."


def test_correct_guess_records_progress_and_attack_once(guard_reply: None, fake_db: FakeDb) -> None:
    """Clearing a level stores progress, and the attack only on the first clear."""
    client = TestClient(app)
    client.post("/api/chat", json=CHAT_BODY)
    for _ in range(2):
        assert client.post("/api/guess", json={"level": 1, "guess": "testword"}).json() == {"correct": True}
    assert len(fake_db.cleared) == 1
    assert len(fake_db.attacks) == 1
    assert client.get("/api/progress").json() == {"cleared_levels": [1]}


def test_wrong_guess_records_nothing(guard_reply: None, fake_db: FakeDb) -> None:
    """A miss leaves no progress behind."""
    TestClient(app).post("/api/guess", json={"level": 1, "guess": "nope"})
    assert not fake_db.cleared


def test_hash_ip_is_salted_and_stable(monkeypatch: pytest.MonkeyPatch) -> None:
    """The same IP hashes the same way, differently per salt, and never to itself."""
    first = hash_ip("1.2.3.4")
    assert first == hash_ip("1.2.3.4")
    assert "1.2.3.4" not in first
    monkeypatch.setenv("IP_HASH_SALT", "other-salt")
    assert hash_ip("1.2.3.4") != first


def test_hash_ip_requires_a_salt(monkeypatch: pytest.MonkeyPatch) -> None:
    """Hashing without a salt would be brute-forceable, so it refuses."""
    monkeypatch.delenv("IP_HASH_SALT")
    with pytest.raises(RuntimeError):
        hash_ip("1.2.3.4")


def test_session_over_per_minute_limit_must_slow_down(monkeypatch: pytest.MonkeyPatch) -> None:
    """The 9th message in a minute is refused with a wait time."""
    monkeypatch.setenv("RATE_CHAT_PER_MIN_SESSION", "8")
    store = MemoryStore()
    decisions = [asyncio.run(ratelimit.check_chat("s", "ip", store, now=1000.0)) for _ in range(9)]
    assert all(d.allowed for d in decisions[:8])
    assert decisions[8].reason == "slow_down"
    assert 0 < decisions[8].retry_after <= 60


def test_new_window_resets_the_count() -> None:
    """After the minute passes, the player can chat again."""
    store = MemoryStore()
    for _ in range(9):
        asyncio.run(ratelimit.check_chat("s", "ip", store, now=1000.0))
    assert asyncio.run(ratelimit.check_chat("s", "ip", store, now=1100.0)).allowed


def test_spent_global_budget_closes_the_vault(monkeypatch: pytest.MonkeyPatch) -> None:
    """Once everyone together used the daily budget, new players are turned away too."""
    monkeypatch.setenv("DAILY_BUDGET_DEFENDER", "2")
    store = MemoryStore()
    results = [asyncio.run(ratelimit.check_chat(f"s{i}", f"ip{i}", store, now=1000.0)) for i in range(3)]
    assert [r.allowed for r in results] == [True, True, False]
    assert results[2].reason == "vault_closed"


def test_blocked_spammer_does_not_burn_the_global_budget(monkeypatch: pytest.MonkeyPatch) -> None:
    """Requests refused by personal limits never touch the shared budget."""
    monkeypatch.setenv("RATE_CHAT_PER_MIN_SESSION", "1")
    store = MemoryStore()
    for _ in range(5):
        asyncio.run(ratelimit.check_chat("s", "ip", store, now=1000.0))
    budget_keys = [k for k in store.counts if k.startswith("rl:budget")]
    assert store.counts[budget_keys[0]] == 1


def test_redis_outage_fails_closed() -> None:
    """If the limiter cannot count, nobody gets through."""
    decision = asyncio.run(ratelimit.check_chat("s", "ip", BrokenStore(), now=1000.0))
    assert not decision.allowed
    assert decision.reason == "vault_closed"


def test_no_store_means_no_limits() -> None:
    """Local development without Upstash is unlimited."""
    assert asyncio.run(ratelimit.check_chat("s", "ip", None, now=1000.0)).allowed


def test_route_returns_429_with_code(guard_reply: None, monkeypatch: pytest.MonkeyPatch) -> None:
    """The frontend learns which designed screen to show from the 429 body."""

    async def closed(*_args: object) -> ratelimit.Decision:
        return ratelimit.Decision(allowed=False, reason="vault_closed", retry_after=120)

    monkeypatch.setattr("api.routes.chat.ratelimit.check_chat", closed)
    response = TestClient(app).post("/api/chat", json=CHAT_BODY)
    assert response.status_code == 429
    assert response.json()["detail"] == {"code": "vault_closed", "retry_after": 120}
    assert response.headers["retry-after"] == "120"


def test_guess_flood_is_limited(guard_reply: None, monkeypatch: pytest.MonkeyPatch) -> None:
    """A script cannot try words faster than the per-minute guess limit."""
    monkeypatch.setenv("RATE_GUESS_PER_MIN_SESSION", "3")
    store = MemoryStore()
    monkeypatch.setattr(ratelimit, "default_store", lambda: store)
    client = TestClient(app)
    codes = [client.post("/api/guess", json={"level": 1, "guess": f"g{i}"}).status_code for i in range(5)]
    assert codes == [200, 200, 200, 429, 429]
