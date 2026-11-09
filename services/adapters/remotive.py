import logging
from typing import Any

from services.adapters.base import (
    OpportunityAdapter,
    is_recent_publication,
    normalize_published_date,
)


logger = logging.getLogger(__name__)


class RemotiveAdapter(OpportunityAdapter):
    source_name = "Remotive Global API"
    category = "job"
    source_reliability = 90
    url = "https://remotive.com/api/remote-jobs?category=software-dev&limit=20"

    def fetch(self) -> list[dict[str, Any]]:
        self.last_error = None
        try:
            payload = self.client.get_json(self.url)
        except Exception as exc:
            self.last_error = str(exc)
            logger.error("Remotive API hatasi: %s", exc)
            return []

        if not isinstance(payload, dict) or not isinstance(payload.get("jobs"), list):
            self.last_error = "Invalid response payload: expected a jobs list."
            logger.error("Remotive API yanit formati gecersiz.")
            return []

        opportunities = []
        for item in payload["jobs"]:
            pub_date = normalize_published_date(item.get("publication_date"))
            if not is_recent_publication(pub_date):
                continue
            opportunities.append(
                self.opportunity(
                    title=item.get("title", ""),
                    company=item.get("company_name", "Doğrulanmış Şirket"),
                    url=item.get("url", ""),
                    location=item.get("candidate_required_location", "Global Remote"),
                    tags=item.get("tags", []),
                    description=item.get("description", "")[:350],
                    published_at=pub_date,
                    metadata={
                        "application_url": item.get("url", ""),
                        "candidate_required_location": item.get("candidate_required_location", ""),
                        "workplace_type": item.get("job_type", ""),
                    },
                )
            )
        opportunities.sort(key=lambda item: item["published_at"], reverse=True)
        return opportunities[:20]
