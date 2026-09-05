import datetime as dt
import json
import logging
from pathlib import Path
from typing import Any

from services.state_io import atomic_write_json
from services.url_utils import canonicalize_url, clean_url


MEMORY_FILE = "seen_jobs.json"
logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return dt.datetime.now(dt.UTC).isoformat(timespec="seconds")


def _coerce_record(entry: Any, timestamp: str) -> dict[str, Any] | None:
    if isinstance(entry, str):
        url = clean_url(entry)
        canonical_url = canonicalize_url(url)
        if not canonical_url:
            return None
        return {
            "url": url,
            "canonical_url": canonical_url,
            "title": "",
            "company": "",
            "source": "legacy",
            "first_seen_at": timestamp,
            "last_seen_at": timestamp,
            "score": None,
        }

    if not isinstance(entry, dict):
        return None

    url = clean_url(entry.get("url") or entry.get("canonical_url"))
    canonical_url = canonicalize_url(entry.get("canonical_url") or url)
    if not canonical_url:
        return None

    return {
        "url": url,
        "canonical_url": canonical_url,
        "title": str(entry.get("title") or ""),
        "company": str(entry.get("company") or ""),
        "source": str(entry.get("source") or ""),
        "first_seen_at": str(entry.get("first_seen_at") or timestamp),
        "last_seen_at": str(entry.get("last_seen_at") or timestamp),
        "score": entry.get("score"),
    }


def _dedupe_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: dict[str, dict[str, Any]] = {}

    for record in records:
        canonical_url = record["canonical_url"]
        existing = deduped.get(canonical_url)
        if not existing:
            deduped[canonical_url] = record
            continue

        existing["last_seen_at"] = record.get("last_seen_at") or existing["last_seen_at"]
        for field in ("title", "company", "source", "url", "score"):
            if record.get(field) not in ("", None):
                existing[field] = record[field]

    return list(deduped.values())


def load_seen_jobs(path: str | Path = MEMORY_FILE) -> list[dict[str, Any]]:
    """Load seen opportunity records, accepting both legacy URL lists and v2 records."""
    memory_path = Path(path)
    if not memory_path.exists():
        return []

    try:
        with memory_path.open(encoding="utf-8") as handle:
            raw_data = json.load(handle)
    except json.JSONDecodeError as exc:
        logger.error("Hafiza dosyasi JSON olarak okunamadi: %s", exc)
        return []

    timestamp = _now_iso()
    if isinstance(raw_data, dict):
        raw_entries = raw_data.get("jobs", [])
    elif isinstance(raw_data, list):
        raw_entries = raw_data
    else:
        logger.warning("Hafiza dosyasinda beklenmeyen format bulundu: %s", type(raw_data).__name__)
        return []

    records = [_coerce_record(entry, timestamp) for entry in raw_entries]
    return _dedupe_records([record for record in records if record])


def load_seen_canonical_urls(path: str | Path = MEMORY_FILE) -> set[str]:
    return {record["canonical_url"] for record in load_seen_jobs(path)}


def build_seen_job_record(job: str | dict[str, Any], timestamp: str | None = None) -> dict[str, Any] | None:
    timestamp = timestamp or _now_iso()
    if isinstance(job, str):
        return _coerce_record(job, timestamp)

    if not isinstance(job, dict):
        return None

    url = clean_url(job.get("url"))
    canonical_url = canonicalize_url(job.get("canonical_url") or url)
    if not canonical_url:
        return None

    return {
        "url": url,
        "canonical_url": canonical_url,
        "title": str(job.get("title") or ""),
        "company": str(job.get("company") or ""),
        "source": str(job.get("source") or ""),
        "first_seen_at": timestamp,
        "last_seen_at": timestamp,
        "score": job.get("score"),
    }


def add_seen_jobs(new_jobs: list[str | dict[str, Any]], path: str | Path = MEMORY_FILE) -> int:
    """Add delivered opportunities to memory and return the number of new records."""
    timestamp = _now_iso()
    records = load_seen_jobs(path)
    records_by_url = {record["canonical_url"]: record for record in records}
    added_count = 0

    for job in new_jobs:
        record = build_seen_job_record(job, timestamp)
        if not record:
            continue

        existing = records_by_url.get(record["canonical_url"])
        if existing:
            existing["last_seen_at"] = timestamp
            if record.get("score") is not None:
                existing["score"] = record["score"]
            continue

        records.append(record)
        records_by_url[record["canonical_url"]] = record
        added_count += 1

    if added_count:
        atomic_write_json(path, records)
        logger.info("%s yeni ilan/firsat hafizaya kaydedildi.", added_count)

    return added_count


def migrate_seen_jobs_file(path: str | Path = MEMORY_FILE) -> int:
    """Rewrite memory into the structured v2 list format and return record count."""
    records = load_seen_jobs(path)
    atomic_write_json(path, records)
    logger.info("Hafiza dosyasi yapilandirilmis formata tasindi. record_count=%s", len(records))
    return len(records)
