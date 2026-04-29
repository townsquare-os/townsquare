"""Test the wiki agent tools (read_wiki, write_wiki) without an LLM call."""

from townsquare.agent.tools import handle_read_wiki, handle_write_wiki
from townsquare.db import session_scope


def test_write_then_read(fresh_db):
    write = handle_write_wiki(
        args={
            "slug": "q3-launch",
            "title": "Q3 Launch",
            "body_markdown": "# Plan\n\n- step 1\n- step 2",
        },
        session_factory=session_scope,
        actor_email="alice@example.com",
    )
    assert write["ok"] is True
    assert write["created"] is True
    assert write["version"] == 1

    read = handle_read_wiki(args={"slug": "q3-launch"}, session_factory=session_scope)
    assert read["found"] is True
    assert read["title"] == "Q3 Launch"
    assert "step 1" in read["body_markdown"]
    assert read["version"] == 1


def test_write_increments_version(fresh_db):
    handle_write_wiki(
        args={"slug": "p", "title": "T", "body_markdown": "v1"},
        session_factory=session_scope,
        actor_email="a@z.com",
    )
    out = handle_write_wiki(
        args={"slug": "p", "title": "T", "body_markdown": "v2"},
        session_factory=session_scope,
        actor_email="b@z.com",
    )
    assert out["version"] == 2


def test_read_missing_returns_not_found(fresh_db):
    r = handle_read_wiki(args={"slug": "does-not-exist"}, session_factory=session_scope)
    assert r["found"] is False
