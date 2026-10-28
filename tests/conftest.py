"""Shared test setup: an in-memory stand-in for the database.

Route tests should exercise our logic (limits, sessions, fail-closed), not
Neon's network, so every query function is replaced by a fake that records
what the app tried to store.
"""

from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4

import pytest

from api.db import queries
from api.index import app
from api.session import db_connection


@dataclass
class FakeDb:
    """Records what the API wrote, and answers the few reads it makes."""

    sessions: set[UUID] = field(default_factory=set)
    attempts: list[dict[str, Any]] = field(default_factory=list)
    cleared: set[tuple[UUID, int]] = field(default_factory=set)
    attacks: list[tuple[UUID, int]] = field(default_factory=list)


@pytest.fixture(autouse=True)
def fake_db(monkeypatch: pytest.MonkeyPatch) -> Iterator[FakeDb]:
    """Swaps the database layer for memory and sets the env the API needs."""
    db = FakeDb()
    monkeypatch.setenv("IP_HASH_SALT", "test-salt")
    # No Upstash in tests unless a test builds its own store: limits are off by default.
    monkeypatch.delenv("UPSTASH_REDIS_REST_URL", raising=False)
    monkeypatch.delenv("UPSTASH_REDIS_REST_TOKEN", raising=False)

    async def fake_connection() -> Any:
        yield object()

    async def session_exists(_conn: Any, session_id: UUID) -> bool:
        return session_id in db.sessions

    async def create_session(_conn: Any, _ip_hash: str) -> UUID:
        session_id = uuid4()
        db.sessions.add(session_id)
        return session_id

    async def ensure_defense_version(*_args: Any) -> int:
        return 1

    async def save_attempt(_conn: Any, session_id: UUID, level_id: int, version: int, *rest: Any) -> None:
        db.attempts.append(
            {"session": session_id, "level": level_id, "version": version, "message": rest[0], "reply": rest[1], "trace": rest[2]}
        )

    async def cleared_levels(_conn: Any, session_id: UUID) -> list[int]:
        return sorted(level for sid, level in db.cleared if sid == session_id)

    async def mark_cleared(_conn: Any, session_id: UUID, level_id: int) -> bool:
        first = (session_id, level_id) not in db.cleared
        db.cleared.add((session_id, level_id))
        return first

    async def save_attack(_conn: Any, session_id: UUID, level_id: int) -> None:
        db.attacks.append((session_id, level_id))

    monkeypatch.setattr(queries, "session_exists", session_exists)
    monkeypatch.setattr(queries, "create_session", create_session)
    monkeypatch.setattr(queries, "ensure_defense_version", ensure_defense_version)
    monkeypatch.setattr(queries, "save_attempt", save_attempt)
    monkeypatch.setattr(queries, "cleared_levels", cleared_levels)
    monkeypatch.setattr(queries, "mark_cleared", mark_cleared)
    monkeypatch.setattr(queries, "save_attack_from_session", save_attack)
    app.dependency_overrides[db_connection] = fake_connection
    yield db
    app.dependency_overrides.clear()
