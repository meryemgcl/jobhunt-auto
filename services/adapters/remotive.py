import datetime as dt
import logging
from typing import Any

from services.adapters.base import OpportunityAdapter


logger = logging.getLogger(__name__)


class RemotiveAdapter(OpportunityAdapter):
    source_name = "Remotive Global API"
    category = "job"
    source_reliability = 90
    url = "https://remotive.com/api/remote-jobs?category=software-dev&limit=20"

    def fetch(self) -> list[dict[str, Any]]:
        try:
            payload = self.client.get_json(self.url)
        except Exception as exc:
            logger.error("Remotive API hatasi: %s", exc)
            return []

        opportunities = []
        for item in payload.get("jobs", []):
            pub_date = item.get("publication_date", "")[:10] or dt.datetime.now(dt.UTC).strftime("%Y-%m-%d")
            opportunities.append(
                self.opportunity(
                    title=item.get("title", ""),
                    company=item.get("company_name", "Doğrulanmış Şirket"),
                    url=item.get("url", ""),
                    location=item.get("candidate_required_location", "Global Remote"),
                    tags=item.get("tags", []),
                    description=item.get("description", "")[:350],
                    published_at=pub_date,
                )
            )
        return opportunities
