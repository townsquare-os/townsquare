"""Scaffold-level smoke tests."""

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

from townsquare.auth.crypto import TokenCrypto
from townsquare.auth.google_sso import GoogleWorkspaceSSO
from townsquare.web.app import app


def test_package_imports():
    import townsquare

    assert townsquare.__version__ == "0.1.0"


def test_settings_load_with_env(monkeypatch):
    monkeypatch.setenv("WORKSPACE_DOMAIN", "test.com")
    monkeypatch.setenv("FERNET_KEY", Fernet.generate_key().decode())
    from townsquare.settings import get_settings

    s = get_settings()
    assert s.port == 8000
    assert s.runtime_env in ("dev", "staging", "prod")
    assert s.workspace_domain == "test.com"


def test_app_boots_and_serves_index():
    client = TestClient(app)
    r = client.get("/")
    assert r.status_code == 200
    assert "townsquare" in r.text


def test_healthz():
    client = TestClient(app)
    r = client.get("/healthz")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["version"] == "0.1.0"


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
