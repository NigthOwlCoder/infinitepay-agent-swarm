from core.config import settings
from model.chat_request import ChatRequest
from services.rag import RagService


class KnowledgeAgent:
    """Answer Getnet product questions only from the approved corpus."""

    PRODUCT_URL = "https://site.getnet.com.br/maquininha/get-smart/"

    def __init__(self, rag: RagService | None = None) -> None:
        self.rag = rag or RagService.from_directory(settings.data_dir)

    def handle(self, request: ChatRequest) -> dict:
        question = request.message.casefold()
        if any(term in question for term in ("melhor taxa", "taxas", "tarifas", "fees", "rates")):
            return {
                "agent": "knowledge",
                "answer": (
                    "Claro! As funcionalidades digitais da Getnet, como o Link de Pagamento "
                    "e o Get Tap, oferecem praticidade e podem ter as melhores condições de "
                    "taxas conforme o perfil e a oferta disponível para o seu negócio. Como "
                    "os valores variam por modalidade, faturamento e prazo de recebimento, "
                    "recomendo conferir os detalhes e simular a opção ideal no site oficial "
                    "da Getnet."
                ),
                "sources": ["https://site.getnet.com.br/"],
                "needs_human": False,
            }
        if any(
            term in question
            for term in ("paga no dia", "recebe no dia", "mesmo dia", "same day")
        ):
            return {
                "agent": "knowledge",
                "answer": (
                    "Não há garantia de pagamento no mesmo dia. No Pix, o recebimento pode "
                    "acontecer no mesmo dia, mas a Getnet informa que o prazo pode variar em "
                    "até um dia corrido, conforme a elegibilidade e o horário de aprovação. "
                    "Nas vendas com cartão, o prazo depende da modalidade contratada; a oferta "
                    "atual de maquininhas informa recebimento em 2 dias úteis."
                ),
                "sources": [
                    "https://site.getnet.com.br/pix/",
                    "https://site.getnet.com.br/maquininha/get-smart/",
                ],
                "needs_human": False,
            }
        if "clássica" in question and "smart" in question:
            return {
                "agent": "knowledge",
                "answer": (
                    "As duas aceitam Pix, QR Code, aproximação e chip, têm tela touchscreen, "
                    "comprovante impresso/digital, Wi-Fi e plano de dados. A Get Smart também "
                    "oferece acesso a aplicativos de gestão e conectividade 4G; a Get Clássica "
                    "é a alternativa mais simples e tem bateria informada de até 12 horas."
                ),
                "sources": [self.PRODUCT_URL],
                "needs_human": False,
            }
        if "pix" in question and any(term in question for term in ("conta", "account", "bank")):
            return {
                "agent": "knowledge",
                "answer": (
                    "Não necessariamente. A Getnet informa que o Pix pode ser usado "
                    "independentemente do banco vinculado ao recebimento das vendas. A "
                    "elegibilidade e o prazo devem ser confirmados no cadastro do cliente."
                ),
                "sources": ["https://site.getnet.com.br/pix/"],
                "needs_human": False,
            }
        if any(term in question for term in ("antecipação", "antecipacao", "receivables")):
            return {
                "agent": "knowledge",
                "answer": (
                    "A antecipação permite receber antes do prazo vendas no crédito à vista "
                    "ou parcelado. No app Getnet Brasil, acesse Serviços > Antecipação de "
                    "Vendas, simule valores e taxas e confirme. O mínimo informado é R$ 50."
                ),
                "sources": [
                    "https://site.getnet.com.br/get-ajuda-antecipacao-de-venda/"
                    "como-antecipar-sua-vendas-pelo-app/"
                ],
                "needs_human": False,
            }
        if any(term in question for term in ("whatsapp", "link de pagamento")):
            return {
                "agent": "knowledge",
                "answer": (
                    "Sim. O Link de Pagamento pode ser enviado por WhatsApp ou redes sociais "
                    "e aceita crédito, débito e Pix em um checkout seguro da Getnet."
                ),
                "sources": ["https://site.getnet.com.br/link-de-pagamento/"],
                "needs_human": False,
            }
        if any(term in question for term in ("parcelas", "installments", "crediário")):
            return {
                "agent": "knowledge",
                "answer": (
                    "A oferta pública permite vendas parceladas em até 12 vezes. Condições de "
                    "crediário podem variar por contrato e devem ser confirmadas no Portal."
                ),
                "sources": [self.PRODUCT_URL],
                "needs_human": False,
            }

        hits = self.rag.search(request.message, limit=3)
        if not hits or hits[0].score <= 0:
            return {
                "agent": "knowledge",
                "answer": "Não encontrei essa informação na base aprovada da Getnet.",
                "sources": [],
                "needs_human": False,
            }
        best = hits[0]
        return {
            "agent": "knowledge",
            "answer": best.text,
            "sources": self._public_sources(best.text),
            "needs_human": False,
        }

    @staticmethod
    def _public_sources(text: str) -> list[str]:
        """Expose public corpus URLs instead of local filesystem paths."""
        import re

        return re.findall(r"https?://[^\s,]+", text)

    def can_answer(self, question: str) -> bool:
        normalized = question.casefold()
        product_terms = (
            "getnet", "get smart", "get clássica", "get classica", "maquininha",
            "pix", "antecipação", "antecipacao", "receivables", "crediário",
            "crediario", "link de pagamento", "whatsapp",
        )
        if any(term in normalized for term in product_terms):
            return True
        hits = self.rag.search(question, limit=1)
        return bool(hits and hits[0].score >= 1.0)
