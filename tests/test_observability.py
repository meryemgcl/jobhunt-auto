from services.observability import (
    build_run_summary,
    detect_source_alerts,
    summarize_job_quality,
    summarize_sources,
    write_daily_summary,
)


def test_observability_summarizes_sources_and_alerts(tmp_path):
    counts = summarize_sources(
        [
            {"source": "Remotive Global API"},
            {"source": "Remotive Global API"},
            {"source": "Dev.to API"},
        ]
    )

    alerts = detect_source_alerts(counts, source_errors={"Arbeitnow API": 1})

    assert counts["Remotive Global API"] == 2
    assert any("Arbeitnow API" in alert for alert in alerts)
    assert detect_source_alerts(counts) == []

    summary = build_run_summary(
        run_id="run-1",
        started_at="2026-09-05T09:00:00+00:00",
        total_collected=3,
        matched_count=1,
        duplicate_count=0,
        invalid_url_count=0,
        email_sent=True,
        dashboard_updated=True,
        memory_added_count=1,
        source_counts=counts,
        source_errors={"Arbeitnow API": 1},
    )
    path = tmp_path / "RUN_SUMMARY.md"

    assert write_daily_summary(summary, path) is True
    assert "Remotive Global API" in path.read_text(encoding="utf-8")


def test_job_source_quality_tracks_companies_matches_dates_and_application_links():
    quality = summarize_job_quality(
        [
            {
                "source": "Lever",
                "company": "Trendyol",
                "canonical_url": "https://jobs.example/1",
                "published_at": "2026-10-19",
                "metadata": {"application_url": "https://jobs.example/1/apply"},
            },
            {
                "source": "Lever",
                "company": "Trendyol",
                "canonical_url": "https://jobs.example/2",
                "published_at": "",
                "metadata": {},
            },
            {
                "source": "Lever",
                "company": "iyzico",
                "canonical_url": "https://jobs.example/3",
                "published_at": "2026-10-18",
                "metadata": {"application_url": "https://jobs.example/3/apply"},
            },
        ],
        matched_urls={"https://jobs.example/1", "https://jobs.example/3"},
    )

    assert quality["Lever"] == {
        "jobs": 3,
        "matched": 2,
        "companies": 2,
        "dated": 2,
        "application_links": 2,
        "locations": 0,
    }
