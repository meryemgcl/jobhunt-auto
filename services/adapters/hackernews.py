import logging
from typing import Any

from services.adapters.base import OpportunityAdapter, normalize_published_date


logger = logging.getLogger(__name__)


class HackerNewsAdapter(OpportunityAdapter):
    source_name = "HackerNews API"
    category = "news"
    source_reliability = 78
    topstories_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
    item_url = "https://hacker-news.firebaseio.com/v0/item/{item_id}.json"

    def fetch(self) -> list[dict[str, Any]]:
        self.last_error = None
        try:
            top_ids = self.client.get_json(self.topstories_url)
        except Exception as exc:
            self.last_error = str(exc)
            logger.error("HackerNews top stories hatasi: %s", exc)
            return []

        if not isinstance(top_ids, list):
            self.last_error = "Invalid response payload: expected a story ID list."
            logger.error("HackerNews top stories yanit formati gecersiz.")
            return []

        opportunities = []
        item_errors = 0
        for item_id in top_ids[:3]:
            try:
                item = self.client.get_json(self.item_url.format(item_id=item_id))
            except Exception as exc:
                item_errors += 1
                logger.warning("HackerNews item hatasi item_id=%s error=%s", item_id, exc)
                continue
            if item and item.get("url"):
                opportunities.append(
                    self.opportunity(
                        title=item.get("title", ""),
                        url=item.get("url", ""),
                        published_at=normalize_published_date(item.get("time")),
                    )
                )
        if item_errors:
            self.last_error = f"{item_errors} story item request(s) failed."
        return opportunities
