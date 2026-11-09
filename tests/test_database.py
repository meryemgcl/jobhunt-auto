import sqlite3

from services.database import (
    init_database,
    enqueue_email_outbox,
    load_pending_email_outbox,
    load_feedback_index,
    load_feedback_keyword_weights,
    load_seen_canonical_urls_from_db,
    record_feedback,
    record_run_summary,
    record_email_outbox_attempt,
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
        error_count = conn.execute(
            "SELECT error_count FROM source_runs WHERE run_id='run-2' AND source='Arbeitnow API'"
        ).fetchone()[0]

    assert total_collected == 3
    assert source_runs == 2
    assert error_count == 1


def test_seen_opportunities_are_blocked_and_legacy_hash_is_not_identity(tmp_path):
    db_path = tmp_path / "jobhunt.db"
    job = {
        "title": "Junior Python Developer",
        "url": "https://example.com/job?utm_source=mail",
        "canonical_url": "legacy-content-hash",
    }

    assert upsert_opportunities([job], status="seen", path=db_path) == 1
    assert load_seen_canonical_urls_from_db(db_path) == {"https://example.com/job"}


def test_email_outbox_retries_failed_delivery_and_marks_batch_sent(tmp_path):
    db_path = tmp_path / "outbox.db"
    job = {
        "title": "Junior Python Engineer",
        "url": "https://example.com/job?utm_source=mail",
        "category": "job",
    }
    upsert_opportunities([job], status="seen", path=db_path)

    assert enqueue_email_outbox(
        "run-outbox",
        "<html>saved newsletter</html>",
        1,
        [job],
        path=db_path,
    )
    [pending] = load_pending_email_outbox(path=db_path)
    assert pending["id"] == "run-outbox"
    assert pending["canonical_urls"] == ["https://example.com/job"]

    assert record_email_outbox_attempt(
        "run-outbox",
        success=False,
        error="SMTP unavailable",
        path=db_path,
    )
    [retry] = load_pending_email_outbox(path=db_path)
    assert retry["attempt_count"] == 1
    assert retry["last_error"] == "SMTP unavailable"

    assert record_email_outbox_attempt("run-outbox", success=True, path=db_path)
    assert load_pending_email_outbox(path=db_path) == []
    with sqlite3.connect(db_path) as conn:
        status = conn.execute(
            "SELECT status FROM opportunities WHERE canonical_url='https://example.com/job'"
        ).fetchone()[0]
        outbox_status = conn.execute(
            "SELECT status FROM email_outbox WHERE id='run-outbox'"
        ).fetchone()[0]
    assert status == "sent"
    assert outbox_status == "sent"


def test_run_summary_persists_source_quality_metrics(tmp_path):
    db_path = tmp_path / "quality.db"

    record_run_summary(
        {
            "run_id": "quality-run",
            "started_at": "2026-10-20T09:00:00+00:00",
            "job_source_quality": {
                "Lever Career Pages": {
                    "jobs": 8,
                    "companies": 4,
                    "dated": 8,
                    "application_links": 8,
                    "locations": 7,
                }
            },
        },
        path=db_path,
    )

    with sqlite3.connect(db_path) as conn:
        quality_json = conn.execute(
            "SELECT job_source_quality_json FROM run_summaries WHERE run_id='quality-run'"
        ).fetchone()[0]
    assert '"companies": 4' in quality_json
