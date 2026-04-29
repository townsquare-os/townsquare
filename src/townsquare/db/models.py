"""SQLAlchemy 2.0 typed models — schema for v0.1."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), primary_key=True)
    domain: Mapped[str] = mapped_column(String(255), index=True)
    name: Mapped[str | None] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(32), default="member")
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    last_seen_at: Mapped[datetime | None]

    connections: Mapped[list[Connection]] = relationship(back_populates="user")


class Connection(Base):
    __tablename__ = "connections"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_email: Mapped[str] = mapped_column(ForeignKey("users.email"), index=True)
    source: Mapped[str] = mapped_column(String(64), index=True)
    oauth_token_encrypted: Mapped[bytes]
    refresh_token_encrypted: Mapped[bytes | None]
    granted_scopes: Mapped[list[str]] = mapped_column(JSON, default=list)
    connected_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    last_refreshed_at: Mapped[datetime | None]
    is_active: Mapped[bool] = mapped_column(default=True)

    user: Mapped[User] = relationship(back_populates="connections")


class QueryLog(Base):
    __tablename__ = "query_log"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_email: Mapped[str] = mapped_column(ForeignKey("users.email"), index=True)
    query_text: Mapped[str] = mapped_column(Text)
    selected_users: Mapped[list[str]] = mapped_column(JSON, default=list)
    selected_sources: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    answer: Mapped[str | None] = mapped_column(Text)
    latency_ms: Mapped[float | None]
    tokens_used: Mapped[int | None]
    cost_usd: Mapped[float | None]
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, index=True)


class WikiPage(Base):
    __tablename__ = "wiki_pages"

    slug: Mapped[str] = mapped_column(String(255), primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    body_markdown: Mapped[str] = mapped_column(Text, default="")
    created_by: Mapped[str | None] = mapped_column(ForeignKey("users.email"))
    last_edited_by: Mapped[str | None] = mapped_column(ForeignKey("users.email"))
    last_edited_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    version: Mapped[int] = mapped_column(default=1)


class CrmDeal(Base):
    __tablename__ = "crm_deals"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255))
    stage: Mapped[str] = mapped_column(String(64), default="open")
    value_usd: Mapped[float | None]
    owner_email: Mapped[str | None] = mapped_column(ForeignKey("users.email"))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class CrmContact(Base):
    __tablename__ = "crm_contacts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(255), index=True)
    company: Mapped[str | None] = mapped_column(String(255))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class CrmAccount(Base):
    __tablename__ = "crm_accounts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255))
    domain: Mapped[str | None] = mapped_column(String(255), index=True)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
