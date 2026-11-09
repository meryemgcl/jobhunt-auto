#!/usr/bin/env python3
"""One-time migration of a local JobHunt SQLite database to PostgreSQL."""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.database import _opportunity_row, connect, init_database, utc_now_iso
from services.url_utils import canonicalize_url, clean_url


STATE_TABLES = ("opportunities", "score_history", "feedback", "run_summaries", "source_runs")


def _read_rows(connection: sqlite3.Connection, table: str) -> list[dict[str, Any]]:
    tables = {
        row["name"]
        for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
    }
    if table not in tables:
        return []
    return [dict(row) for row in connection.execute(f"SELECT * FROM {table}")]


def _prepare_opportunities(
    source_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, str], int, int]:
    records_by_url: dict[str, dict[str, Any]] = {}
    canonical_urls: dict[str, str] = {}
    invalid_count = 0

    for row in source_rows:
        url = clean_url(row.get("url") or row.get("canonical_url"))
        canonical_url = canonicalize_url(url)
        if not canonical_url:
            invalid_count += 1
            continue
        canonical_urls[str(row.get("canonical_url") or canonical_url)] = canonical_url
        try:
            metadata = json.loads(row.get("metadata_json") or "{}")
        except json.JSONDecodeError as exc:
            raise ValueError("SQLite opportunities contain invalid metadata JSON.") from exc
        record = {
            "url": url,
            "canonical_url": canonical_url,
            "title": row.get("title") or "",
            "company": row.get("company") or "",
            "source": row.get("source") or "",
            "category": row.get("category") or "job",
            "first_seen_at": row.get("first_seen_at") or utc_now_iso(),
            "last_seen_at": row.get("last_seen_at") or utc_now_iso(),
            "score": row.get("latest_score"),
            "match_reason": row.get("latest_match_reason") or "",
            "source_reliability": row.get("source_reliability", 70),
            "freshness_score": row.get("freshness_score", 50),
            "status": row.get("status") or "seen",
            "metadata": metadata,
        }
        existing = records_by_url.get(canonical_url)
        if existing is None:
            records_by_url[canonical_url] = record
            continue

        first_seen_at = min(existing["first_seen_at"], record["first_seen_at"])
        last_seen_at = max(existing["last_seen_at"], record["last_seen_at"])
        if record["last_seen_at"] >= existing["last_seen_at"]:
            existing.update(record)
        existing["first_seen_at"] = first_seen_at
        existing["last_seen_at"] = last_seen_at

    records = [records_by_url[url] for url in sorted(records_by_url)]
    duplicate_count = len(source_rows) - invalid_count - len(records)
    return records, canonical_urls, invalid_count, duplicate_count


def _assert_empty_target(connection) -> None:
    for table in STATE_TABLES:
        count = connection.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()["count"]
        if count:
            raise RuntimeError(
                f"PostgreSQL table {table} is not empty; migrate before the first production run."
            )


def migrate(source_path: Path, *, apply: bool) -> dict[str, int]:
    if not source_path.is_file():
        raise FileNotFoundError(f"SQLite database not found: {source_path}")

    with sqlite3.connect(source_path) as source:
        source.row_factory = sqlite3.Row
        source_data = {table: _read_rows(source, table) for table in STATE_TABLES}

    opportunity_rows, canonical_map, invalid_count, duplicate_count = _prepare_opportunities(
        source_data["opportunities"]
    )
    counts = {table: len(rows) for table, rows in source_data.items()}
    counts["invalid_opportunities"] = invalid_count
    counts["canonical_duplicates"] = duplicate_count
    if not apply:
        return counts

    if not os.getenv("DATABASE_URL"):
        raise ValueError("Set DATABASE_URL to the empty managed PostgreSQL database before applying.")

    init_database()
    now = utc_now_iso()
    with connect() as target:
        _assert_empty_target(target)
        opportunity_values = [
            _opportunity_row(record, str(record["status"]), now)
            for record in opportunity_rows
        ]
        target.executemany(
            """
            INSERT INTO opportunities (
                canonical_url, url, title, company, source, category,
                first_seen_at, last_seen_at, latest_score, latest_match_reason,
                source_reliability, freshness_score, status, metadata_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(canonical_url) DO NOTHING
            """,
            opportunity_values,
        )

        score_values = [
            (
                row["id"],
                canonical_map.get(str(row["canonical_url"])),
                row["score"],
                row.get("reason") or "",
                row["observed_at"],
                row.get("run_id"),
            )
            for row in source_data["score_history"]
            if canonical_map.get(str(row["canonical_url"]))
        ]
        target.executemany(
            """
            INSERT INTO score_history(id, canonical_url, score, reason, observed_at, run_id)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO NOTHING
            """,
            score_values,
        )

        feedback_values = [
            (
                row["id"],
                canonical_map.get(str(row["canonical_url"])),
                row["feedback"],
                row.get("note") or "",
                row["created_at"],
            )
            for row in source_data["feedback"]
            if canonical_map.get(str(row["canonical_url"]))
        ]
        target.executemany(
            """
            INSERT INTO feedback(id, canonical_url, feedback, note, created_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id) DO NOTHING
            """,
            feedback_values,
        )

        run_values = [
            (
                row["run_id"],
                row["started_at"],
                row["finished_at"],
                row.get("total_collected", 0),
                row.get("matched_count", 0),
                row.get("duplicate_count", 0),
                row.get("invalid_url_count", 0),
                row.get("email_sent", 0),
                row.get("dashboard_updated", 0),
                row.get("memory_added_count", 0),
                row.get("source_counts_json") or "{}",
                row.get("source_errors_json") or "{}",
                row.get("alerts_json") or "[]",
            )
            for row in source_data["run_summaries"]
        ]
        target.executemany(
            """
            INSERT INTO run_summaries (
                run_id, started_at, finished_at, total_collected, matched_count,
                duplicate_count, invalid_url_count, email_sent, dashboard_updated,
                memory_added_count, source_counts_json, source_errors_json, alerts_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(run_id) DO NOTHING
            """,
            run_values,
        )

        source_run_values = [
            (
                row["id"],
                row["run_id"],
                row["source"],
                row.get("collected_count", 0),
                row.get("error_count", 0),
                row["created_at"],
            )
            for row in source_data["source_runs"]
        ]
        target.executemany(
            """
            INSERT INTO source_runs(id, run_id, source, collected_count, error_count, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO NOTHING
            """,
            source_run_values,
        )

        for table in ("score_history", "feedback", "source_runs"):
            target.execute(
                f"""
                SELECT setval(
                    pg_get_serial_sequence('{table}', 'id'),
                    COALESCE((SELECT MAX(id) FROM {table}), 1),
                    EXISTS(SELECT 1 FROM {table})
                )
                """
            )

    return counts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path(os.getenv("JOBHUNT_DB_PATH", "jobhunt.db")))
    parser.add_argument("--apply", action="store_true", help="Write data to the empty PostgreSQL target.")
    args = parser.parse_args()
    load_dotenv()

    try:
        counts = migrate(args.source, apply=args.apply)
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        parser.error(str(exc))

    print(json.dumps({"applied": args.apply, "rows": counts}, indent=2))
    if not args.apply:
        print("Dry run only. Add --apply to migrate into an empty PostgreSQL database.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
