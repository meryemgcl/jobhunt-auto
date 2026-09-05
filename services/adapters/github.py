import logging
import os
from typing import Any

from services.adapters.base import OpportunityAdapter


logger = logging.getLogger(__name__)


class GitHubIssuesAdapter(OpportunityAdapter):
    source_name = "GitHub Issues API"
    category = "open_source"
    source_reliability = 92
    url = (
        "https://api.github.com/search/issues"
        "?q=label:%22good%20first%20issue%22+language:python+state:open"
        "&sort=updated&order=desc&per_page=3"
    )

    def fetch(self) -> list[dict[str, Any]]:
        headers = {
            "Accept": "application/vnd.github.v3+json",
        }
        token = os.getenv("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"

        try:
            payload = self.client.get_json(self.url, headers=headers)
        except Exception as exc:
            logger.error("GitHub Issues API hatasi: %s", exc)
            return []

        opportunities = []
        for item in payload.get("items", [])[:3]:
            repo_name = "/".join(item.get("repository_url", "").split("/")[-2:])
            opportunities.append(
                self.opportunity(
                    title=item.get("title", ""),
                    url=item.get("html_url", ""),
                    repo=repo_name,
                    comments=item.get("comments", 0),
                    created_at=item.get("created_at", "")[:10],
                )
            )
        return opportunities
