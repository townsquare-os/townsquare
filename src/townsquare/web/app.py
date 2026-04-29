"""FastAPI app factory."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from townsquare import __version__


def create_app() -> FastAPI:
    app = FastAPI(
        title="townsquare",
        description="The self-hostable open-source company OS",
        version=__version__,
    )

    @app.get("/", response_class=HTMLResponse)
    async def index() -> str:
        return f"""<!DOCTYPE html>
<html><head>
<title>townsquare</title>
<meta charset="utf-8">
<style>
  body {{ font-family: ui-sans-serif, system-ui, sans-serif; max-width: 720px; margin: 80px auto; padding: 0 24px; color: #1a1a1a; }}
  h1 {{ font-size: 48px; margin-bottom: 8px; letter-spacing: -1px; }}
  p {{ color: #555; line-height: 1.6; }}
  code {{ background: #f3f4f6; padding: 2px 6px; border-radius: 4px; font-size: 0.9em; }}
  .v {{ color: #888; font-size: 14px; }}
</style>
</head><body>
<h1>townsquare</h1>
<p class="v">v{__version__} · alpha · scaffold</p>
<p>The self-hostable company OS. Google Workspace SSO. Per-user data connections.
   Privacy-preserving federation across users.</p>
<p>This is the v0.1 scaffold. Auth and connectors land in weeks 1–3.
   See <code>ROADMAP.md</code>.</p>
</body></html>"""

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok", "version": __version__}

    return app


app = create_app()
