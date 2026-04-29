"""Gmail connector — searches under the user's own access token.

Stub for v0.1 scaffold. Real implementation in week 3 via
google-api-python-client.
"""

from __future__ import annotations

from townsquare.connectors.base import Item


class GmailConnector:
    source_id = "gmail"
    required_scopes = ["https://www.googleapis.com/auth/gmail.readonly"]
    supports_update = False

    async def search(self, query: str, access_token: str, limit: int = 20) -> list[Item]:
        raise NotImplementedError("week 3")

    async def fetch(self, item_id: str, access_token: str) -> Item | None:
        raise NotImplementedError("week 3")
