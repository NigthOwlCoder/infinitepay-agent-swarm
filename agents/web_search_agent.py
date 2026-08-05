import os
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import quote_plus
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from model.chat_request import ChatRequest


class WebSearchAgent:
    """Handle time-sensitive questions without fabricating current facts."""

    DATE_PATTERN = re.compile(
        r"(que|qual)\s+(dia|data).*hoje|dia de hoje|today'?s? date|what day is it"
    )

    def handle(self, request: ChatRequest) -> dict:
        question = request.message.casefold()
        if self.DATE_PATTERN.search(question):
            try:
                sao_paulo = ZoneInfo("America/Sao_Paulo")
            except ZoneInfoNotFoundError:
                sao_paulo = timezone(timedelta(hours=-3), name="America/Sao_Paulo")
            now = datetime.now(sao_paulo)
            weekdays = (
                "segunda-feira", "terça-feira", "quarta-feira", "quinta-feira",
                "sexta-feira", "sábado", "domingo",
            )
            months = (
                "janeiro", "fevereiro", "março", "abril", "maio", "junho",
                "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
            )
            answer = (
                f"Hoje é {weekdays[now.weekday()]}, {now.day} de "
                f"{months[now.month - 1]} de {now.year}."
            )
            return {
                "agent": "web_search",
                "answer": answer,
                "sources": ["Relógio do servidor · fuso America/Sao_Paulo"],
                "needs_human": False,
            }
        search_url = os.getenv("WEB_SEARCH_URL", "https://duckduckgo.com/?q=")
        url = search_url + quote_plus(request.message)
        return {
            "agent": "web_search",
            "answer": "Essa pergunta exige informação atual. Consulte a busca indicada.",
            "sources": [url],
            "needs_human": False,
        }
