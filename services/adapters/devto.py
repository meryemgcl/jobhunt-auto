import logging
from typing import Any

from services.adapters.base import OpportunityAdapter


logger = logging.getLogger(__name__)


class DevToAdapter(OpportunityAdapter):
    source_name = "Dev.to API"
    category = "news"
    source_reliability = 82
    url = "https://dev.to/api/articles?tag=python&top=1"

    def fetch(self) -> list[dict[str, Any]]:
        try:
            payload = self.client.get_json(self.url)
        except Exception as exc:
            logger.error("Dev.to haber hatasi: %s", exc)
            return []

        return [
            self.opportunity(
                title=item.get("title", ""),
                url=item.get("url", ""),
                source=f"Dev.to ({item.get('user', {}).get('name', 'Yazar')})",
                published_at=item.get("published_at", "")[:10],
                metadata={"readable_publish_date": item.get("readable_publish_date", "")},
            )
            for item in payload[:3]
        ]
