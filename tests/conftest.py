"""Pytest fixtures — sqlite test DB, FERNET_KEY, FastAPI dep overrides."""

from __future__ import annotations

import os
import tempfile

import pytest
from cryptography.fernet import Fernet


def _set_env_for_tests() -> None:
    """Set required env vars before any townsquare module is imported."""
    if "FERNET_KEY" not in os.environ:
        os.environ["FERNET_KEY"] = Fernet.generate_key().decode()
    if "WORKSPACE_DOMAIN" not in os.environ:
        os.environ["WORKSPACE_DOMAIN"] = "test.com"
    if "GOOGLE_CLIENT_ID" not in os.environ:
        os.environ["GOOGLE_CLIENT_ID"] = "fake-client-id"
    if "GOOGLE_CLIENT_SECRET" not in os.environ:
        os.environ["GOOGLE_CLIENT_SECRET"] = "fake-client-secret"
    if "SECRET_KEY" not in os.environ:
        os.environ["SECRET_KEY"] = "test-secret-32-bytes-or-more-zzzzzzz"

    # SQLite test DB.
    if "DB_URL" not in os.environ:
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        os.environ["DB_URL"] = f"sqlite:///{tmp.name}"


_set_env_for_tests()


@pytest.fixture(autouse=True)
def reset_module_caches():
    """Clear the lru_cache caches between tests so settings/SSO/crypto reload."""
    # Drop any cached settings/SSO/crypto so each test sees current env.
    from townsquare.web import deps

    for fn in (
        deps.get_cached_settings,
        deps.get_token_crypto,
        deps.get_sso,
    ):
        fn.cache_clear()
    yield


@pytest.fixture
def fresh_db():
    """Drop + recreate all tables before each test."""
    from townsquare.db import reset_db

    reset_db()
    yield
