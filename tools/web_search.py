import base64
import logging
import os
import re
from dataclasses import dataclass
from html.parser import HTMLParser
from urllib.parse import parse_qs, quote_plus, unquote, urlparse

import httpx

logger = logging.getLogger(__name__)


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
    """Search the web, preferring OpenAI web search when it is configured."""

    endpoint = "https://api.duckduckgo.com/"

    def search(self, query: str) -> WebResult | None:
        if api_key := os.getenv("OPENAI_API_KEY"):
            result = self._search_openai(query, api_key)
            if result:
                return result

        # Keyless providers keep demos working but may be blocked by hosting services.
        return self._search_public(query)

    def _search_openai(self, query: str, api_key: str) -> WebResult | None:
        try:
            response = httpx.post(
                "https://api.openai.com/v1/responses",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": os.getenv("OPENAI_WEB_SEARCH_MODEL", "gpt-4.1-mini"),
                    "tools": [{"type": "web_search_preview"}],
                    "input": (
                        "Responda em português do Brasil, de forma direta e factual. "
                        "Pesquise na web antes de responder e priorize fontes confiáveis. "
                        f"Pergunta: {query}"
                    ),
                },
                timeout=25.0,
            )
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("OpenAI web search failed: %s", exc)
            return None

        texts: list[str] = []
        sources: list[str] = []
        for item in payload.get("output", []):
            for content in item.get("content", []):
                if content.get("type") != "output_text":
                    continue
                if answer_text := content.get("text"):
                    texts.append(answer_text.strip())
                for annotation in content.get("annotations", []):
                    if url := annotation.get("url"):
                        sources.append(url)

        answer = "\n".join(text for text in texts if text)
        source = next(iter(dict.fromkeys(sources)), "")
        if not answer or not source:
            logger.warning("OpenAI web search returned no citable answer")
            return None
        return WebResult(answer=answer, source=source)

    def _search_public(self, query: str) -> WebResult | None:
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
        except (httpx.HTTPError, ValueError) as exc:
            logger.info("DuckDuckGo instant answer failed: %s", exc)
        else:
            answer = payload.get("Answer") or payload.get("AbstractText")
            source = payload.get("AbstractURL")
            if answer and source:
                return WebResult(answer=answer, source=source)

            for topic in payload.get("RelatedTopics", []):
                if isinstance(topic, dict) and topic.get("Text") and topic.get("FirstURL"):
                    return WebResult(answer=topic["Text"], source=topic["FirstURL"])
        return (
            self._search_html(query)
            or self._search_wikipedia(query)
            or self._search_via_reader(query)
        )

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

    def _search_via_reader(self, query: str) -> WebResult | None:
        search_url = (
            "https://r.jina.ai/http://www.bing.com/search?q=" + quote_plus(query)
        )
        try:
            response = httpx.get(search_url, timeout=15.0)
            response.raise_for_status()
        except httpx.HTTPError:
            return None

        match = re.search(
            r"## \[([^]]+)]\((https://www\.bing\.com/ck/a[^)]+)\)\s+"
            r"(.+?)(?=\n\d+\.)",
            response.text,
            flags=re.DOTALL,
        )
        if not match:
            return None

        title, redirect_url, snippet = match.groups()
        source = self._decode_bing_url(redirect_url)
        if not source:
            return None

        page_text = self._read_page(source)
        answer = page_text or re.sub(r"\s+", " ", snippet).strip()
        if not answer:
            return None
        return WebResult(answer=f"{title}: {answer}", source=source)

    @staticmethod
    def _decode_bing_url(url: str) -> str:
        encoded = parse_qs(urlparse(url).query).get("u", [""])[0]
        if not encoded.startswith("a1"):
            return ""
        payload = encoded[2:]
        try:
            padding = "=" * (-len(payload) % 4)
            return base64.urlsafe_b64decode(payload + padding).decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            return ""

    @staticmethod
    def _read_page(source: str) -> str:
        parsed = urlparse(source)
        if parsed.scheme not in {"http", "https"}:
            return ""
        reader_url = "https://r.jina.ai/http://" + parsed.netloc + parsed.path
        try:
            response = httpx.get(reader_url, timeout=15.0)
            response.raise_for_status()
        except httpx.HTTPError:
            return ""
        content = response.text.split("Markdown Content:", 1)[-1].strip()
        clean = re.sub(r"!\[[^]]*]\([^)]+\)", "", content)
        clean = re.sub(r"\[([^]]+)]\([^)]+\)", r"\1", clean)
        clean = re.sub(r"[#*`_|]+", "", clean)
        clean = re.sub(r"\s+", " ", clean).strip()
        return clean[:700].rsplit(" ", 1)[0]

    @staticmethod
    def _direct_url(url: str) -> str:
        query = parse_qs(urlparse(url).query)
        return unquote(query.get("uddg", [url])[0])
