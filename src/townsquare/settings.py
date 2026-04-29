"""Pydantic settings driven by environment variables."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    host: str = "0.0.0.0"
    port: int = 8000
    runtime_env: str = Field("dev", description="dev | staging | prod")
    secret_key: str = Field("change-me-32-bytes-or-more-do-not-use-in-prod")
    fernet_key: str = Field("", description="Base64 32-byte Fernet key for OAuth tokens at rest.")

    db_url: str = Field("postgresql+psycopg://townsquare:townsquare@localhost:5432/townsquare")

    google_client_id: str = ""
    google_client_secret: str = ""
    workspace_domain: str = Field(
        "", description="e.g. 'example.com' — restricts SSO to this domain"
    )
    google_redirect_uri: str = "http://localhost:8000/auth/google/callback"

    llm_provider: str = "anthropic"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    google_oauth_scopes: list[str] = [
        "openid",
        "email",
        "profile",
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/drive.readonly",
        "https://www.googleapis.com/auth/calendar.readonly",
    ]

    per_user_query_budget_usd_daily: float = 5.0
    per_query_token_cap: int = 50_000

    log_level: str = "INFO"
    enable_audit_log: bool = True


def get_settings() -> Settings:
    return Settings()
