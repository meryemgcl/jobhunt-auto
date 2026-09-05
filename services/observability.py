import datetime as dt
import logging
from collections import Counter
from pathlib import Path
from typing import Any

from services.state_io import atomic_write_text


RUN_SUMMARY_FILE = "RUN_SUMMARY.md"
MONITORED_SOURCES = ("Remotive Global API", "Arbeitnow API", "GitHub Issues API")

logger = logging.getLogger(__name__)


def summarize_sources(opportunities: list[dict[str, Any]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for item in opportunities:
        source = item.get("source") or item.get("platform") or item.get("organization") or "unknown"
        counts[str(source)] += 1
    return dict(sorted(counts.items()))


def detect_source_alerts(
    source_counts: dict[str, int],
    *,
    monitored_sources: tuple[str, ...] = MONITORED_SOURCES,
) -> list[str]:
    alerts = []
    if sum(source_counts.values()) == 0:
        alerts.append("Hiç fırsat toplanamadı; ağ bağlantısı, adapter hataları ve API limitleri kontrol edilmeli.")

    for source in monitored_sources:
        if source_counts.get(source, 0) == 0:
            alerts.append(f"{source}: bu çalıştırmada 0 kayıt döndü; kaynak sağlığı veya rate limit kontrol edilmeli.")

    return alerts


def infer_source_errors(
    source_counts: dict[str, int],
    *,
    monitored_sources: tuple[str, ...] = MONITORED_SOURCES,
) -> dict[str, int]:
    return {source: 1 for source in monitored_sources if source_counts.get(source, 0) == 0}


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
) -> dict[str, Any]:
    source_errors = infer_source_errors(source_counts)
    alerts = detect_source_alerts(source_counts)
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
        "alerts": alerts,
    }


def write_daily_summary(summary: dict[str, Any], path: str | Path = RUN_SUMMARY_FILE) -> bool:
    source_lines = [
        f"- `{source}`: {count}" for source, count in sorted(dict(summary.get("source_counts") or {}).items())
    ]
    alert_lines = [f"- {alert}" for alert in summary.get("alerts", [])]

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
