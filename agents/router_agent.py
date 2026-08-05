from __future__ import annotations

import re
from dataclasses import asdict, dataclass

from agents.base import Agent
from agents.conversation_agent import ConversationAgent
from agents.customer_support_agent import CustomerSupportAgent
from agents.knowledge_agent import KnowledgeAgent
from agents.utility_agent import UtilityAgent
from agents.web_search_agent import WebSearchAgent
from model.chat_request import ChatRequest


@dataclass(frozen=True)
class RouteDecision:
    agent: str
    reason: str


class RouterAgent:
    """Classify user intent and delegate work to one specialist."""

    GREETING = re.compile(
        r"^\s*(oi+|ol[áa]|bom dia|boa tarde|boa noite|e a[ií])\s*[!,.?]*\s*$",
        re.IGNORECASE,
    )
    NEGATIVE_FEEDBACK = re.compile(
        r"\b(burro|idiota|inútil|inutil|péssimo|pessimo|não sabe|nao sabe)\b",
        re.IGNORECASE,
    )
    MATH = re.compile(
        r"(?:quanto\s+(?:é|e)\s+)?[-+]?\d+(?:[.,]\d+)?\s*[x×*+\-/÷^%]\s*"
        r"[-+]?\d+(?:[.,]\d+)?",
        re.IGNORECASE,
    )
    SUPPORT = re.compile(
        r"\b(minha|meu|não consigo|nao consigo|entrar|login|sign in|"
        r"transfer\w*|saldo|bloquead\w*|suporte)\b",
        re.IGNORECASE,
    )
    GENERAL = re.compile(
        r"\b(not[ií]cia|hoje|ontem|último|ultimo|palmeiras|clima|tempo|"
        r"presidente|cotação)\b",
        re.IGNORECASE,
    )

    def __init__(self, agents: dict[str, Agent] | None = None) -> None:
        self.agents = agents or {
            "conversation": ConversationAgent(),
            "utility": UtilityAgent(),
            "knowledge": KnowledgeAgent(),
            "web_search": WebSearchAgent(),
            "customer_support": CustomerSupportAgent(),
        }

    def decide(self, message: str) -> RouteDecision:
        rules = (
            (self.GREETING, "conversation", "greeting or social message"),
            (self.NEGATIVE_FEEDBACK, "conversation", "negative feedback or insult"),
            (self.MATH, "utility", "deterministic arithmetic expression"),
            (self.SUPPORT, "customer_support", "request needs user/account context"),
            (self.GENERAL, "web_search", "time-sensitive or general-purpose question"),
        )
        for pattern, agent, reason in rules:
            if pattern.search(message):
                return RouteDecision(agent, reason)
        return RouteDecision("knowledge", "InfinitePay product question")

    def route(self, request: ChatRequest) -> dict:
        decision = self.decide(request.message)
        result = self.agents[decision.agent].handle(request)
        return {**result, "routing": asdict(decision)}
