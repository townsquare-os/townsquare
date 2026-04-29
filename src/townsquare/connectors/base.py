"""Connector protocol — every per-source data adapter implements this."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class Item:
    id: str
    title: str
    snippet: str
    url: str | None = None
    occurred_at: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    source: str = ""
    user_email: str = ""


class Connector(Protocol):
    source_id: str
    required_scopes: list[str]
    supports_update: bool

    async def search(self, query: str, access_token: str, limit: int = 20) -> list[Item]: ...

    async def fetch(self, item_id: str, access_token: str) -> Item | None: ...
