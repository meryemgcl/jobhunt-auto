import logging

from config import ASHBY_BOARDS, GREENHOUSE_BOARDS, LEVER_BOARDS, SEARCH_PROMPTS
from services.adapters import (
    AshbyAdapter,
    ArbeitnowAdapter,
    DevToAdapter,
    DuckDuckGoAdapter,
    GreenhouseAdapter,
    HackerNewsAdapter,
    HackerNewsJobsAdapter,
    LeverAdapter,
    RemotiveAdapter,
    StaticOpportunityAdapter,
)

logger = logging.getLogger(__name__)
_SOURCE_ERRORS: dict[str, int] = {}


def reset_source_errors() -> None:
    _SOURCE_ERRORS.clear()


def get_source_errors() -> dict[str, int]:
    return dict(_SOURCE_ERRORS)


def record_source_error(source: str) -> None:
    _SOURCE_ERRORS[source] = _SOURCE_ERRORS.get(source, 0) + 1


from concurrent.futures import ThreadPoolExecutor, as_completed

def _collect_from_adapters(adapters, max_workers: int = 4):
    """Adaptorleri paralel calistirir; bir adapter hata verse digerleri etkilenmez."""
    if not adapters:
        return []

    opportunities = []

    def _fetch_safe(adapter):
        try:
            items = adapter.fetch()
            logger.info("Adapter tamamlandi. adapter=%s count=%s", adapter.__class__.__name__, len(items))
            if getattr(adapter, "last_error", None):
                record_source_error(getattr(adapter, "source_name", adapter.__class__.__name__))
            return items
        except Exception as exc:
            logger.error("Adapter hata verdi, atlanıyor. adapter=%s error=%s", adapter.__class__.__name__, exc)
            record_source_error(getattr(adapter, "source_name", adapter.__class__.__name__))
            return []

    workers = min(len(adapters), max_workers)
    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_adapter = {executor.submit(_fetch_safe, a): a for a in adapters}
        for future in as_completed(future_to_adapter):
            try:
                res = future.result()
                if res:
                    opportunities.extend(res)
            except Exception as exc:
                adapter = future_to_adapter[future]
                logger.error("Adapter future sonucunda hata: %s error=%s", adapter.__class__.__name__, exc)

    return opportunities


def _bootcamp_mapper(result, _prompt):
    return {
        "title": result.get("title", "Yazılım & AI Bootcamp Programı"),
        "url": result["href"],
        "status": "Search result; confirm application dates",
        "source": "Bootcamp Search",
        "source_reliability": 65,
    }


def _rd_project_mapper(result, _prompt):
    return {
        "title": result.get("title", "TÜBİTAK 2209 Öğrenci Araştırma Projeleri"),
        "url": result["href"],
        "description": result.get("body", "")[:350],
        "status": "Search result; confirm application dates",
        "source": "AR-GE Search",
        "source_reliability": 65,
    }

def fetch_jobs():
    """
    Fetch current jobs from structured feeds and employer career-board APIs.
    General web search results are excluded because they are not verified postings.
    """
    adapters = [
        RemotiveAdapter(),
        ArbeitnowAdapter(),
        GreenhouseAdapter(boards=GREENHOUSE_BOARDS),
        LeverAdapter(boards=LEVER_BOARDS),
        AshbyAdapter(boards=ASHBY_BOARDS),
        HackerNewsJobsAdapter(),
    ]
    return _collect_from_adapters(adapters)

def fetch_bootcamps_and_camps():
    """Ucretsiz egitim kamplari, bootcamp ve akademi programlarini ceker."""
    return _collect_from_adapters([
        DuckDuckGoAdapter(
            prompts=SEARCH_PROMPTS.get("BOOTCAMPS", []),
            category="bootcamp",
            max_results=1,
            result_mapper=_bootcamp_mapper,
        )
    ])

def fetch_r_and_d_projects():
    """TÜBİTAK 2209 ve Teknokent AR-GE Proje Destek ve Fırsatlarını ceker."""
    return _collect_from_adapters([
        DuckDuckGoAdapter(
            prompts=SEARCH_PROMPTS.get("RD_PROJECTS", []),
            category="rd_project",
            max_results=1,
            result_mapper=_rd_project_mapper,
        )
    ])

def fetch_podcasts():
    """No verified podcast feed is configured; avoid presenting stale static links."""
    return []

def fetch_hackathons():
    """Yarışma ve Hackathon platformlarını derler."""
    adapter = StaticOpportunityAdapter(
        [
            {
                "title": "Devpost Global & Online Hackathon Directory",
                "url": "https://devpost.com/hackathons?challenge_type[]=online",
                "platform": "Devpost",
                "status": "Listing directory; confirm active dates",
            },
            {
                "title": "TEKNOFEST Competitions Directory",
                "url": "https://www.teknofest.org/tr/competitions/",
                "platform": "TEKNOFEST",
                "status": "Official listing directory; confirm active dates",
            },
            {
                "title": "Kaggle Competitions Directory",
                "url": "https://www.kaggle.com/competitions",
                "platform": "Kaggle",
                "status": "Competition directory; confirm active dates",
            },
        ],
        category="hackathon",
    )
    return adapter.fetch()

def fetch_tech_news():
    """HackerNews ve Dev.to üzerinden en taze haberleri çeker."""
    news = _collect_from_adapters([DevToAdapter(), HackerNewsAdapter()])
    for item in news:
        item["date"] = item.get("metadata", {}).get("readable_publish_date") or item.get("published_at", "")
    return news
