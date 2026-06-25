"""Connector registry — single source of truth for which sources are wired."""

from __future__ import annotations

from townsquare.connectors.base import Connector
from townsquare.connectors.calendar import CalendarConnector
from townsquare.connectors.drive import DriveConnector
from townsquare.connectors.github import GitHubConnector
from townsquare.connectors.gmail import GmailConnector
from townsquare.connectors.linear import LinearConnector
from townsquare.connectors.slack import SlackConnector


def default_registry() -> dict[str, Connector]:
    return {
        "gmail": GmailConnector(),
        "drive": DriveConnector(),
        "calendar": CalendarConnector(),
        "slack": SlackConnector(),
        "github": GitHubConnector(),
        "linear": LinearConnector(),
    }
