"""User auto-provisioning + connection storage tests."""

from cryptography.fernet import Fernet

from townsquare.auth.crypto import TokenCrypto
from townsquare.auth.google_sso import GoogleUserClaims
from townsquare.auth.users import (
    get_user_token,
    store_google_connections,
    upsert_user_from_claims,
)
from townsquare.db import session_scope


def make_claims(email="alice@zingly.com", domain="zingly.com", verified=True):
    return GoogleUserClaims(
        email=email,
        email_verified=verified,
        domain=domain,
        name=email.split("@")[0].capitalize(),
        picture=None,
        sub="abc123",
    )


def test_upsert_creates_user_on_first_login(fresh_db):
    claims = make_claims()
    with session_scope() as s:
        user = upsert_user_from_claims(s, claims)
        assert user.email == "alice@zingly.com"
        assert user.domain == "zingly.com"
        assert user.role == "member"
        assert user.is_active is True


def test_upsert_updates_last_seen_on_repeat_login(fresh_db):
    claims = make_claims()
    with session_scope() as s:
        user = upsert_user_from_claims(s, claims)
        first_seen = user.last_seen_at
    import time

    time.sleep(0.01)
    with session_scope() as s:
        user = upsert_user_from_claims(s, claims)
    assert user.last_seen_at >= first_seen


def test_store_google_connections_creates_three_per_user(fresh_db):
    claims = make_claims()
    crypto = TokenCrypto(Fernet.generate_key().decode())
    granted = [
        "openid",
        "email",
        "profile",
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/drive.readonly",
        "https://www.googleapis.com/auth/calendar.readonly",
    ]
    token = {"access_token": "ya29.fake", "refresh_token": "1//refresh"}

    with session_scope() as s:
        upsert_user_from_claims(s, claims)
        conns = store_google_connections(
            session=s,
            crypto=crypto,
            user_email=claims.email,
            token_dict=token,
            granted_scopes=granted,
        )
        assert sorted(c.source for c in conns) == ["calendar", "drive", "gmail"]


def test_token_roundtrip_via_get_user_token(fresh_db):
    claims = make_claims()
    crypto = TokenCrypto(Fernet.generate_key().decode())
    granted = ["https://www.googleapis.com/auth/gmail.readonly"]
    token = {"access_token": "ya29.real-token-value", "refresh_token": None}

    with session_scope() as s:
        upsert_user_from_claims(s, claims)
        store_google_connections(
            session=s,
            crypto=crypto,
            user_email=claims.email,
            token_dict=token,
            granted_scopes=granted,
        )
    with session_scope() as s:
        recovered = get_user_token(s, crypto, claims.email, "gmail")
    assert recovered == "ya29.real-token-value"
