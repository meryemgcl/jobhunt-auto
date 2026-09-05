import datetime as dt
import logging
from typing import Any

from services.adapters.base import OpportunityAdapter


logger = logging.getLogger(__name__)


class ArbeitnowAdapter(OpportunityAdapter):
    source_name = "Arbeitnow API"
    category = "job"
    source_reliability = 88
    url = "https://www.arbeitnow.com/api/job-board-api"

    def fetch(self) -> list[dict[str, Any]]:
        try:
            payload = self.client.get_json(self.url)
        except Exception as exc:
            logger.error("Arbeitnow API hatasi: %s", exc)
            return []

        opportunities = []
        for item in payload.get("data", [])[:20]:
            created_ts = item.get("created_at", 0)
            pub_date = (
                dt.datetime.fromtimestamp(created_ts, tz=dt.UTC).strftime("%Y-%m-%d")
                if created_ts
                else dt.datetime.now(dt.UTC).strftime("%Y-%m-%d")
            )
            opportunities.append(
                self.opportunity(
                    title=item.get("title", ""),
                    company=item.get("company_name", "Doğrulanmış Şirket"),
                    url=item.get("url", ""),
                    location=item.get("location", "Remote"),
                    tags=item.get("tags", []),
                    description=item.get("description", "")[:350],
                    published_at=pub_date,
                )
            )
        return opportunities
