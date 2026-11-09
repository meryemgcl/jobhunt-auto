import logging
from typing import Any
from urllib.parse import quote

from services.adapters.base import (
    OpportunityAdapter,
    is_recent_publication,
    normalize_published_date,
)


logger = logging.getLogger(__name__)


class AshbyAdapter(OpportunityAdapter):
    source_name = "Ashby Career Pages"
    category = "job"
    source_reliability = 92
    api_url = "https://api.ashbyhq.com/posting-api/job-board/{board}"

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

        for board, company in self.boards.items():
            url = self.api_url.format(board=quote(board, safe=""))
            try:
                payload = self.client.get_json(url)
                if not isinstance(payload, dict) or not isinstance(payload.get("jobs"), list):
                    raise ValueError("Invalid response payload: expected a jobs list.")
            except Exception as exc:
                failed_boards.append(board)
                logger.warning("Ashby board request failed. board=%s error=%s", board, exc)
                continue

            board_jobs = []
            for item in payload["jobs"]:
                if item.get("isListed") is False:
                    continue
                published_at = normalize_published_date(item.get("publishedAt"))
                if not is_recent_publication(published_at):
                    continue

                address = item.get("address") or {}
                postal_address = address.get("postalAddress") if isinstance(address, dict) else {}
                country = (postal_address or {}).get("addressCountry", "")
                location = item.get("location") or ""
                if not location and country:
                    location = country
                tags = [
                    str(value)
                    for value in (item.get("employmentType"), item.get("department"), item.get("team"))
                    if value
                ]
                board_jobs.append(
                    (
                        published_at,
                        self.opportunity(
                            title=item.get("title", ""),
                            company=company,
                            url=item.get("jobUrl", ""),
                            location=location,
                            tags=tags,
                            description=(item.get("descriptionPlain") or "")[:700],
                            published_at=published_at,
                            metadata={
                                "application_url": item.get("applyUrl", ""),
                                "country": country,
                                "eligible_countries": [country] if country else [],
                                "workplace_type": item.get("workplaceType", ""),
                                "is_remote": item.get("isRemote"),
                                "department": item.get("department", ""),
                                "team": item.get("team", ""),
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
            self.last_error = f"{len(failed_boards)} of {len(self.boards)} Ashby board request(s) failed."
        return opportunities
