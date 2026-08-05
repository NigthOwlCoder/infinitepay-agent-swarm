import os
from urllib.parse import quote_plus

class WebSearchAgent:
    def handle(self, request):
        url = os.getenv("WEB_SEARCH_URL", "https://duckduckgo.com/?q=") + quote_plus(request.message)
        return {"agent": "web_search", "answer": "Essa pergunta exige informação atual. Consulte o resultado de busca indicado.", "sources": [url], "needs_human": False}
