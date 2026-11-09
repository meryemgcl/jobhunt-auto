import datetime as dt
import logging
from collections import Counter
from pathlib import Path
from typing import Any

from services.state_io import atomic_write_text


RUN_SUMMARY_FILE = "RUN_SUMMARY.md"

logger = logging.getLogger(__name__)


def summarize_sources(opportunities: list[dict[str, Any]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for item in opportunities:
        source = item.get("source") or item.get("platform") or item.get("organization") or "unknown"
        counts[str(source)] += 1
    return dict(sorted(counts.items()))


def summarize_job_quality(
    jobs: list[dict[str, Any]],
    *,
    matched_urls: set[str] | None = None,
) -> dict[str, dict[str, int]]:
    matched_urls = matched_urls or set()
    grouped: dict[str, list[dict[str, Any]]] = {}
    for job in jobs:
        source = str(job.get("source") or "unknown")
        grouped.setdefault(source, []).append(job)

    quality = {}
    for source, source_jobs in sorted(grouped.items()):
        count = len(source_jobs)
        quality[source] = {
            "jobs": count,
            "matched": sum(str(job.get("canonical_url") or job.get("url") or "") in matched_urls for job in source_jobs),
            "companies": len(
                {
                    str(job.get("company") or "").strip().casefold()
                    for job in source_jobs
                    if str(job.get("company") or "").strip()
                }
            ),
            "dated": sum(bool(job.get("published_at")) for job in source_jobs),
            "application_links": sum(
                bool((job.get("metadata") or {}).get("application_url"))
                for job in source_jobs
            ),
            "locations": sum(bool(job.get("location")) for job in source_jobs),
        }
    return quality


def detect_source_alerts(
    source_counts: dict[str, int],
    *,
    source_errors: dict[str, int] | None = None,
) -> list[str]:
    alerts = []
    if sum(source_counts.values()) == 0:
        alerts.append("Hiç fırsat toplanamadı; ağ bağlantısı, adapter hataları ve API limitleri kontrol edilmeli.")

    for source, error_count in sorted((source_errors or {}).items()):
        if error_count:
            alerts.append(f"{source}: {error_count} source request(s) failed; inspect run logs.")

    return alerts


def build_run_summary(
    *,
    run_id: str,
    started_at: str,
    total_collected: int,
    matched_count: int,
    duplicate_count: int,
    invalid_url_count: int,
    email_sent: bool,
    dashboard_updated: bool,
    memory_added_count: int,
    source_counts: dict[str, int],
    source_errors: dict[str, int] | None = None,
    job_source_quality: dict[str, dict[str, int]] | None = None,
) -> dict[str, Any]:
    source_errors = dict(source_errors or {})
    alerts = detect_source_alerts(source_counts, source_errors=source_errors)
    return {
        "run_id": run_id,
        "started_at": started_at,
        "finished_at": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "total_collected": total_collected,
        "matched_count": matched_count,
        "duplicate_count": duplicate_count,
        "invalid_url_count": invalid_url_count,
        "email_sent": email_sent,
        "dashboard_updated": dashboard_updated,
        "memory_added_count": memory_added_count,
        "source_counts": source_counts,
        "source_errors": source_errors,
        "job_source_quality": job_source_quality or {},
        "alerts": alerts,
    }


def write_daily_summary(summary: dict[str, Any], path: str | Path = RUN_SUMMARY_FILE) -> bool:
    source_lines = [
        f"- `{source}`: {count}" for source, count in sorted(dict(summary.get("source_counts") or {}).items())
    ]
    alert_lines = [f"- {alert}" for alert in summary.get("alerts", [])]
    quality_lines = [
        (
            f"- `{source}`: {metrics.get('jobs', 0)} ilan, "
            f"{metrics.get('companies', 0)} şirket, "
            f"{metrics.get('matched', 0)} eşleşme, "
            f"{metrics.get('dated', 0)} tarihli, "
            f"{metrics.get('application_links', 0)} doğrudan başvuru bağlantılı, "
            f"{metrics.get('locations', 0)} konumlu"
        )
        for source, metrics in sorted(dict(summary.get("job_source_quality") or {}).items())
    ]

    content = "\n".join(
        [
            "# JobHunt-Auto Run Summary",
            "",
            f"- Run ID: `{summary.get('run_id')}`",
            f"- Started At: `{summary.get('started_at')}`",
            f"- Finished At: `{summary.get('finished_at')}`",
            f"- Total Collected: `{summary.get('total_collected', 0)}`",
            f"- Matched Jobs: `{summary.get('matched_count', 0)}`",
            f"- Duplicates Skipped: `{summary.get('duplicate_count', 0)}`",
            f"- Invalid URLs Skipped: `{summary.get('invalid_url_count', 0)}`",
            f"- Email Sent: `{bool(summary.get('email_sent'))}`",
            f"- Dashboard Updated: `{bool(summary.get('dashboard_updated'))}`",
            f"- Memory Added Count: `{summary.get('memory_added_count', 0)}`",
            "",
            "## Source Counts",
            "",
            "\n".join(source_lines) if source_lines else "- No source data.",
            "",
            "## Job Source Quality",
            "",
            "\n".join(quality_lines) if quality_lines else "- No job source data.",
            "",
            "## Alerts",
            "",
            "\n".join(alert_lines) if alert_lines else "- No active alerts.",
            "",
        ]
    )

    try:
        atomic_write_text(path, content)
    except Exception as exc:
        logger.error("Gunluk run ozeti yazilamadi: %s", exc)
        return False

    logger.info("Gunluk run ozeti yazildi. path=%s", path)
    return True
