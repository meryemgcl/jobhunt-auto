import sqlite3

from scripts.migrate_sqlite_to_postgres import _prepare_opportunities, migrate


def test_sqlite_migration_dry_run_counts_rows_without_connecting_to_postgres(tmp_path):
    database = tmp_path / "source.db"
    with sqlite3.connect(database) as connection:
        connection.execute(
            """
            CREATE TABLE opportunities (
                canonical_url TEXT PRIMARY KEY,
                url TEXT NOT NULL,
                title TEXT NOT NULL,
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
            )
            """
        )
        connection.execute(
            """
            INSERT INTO opportunities (
                canonical_url, url, title, first_seen_at, last_seen_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                "legacy-hash",
                "https://example.com/job?utm_source=mail",
                "Junior Python Developer",
                "2026-10-01T00:00:00+00:00",
                "2026-10-02T00:00:00+00:00",
            ),
        )

    counts = migrate(database, apply=False)

    assert counts["opportunities"] == 1
    assert counts["invalid_opportunities"] == 0


def test_migration_normalizes_legacy_content_hash_keys():
    records, canonical_map, invalid_count, duplicate_count = _prepare_opportunities(
        [
            {
                "canonical_url": "legacy-content-hash",
                "url": "https://example.com/job?utm_source=mail",
                "title": "Junior Python Developer",
                "metadata_json": "{}",
            }
        ]
    )

    assert records[0]["canonical_url"] == "https://example.com/job"
    assert canonical_map["legacy-content-hash"] == "https://example.com/job"
    assert invalid_count == 0
    assert duplicate_count == 0
