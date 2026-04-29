"""Federation layer — routes a query across users' per-source connectors.

Privacy is enforced at the source: each per-target query runs under
that user's encrypted tokens; the central agent never holds another
user's plaintext token.
"""

from townsquare.federation.router import FanoutResult, FanoutTarget, FederatedRouter

__all__ = ["FederatedRouter", "FanoutTarget", "FanoutResult"]
