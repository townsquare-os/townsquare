"""Google Workspace SSO with strict domain restriction.

Stub for v0.1 scaffold — full Authlib wire-up lands in week 1.

Critical security note: the `hd` query parameter is a *hint* only.
We MUST verify the returned ID token's `hd` claim AND `email_verified`
claim server-side before accepting the user.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GoogleUserClaims:
    email: str
    email_verified: bool
    domain: str
    name: str | None
    sub: str  # stable Google user ID


class DomainRestrictionError(Exception):
    """Raised when SSO succeeds but the user's domain is not allowed."""


class GoogleWorkspaceSSO:
    def __init__(self, client_id: str, client_secret: str, workspace_domain: str) -> None:
        if not workspace_domain:
            raise ValueError("workspace_domain is required for domain restriction")
        self.client_id = client_id
        self.client_secret = client_secret
        self.workspace_domain = workspace_domain.lower()

    def authorize_url(self, redirect_uri: str, state: str, scopes: list[str]) -> str:
        raise NotImplementedError("week 1 — wire up via Authlib")

    async def handle_callback(self, code: str, redirect_uri: str):
        raise NotImplementedError("week 1 — wire up via Authlib")

    def _verify_domain(self, claims: GoogleUserClaims) -> None:
        if not claims.email_verified:
            raise DomainRestrictionError("email_verified=false; rejecting login")
        if claims.domain.lower() != self.workspace_domain:
            raise DomainRestrictionError(
                f"domain '{claims.domain}' not allowed; expected '{self.workspace_domain}'"
            )
