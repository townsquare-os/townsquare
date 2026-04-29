"""Federation router — fans queries across selected (user, source) targets.

Stub for v0.1 scaffold. Real implementation in week 4.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from townsquare.connectors.base import Item


@dataclass
class FanoutTarget:
    user_email: str
    source: str


@dataclass
class FanoutResult:
    targets: list[FanoutTarget]
    items: list[Item]
    errors: list[dict[str, Any]]
    total_latency_ms: float


class FederatedRouter:
    def __init__(self, db_session_factory, token_crypto, connector_registry) -> None:
        self._db = db_session_factory
        self._crypto = token_crypto
        self._connectors = connector_registry

    async def fanout(
        self,
        query: str,
        targets: list[FanoutTarget],
        per_target_budget_ms: int = 5000,
    ) -> FanoutResult:
        raise NotImplementedError("week 4 — implement asyncio.gather fanout")
