"""townsquare admin CLI."""

from __future__ import annotations

import secrets

import click

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
    """Generate fresh values for FERNET_KEY and SECRET_KEY."""
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
    """Create database tables (alpha — replace with Alembic migrations)."""
    from sqlalchemy import create_engine

    from townsquare.db.models import Base
    from townsquare.settings import get_settings

    settings = get_settings()
    engine = create_engine(settings.db_url)
    Base.metadata.create_all(engine)
    click.echo(f"Initialised tables at {settings.db_url}")


if __name__ == "__main__":
    main()
