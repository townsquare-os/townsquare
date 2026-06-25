"""Per-source connection routes: Slack OAuth + GitHub PAT.

Each connection is the *user's own* — Bob's Slack token only sees what
Bob can see; Carol's GitHub PAT only sees what Carol's GitHub user
account can see. This is the federation guarantee at the source.
"""

from __future__ import annotations

import secrets

import httpx
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from townsquare.auth.crypto import TokenCrypto
from townsquare.auth.users import deactivate_connection, upsert_connection
from townsquare.db.models import User
from townsquare.web.deps import get_cached_settings, get_current_user, get_db, get_token_crypto
from townsquare.web.templating import render

router = APIRouter()


# ─── Slack OAuth ──────────────────────────────────────────────────────


@router.get("/connections/slack/connect")
async def slack_connect(request: Request, user: User = Depends(get_current_user)):
    """Start the Slack OAuth flow with user_scope (xoxp), not bot_scope."""
    settings = get_cached_settings()
    if not (settings.slack_client_id and settings.slack_client_secret):
        raise HTTPException(
            503, "Slack is not configured. Set SLACK_CLIENT_ID + SLACK_CLIENT_SECRET in .env."
        )

    state = secrets.token_urlsafe(24)
    request.session["slack_oauth_state"] = state
    redirect_uri = str(request.url_for("slack_callback"))

    user_scopes = "search:read,users:read,users:read.email"
    url = (
        "https://slack.com/oauth/v2/authorize"
        f"?client_id={settings.slack_client_id}"
        f"&user_scope={user_scopes}"
        f"&redirect_uri={redirect_uri}"
        f"&state={state}"
    )
    return RedirectResponse(url, status_code=303)


@router.get("/connections/slack/callback", name="slack_callback")
async def slack_callback(
    request: Request,
    code: str = "",
    state: str = "",
    error: str = "",
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    crypto: TokenCrypto = Depends(get_token_crypto),
):
    if error:
        raise HTTPException(400, f"slack oauth error: {error}")
    expected_state = request.session.pop("slack_oauth_state", None)
    if not state or state != expected_state:
        raise HTTPException(400, "slack state mismatch — possible CSRF")
    if not code:
        raise HTTPException(400, "slack callback missing code")

    settings = get_cached_settings()
    redirect_uri = str(request.url_for("slack_callback"))
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.post(
            "https://slack.com/api/oauth.v2.access",
            data={
                "client_id": settings.slack_client_id,
                "client_secret": settings.slack_client_secret,
                "code": code,
                "redirect_uri": redirect_uri,
            },
        )
        r.raise_for_status()
        payload = r.json()

    if not payload.get("ok"):
        raise HTTPException(400, f"slack oauth refused: {payload.get('error', 'unknown')}")

    # Pull the user-token (xoxp), not the bot-token (xoxb).
    authed_user = payload.get("authed_user") or {}
    user_token = authed_user.get("access_token")
    if not user_token or not user_token.startswith("xoxp-"):
        raise HTTPException(
            400,
            "slack returned no user-token. Check that user_scope was requested (not bot_scope).",
        )
    granted = (authed_user.get("scope") or "").split(",")

    upsert_connection(
        session=db,
        crypto=crypto,
        user_email=user.email,
        source="slack",
        access_token=user_token,
        refresh_token=None,
        granted_scopes=granted,
    )
    return RedirectResponse("/connections", status_code=303)


@router.post("/connections/slack/disconnect")
async def slack_disconnect(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    deactivate_connection(db, user.email, "slack")
    return RedirectResponse("/connections", status_code=303)


# ─── GitHub PAT (personal access token) ───────────────────────────────


@router.get("/connections/github/connect", response_class=HTMLResponse)
async def github_connect_form(
    request: Request,
    user: User = Depends(get_current_user),
):
    """Render a small form where the user pastes a fine-grained PAT.

    GitHub's classic OAuth web flow requires the user's GitHub account to
    be admin-confirmed in their org for org-private repo access — the
    fine-grained PAT route is simpler for v0.1 and gives users full
    control over which repos townsquare sees.
    """
    return render(
        request,
        "connect_github.html",
        user=user,
        workspace_domain=get_cached_settings().workspace_domain,
    )


@router.post("/connections/github/connect")
async def github_connect_save(
    request: Request,
    pat: str = Form(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    crypto: TokenCrypto = Depends(get_token_crypto),
):
    pat = pat.strip()
    if not (pat.startswith("ghp_") or pat.startswith("github_pat_")):
        raise HTTPException(
            400, "this doesn't look like a GitHub PAT (must start with ghp_ or github_pat_)"
        )

    # Verify the token works and capture the GitHub login.
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(
            "https://api.github.com/user",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {pat}",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        if r.status_code == 401:
            raise HTTPException(
                400, "GitHub rejected the PAT (401). Generate a new one and try again."
            )
        r.raise_for_status()
        gh_user = r.json()

    upsert_connection(
        session=db,
        crypto=crypto,
        user_email=user.email,
        source="github",
        access_token=pat,
        refresh_token=None,
        granted_scopes=[f"login:{gh_user.get('login', '?')}"],
    )
    return RedirectResponse("/connections", status_code=303)


@router.post("/connections/github/disconnect")
async def github_disconnect(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    deactivate_connection(db, user.email, "github")
    return RedirectResponse("/connections", status_code=303)


# ------ Linear Connector (OAuth) ------ #
@router.get("/connections/linear/connect")
async def linear_connect(request: Request, user: User = Depends(get_current_user)):
    """Start the Linear OAuth flow."""
    settings = get_cached_settings()
    if not (settings.linear_client_id and settings.linear_client_secret):
        raise HTTPException(
            503, "Linear is not configured. Set LINEAR_CLIENT_ID + LINEAR_CLIENT_SECRET in .env."
        )

    state = secrets.token_urlsafe(24)
    request.session["linear_oauth_state"] = state
    redirect_uri = str(request.url_for("linear_callback"))

    url = (
        "https://linear.app/oauth/authorize"
        f"?client_id={settings.linear_client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&state={state}"
        f"&scope=read"
        f"&response_type=code"
    )
    return RedirectResponse(url, status_code=303)


@router.get("/connections/linear/callback", name="linear_callback")
async def linear_callback(
    request: Request,
    code: str = "",
    state: str = "",
    error: str = "",
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    crypto: TokenCrypto = Depends(get_token_crypto),
):
    if error:
        raise HTTPException(400, f"linear oauth error: {error}")
    expected_state = request.session.pop("linear_oauth_state", None)
    if not state or state != expected_state:
        raise HTTPException(400, "linear state mismatch — possible CSRF")
    if not code:
        raise HTTPException(400, "linear callback missing code")

    settings = get_cached_settings()
    redirect_uri = str(request.url_for("linear_callback"))
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.post(
            "https://api.linear.app/oauth/token",
            data={
                "client_id": settings.linear_client_id,
                "client_secret": settings.linear_client_secret,
                "code": code,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        r.raise_for_status()
        payload = r.json()

    access_token = payload.get("access_token")
    if not access_token:
        raise HTTPException(400, "linear returned no access token.")

    upsert_connection(
        session=db,
        crypto=crypto,
        user_email=user.email,
        source="linear",
        access_token=access_token,
        refresh_token=None,
        granted_scopes=["read"],
    )
    return RedirectResponse("/connections", status_code=303)


@router.post("/connections/linear/disconnect")
async def linear_disconnect(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    deactivate_connection(db, user.email, "linear")
    return RedirectResponse("/connections", status_code=303)
