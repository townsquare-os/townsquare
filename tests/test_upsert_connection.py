"""Generic per-source connection upsert (Slack / GitHub / etc.)."""

from cryptography.fernet import Fernet
from sqlalchemy import select

from townsquare.auth.crypto import TokenCrypto
from townsquare.auth.google_sso import GoogleUserClaims
from townsquare.auth.users import (
    deactivate_connection,
    get_user_token,
    upsert_connection,
    upsert_user_from_claims,
)
from townsquare.db import session_scope
from townsquare.db.models import Connection


def _seed_user(email="alice@example.com"):
    claims = GoogleUserClaims(
        email=email,
        email_verified=True,
        domain=email.split("@", 1)[1],
        name="Alice",
        picture=None,
        sub="x",
    )
    with session_scope() as s:
        upsert_user_from_claims(s, claims)


def test_upsert_connection_creates_row(fresh_db):
    _seed_user()
    crypto = TokenCrypto(Fernet.generate_key().decode())
    with session_scope() as s:
        upsert_connection(
            session=s,
            crypto=crypto,
            user_email="alice@example.com",
            source="slack",
            access_token="xoxp-real-user-token",
            granted_scopes=["search:read"],
        )

    with session_scope() as s:
        token = get_user_token(s, crypto, "alice@example.com", "slack")
    assert token == "xoxp-real-user-token"


def test_upsert_connection_updates_existing(fresh_db):
    _seed_user()
    crypto = TokenCrypto(Fernet.generate_key().decode())
    with session_scope() as s:
        upsert_connection(
            session=s,
            crypto=crypto,
            user_email="alice@example.com",
            source="github",
            access_token="ghp_old",
        )
    with session_scope() as s:
        upsert_connection(
            session=s,
            crypto=crypto,
            user_email="alice@example.com",
            source="github",
            access_token="ghp_new",
        )
        rows = (
            s.execute(
                select(Connection).where(
                    Connection.user_email == "alice@example.com",
                    Connection.source == "github",
                )
            )
            .scalars()
            .all()
        )
    assert len(rows) == 1
    with session_scope() as s:
        assert get_user_token(s, crypto, "alice@example.com", "github") == "ghp_new"


def test_deactivate_connection_flips_flag(fresh_db):
    _seed_user()
    crypto = TokenCrypto(Fernet.generate_key().decode())
    with session_scope() as s:
        upsert_connection(
            session=s,
            crypto=crypto,
            user_email="alice@example.com",
            source="slack",
            access_token="xoxp-fake",
        )
    with session_scope() as s:
        ok = deactivate_connection(s, "alice@example.com", "slack")
    assert ok is True
    with session_scope() as s:
        token = get_user_token(s, crypto, "alice@example.com", "slack")
    # get_user_token only returns active rows.
    assert token is None


def test_deactivate_missing_returns_false(fresh_db):
    _seed_user()
    with session_scope() as s:
        ok = deactivate_connection(s, "alice@example.com", "slack")
    assert ok is False
