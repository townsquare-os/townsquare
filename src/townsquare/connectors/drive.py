"""Google Drive connector — searches under the user's own access token."""

from __future__ import annotations

from townsquare.connectors.base import Item


class DriveConnector:
    source_id = "drive"
    required_scopes = ["https://www.googleapis.com/auth/drive.readonly"]
    supports_update = False

    async def search(self, query: str, access_token: str, limit: int = 20) -> list[Item]:
        raise NotImplementedError("week 3")

    async def fetch(self, item_id: str, access_token: str) -> Item | None:
        raise NotImplementedError("week 3")
