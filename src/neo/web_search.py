from __future__ import annotations

import html
import re
from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse

import httpx


@dataclass(frozen=True, slots=True)
class WebResult:
    title: str
    url: str
    snippet: str


class WebSearchClient:
    """Small keyless web search adapter; used only for explicit web/current queries."""

    def __init__(self, timeout: float = 12.0) -> None:
        self.timeout = timeout

    def search(self, query: str, limit: int = 5) -> list[WebResult]:
        response = httpx.get(
            "https://html.duckduckgo.com/html/",
            params={"q": query},
            headers={"User-Agent": "NEO-Desktop/1.0"},
            timeout=self.timeout,
            follow_redirects=True,
        )
        response.raise_for_status()
        links = re.findall(
            r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
            response.text,
            flags=re.DOTALL,
        )
        snippets = re.findall(
            r'class="result__snippet"[^>]*>(.*?)</(?:a|div)>',
            response.text,
            flags=re.DOTALL,
        )
        results = []
        for index, (url, title) in enumerate(links[:limit]):
            parsed = parse_qs(urlparse(html.unescape(url)).query)
            target = parsed.get("uddg", [html.unescape(url)])[0]
            snippet = snippets[index] if index < len(snippets) else ""
            results.append(WebResult(self._clean(title), target, self._clean(snippet)))
        return results

    @staticmethod
    def _clean(value: str) -> str:
        return html.unescape(re.sub(r"<[^>]+>", "", value)).strip()
