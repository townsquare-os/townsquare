"""Selector — decides which (user, source) targets to fan a query to.

Stub for v0.1 scaffold. Real implementation in week 4.

v0.1 default: all active users in the configured domain × all sources
each user has connected.
"""

from __future__ import annotations

from townsquare.federation.router import FanoutTarget


class Selector:
    def __init__(self, db_session_factory) -> None:
        self._db = db_session_factory

    async def select(self, query: str, asking_user: str) -> list[FanoutTarget]:
        raise NotImplementedError("week 4")
