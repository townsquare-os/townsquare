"""townsquare admin CLI."""

from __future__ import annotations

import secrets

import click
from sqlalchemy import select

from townsquare import __version__


@click.group()
@click.version_option(version=__version__, prog_name="townsquare")
def main() -> None:
    """townsquare — the self-hostable company OS."""


@main.command()
def version() -> None:
    """Print the installed townsquare version."""
    click.echo(f"townsquare {__version__}")


@main.command(name="gen-secrets")
def gen_secrets() -> None:
    """Generate fresh values for FERNET_KEY and SECRET_KEY.

    Paste the output into your .env file. Both must be 32+ bytes.
    """
    from cryptography.fernet import Fernet

    click.echo(f"FERNET_KEY={Fernet.generate_key().decode()}")
    click.echo(f"SECRET_KEY={secrets.token_urlsafe(48)}")


@main.command()
@click.option("--host", default="0.0.0.0")
@click.option("--port", default=8000, type=int)
@click.option("--reload", is_flag=True, help="Enable hot reload (dev only).")
def serve(host: str, port: int, reload: bool) -> None:
    """Run the townsquare web server."""
    try:
        import uvicorn
    except ImportError as e:
        raise click.ClickException("Missing uvicorn — pip install townsquare") from e

    uvicorn.run(
        "townsquare.web.app:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )


@main.command(name="init-db")
def init_db() -> None:
    """Create database tables (idempotent — safe to run on every container start)."""
    from townsquare.db import init_db as _init_db
    from townsquare.settings import get_settings

    settings = get_settings()
    _init_db()
    click.echo(f"Initialised tables at {_redact_db_url(settings.db_url)}")


# ─── admin ─────────────────────────────────────────────────────────────


@main.group()
def admin() -> None:
    """Administrative actions: list users, promote, deactivate."""


@admin.command(name="list-users")
def list_users() -> None:
    """List every registered user."""
    from townsquare.db import session_scope
    from townsquare.db.models import User

    with session_scope() as s:
        users = s.execute(select(User).order_by(User.created_at)).scalars().all()
        if not users:
            click.echo("(no users yet — first SSO login will create one)")
            return
        click.echo(f"{'EMAIL':<40} {'ROLE':<8} {'ACTIVE':<7} {'LAST SEEN':<20}")
        for u in users:
            last = u.last_seen_at.strftime("%Y-%m-%d %H:%M") if u.last_seen_at else "-"
            click.echo(f"{u.email:<40} {u.role:<8} {str(u.is_active):<7} {last:<20}")


@admin.command()
@click.argument("email")
def promote(email: str) -> None:
    """Promote a user to admin."""
    from townsquare.db import session_scope
    from townsquare.db.models import User

    email = email.strip().lower()
    with session_scope() as s:
        user = s.get(User, email)
        if user is None:
            raise click.ClickException(
                f"User '{email}' not found. They must log in via SSO at least once first."
            )
        user.role = "admin"
        click.echo(f"Promoted {email} to admin.")


@admin.command()
@click.argument("email")
def demote(email: str) -> None:
    """Demote an admin back to member."""
    from townsquare.db import session_scope
    from townsquare.db.models import User

    email = email.strip().lower()
    with session_scope() as s:
        user = s.get(User, email)
        if user is None:
            raise click.ClickException(f"User '{email}' not found.")
        user.role = "member"
        click.echo(f"Demoted {email} to member.")


@admin.command()
@click.argument("email")
def deactivate(email: str) -> None:
    """Mark a user inactive — their data stops being federated. Use when an employee leaves."""
    from townsquare.db import session_scope
    from townsquare.db.models import Connection, User

    email = email.strip().lower()
    with session_scope() as s:
        user = s.get(User, email)
        if user is None:
            raise click.ClickException(f"User '{email}' not found.")
        user.is_active = False
        # Also deactivate every connection so the federation router skips them.
        from sqlalchemy import update

        s.execute(update(Connection).where(Connection.user_email == email).values(is_active=False))
        click.echo(
            f"Deactivated {email}. Their connections are also disabled. "
            "Run `townsquare admin forget <email>` to fully purge their data."
        )


@admin.command()
@click.argument("email")
@click.option("--yes", is_flag=True, help="Skip confirmation prompt.")
def forget(email: str, yes: bool) -> None:
    """Permanently delete all data for a user (GDPR erasure).

    Removes: User row, every Connection (with encrypted tokens), every QueryLog they originated.
    Wiki pages they created or edited are preserved (org-shared).
    """
    from sqlalchemy import delete

    from townsquare.db import session_scope
    from townsquare.db.models import Connection, QueryLog, User

    email = email.strip().lower()
    if not yes:
        click.confirm(
            f"This permanently deletes ALL data for {email}. Continue?",
            abort=True,
        )
    with session_scope() as s:
        if s.get(User, email) is None:
            raise click.ClickException(f"User '{email}' not found.")
        s.execute(delete(QueryLog).where(QueryLog.user_email == email))
        s.execute(delete(Connection).where(Connection.user_email == email))
        s.execute(delete(User).where(User.email == email))
    click.echo(f"Forgot {email}. All connections, query logs, and the user row are gone.")


def _redact_db_url(url: str) -> str:
    """Hide password in DB URL when echoing for human consumption."""
    if "://" not in url or "@" not in url:
        return url
    scheme, rest = url.split("://", 1)
    if "@" not in rest:
        return url
    creds, host = rest.split("@", 1)
    if ":" in creds:
        user, _ = creds.split(":", 1)
        return f"{scheme}://{user}:***@{host}"
    return url


@admin.command(name="stats")
def stats() -> None:
    """Print usage summary."""
    from datetime import UTC, datetime, timedelta

    from sqlalchemy import func

    from townsquare.db import session_scope
    from townsquare.db.models import Connection, QueryLog, User

    now = datetime.now(UTC)
    week_ago = now - timedelta(days=7)

    with session_scope() as s:
        # Active users
        active_users = (
            s.query(func.count(User.email)).filter(User.is_active.is_(True)).scalar() or 0
        )

        # Connections per source
        rows = (
            s.query(Connection.source, func.count(Connection.id))
            .filter(Connection.is_active.is_(True))
            .group_by(Connection.source)
            .all()
        )
        conn_map = {k: v for k, v in rows}

        # Query stats (last 7 days)
        total, avg_latency, total_cost = (
            s.query(
                func.count(QueryLog.id),
                func.avg(QueryLog.latency_ms),
                func.sum(QueryLog.cost_usd),
            )
            .filter(QueryLog.created_at >= week_ago)
            .one()
        )

        total = total or 0
        avg_latency = float(avg_latency or 0)
        total_cost = float(total_cost or 0)

        # Last query
        last = s.query(QueryLog).order_by(QueryLog.created_at.desc()).first()

        # Output
        click.echo(f"USERS               {active_users} active")
        click.echo(f"QUERIES this week   {total}")
        click.echo("")
        click.echo("CONNECTIONS")

        for source in ["gmail", "drive", "calendar", "slack", "github"]:
            count = conn_map.get(source, 0)
            click.echo(f"  {source:<16}{count} users")

        click.echo("")
        click.echo("QUERIES (last 7 days)")
        click.echo(f"  total             {total}")
        click.echo(f"  avg latency       {avg_latency / 1000:.1f}s")
        click.echo(f"  total cost USD    ${total_cost:.2f}")

        click.echo("")
        click.echo("LAST QUERY")

        if last:
            email = getattr(last, "user_email", "—")
            query = getattr(last, "query_text", "")
            click.echo(f'  {email} — "{query}"')
        else:
            click.echo("  —")


if __name__ == "__main__":
    main()
