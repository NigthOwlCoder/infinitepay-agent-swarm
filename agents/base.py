from typing import Protocol

from model.chat_request import ChatRequest


class Agent(Protocol):
    """Contract implemented by every specialist in the swarm."""

    def handle(self, request: ChatRequest) -> dict:
        """Process one validated request and return a serializable response."""
