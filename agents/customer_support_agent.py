from model.chat_request import ChatRequest
from tools.customer_tools import get_account_status, get_recent_activity


class CustomerSupportAgent:
    def handle(self, request: ChatRequest) -> dict:
        status = get_account_status(request.user_id)
        activity = get_recent_activity(request.user_id)
        message = request.message.casefold()
        if any(term in message for term in ("entrar", "login", "sign in")):
            answer = (
                "Confirme e-mail/telefone, redefina a senha e atualize o app. "
                "Nunca compartilhe senha ou código de verificação."
            )
        elif "transfer" in message:
            answer = (
                "Verifique saldo, destinatário e limites. "
                f"Status: {status['status']}; último evento: {activity[0]['description']}."
            )
        elif "pix" in message and any(
            term in message for term in ("pedir", "solicitar", "receber", "quero")
        ):
            answer = (
                "Você pode solicitar pagamentos na área logada se tiver parcelas a receber. "
                "O Pix permite receber o pagamento de forma instantânea, 24 horas por dia. "
                "A disponibilidade da solicitação depende das parcelas elegíveis exibidas "
                "na sua conta."
            )
        else:
            answer = (
                f"Sua conta está com status '{status['status']}'. "
                "Posso ajudar com acesso ou transferências."
            )
        needs_human = status["status"] != "active"
        if needs_human:
            answer += " Encaminhei o caso para atendimento humano."
        return {
            "agent": "customer_support",
            "answer": answer,
            "sources": ["customer_account", "recent_activity"],
            "needs_human": needs_human,
        }
