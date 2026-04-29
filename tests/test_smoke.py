"""Scaffold-level smoke tests."""

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

from townsquare.auth.crypto import TokenCrypto
from townsquare.auth.google_sso import GoogleWorkspaceSSO


def test_package_imports():
    import townsquare

    assert townsquare.__version__ == "0.1.0"


def test_settings_load_with_env():
    from townsquare.settings import get_settings

    s = get_settings()
    assert s.port == 8000
    assert s.runtime_env in ("dev", "staging", "prod")
    assert s.workspace_domain == "test.com"


def test_app_boots_and_serves_index(fresh_db):
    from townsquare.web.app import create_app

    app = create_app()
    client = TestClient(app)
    r = client.get("/")
    assert r.status_code == 200
    assert "townsquare" in r.text


def test_healthz(fresh_db):
    from townsquare.web.app import create_app

    app = create_app()
    client = TestClient(app)
    r = client.get("/healthz")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["version"] == "0.1.0"


def test_unauthenticated_root_shows_login(fresh_db):
    from townsquare.web.app import create_app

    app = create_app()
    client = TestClient(app)
    r = client.get("/")
    assert r.status_code == 200
    assert "Sign in with Google" in r.text


def test_protected_route_redirects_when_unauthenticated(fresh_db):
    from townsquare.web.app import create_app

    app = create_app()
    client = TestClient(app)
    r = client.get("/connections", follow_redirects=False)
    # Either 401 with Location header, or redirect — accept either.
    assert r.status_code in (302, 303, 307, 401)


def test_token_crypto_roundtrip():
    key = Fernet.generate_key().decode()
    crypto = TokenCrypto(key)
    plaintext = "ya29.a0AfH6S-fake-google-token"
    ct = crypto.encrypt(plaintext)
    assert ct != plaintext.encode()
    assert crypto.decrypt(ct) == plaintext


def test_token_crypto_rejects_empty_key():
    with pytest.raises(ValueError):
        TokenCrypto("")


def test_google_sso_requires_workspace_domain():
    with pytest.raises(ValueError):
        GoogleWorkspaceSSO(client_id="x", client_secret="y", workspace_domain="")


def test_google_sso_verify_domain_rejects_mismatch():
    from townsquare.auth.google_sso import (
        DomainRestrictionError,
        GoogleUserClaims,
    )

    sso = GoogleWorkspaceSSO(client_id="x", client_secret="y", workspace_domain="zingly.com")
    bad = GoogleUserClaims(
        email="alice@gmail.com",
        email_verified=True,
        domain="gmail.com",
        name="Alice",
        picture=None,
        sub="1",
    )
    with pytest.raises(DomainRestrictionError):
        sso.verify_domain(bad)


def test_google_sso_verify_domain_rejects_unverified_email():
    from townsquare.auth.google_sso import (
        DomainRestrictionError,
        GoogleUserClaims,
    )

    sso = GoogleWorkspaceSSO(client_id="x", client_secret="y", workspace_domain="zingly.com")
    unverified = GoogleUserClaims(
        email="alice@zingly.com",
        email_verified=False,
        domain="zingly.com",
        name="Alice",
        picture=None,
        sub="1",
    )
    with pytest.raises(DomainRestrictionError):
        sso.verify_domain(unverified)


def test_google_sso_verify_domain_accepts_match():
    from townsquare.auth.google_sso import GoogleUserClaims

    sso = GoogleWorkspaceSSO(client_id="x", client_secret="y", workspace_domain="zingly.com")
    good = GoogleUserClaims(
        email="alice@zingly.com",
        email_verified=True,
        domain="zingly.com",
        name="Alice",
        picture=None,
        sub="1",
    )
    sso.verify_domain(good)  # no raise
