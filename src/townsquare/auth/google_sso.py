"""Google Workspace SSO with strict domain restriction.

Uses Authlib's Starlette integration (works with FastAPI). The `hd`
parameter is set as a hint, but enforcement happens server-side after
ID token verification — `hd` claim AND `email_verified` claim must
match before we accept the user.
"""

from __future__ import annotations

from dataclasses import dataclass

import httpx
from authlib.integrations.starlette_client import OAuth, OAuthError


@dataclass(frozen=True)
class GoogleUserClaims:
    email: str
    email_verified: bool
    domain: str
    name: str | None
    picture: str | None
    sub: str


class DomainRestrictionError(Exception):
    """Raised when SSO succeeds but the user's domain is not allowed."""


class GoogleWorkspaceSSO:
    """Google Workspace SSO orchestrator.

    Args:
        client_id: from Google Cloud Console OAuth client.
        client_secret: from Google Cloud Console OAuth client.
        workspace_domain: e.g. "example.com". Login is rejected for any
            other domain.
        scopes: OAuth scopes to request. The default list covers SSO +
            Gmail/Drive/Calendar read so a single grant covers all v0.1
            connectors.
    """

    DEFAULT_SCOPES = [
        "openid",
        "email",
        "profile",
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/drive.readonly",
        "https://www.googleapis.com/auth/calendar.readonly",
    ]

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        workspace_domain: str,
        scopes: list[str] | None = None,
    ) -> None:
        if not workspace_domain:
            raise ValueError("workspace_domain is required for domain restriction")
        self.client_id = client_id
        self.client_secret = client_secret
        self.workspace_domain = workspace_domain.lower()
        self.scopes = scopes or self.DEFAULT_SCOPES

        self._oauth = OAuth()
        self._oauth.register(
            name="google",
            client_id=client_id,
            client_secret=client_secret,
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={
                "scope": " ".join(self.scopes),
                "prompt": "consent",
                "access_type": "offline",
                "hd": self.workspace_domain,
            },
        )

    @property
    def client(self):
        """The underlying Authlib OAuth client (for FastAPI integration)."""
        return self._oauth.google

    async def fetch_userinfo(self, access_token: str) -> GoogleUserClaims:
        """Call Google's userinfo endpoint with the access token.

        Used as a defence-in-depth check after ID-token verification:
        confirms the access token actually belongs to a Workspace user.
        """
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(
                "https://openidconnect.googleapis.com/v1/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            r.raise_for_status()
            data = r.json()
        return self._claims_from_userinfo(data)

    @staticmethod
    def _claims_from_userinfo(data: dict) -> GoogleUserClaims:
        email = (data.get("email") or "").lower()
        domain = email.split("@", 1)[1] if "@" in email else ""
        return GoogleUserClaims(
            email=email,
            email_verified=bool(data.get("email_verified", False)),
            domain=domain,
            name=data.get("name"),
            picture=data.get("picture"),
            sub=data.get("sub", ""),
        )

    @staticmethod
    def claims_from_id_token(id_token_payload: dict) -> GoogleUserClaims:
        """Parse claims from an Authlib-verified ID token payload."""
        email = (id_token_payload.get("email") or "").lower()
        # Google sets `hd` to the Workspace domain for Workspace accounts.
        domain = (id_token_payload.get("hd") or "").lower()
        if not domain and "@" in email:
            domain = email.split("@", 1)[1]
        return GoogleUserClaims(
            email=email,
            email_verified=bool(id_token_payload.get("email_verified", False)),
            domain=domain,
            name=id_token_payload.get("name"),
            picture=id_token_payload.get("picture"),
            sub=id_token_payload.get("sub", ""),
        )

    def verify_domain(self, claims: GoogleUserClaims) -> None:
        """Raise DomainRestrictionError if the user's domain isn't allowed.

        Both `email_verified=true` and matching `hd` are required.
        """
        if not claims.email:
            raise DomainRestrictionError("login claims missing email")
        if not claims.email_verified:
            raise DomainRestrictionError("email_verified=false; rejecting login")
        if claims.domain.lower() != self.workspace_domain:
            raise DomainRestrictionError(
                f"domain '{claims.domain}' not allowed; expected '{self.workspace_domain}'"
            )


__all__ = ["GoogleWorkspaceSSO", "GoogleUserClaims", "DomainRestrictionError", "OAuthError"]
