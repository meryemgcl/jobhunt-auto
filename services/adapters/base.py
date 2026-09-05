import logging
from abc import ABC, abstractmethod
from typing import Any

from services.http_client import ResilientHttpClient
from services.models import Opportunity


logger = logging.getLogger(__name__)


class OpportunityAdapter(ABC):
    source_name = "Unknown"
    category = "generic"
    source_reliability = 70

    def __init__(self, client: ResilientHttpClient | None = None):
        self.client = client or ResilientHttpClient()

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

    def fetch(self) -> list[dict[str, Any]]:
        opportunities = []
        for item in self.items:
            payload = dict(item)
            payload.setdefault("source", payload.get("platform") or payload.get("organization") or self.source_name)
            payload.setdefault("category", self.category)
            payload.setdefault("source_reliability", 80)
            opportunities.append(Opportunity(**payload).to_dict())
        return opportunities
