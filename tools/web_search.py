from dataclasses import dataclass
from html.parser import HTMLParser
from urllib.parse import parse_qs, unquote, urlparse

import httpx


@dataclass(frozen=True)
class WebResult:
    answer: str
    source: str


class _DuckDuckGoParser(HTMLParser):
    """Extract the first organic result without depending on a scraping library."""

    def __init__(self) -> None:
        super().__init__()
        self.capture: str | None = None
        self.link = ""
        self.title: list[str] = []
        self.snippet: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        classes = (attributes.get("class") or "").split()
        if tag == "a" and "result__a" in classes and not self.link:
            self.capture = "title"
            self.link = attributes.get("href") or ""
        elif "result__snippet" in classes and not self.snippet:
            self.capture = "snippet"

    def handle_endtag(self, tag: str) -> None:
        if tag in {"a", "div", "span"}:
            self.capture = None

    def handle_data(self, data: str) -> None:
        if self.capture == "title":
            self.title.append(data.strip())
        elif self.capture == "snippet":
            self.snippet.append(data.strip())


class WebSearchTool:
    """Search DuckDuckGo's public instant-answer index with a bounded timeout."""

    endpoint = "https://api.duckduckgo.com/"

    def search(self, query: str) -> WebResult | None:
        params = {
            "q": query,
            "format": "json",
            "no_html": "1",
            "no_redirect": "1",
            "skip_disambig": "1",
        }
        try:
            response = httpx.get(self.endpoint, params=params, timeout=8.0)
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError):
            return None

        answer = payload.get("Answer") or payload.get("AbstractText")
        source = payload.get("AbstractURL")
        if answer and source:
            return WebResult(answer=answer, source=source)

        for topic in payload.get("RelatedTopics", []):
            if isinstance(topic, dict) and topic.get("Text") and topic.get("FirstURL"):
                return WebResult(answer=topic["Text"], source=topic["FirstURL"])
        return self._search_html(query) or self._search_wikipedia(query)

    def _search_html(self, query: str) -> WebResult | None:
        try:
            response = httpx.get(
                "https://html.duckduckgo.com/html/",
                params={"q": query},
                headers={"User-Agent": "Mozilla/5.0 AgentSwarm/1.1"},
                timeout=8.0,
                follow_redirects=True,
            )
            response.raise_for_status()
        except httpx.HTTPError:
            return None

        parser = _DuckDuckGoParser()
        parser.feed(response.text)
        text = " ".join(part for part in parser.snippet if part).strip()
        title = " ".join(part for part in parser.title if part).strip()
        source = self._direct_url(parser.link)
        if not text or not source:
            return None
        return WebResult(answer=f"{title}: {text}" if title else text, source=source)

    def _search_wikipedia(self, query: str) -> WebResult | None:
        params = {
            "action": "query",
            "generator": "search",
            "gsrsearch": query,
            "gsrlimit": "1",
            "prop": "extracts|info",
            "exintro": "1",
            "explaintext": "1",
            "inprop": "url",
            "format": "json",
        }
        try:
            response = httpx.get(
                "https://pt.wikipedia.org/w/api.php",
                params=params,
                headers={"User-Agent": "AgentSwarm/1.1 educational challenge"},
                timeout=8.0,
            )
            response.raise_for_status()
            pages = response.json().get("query", {}).get("pages", {})
        except (httpx.HTTPError, ValueError):
            return None

        if not pages:
            return None
        page = next(iter(pages.values()))
        extract = (page.get("extract") or "").strip()
        source = page.get("fullurl")
        if not extract or not source:
            return None
        summary = extract[:700].rsplit(" ", 1)[0]
        return WebResult(answer=summary, source=source)

    @staticmethod
    def _direct_url(url: str) -> str:
        query = parse_qs(urlparse(url).query)
        return unquote(query.get("uddg", [url])[0])
