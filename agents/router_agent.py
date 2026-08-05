from __future__ import annotations
import re
from dataclasses import asdict, dataclass
from agents.customer_support_agent import CustomerSupportAgent
from agents.conversation_agent import ConversationAgent
from agents.knowledge_agent import KnowledgeAgent
from agents.web_search_agent import WebSearchAgent

@dataclass(frozen=True)
class RouteDecision:
    agent: str
    reason: str

class RouterAgent:
    GREETING = re.compile(r"^\s*(oi+|ol[áa]|bom dia|boa tarde|boa noite|e a[ií])\s*[!,.?]*\s*$", re.I)
    SUPPORT = re.compile(r"\b(minha|meu|não consigo|nao consigo|entrar|login|sign in|transfer\w*|saldo|bloquead\w*|suporte)\b", re.I)
    GENERAL = re.compile(r"\b(not[ií]cia|hoje|ontem|último|ultimo|palmeiras|clima|tempo|presidente|cotação)\b", re.I)

    def __init__(self):
        self.conversation = ConversationAgent()
        self.knowledge = KnowledgeAgent()
        self.web_search = WebSearchAgent()
        self.support = CustomerSupportAgent()

    def decide(self, message: str) -> RouteDecision:
        if self.GREETING.match(message):
            return RouteDecision("conversation", "greeting or social message")
        if self.SUPPORT.search(message):
            return RouteDecision("customer_support", "request needs user/account context")
        if self.GENERAL.search(message):
            return RouteDecision("web_search", "time-sensitive or general-purpose question")
        return RouteDecision("knowledge", "InfinitePay product question")

    def route(self, request):
        decision = self.decide(request.message)
        agent = {"conversation": self.conversation, "knowledge": self.knowledge, "web_search": self.web_search, "customer_support": self.support}[decision.agent]
        result = agent.handle(request)
        result["routing"] = asdict(decision)
        return result
