import datetime as dt
import json
import logging
import os
import re
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from services.url_utils import canonicalize_url, clean_url


DEFAULT_DB_PATH = "jobhunt.db"
VALID_FEEDBACK = {"uygun", "alakasız", "basvurdum"}
FEEDBACK_STATUS = {
    "uygun": "fit",
    "alakasız": "irrelevant",
    "basvurdum": "applied",
}
FEEDBACK_STOPWORDS = {
    "and",
    "api",
    "bir",
    "developer",
    "engineer",
    "for",
    "ile",
    "job",
    "junior",
    "remote",
    "software",
    "staj",
    "the",
    "uzaktan",
    "yazilim",
    "yazılım",
}

logger = logging.getLogger(__name__)


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS opportunities (
    canonical_url TEXT PRIMARY KEY,
    url TEXT NOT NULL,
    title TEXT NOT NULL DEFAULT '',
    company TEXT NOT NULL DEFAULT '',
    source TEXT NOT NULL DEFAULT '',
    category TEXT NOT NULL DEFAULT '',
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    latest_score REAL,
    latest_match_reason TEXT NOT NULL DEFAULT '',
    source_reliability INTEGER NOT NULL DEFAULT 70,
    freshness_score INTEGER NOT NULL DEFAULT 50,
    status TEXT NOT NULL DEFAULT 'seen',
    metadata_json TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_opportunities_status ON opportunities(status);
CREATE INDEX IF NOT EXISTS idx_opportunities_source ON opportunities(source);
CREATE INDEX IF NOT EXISTS idx_opportunities_last_seen ON opportunities(last_seen_at);

CREATE TABLE IF NOT EXISTS score_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_url TEXT NOT NULL,
    score REAL NOT NULL,
    reason TEXT NOT NULL DEFAULT '',
    observed_at TEXT NOT NULL,
    run_id TEXT,
    FOREIGN KEY (canonical_url) REFERENCES opportunities(canonical_url) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_score_history_url ON score_history(canonical_url);
CREATE INDEX IF NOT EXISTS idx_score_history_run ON score_history(run_id);

CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_url TEXT NOT NULL,
    feedback TEXT NOT NULL CHECK (feedback IN ('uygun', 'alakasız', 'basvurdum')),
    note TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    FOREIGN KEY (canonical_url) REFERENCES opportunities(canonical_url) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_feedback_url ON feedback(canonical_url);

CREATE TABLE IF NOT EXISTS run_summaries (
    run_id TEXT PRIMARY KEY,
    started_at TEXT NOT NULL,
    finished_at TEXT NOT NULL,
    total_collected INTEGER NOT NULL DEFAULT 0,
    matched_count INTEGER NOT NULL DEFAULT 0,
    duplicate_count INTEGER NOT NULL DEFAULT 0,
    invalid_url_count INTEGER NOT NULL DEFAULT 0,
    email_sent INTEGER NOT NULL DEFAULT 0,
    dashboard_updated INTEGER NOT NULL DEFAULT 0,
    memory_added_count INTEGER NOT NULL DEFAULT 0,
    source_counts_json TEXT NOT NULL DEFAULT '{}',
    source_errors_json TEXT NOT NULL DEFAULT '{}',
    alerts_json TEXT NOT NULL DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS source_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    source TEXT NOT NULL,
    collected_count INTEGER NOT NULL DEFAULT 0,
    error_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_source_runs_source ON source_runs(source);
CREATE INDEX IF NOT EXISTS idx_source_runs_run ON source_runs(run_id);
"""


def utc_now_iso() -> str:
    return dt.datetime.now(dt.UTC).isoformat(timespec="seconds")


def get_db_path(path: str | Path | None = None) -> Path:
    return Path(path or os.getenv("JOBHUNT_DB_PATH") or DEFAULT_DB_PATH)


@contextmanager
def connect(path: str | Path | None = None) -> Iterator[sqlite3.Connection]:
    db_path = get_db_path(path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_database(path: str | Path | None = None) -> Path:
    db_path = get_db_path(path)
    with connect(db_path) as conn:
        conn.executescript(SCHEMA_SQL)
        conn.execute(
            "INSERT OR IGNORE INTO schema_migrations(version, applied_at) VALUES (?, ?)",
            (1, utc_now_iso()),
        )
    logger.info("SQLite state hazir. path=%s", db_path)
    return db_path


def _json_dump(value: Any) -> str:
    return json.dumps(value or {}, ensure_ascii=False, sort_keys=True)


def _clamped_int(value: Any, default: int) -> int:
    try:
        return max(0, min(100, int(float(value))))
    except (TypeError, ValueError):
        return default


def _opportunity_row(job: dict[str, Any], status: str, timestamp: str) -> tuple[Any, ...] | None:
    url = clean_url(job.get("url") or job.get("canonical_url"))
    canonical_url = canonicalize_url(job.get("canonical_url") or url)
    if not canonical_url:
        return None

    metadata = dict(job.get("metadata") or {})
    for key in ("platform", "organization", "repo", "type", "tags"):
        if key in job and job.get(key) not in ("", None, []):
            metadata[key] = job[key]

    return (
        canonical_url,
        url or canonical_url,
        str(job.get("title") or ""),
        str(job.get("company") or ""),
        str(job.get("source") or ""),
        str(job.get("category") or "job"),
        str(job.get("first_seen_at") or timestamp),
        str(job.get("last_seen_at") or timestamp),
        job.get("score"),
        str(job.get("match_reason") or ""),
        _clamped_int(job.get("source_reliability"), 70),
        _clamped_int(job.get("freshness_score"), 50),
        status,
        _json_dump(metadata),
    )


def upsert_opportunities(
    opportunities: list[dict[str, Any]],
    *,
    status: str = "seen",
    path: str | Path | None = None,
) -> int:
    init_database(path)
    timestamp = utc_now_iso()
    rows = [_opportunity_row(job, status, timestamp) for job in opportunities]
    rows = [row for row in rows if row]
    if not rows:
        return 0

    with connect(path) as conn:
        conn.executemany(
            """
            INSERT INTO opportunities (
                canonical_url, url, title, company, source, category,
                first_seen_at, last_seen_at, latest_score, latest_match_reason,
                source_reliability, freshness_score, status, metadata_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(canonical_url) DO UPDATE SET
                url = excluded.url,
                title = CASE WHEN excluded.title != '' THEN excluded.title ELSE opportunities.title END,
                company = CASE WHEN excluded.company != '' THEN excluded.company ELSE opportunities.company END,
                source = CASE WHEN excluded.source != '' THEN excluded.source ELSE opportunities.source END,
                category = CASE WHEN excluded.category != '' THEN excluded.category ELSE opportunities.category END,
                last_seen_at = excluded.last_seen_at,
                latest_score = COALESCE(excluded.latest_score, opportunities.latest_score),
                latest_match_reason = CASE
                    WHEN excluded.latest_match_reason != '' THEN excluded.latest_match_reason
                    ELSE opportunities.latest_match_reason
                END,
                source_reliability = excluded.source_reliability,
                freshness_score = excluded.freshness_score,
                status = CASE
                    WHEN opportunities.status IN ('fit', 'irrelevant', 'applied')
                        AND excluded.status IN ('seen', 'sent')
                    THEN opportunities.status
                    ELSE excluded.status
                END,
                metadata_json = excluded.metadata_json
            """,
            rows,
        )

    logger.info("SQLite opportunities guncellendi. count=%s status=%s", len(rows), status)
    return len(rows)


def record_score_history(
    opportunities: list[dict[str, Any]],
    *,
    run_id: str | None = None,
    path: str | Path | None = None,
) -> int:
    init_database(path)
    timestamp = utc_now_iso()
    rows: list[tuple[Any, ...]] = []
    for job in opportunities:
        canonical_url = canonicalize_url(job.get("canonical_url") or job.get("url"))
        if not canonical_url or job.get("score") is None:
            continue
        rows.append((canonical_url, float(job.get("score")), str(job.get("match_reason") or ""), timestamp, run_id))

    if not rows:
        return 0

    with connect(path) as conn:
        conn.executemany(
            """
            INSERT INTO score_history(canonical_url, score, reason, observed_at, run_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            rows,
        )

    logger.info("SQLite skor gecmisi kaydedildi. count=%s", len(rows))
    return len(rows)


def load_seen_canonical_urls_from_db(
    path: str | Path | None = None,
    *,
    blocking_statuses: tuple[str, ...] = ("sent", "fit", "irrelevant", "applied"),
) -> set[str]:
    init_database(path)
    placeholders = ",".join("?" for _ in blocking_statuses)
    with connect(path) as conn:
        rows = conn.execute(
            f"SELECT canonical_url FROM opportunities WHERE status IN ({placeholders})",
            blocking_statuses,
        ).fetchall()
    return {str(row["canonical_url"]) for row in rows}


def normalize_feedback(value: str) -> str:
    normalized = str(value or "").strip().casefold()
    aliases = {
        "fit": "uygun",
        "uygun": "uygun",
        "relevant": "uygun",
        "irrelevant": "alakasız",
        "alakasiz": "alakasız",
        "alakasız": "alakasız",
        "applied": "basvurdum",
        "başvurdum": "basvurdum",
        "basvurdum": "basvurdum",
    }
    feedback = aliases.get(normalized)
    if feedback not in VALID_FEEDBACK:
        raise ValueError("feedback must be one of: uygun, alakasız, basvurdum")
    return feedback


def record_feedback(
    url: str,
    feedback: str,
    *,
    note: str = "",
    path: str | Path | None = None,
) -> str:
    init_database(path)
    clean = clean_url(url)
    canonical_url = canonicalize_url(clean)
    if not canonical_url:
        raise ValueError("A valid http/https URL is required for feedback.")

    normalized_feedback = normalize_feedback(feedback)
    timestamp = utc_now_iso()
    status = FEEDBACK_STATUS[normalized_feedback]

    with connect(path) as conn:
        conn.execute(
            """
            INSERT INTO opportunities (
                canonical_url, url, first_seen_at, last_seen_at, status
            )
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(canonical_url) DO UPDATE SET
                last_seen_at = excluded.last_seen_at,
                status = excluded.status
            """,
            (canonical_url, clean or canonical_url, timestamp, timestamp, status),
        )
        conn.execute(
            """
            INSERT INTO feedback(canonical_url, feedback, note, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (canonical_url, normalized_feedback, str(note or ""), timestamp),
        )

    logger.info("Kullanici geri bildirimi kaydedildi. canonical_url=%s feedback=%s", canonical_url, normalized_feedback)
    return canonical_url


def load_feedback_index(path: str | Path | None = None) -> dict[str, str]:
    init_database(path)
    feedback_by_url: dict[str, str] = {}
    with connect(path) as conn:
        rows = conn.execute(
            """
            SELECT canonical_url, feedback
            FROM feedback
            ORDER BY created_at ASC, id ASC
            """
        ).fetchall()
    for row in rows:
        feedback_by_url[str(row["canonical_url"])] = str(row["feedback"])
    return feedback_by_url


def _feedback_terms(text: str) -> set[str]:
    terms = set()
    for raw_term in re.findall(r"[a-zA-ZçğıöşüÇĞİÖŞÜ0-9+#.]{3,}", str(text or "").casefold()):
        term = raw_term.strip(".")
        if term and term not in FEEDBACK_STOPWORDS and not term.isdigit():
            terms.add(term)
    return terms


def load_feedback_keyword_weights(path: str | Path | None = None) -> dict[str, int]:
    init_database(path)
    weights: dict[str, int] = {}
    feedback_deltas = {"uygun": 2, "basvurdum": 1, "alakasız": -4}

    with connect(path) as conn:
        rows = conn.execute(
            """
            SELECT f.feedback, o.title, o.company, o.category, o.metadata_json
            FROM feedback f
            LEFT JOIN opportunities o ON o.canonical_url = f.canonical_url
            ORDER BY f.created_at ASC, f.id ASC
            """
        ).fetchall()

    for row in rows:
        try:
            metadata = json.loads(row["metadata_json"] or "{}")
        except json.JSONDecodeError:
            metadata = {}

        tags = metadata.get("tags") or []
        text = " ".join(
            [
                str(row["title"] or ""),
                str(row["company"] or ""),
                str(row["category"] or ""),
                " ".join(str(tag) for tag in tags),
            ]
        )
        delta = feedback_deltas.get(str(row["feedback"]), 0)
        for term in _feedback_terms(text):
            weights[term] = max(-12, min(8, weights.get(term, 0) + delta))

    return dict(sorted((term, weight) for term, weight in weights.items() if weight))


def record_run_summary(summary: dict[str, Any], *, path: str | Path | None = None) -> None:
    init_database(path)
    run_id = str(summary.get("run_id") or utc_now_iso())
    started_at = str(summary.get("started_at") or utc_now_iso())
    finished_at = str(summary.get("finished_at") or utc_now_iso())
    source_counts = dict(summary.get("source_counts") or {})
    source_errors = dict(summary.get("source_errors") or {})
    alerts = list(summary.get("alerts") or [])

    with connect(path) as conn:
        conn.execute(
            """
            INSERT INTO run_summaries (
                run_id, started_at, finished_at, total_collected, matched_count,
                duplicate_count, invalid_url_count, email_sent, dashboard_updated,
                memory_added_count, source_counts_json, source_errors_json, alerts_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(run_id) DO UPDATE SET
                finished_at = excluded.finished_at,
                total_collected = excluded.total_collected,
                matched_count = excluded.matched_count,
                duplicate_count = excluded.duplicate_count,
                invalid_url_count = excluded.invalid_url_count,
                email_sent = excluded.email_sent,
                dashboard_updated = excluded.dashboard_updated,
                memory_added_count = excluded.memory_added_count,
                source_counts_json = excluded.source_counts_json,
                source_errors_json = excluded.source_errors_json,
                alerts_json = excluded.alerts_json
            """,
            (
                run_id,
                started_at,
                finished_at,
                int(summary.get("total_collected") or 0),
                int(summary.get("matched_count") or 0),
                int(summary.get("duplicate_count") or 0),
                int(summary.get("invalid_url_count") or 0),
                1 if summary.get("email_sent") else 0,
                1 if summary.get("dashboard_updated") else 0,
                int(summary.get("memory_added_count") or 0),
                _json_dump(source_counts),
                _json_dump(source_errors),
                json.dumps(alerts, ensure_ascii=False),
            ),
        )

        source_rows = []
        for source in sorted(set(source_counts) | set(source_errors)):
            source_rows.append(
                (
                    run_id,
                    source,
                    int(source_counts.get(source) or 0),
                    int(source_errors.get(source) or 0),
                    finished_at,
                )
            )
        conn.executemany(
            """
            INSERT INTO source_runs(run_id, source, collected_count, error_count, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            source_rows,
        )

    logger.info("Run ozeti SQLite veritabanina kaydedildi. run_id=%s", run_id)
