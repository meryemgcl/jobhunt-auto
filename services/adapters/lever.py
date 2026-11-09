import logging
from typing import Any
from urllib.parse import quote

from services.adapters.base import (
    OpportunityAdapter,
    is_recent_publication,
    normalize_published_date,
)


logger = logging.getLogger(__name__)


class LeverAdapter(OpportunityAdapter):
    source_name = "Lever Career Pages"
    category = "job"
    source_reliability = 92
    api_url = "https://api.lever.co/v0/postings/{site}?mode=json"

    def __init__(
        self,
        boards: dict[str, str],
        client=None,
        max_results_per_board: int = 20,
    ):
        super().__init__(client=client)
        if max_results_per_board < 1:
            raise ValueError("max_results_per_board must be positive.")
        self.boards = boards
        self.max_results_per_board = max_results_per_board

    def fetch(self) -> list[dict[str, Any]]:
        self.last_error = None
        opportunities = []
        failed_boards = []

        for site, company in self.boards.items():
            url = self.api_url.format(site=quote(site, safe=""))
            try:
                payload = self.client.get_json(url)
                if not isinstance(payload, list):
                    raise ValueError("Invalid response payload: expected a postings list.")
            except Exception as exc:
                failed_boards.append(site)
                logger.warning("Lever board request failed. board=%s error=%s", site, exc)
                continue

            board_jobs = []
            for item in payload:
                published_at = normalize_published_date(item.get("createdAt"))
                if not is_recent_publication(published_at):
                    continue

                categories = item.get("categories") or {}
                location = categories.get("location") or ", ".join(categories.get("allLocations") or [])
                country = item.get("country") or ""
                tags = [
                    str(categories[key])
                    for key in ("commitment", "department", "team")
                    if categories.get(key)
                ]
                board_jobs.append(
                    (
                        published_at,
                        self.opportunity(
                            title=item.get("text", ""),
                            company=company,
                            url=item.get("hostedUrl", ""),
                            location=location,
                            tags=tags,
                            description=(item.get("descriptionPlain") or "")[:700],
                            published_at=published_at,
                            metadata={
                                "application_url": item.get("applyUrl", ""),
                                "country": country,
                                "workplace_type": item.get("workplaceType", ""),
                                "eligible_countries": [country] if country else [],
                                "department": categories.get("department", ""),
                                "team": categories.get("team", ""),
                            },
                        ),
                    )
                )

            board_jobs.sort(key=lambda job: job[0], reverse=True)
            opportunities.extend(
                opportunity
                for _, opportunity in board_jobs[: self.max_results_per_board]
            )

        if failed_boards:
            self.last_error = f"{len(failed_boards)} of {len(self.boards)} Lever board request(s) failed."
        return opportunities
