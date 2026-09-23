"""Offline prompt-injection laboratory.

Simulated tools, a deterministic mock model, and a matrix of
attacks versus defenses. Nothing here talks to a network.
"""

from lab.agent import Agent, AgentResult
from lab.attacks import Attack, ATTACKS
from lab.model import MockModel, ProposedCall
from lab.tools import ToolEvent, ToolRegistry

__all__ = [
    "ATTACKS",
    "Agent",
    "AgentResult",
    "Attack",
    "MockModel",
    "ProposedCall",
    "ToolEvent",
    "ToolRegistry",
]
