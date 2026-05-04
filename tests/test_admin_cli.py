"""Admin CLI tests using Click's CliRunner — no docker/no live DB needed."""

from click.testing import CliRunner

from townsquare.auth.google_sso import GoogleUserClaims
from townsquare.auth.users import upsert_user_from_claims
from townsquare.cli import main
from townsquare.db import session_scope
from townsquare.db.models import User
from townsquare.db.models import Connection, QueryLog
from datetime import datetime


def _make(email="alice@example.com"):
    return GoogleUserClaims(
        email=email,
        email_verified=True,
        domain=email.split("@", 1)[1],
        name=email.split("@")[0].capitalize(),
        picture=None,
        sub="x",
    )


def _seed(email):
    with session_scope() as s:
        upsert_user_from_claims(s, _make(email))


def test_list_users_empty(fresh_db):
    runner = CliRunner()
    out = runner.invoke(main, ["admin", "list-users"])
    assert out.exit_code == 0
    assert "no users yet" in out.output


def test_list_users_shows_seeded(fresh_db):
    _seed("alice@example.com")
    _seed("bob@example.com")
    runner = CliRunner()
    out = runner.invoke(main, ["admin", "list-users"])
    assert out.exit_code == 0
    assert "alice@example.com" in out.output
    assert "bob@example.com" in out.output


def test_promote_then_demote(fresh_db):
    _seed("alice@example.com")
    runner = CliRunner()

    p = runner.invoke(main, ["admin", "promote", "alice@example.com"])
    assert p.exit_code == 0, p.output
    with session_scope() as s:
        assert s.get(User, "alice@example.com").role == "admin"

    d = runner.invoke(main, ["admin", "demote", "alice@example.com"])
    assert d.exit_code == 0, d.output
    with session_scope() as s:
        assert s.get(User, "alice@example.com").role == "member"


def test_promote_unknown_user_errors(fresh_db):
    runner = CliRunner()
    out = runner.invoke(main, ["admin", "promote", "nobody@example.com"])
    assert out.exit_code != 0
    assert "not found" in out.output


def test_deactivate_marks_user_inactive(fresh_db):
    _seed("alice@example.com")
    runner = CliRunner()
    out = runner.invoke(main, ["admin", "deactivate", "alice@example.com"])
    assert out.exit_code == 0, out.output
    with session_scope() as s:
        assert s.get(User, "alice@example.com").is_active is False


def test_forget_removes_user(fresh_db):
    _seed("alice@example.com")
    runner = CliRunner()
    out = runner.invoke(main, ["admin", "forget", "alice@example.com", "--yes"])
    assert out.exit_code == 0, out.output
    with session_scope() as s:
        assert s.get(User, "alice@example.com") is None


def test_gen_secrets_outputs_two_lines():
    runner = CliRunner()
    out = runner.invoke(main, ["gen-secrets"])
    assert out.exit_code == 0
    assert "FERNET_KEY=" in out.output
    assert "SECRET_KEY=" in out.output


def test_version_command():
    runner = CliRunner()
    out = runner.invoke(main, ["version"])
    assert out.exit_code == 0
    assert "townsquare 0.1.0" in out.output

def test_admin_stats_empty(fresh_db):
    runner = CliRunner()
    out = runner.invoke(main, ["admin", "stats"])

    assert out.exit_code == 0
    assert "USERS" in out.output
    assert "0 active" in out.output
    assert "total             0" in out.output

def test_admin_stats_populated(fresh_db):
    _seed("alice@example.com")

    with session_scope() as s:
        user = s.get(User, "alice@example.com")

        # Add connection
        s.add(Connection(
            user_email=user.email,
            source="gmail",
            oauth_token_encrypted=b"dummy",   # ✅ REQUIRED
            refresh_token_encrypted=None,
            is_active=True
        ))

        # Add query log
        s.add(QueryLog(
            user_email=user.email,
            query_text="who's working on auth?",
            latency_ms=3.5,
            cost_usd=0.02,
            created_at=datetime.utcnow()
        ))

    runner = CliRunner()
    out = runner.invoke(main, ["admin", "stats"])

    assert out.exit_code == 0
    assert "1 active" in out.output
    assert "gmail" in out.output
    assert "1 users" in out.output
    assert "avg latency" in out.output
    assert "who's working on auth?" in out.output