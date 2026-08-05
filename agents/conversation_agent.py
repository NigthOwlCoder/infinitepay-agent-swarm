from __future__ import annotations

from model.chat_request import ChatRequest


class ConversationAgent:
    """Handles greetings and lightweight conversational messages."""

    def handle(self, request: ChatRequest) -> dict:
        message = request.message.casefold().strip()
        negative_terms = ("burro", "idiota", "inútil", "inutil", "péssimo", "pessimo")
        if any(term in message for term in negative_terms):
            return {
                "agent": "conversation",
                "answer": "Desculpe. Vou procurar aprender e melhorar. Como posso te ajudar?",
                "sources": [],
                "needs_human": False,
            }
        if "bom dia" in message:
            greeting = "Bom dia!"
        elif "boa tarde" in message:
            greeting = "Boa tarde!"
        elif "boa noite" in message:
            greeting = "Boa noite!"
        else:
            greeting = "Olá!"

        return {
            "agent": "conversation",
            "answer": (
                f"{greeting} Posso te ajudar? Você pode me perguntar sobre a Maquininha "
                "Smart, taxas, Pix, InfiniteTap ou suporte à sua conta."
            ),
            "sources": [],
            "needs_human": False,
        }
