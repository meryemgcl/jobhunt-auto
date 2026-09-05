import main as jobhunt_main


def test_main_returns_false_and_preserves_memory_when_email_fails(monkeypatch):
    memory_updates = []

    monkeypatch.setattr(
        jobhunt_main,
        "get_mock_profile",
        lambda: {"core_skills": ["Python"], "name": "Meryem Guclu"},
    )
    monkeypatch.setattr(jobhunt_main, "load_seen_canonical_urls", lambda: set())
    monkeypatch.setattr(jobhunt_main, "load_seen_jobs", lambda: [])
    monkeypatch.setattr(
        jobhunt_main,
        "fetch_jobs",
        lambda: [
            {
                "title": "Junior Python Developer",
                "company": "Example",
                "url": "https://example.com/job",
                "location": "Remote",
                "tags": ["Python"],
                "description": "Python intern role",
                "published_at": "2026-09-05",
                "source": "Test",
            }
        ],
    )
    monkeypatch.setattr(jobhunt_main, "fetch_good_first_issues", lambda: [])
    monkeypatch.setattr(jobhunt_main, "fetch_bootcamps_and_camps", lambda: [])
    monkeypatch.setattr(jobhunt_main, "fetch_r_and_d_projects", lambda: [])
    monkeypatch.setattr(jobhunt_main, "fetch_podcasts", lambda: [])
    monkeypatch.setattr(jobhunt_main, "fetch_hackathons", lambda: [])
    monkeypatch.setattr(jobhunt_main, "fetch_tech_news", lambda: [])
    monkeypatch.setattr(
        jobhunt_main,
        "analyze_market_skill_gap",
        lambda jobs, skills: {"summary_text": "", "top_market_demands": []},
    )
    monkeypatch.setattr(jobhunt_main, "init_database", lambda: None)
    monkeypatch.setattr(jobhunt_main, "load_seen_canonical_urls_from_db", lambda: set())
    monkeypatch.setattr(jobhunt_main, "load_feedback_index", lambda: {})
    monkeypatch.setattr(jobhunt_main, "upsert_opportunities", lambda opportunities, status="seen": len(opportunities))
    monkeypatch.setattr(jobhunt_main, "record_score_history", lambda opportunities, run_id=None: len(opportunities))
    monkeypatch.setattr(jobhunt_main, "record_run_summary", lambda summary: None)
    monkeypatch.setattr(jobhunt_main, "write_daily_summary", lambda summary: True)
    monkeypatch.setattr(jobhunt_main, "update_career_dashboard", lambda total, matched, gap: None)
    monkeypatch.setattr(jobhunt_main, "build_html_newsletter", lambda **kwargs: "<html></html>")
    monkeypatch.setattr(jobhunt_main, "send_email_newsletter", lambda html, total: False)
    monkeypatch.setattr(jobhunt_main, "add_seen_jobs", lambda urls: memory_updates.extend(urls))

    assert jobhunt_main.main() is False
    assert memory_updates == []
