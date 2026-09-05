import datetime as dt
from dataclasses import asdict, dataclass, field
from typing import Any

from services.url_utils import canonicalize_url, clean_url


def calculate_freshness_score(date_text: str | None) -> int:
    if not date_text:
        return 50

    try:
        published_date = dt.date.fromisoformat(str(date_text)[:10])
    except ValueError:
        return 50

    age_days = max((dt.datetime.now(dt.UTC).date() - published_date).days, 0)
    if age_days <= 1:
        return 100
    if age_days <= 7:
        return 90
    if age_days <= 14:
        return 75
    if age_days <= 30:
        return 55
    return 35


def freshness_label(score: int) -> str:
    if score >= 95:
        return "Çok yeni"
    if score >= 80:
        return "Son hafta"
    if score >= 60:
        return "Yakın dönem"
    if score >= 40:
        return "Tarih belirsiz"
    return "Eski olabilir"


@dataclass
class Opportunity:
    title: str
    url: str
    source: str
    category: str
    company: str = ""
    location: str = ""
    tags: list[str] = field(default_factory=list)
    description: str = ""
    published_at: str = ""
    platform: str = ""
    organization: str = ""
    status: str = ""
    repo: str = ""
    comments: int | str | None = None
    created_at: str = ""
    type: str = ""
    source_reliability: int = 70
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["url"] = clean_url(self.url)
        data["canonical_url"] = canonicalize_url(self.url)
        freshness_source = self.published_at or self.created_at
        data["freshness_score"] = calculate_freshness_score(freshness_source)
        data["freshness_label"] = freshness_label(data["freshness_score"])
        data["source_reliability"] = max(0, min(100, int(self.source_reliability)))
        return data
