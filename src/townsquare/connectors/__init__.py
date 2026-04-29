"""Per-source connectors. Each implements the Connector protocol.

v0.1 ships: gmail, drive, calendar.
v0.2 adds:  slack, notion, github.
"""

from townsquare.connectors.base import Connector, Item

__all__ = ["Connector", "Item"]
