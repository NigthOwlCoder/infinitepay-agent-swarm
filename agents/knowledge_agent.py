from services.rag import RagService

class KnowledgeAgent:
    def __init__(self, rag=None):
        self.rag = rag or RagService.from_directory("data")

    def handle(self, request):
        hits = self.rag.search(request.message, limit=3)
        if not hits or hits[0].score <= 0:
            return {"agent": "knowledge", "answer": "Não encontrei essa informação na base da InfinitePay.", "sources": [], "needs_human": False}
        return {"agent": "knowledge", "answer": "\n\n".join(hit.text for hit in hits), "sources": [hit.source for hit in hits], "needs_human": False}
