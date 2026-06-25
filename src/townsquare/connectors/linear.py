from __future__ import annotations

import httpx

from townsquare.connectors.base import Item

LINEAR_API = "https://api.linear.app/graphql"


class LinearConnector:
    source_id = "linear"
    required_scopes = ["read"]
    supports_update = False

    async def search(self, query, access_token, limit):
        headers = {"Authorization": f"Bearer {access_token}"}
        query_str = """
        query SearchIssues($query: String!, $limit: Int!) {
            issues(filter: { title: { contains: $query } }, first: $limit) {
                nodes {
                    id
                    title
                    description
                    url
                }
            }
        }
        """
        variables = {"query": query, "limit": limit}
        async with httpx.AsyncClient() as client:
            response = await client.post(
                LINEAR_API,
                json={"query": query_str, "variables": variables},
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
            issues = data["data"]["issues"]["nodes"]
            return [
                Item(
                    id=issue["id"],
                    title=issue["title"],
                    description=issue["description"],
                    url=issue["url"],
                )
                for issue in issues
            ]

    async def fetch(self, item_id, access_token):
        headers = {"Authorization": f"Bearer {access_token}"}
        query_str = """
        query GetIssue($id: String!) {
            issue(id: $id) {
                id
                title
                description
                url
            }
        }
        """
        variables = {"id": item_id}
        async with httpx.AsyncClient() as client:
            response = await client.post(
                LINEAR_API,
                json={"query": query_str, "variables": variables},
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
            issue = data["data"]["issue"]
            return Item(
                id=issue["id"],
                title=issue["title"],
                description=issue["description"],
                url=issue["url"],
            )
