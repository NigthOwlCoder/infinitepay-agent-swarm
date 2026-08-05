from __future__ import annotations

class ConversationAgent:
    """Handles greetings and lightweight conversational messages."""

    def handle(self, request):
        message = request.message.casefold().strip()
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
