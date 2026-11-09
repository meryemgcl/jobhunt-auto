import logging
import time
from collections.abc import Callable
from typing import Any

try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

from services.adapters.base import OpportunityAdapter


logger = logging.getLogger(__name__)
SEARCH_TIMEOUT_SECONDS = 10
SEARCH_ATTEMPTS = 2


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
        self.last_error = None
        opportunities = []
        try:
            ddgs = DDGS(timeout=SEARCH_TIMEOUT_SECONDS)
        except Exception as exc:
            self.last_error = str(exc)
            logger.error("DuckDuckGo adapter baslatilamadi: %s", exc)
            return []

        failed_prompts = 0
        for prompt in self.prompts:
            results = []
            for attempt in range(SEARCH_ATTEMPTS):
                try:
                    results = list(ddgs.text(prompt, max_results=self.max_results))
                    break  # Basarili olursa retry dongusunden cik
                except Exception as exc:
                    wait_time = 2**attempt
                    logger.warning(
                        "DuckDuckGo search warning (%s) - attempt %s/%s: %s. Retrying in %s seconds.",
                        prompt,
                        attempt + 1,
                        SEARCH_ATTEMPTS,
                        exc,
                        wait_time,
                    )
                    time.sleep(wait_time)
                    if attempt == SEARCH_ATTEMPTS - 1:
                        failed_prompts += 1
            
            if not results:
                continue

            for result in results:
                title = result.get("title", "")
                if not title or "..." == title.strip() or not result.get("href"):
                    continue
                payload = self.result_mapper(result, prompt)
                payload.setdefault("description", result.get("body", "")[:350])
                payload.setdefault("url", result.get("href", ""))
                payload.setdefault("title", title)
                payload.setdefault("source", self.source_name)
                payload.setdefault("source_reliability", self.source_reliability)
                opportunities.append(self.opportunity(**payload))

        if failed_prompts:
            self.last_error = f"{failed_prompts} search prompt(s) failed after retries."
        return opportunities
