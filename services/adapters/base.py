import datetime as dt
import logging
import os
from abc import ABC, abstractmethod
from typing import Any

from services.http_client import ResilientHttpClient
from services.models import Opportunity


logger = logging.getLogger(__name__)

_MAX_JOB_AGE_DAYS = int(os.getenv("JOBHUNT_MAX_JOB_AGE_DAYS", "30"))
if not 1 <= _MAX_JOB_AGE_DAYS <= 365:
    raise ValueError("JOBHUNT_MAX_JOB_AGE_DAYS must be between 1 and 365.")


def normalize_published_date(value: Any) -> str:
    if isinstance(value, (int, float)):
        try:
            if abs(value) >= 100_000_000_000:
                value /= 1000
            return dt.datetime.fromtimestamp(value, tz=dt.UTC).date().isoformat()
        except (OverflowError, OSError, ValueError):
            return ""
    if not isinstance(value, str) or not value.strip():
        return ""

    normalized = value.strip().replace("Z", "+00:00")
    try:
        return dt.datetime.fromisoformat(normalized).date().isoformat()
    except ValueError:
        try:
            return dt.date.fromisoformat(normalized[:10]).isoformat()
        except ValueError:
            return ""


def is_recent_publication(value: Any) -> bool:
    published_date = normalize_published_date(value)
    if not published_date:
        return True
    age_days = (dt.datetime.now(dt.UTC).date() - dt.date.fromisoformat(published_date)).days
    return 0 <= age_days <= _MAX_JOB_AGE_DAYS


class OpportunityAdapter(ABC):
    source_name = "Unknown"
    category = "generic"
    source_reliability = 70

    def __init__(self, client: ResilientHttpClient | None = None):
        self.client = client or ResilientHttpClient()
        self.last_error: str | None = None

    @abstractmethod
    def fetch(self) -> list[dict[str, Any]]:
        raise NotImplementedError

    def opportunity(self, **kwargs) -> dict[str, Any]:
        kwargs.setdefault("source", self.source_name)
        kwargs.setdefault("category", self.category)
        kwargs.setdefault("source_reliability", self.source_reliability)
        return Opportunity(**kwargs).to_dict()


class StaticOpportunityAdapter(OpportunityAdapter):
    def __init__(self, items: list[dict[str, Any]], category: str, source_name: str = "Static Curated"):
        self.client = None
        self.items = items
        self.category = category
        self.source_name = source_name
        self.last_error = None

    def fetch(self) -> list[dict[str, Any]]:
        opportunities = []
        for item in self.items:
            payload = dict(item)
            payload.setdefault("source", payload.get("platform") or payload.get("organization") or self.source_name)
            payload.setdefault("category", self.category)
            payload.setdefault("source_reliability", 80)
            opportunities.append(Opportunity(**payload).to_dict())
        return opportunities
