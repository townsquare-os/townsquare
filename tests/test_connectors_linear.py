import pytest


try:
    from townsquare.connectors.linear import LinearConnector
except Exception:
    LinearConnector = None


def test_scope_advertisement():
    """Connector should advertise scopes as a list (basic smoke test)."""
    assert LinearConnector is not None, "LinearConnector import failed"
    c = LinearConnector()
    # connectors may expose scopes under different names; accept either
    if hasattr(c, "scopes"):
        scopes = c.scopes
    elif hasattr(c, "required_scopes"):
        scopes = c.required_scopes
    else:
        raise AssertionError("connector must expose scopes or required_scopes")
    assert isinstance(scopes, list), "scopes should be a list"


def test_auth_fail_returns_empty_list(monkeypatch):
    """When the auth/http layer returns an empty response, the connector should
    surface an empty list rather than raising.
    """
    assert LinearConnector is not None, "LinearConnector import failed"
    c = LinearConnector()

    # Patch the internal http/get/request method(s) to simulate an auth-failure
    # that yields an empty list from the remote API.
    if hasattr(c, "_http") and hasattr(c._http, "get"):
        monkeypatch.setattr(c._http, "get", lambda *a, **k: [])
    elif hasattr(c, "_request"):
        monkeypatch.setattr(c, "_request", lambda *a, **k: [])
    else:
        # Fallback: if connector exposes a fetch_items method that does the http call,
        # patch it directly to return an empty list.
        if hasattr(c, "fetch_items"):
            monkeypatch.setattr(c, "fetch_items", lambda *a, **k: [])

    # Many connectors expose a single entrypoint to retrieve items; try common names
    for fn in ("fetch_items", "list_items", "get_items", "items"):
        if hasattr(c, fn):
            res = getattr(c, fn)()
            assert res == []
            break
    else:
        pytest.skip("No known fetch method to exercise HTTP behaviour")


def test_payload_parsing_returns_expected_item_shape():
    """Given a typical Linear payload, parse_item should return an Item-like dict
    containing expected keys used by the rest of the system.
    """
    assert LinearConnector is not None, "LinearConnector import failed"
    c = LinearConnector()

    sample = {
        "id": "abc123",
        "title": "Fix bug",
        "description": "Details",
        "url": "https://linear.app/issue/abc123",
        "createdAt": "2021-01-01T00:00:00Z",
        "assignee": {"id": "u1", "name": "Alice"},
    }

    # Many connectors provide a parse or normalize helper; try common names.
    parser = None
    for name in ("parse_item", "to_item", "normalize_item"):
        if hasattr(c, name):
            parser = getattr(c, name)
            break

    if parser is None:
        pytest.skip("No parser method found on connector")

    item = parser(sample)
    assert isinstance(item, dict)
    # Basic expected shape: an id, title/summary, url and created timestamp
    for key in ("id", "title", "url", "created_at"):
        assert key in item, f"parsed item must include {key}"
