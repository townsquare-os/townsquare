"""Central agent runner — Claude Agent SDK wired to townsquare's tools.

Stub for v0.1 scaffold. Real implementation in week 4.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AgentConfig:
    model: str = "claude-sonnet-4-6"
    max_steps: int = 8
    max_tokens: int = 50_000
    max_cost_usd: float = 0.50


class CentralAgent:
    def __init__(self, config: AgentConfig, federated_router, shared_brain) -> None:
        self.config = config
        self._router = federated_router
        self._brain = shared_brain

    async def ask(self, question: str, asking_user: str):
        raise NotImplementedError("week 4 — wire Claude Agent SDK with townsquare tools")
