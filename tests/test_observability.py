from services.observability import build_run_summary, detect_source_alerts, summarize_sources, write_daily_summary


def test_observability_summarizes_sources_and_alerts(tmp_path):
    counts = summarize_sources(
        [
            {"source": "Remotive Global API"},
            {"source": "Remotive Global API"},
            {"source": "Dev.to API"},
        ]
    )

    alerts = detect_source_alerts(counts)

    assert counts["Remotive Global API"] == 2
    assert any("Arbeitnow API" in alert for alert in alerts)

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
    )
    path = tmp_path / "RUN_SUMMARY.md"

    assert write_daily_summary(summary, path) is True
    assert "Remotive Global API" in path.read_text(encoding="utf-8")
