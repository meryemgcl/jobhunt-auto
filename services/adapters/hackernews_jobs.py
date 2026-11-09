import logging
from typing import Any

from services.adapters.base import (
    OpportunityAdapter,
    is_recent_publication,
    normalize_published_date,
)


logger = logging.getLogger(__name__)


class HackerNewsJobsAdapter(OpportunityAdapter):
    source_name = "Hacker News Hiring"
    category = "job"
    source_reliability = 82
    jobstories_url = "https://hacker-news.firebaseio.com/v0/jobstories.json"
    item_url = "https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
    story_url = "https://news.ycombinator.com/item?id={item_id}"

    def __init__(self, client=None, max_results: int = 20):
        super().__init__(client=client)
        if max_results < 1:
            raise ValueError("max_results must be positive.")
        self.max_results = max_results

    def fetch(self) -> list[dict[str, Any]]:
        self.last_error = None
        try:
            item_ids = self.client.get_json(self.jobstories_url)
        except Exception as exc:
            self.last_error = str(exc)
            logger.error("Hacker News hiring feed request failed: %s", exc)
            return []

        if not isinstance(item_ids, list):
            self.last_error = "Invalid response payload: expected a job story ID list."
            logger.error("Hacker News hiring feed returned an invalid payload.")
            return []

        opportunities = []
        failed_items = 0
        for item_id in item_ids[: self.max_results]:
            try:
                item = self.client.get_json(self.item_url.format(item_id=item_id))
            except Exception as exc:
                failed_items += 1
                logger.warning("Hacker News job item request failed. item_id=%s error=%s", item_id, exc)
                continue

            if not isinstance(item, dict) or item.get("dead") or item.get("deleted"):
                continue

            published_at = normalize_published_date(item.get("time"))
            if not is_recent_publication(published_at):
                continue

            opportunities.append(
                self.opportunity(
                    title=item.get("title", ""),
                    url=self.story_url.format(item_id=item_id),
                    published_at=published_at,
                    description=item.get("text", "")[:350],
                    metadata={
                        "author": item.get("by", ""),
                        "application_url": item.get("url", ""),
                        "eligible_countries": [],
                        "hacker_news_item_id": item_id,
                    },
                )
            )

        if failed_items:
            self.last_error = f"{failed_items} Hacker News job item request(s) failed."
        return opportunities
