import datetime as dt
import logging
from typing import Any

from services.adapters.base import OpportunityAdapter


logger = logging.getLogger(__name__)


class HackerNewsAdapter(OpportunityAdapter):
    source_name = "HackerNews API"
    category = "news"
    source_reliability = 78
    topstories_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
    item_url = "https://hacker-news.firebaseio.com/v0/item/{item_id}.json"

    def fetch(self) -> list[dict[str, Any]]:
        try:
            top_ids = self.client.get_json(self.topstories_url)[:3]
        except Exception as exc:
            logger.error("HackerNews top stories hatasi: %s", exc)
            return []

        opportunities = []
        current_date = dt.datetime.now(dt.UTC).strftime("%Y-%m-%d")
        for item_id in top_ids:
            try:
                item = self.client.get_json(self.item_url.format(item_id=item_id))
            except Exception as exc:
                logger.warning("HackerNews item hatasi item_id=%s error=%s", item_id, exc)
                continue
            if item and item.get("url"):
                opportunities.append(
                    self.opportunity(
                        title=item.get("title", ""),
                        url=item.get("url", ""),
                        published_at=current_date,
                    )
                )
        return opportunities
