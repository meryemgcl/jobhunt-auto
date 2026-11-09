import logging
from typing import Any
from urllib.parse import quote

from services.adapters.base import (
    OpportunityAdapter,
    is_recent_publication,
    normalize_published_date,
)


logger = logging.getLogger(__name__)


class GreenhouseAdapter(OpportunityAdapter):
    source_name = "Greenhouse Career Pages"
    category = "job"
    source_reliability = 92
    api_url = "https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=false"

    def __init__(
        self,
        boards: list[str],
        client=None,
        max_results_per_board: int = 12,
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

        for board in self.boards:
            url = self.api_url.format(board=quote(board, safe=""))
            try:
                payload = self.client.get_json(url)
                if not isinstance(payload, dict) or not isinstance(payload.get("jobs"), list):
                    raise ValueError("Invalid response payload: expected a jobs list.")
            except Exception as exc:
                failed_boards.append(board)
                logger.warning("Greenhouse board request failed. board=%s error=%s", board, exc)
                continue

            board_jobs = []
            for item in payload["jobs"]:
                published_at = normalize_published_date(item.get("first_published"))
                freshness_date = published_at or normalize_published_date(item.get("updated_at"))
                if not is_recent_publication(freshness_date):
                    continue

                location = item.get("location") or {}
                if isinstance(location, dict):
                    location = location.get("name", "")
                departments = item.get("departments") or []
                board_jobs.append(
                    (
                        freshness_date,
                        self.opportunity(
                            title=item.get("title", ""),
                            company=item.get("company_name") or board,
                            url=item.get("absolute_url", ""),
                            location=location,
                            published_at=published_at,
                            metadata={
                                "application_url": item.get("absolute_url", ""),
                                "department": [
                                    department.get("name", "")
                                    for department in departments
                                    if isinstance(department, dict)
                                ],
                                "board": board,
                                "updated_at": item.get("updated_at", ""),
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
            self.last_error = (
                f"{len(failed_boards)} of {len(self.boards)} Greenhouse board request(s) failed."
            )
        return opportunities
