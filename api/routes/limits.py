"""Turns a rate-limit decision into the HTTP answer the frontend understands."""

from fastapi import HTTPException

from api.ratelimit import Decision


def raise_if_refused(decision: Decision) -> None:
    """Raises a 429 carrying a machine-readable code when a request is refused.

    The code (not the status text) tells the frontend which designed screen to
    show: a gentle "slow down" or the "vault closed for today" state.

    Args:
        decision: Result of a rate-limit check.

    Raises:
        HTTPException: 429 with ``detail = {"code", "retry_after"}`` and a
            ``Retry-After`` header, if the decision is not allowed.
    """
    if decision.allowed:
        return
    raise HTTPException(
        status_code=429,
        detail={"code": decision.reason, "retry_after": decision.retry_after},
        headers={"Retry-After": str(decision.retry_after)},
    )
