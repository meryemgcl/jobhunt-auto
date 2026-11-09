import logging
from typing import Any

from services.adapters.base import (
    OpportunityAdapter,
    is_recent_publication,
    normalize_published_date,
)


logger = logging.getLogger(__name__)


class ArbeitnowAdapter(OpportunityAdapter):
    source_name = "Arbeitnow API"
    category = "job"
    source_reliability = 88
    url = "https://www.arbeitnow.com/api/job-board-api"

    def fetch(self) -> list[dict[str, Any]]:
        self.last_error = None
        try:
            payload = self.client.get_json(self.url)
        except Exception as exc:
            self.last_error = str(exc)
            logger.error("Arbeitnow API hatasi: %s", exc)
            return []

        if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
            self.last_error = "Invalid response payload: expected a data list."
            logger.error("Arbeitnow API yanit formati gecersiz.")
            return []

        opportunities = []
        for item in payload["data"]:
            pub_date = normalize_published_date(item.get("created_at"))
            if not is_recent_publication(pub_date):
                continue
            opportunities.append(
                self.opportunity(
                    title=item.get("title", ""),
                    company=item.get("company_name", "Doğrulanmış Şirket"),
                    url=item.get("url", ""),
                    location=item.get("location", "Remote"),
                    tags=item.get("tags", []),
                    description=item.get("description", "")[:350],
                    published_at=pub_date,
                    metadata={
                        "application_url": item.get("url", ""),
                        "eligible_countries": item.get("eligible_countries", []),
                        "remote": bool(item.get("remote")),
                    },
                )
            )
        opportunities.sort(key=lambda item: item["published_at"], reverse=True)
        return opportunities[:30]
