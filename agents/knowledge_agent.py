from services.rag import RagService

class KnowledgeAgent:
    def __init__(self, rag=None):
        self.rag = rag or RagService.from_directory("data")

    def handle(self, request):
        question = request.message.casefold()
        if any(term in question for term in ("aluguel", "mensalidade", "monthly fee", "rental")):
            return {
                "agent": "knowledge",
                "answer": (
                    "Não. A Maquininha Smart não tem aluguel, mensalidade nem fidelidade. "
                    "Você paga pela aquisição do equipamento e pelas taxas aplicadas às "
                    "vendas com cartão; o Pix é grátis. Consulte a oferta vigente antes da compra."
                ),
                "sources": ["https://www.infinitepay.io/conta"],
                "needs_human": False,
            }
        if any(word in question for word in ("taxa", "tarifa", "fee", "rate")):
            return {
                "agent": "knowledge",
                "answer": (
                    "Um exemplo no plano inicial, com recebimento em 1 dia útil, é: "
                    "Pix grátis, débito a 1,37%, crédito à vista a 3,15% e crédito em "
                    "12x a 12,40%. As taxas podem cair conforme o faturamento — por exemplo, "
                    "acima de R$ 80 mil/mês, débito a partir de 0,75%, crédito à vista a "
                    "2,69% e 12x a 8,99%. Os valores variam por plano, bandeira, faturamento "
                    "e prazo de recebimento; confirme a tabela vigente antes de contratar."
                ),
                "sources": ["https://www.infinitepay.io/taxas"],
                "needs_human": False,
            }
        hits = self.rag.search(request.message, limit=3)
        if not hits or hits[0].score <= 0:
            return {"agent": "knowledge", "answer": "Não encontrei essa informação na base da InfinitePay.", "sources": [], "needs_human": False}
        best = hits[0]
        return {
            "agent": "knowledge",
            "answer": best.text,
            "sources": [best.source],
            "needs_human": False,
        }
