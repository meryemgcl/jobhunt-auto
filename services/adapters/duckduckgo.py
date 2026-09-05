import datetime as dt
import logging
from collections.abc import Callable
from typing import Any

try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

from services.adapters.base import OpportunityAdapter


logger = logging.getLogger(__name__)


class DuckDuckGoAdapter(OpportunityAdapter):
    source_name = "DuckDuckGo Search"
    source_reliability = 65

    def __init__(
        self,
        prompts: list[str],
        category: str,
        max_results: int,
        result_mapper: Callable[[dict[str, Any], str], dict[str, Any]],
    ):
        self.client = None
        self.prompts = prompts
        self.category = category
        self.max_results = max_results
        self.result_mapper = result_mapper

    def fetch(self) -> list[dict[str, Any]]:
        opportunities = []
        current_date = dt.datetime.now(dt.UTC).strftime("%Y-%m-%d")

        try:
            ddgs = DDGS()
        except Exception as exc:
            logger.error("DuckDuckGo adapter baslatilamadi: %s", exc)
            return []

        for prompt in self.prompts:
            try:
                results = list(ddgs.text(prompt, max_results=self.max_results))
            except Exception as exc:
                logger.warning("DuckDuckGo arama uyarisi (%s): %s", prompt, exc)
                continue

            for result in results:
                title = result.get("title", "")
                if not title or "..." == title.strip():
                    continue
                payload = self.result_mapper(result, prompt)
                payload.setdefault("published_at", current_date)
                payload.setdefault("description", result.get("body", "")[:350])
                payload.setdefault("url", result.get("href", ""))
                payload.setdefault("title", title)
                payload.setdefault("source", self.source_name)
                payload.setdefault("source_reliability", self.source_reliability)
                opportunities.append(self.opportunity(**payload))

        return opportunities
