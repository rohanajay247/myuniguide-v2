"""Request limiting for the public deployment.

In-memory and per-process: state resets on cold start and is not shared across
Cloud Run instances, so with max-instances 3 the real ceiling is roughly 3x
what is configured here. Acceptable for a demo — the Gemini spending cap is the
hard backstop; this just stops one visitor burning through it in a minute.
"""

import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request

PER_IP_PER_HOUR = 20
GLOBAL_PER_DAY = 500

_hits: dict[str, deque[float]] = defaultdict(deque)
_today: deque[float] = deque()


def _prune(q: deque[float], window: float) -> None:
    cutoff = time.time() - window
    while q and q[0] < cutoff:
        q.popleft()


def check(request: Request) -> None:
    ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip() or (
        request.client.host if request.client else "unknown"
    )

    _prune(_today, 86400)
    if len(_today) >= GLOBAL_PER_DAY:
        raise HTTPException(
            status_code=429,
            detail="Daily query limit reached for this demo. Try again tomorrow.",
        )

    q = _hits[ip]
    _prune(q, 3600)
    if len(q) >= PER_IP_PER_HOUR:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit: {PER_IP_PER_HOUR} questions per hour. Try again later.",
        )

    now = time.time()
    q.append(now)
    _today.append(now)

    if len(_hits) > 5000:  # crude guard against unbounded growth
        _hits.clear()