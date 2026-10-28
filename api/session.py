"""Anonymous player sessions.

A player is identified by a random id in an HttpOnly cookie. There are no
accounts: the id only ties together one browser's chats, guesses and progress.
Raw IP addresses are never stored, only a salted hash.
"""

import hashlib
import hmac
import os
from collections.abc import AsyncIterator
from uuid import UUID

import asyncpg
from fastapi import Depends, Request, Response
from pydantic import BaseModel

from api.db import queries
from api.db.connection import connect

COOKIE_NAME = "ysnp_session"
COOKIE_MAX_AGE_S = 60 * 60 * 24 * 365


class PlayerSession(BaseModel):
    """The caller's identity for one request.

    Attributes:
        id: Session id (also stored in the cookie).
        ip_hash: Salted hash of the client IP, for rate limiting.
    """

    id: UUID
    ip_hash: str


def client_ip(request: Request) -> str:
    """Finds the caller's IP.

    On Vercel the real client is the first entry of ``X-Forwarded-For``; the
    socket peer is only the proxy.

    Args:
        request: The incoming request.

    Returns:
        The IP as text, or ``"unknown"`` if none can be found.
    """
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def hash_ip(ip: str) -> str:
    """Hashes an IP with a server-side salt so it cannot be reversed by brute force.

    Args:
        ip: Raw IP address.

    Returns:
        Hex digest.

    Raises:
        RuntimeError: If ``IP_HASH_SALT`` is not set. Hashing without a salt
            would be reversible by brute force over the IPv4 space.
    """
    salt = os.environ.get("IP_HASH_SALT", "")
    if not salt:
        raise RuntimeError("IP_HASH_SALT is not set; see .env.example")
    return hmac.new(salt.encode(), ip.encode(), hashlib.sha256).hexdigest()


async def db_connection() -> AsyncIterator[asyncpg.Connection]:
    """Opens one database connection per request and always closes it.

    Sharing a connection across a request's queries avoids paying connection
    setup latency several times per chat turn.

    Yields:
        An open connection.
    """
    conn = await connect()
    try:
        yield conn
    finally:
        await conn.close()


async def current_session(
    request: Request,
    response: Response,
    conn: asyncpg.Connection = Depends(db_connection),
) -> PlayerSession:
    """Returns the caller's session, creating one (and setting the cookie) if needed.

    An unknown or malformed cookie is treated as no cookie: the player simply
    gets a fresh session instead of an error.

    Args:
        request: The incoming request.
        response: Used to set the cookie on a new session.
        conn: Request-scoped database connection.

    Returns:
        The player's session.
    """
    ip_hash = hash_ip(client_ip(request))
    try:
        existing: UUID | None = UUID(request.cookies.get(COOKIE_NAME, ""))
    except ValueError:
        existing = None
    if existing is not None and await queries.session_exists(conn, existing):
        return PlayerSession(id=existing, ip_hash=ip_hash)

    session_id = await queries.create_session(conn, ip_hash)
    secure = request.headers.get("x-forwarded-proto", request.url.scheme) == "https"
    response.set_cookie(
        COOKIE_NAME,
        str(session_id),
        max_age=COOKIE_MAX_AGE_S,
        httponly=True,
        samesite="lax",
        secure=secure,
    )
    return PlayerSession(id=session_id, ip_hash=ip_hash)
