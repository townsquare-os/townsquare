"""Federation router + selector tests using fake connectors."""

from __future__ import annotations

import pytest
from cryptography.fernet import Fernet

from townsquare.auth.crypto import TokenCrypto
from townsquare.auth.google_sso import GoogleUserClaims
from townsquare.auth.users import store_google_connections, upsert_user_from_claims
from townsquare.connectors.base import Item
from townsquare.db import session_scope
from townsquare.federation.router import FanoutTarget, FederatedRouter
from townsquare.federation.selector import Selector


class FakeOK:
    source_id = "gmail"
    required_scopes = ["x"]
    supports_update = False

    async def search(self, query, access_token, limit=10):
        return [
            Item(
                id="m1", title=f"hit:{query}", snippet=f"token={access_token[:6]}", source="gmail"
            ),
        ]

    async def fetch(self, item_id, access_token):
        return None


class FakeBoom:
    source_id = "drive"
    required_scopes = ["x"]
    supports_update = False

    async def search(self, query, access_token, limit=10):
        raise RuntimeError("backend on fire")

    async def fetch(self, item_id, access_token):
        return None


def _seed(crypto: TokenCrypto, email: str, sources: list[tuple[str, str]]):
    """Create user + per-source connections with given (source, token_value) pairs."""
    claims = GoogleUserClaims(
        email=email,
        email_verified=True,
        domain="example.com",
        name=email,
        picture=None,
        sub="x",
    )
    with session_scope() as s:
        upsert_user_from_claims(s, claims)
        # Reuse store_google_connections per source by setting matching scope.
        for source, tok in sources:
            scope_for = {
                "gmail": "https://www.googleapis.com/auth/gmail.readonly",
                "drive": "https://www.googleapis.com/auth/drive.readonly",
                "calendar": "https://www.googleapis.com/auth/calendar.readonly",
            }[source]
            store_google_connections(
                session=s,
                crypto=crypto,
                user_email=email,
                token_dict={"access_token": tok, "refresh_token": None},
                granted_scopes=[scope_for],
            )


@pytest.mark.asyncio
async def test_router_fans_out_and_attributes(fresh_db):
    crypto = TokenCrypto(Fernet.generate_key().decode())
    _seed(crypto, "alice@example.com", [("gmail", "ya29.alice")])
    _seed(crypto, "bob@example.com", [("gmail", "ya29.bob")])

    router = FederatedRouter(
        session_factory=session_scope,
        token_crypto=crypto,
        connector_registry={"gmail": FakeOK()},
    )
    targets = [
        FanoutTarget(user_email="alice@example.com", source="gmail"),
        FanoutTarget(user_email="bob@example.com", source="gmail"),
    ]
    result = await router.fanout(query="refund", targets=targets)
    assert len(result.items) == 2
    users = {item.user_email for item in result.items}
    assert users == {"alice@example.com", "bob@example.com"}
    sources = {item.source for item in result.items}
    assert sources == {"gmail"}
    assert result.errors == []


@pytest.mark.asyncio
async def test_router_isolates_failures(fresh_db):
    crypto = TokenCrypto(Fernet.generate_key().decode())
    _seed(crypto, "alice@example.com", [("gmail", "ya29.alice"), ("drive", "ya29.alice2")])

    router = FederatedRouter(
        session_factory=session_scope,
        token_crypto=crypto,
        connector_registry={"gmail": FakeOK(), "drive": FakeBoom()},
    )
    targets = [
        FanoutTarget(user_email="alice@example.com", source="gmail"),
        FanoutTarget(user_email="alice@example.com", source="drive"),
    ]
    result = await router.fanout(query="x", targets=targets)
    assert len(result.items) == 1  # gmail succeeded
    assert len(result.errors) == 1  # drive failed
    assert "fire" in result.errors[0]["error"]


@pytest.mark.asyncio
async def test_selector_returns_all_active_connections(fresh_db):
    crypto = TokenCrypto(Fernet.generate_key().decode())
    _seed(crypto, "alice@example.com", [("gmail", "ya29.a")])
    _seed(crypto, "bob@example.com", [("drive", "ya29.b")])

    selector = Selector(session_factory=session_scope)
    targets = await selector.select(query="anything", asking_user="alice@example.com")
    assert len(targets) == 2
    by_user = {t.user_email: t.source for t in targets}
    assert by_user == {"alice@example.com": "gmail", "bob@example.com": "drive"}


@pytest.mark.asyncio
async def test_selector_respects_explicit_filters(fresh_db):
    crypto = TokenCrypto(Fernet.generate_key().decode())
    _seed(crypto, "alice@example.com", [("gmail", "ya29.a"), ("drive", "ya29.a2")])
    _seed(crypto, "bob@example.com", [("gmail", "ya29.b")])

    selector = Selector(session_factory=session_scope)
    targets = await selector.select(
        query="x",
        asking_user="alice@example.com",
        explicit_users=["alice@example.com"],
        explicit_sources=["gmail"],
    )
    assert len(targets) == 1
    assert targets[0].user_email == "alice@example.com"
    assert targets[0].source == "gmail"
