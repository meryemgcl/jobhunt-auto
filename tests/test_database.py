import sqlite3

from services.database import (
    init_database,
    load_feedback_index,
    load_feedback_keyword_weights,
    load_seen_canonical_urls_from_db,
    record_feedback,
    record_run_summary,
    record_score_history,
    upsert_opportunities,
)


def test_database_tracks_opportunities_scores_and_feedback(tmp_path):
    db_path = tmp_path / "jobhunt.db"
    job = {
        "title": "Junior Python Developer",
        "company": "Example",
        "url": "https://example.com/job?utm_source=test",
        "source": "Test Source",
        "category": "job",
        "score": 74,
        "match_reason": "Teknoloji Eşleşmesi: PYTHON",
        "source_reliability": 91,
        "freshness_score": 100,
    }

    init_database(db_path)
    assert upsert_opportunities([job], path=db_path) == 1
    assert record_score_history([job], run_id="run-1", path=db_path) == 1
    assert record_feedback("https://example.com/job", "uygun", path=db_path) == "https://example.com/job"

    assert load_feedback_index(db_path) == {"https://example.com/job": "uygun"}
    assert load_seen_canonical_urls_from_db(db_path) == {"https://example.com/job"}
    assert load_feedback_keyword_weights(db_path)["python"] > 0

    with sqlite3.connect(db_path) as conn:
        opportunity_count = conn.execute("SELECT COUNT(*) FROM opportunities").fetchone()[0]
        score_count = conn.execute("SELECT COUNT(*) FROM score_history").fetchone()[0]

    assert opportunity_count == 1
    assert score_count == 1


def test_record_run_summary_persists_source_counts(tmp_path):
    db_path = tmp_path / "jobhunt.db"

    record_run_summary(
        {
            "run_id": "run-2",
            "started_at": "2026-09-05T09:00:00+00:00",
            "finished_at": "2026-09-05T09:01:00+00:00",
            "total_collected": 3,
            "matched_count": 1,
            "source_counts": {"Remotive Global API": 2},
            "source_errors": {"Arbeitnow API": 1},
            "alerts": ["Arbeitnow API: bu çalıştırmada 0 kayıt döndü"],
        },
        path=db_path,
    )

    with sqlite3.connect(db_path) as conn:
        total_collected = conn.execute("SELECT total_collected FROM run_summaries WHERE run_id='run-2'").fetchone()[0]
        source_runs = conn.execute("SELECT COUNT(*) FROM source_runs WHERE run_id='run-2'").fetchone()[0]

    assert total_collected == 3
    assert source_runs == 2
