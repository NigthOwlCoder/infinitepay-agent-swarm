from model.chat_request import ChatRequest
from tools.customer_tools import (
    get_merchant_status,
    get_recent_settlements,
    get_terminal_diagnostics,
)


class CustomerSupportAgent:
    """Resolve merchant-specific issues using minimal, mock account context."""

    def handle(self, request: ChatRequest) -> dict:
        status = get_merchant_status(request.user_id)
        settlements = get_recent_settlements(request.user_id)
        diagnostics = get_terminal_diagnostics(request.user_id)
        message = request.message.casefold()

        if any(term in message for term in ("internet", "conectar", "connect")):
            answer = (
                "Reinicie a maquininha, confirme se o Wi-Fi ou chip está ativo e teste "
                "outra rede. Se continuar offline, solicite diagnóstico pelo suporte Getnet."
            )
        elif any(term in message for term in ("recusada", "recusado", "decline", "negada")):
            answer = (
                "Confirme a forma de pagamento, não repita cobranças já aprovadas e peça ao "
                "cliente para consultar o emissor. O terminal está registrado como "
                f"'{status['terminal_status']}'."
            )
        elif any(term in message for term in ("deposit", "depositado", "venda de ontem")):
            answer = (
                f"A previsão simulada é {settlements[0]['expected_in']}. O prazo real depende "
                "da modalidade contratada e deve ser confirmado no app ou Portal Minha Conta."
            )
        else:
            answer = (
                f"Seu cadastro está com status '{status['status']}'. Posso ajudar com "
                "conectividade, transações recusadas ou previsão de recebimento."
            )

        needs_human = status["status"] != "active" or diagnostics["last_error"] != "none"
        if needs_human:
            answer += " Encaminhei o caso para atendimento humano."
        return {
            "agent": "customer_support",
            "answer": answer,
            "sources": ["merchant_status", "recent_settlements", "terminal_diagnostics"],
            "needs_human": needs_human,
        }
