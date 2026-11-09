import main as jobhunt_main


def test_main_dry_run_writes_preview_without_changing_state(monkeypatch, tmp_path):
    calls = []
    preview_path = tmp_path / "newsletter.html"
    monkeypatch.setenv("JOBHUNT_PREVIEW_PATH", str(preview_path))
    monkeypatch.setattr(
        jobhunt_main,
        "get_profile",
        lambda: {"core_skills": ["Python"], "name": "Test Candidate"},
    )
    monkeypatch.setattr(jobhunt_main, "load_seen_canonical_urls", lambda: set())
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
                "description": "Python junior role",
                "published_at": "2026-10-19",
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
    monkeypatch.setattr(
        jobhunt_main,
        "build_html_newsletter",
        lambda **kwargs: calls.append(("preview", kwargs["matched_jobs"])) or "<html>preview</html>",
    )
    for function_name in (
        "init_database",
        "load_seen_canonical_urls_from_db",
        "load_feedback_index",
        "load_feedback_keyword_weights",
        "enqueue_email_outbox",
        "load_pending_email_outbox",
        "record_email_outbox_attempt",
        "upsert_opportunities",
        "record_score_history",
        "record_run_summary",
        "write_daily_summary",
        "update_career_dashboard",
        "send_email_newsletter",
        "add_seen_jobs",
    ):
        monkeypatch.setattr(
            jobhunt_main,
            function_name,
            lambda *args, _name=function_name, **kwargs: (_ for _ in ()).throw(
                AssertionError(f"{_name} must not run in preview mode")
            ),
        )

    assert jobhunt_main.main(dry_run=True) is True
    assert preview_path.read_text(encoding="utf-8") == "<html>preview</html>"
    assert calls[0][0] == "preview"
    assert calls[0][1][0]["title"] == "Junior Python Developer"


def test_main_returns_false_and_preserves_memory_when_email_fails(monkeypatch):
    memory_updates = []
    operation_order = []

    monkeypatch.setattr(
        jobhunt_main,
        "get_profile",
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
    monkeypatch.setattr(jobhunt_main, "load_pending_email_outbox", lambda limit=1: [])
    monkeypatch.setattr(jobhunt_main, "load_feedback_index", lambda: {})
    monkeypatch.setattr(jobhunt_main, "upsert_opportunities", lambda opportunities, status="seen": len(opportunities))
    monkeypatch.setattr(jobhunt_main, "record_score_history", lambda opportunities, run_id=None: len(opportunities))
    monkeypatch.setattr(jobhunt_main, "record_run_summary", lambda summary: None)
    monkeypatch.setattr(jobhunt_main, "write_daily_summary", lambda summary: True)
    monkeypatch.setattr(jobhunt_main, "update_career_dashboard", lambda total, matched, gap: None)
    monkeypatch.setattr(jobhunt_main, "build_html_newsletter", lambda **kwargs: "<html></html>")
    pending_batches = []

    def queue_newsletter(outbox_id, html_content, total_job_count, opportunities):
        operation_order.append("queue")
        pending_batches.append(
            {
                "id": outbox_id,
                "html_content": html_content,
                "total_job_count": total_job_count,
            }
        )
        return True

    monkeypatch.setattr(jobhunt_main, "enqueue_email_outbox", queue_newsletter)
    monkeypatch.setattr(jobhunt_main, "load_pending_email_outbox", lambda limit=1: pending_batches[:limit])
    monkeypatch.setattr(
        jobhunt_main,
        "record_email_outbox_attempt",
        lambda outbox_id, success, error="", **kwargs: operation_order.append(
            "outbox-sent" if success else "outbox-pending"
        ) or True,
    )
    monkeypatch.setattr(
        jobhunt_main,
        "add_seen_jobs",
        lambda jobs: (memory_updates.extend(jobs), operation_order.append("persist"), len(jobs))[2],
    )
    monkeypatch.setattr(
        jobhunt_main,
        "send_email_newsletter",
        lambda html, total, **kwargs: (operation_order.append("email"), False)[1],
    )

    assert jobhunt_main.main() is False
    assert len(memory_updates) == 1
    assert memory_updates[0]["canonical_url"] == "https://example.com/job"
    assert operation_order == ["queue", "persist", "email", "outbox-pending"]

    operation_order.clear()
    assert jobhunt_main.main() is False
    assert operation_order == ["email", "outbox-pending"]
    assert len(memory_updates) == 1
    assert len(pending_batches) == 1

    operation_order.clear()
    monkeypatch.setattr(
        jobhunt_main,
        "record_email_outbox_attempt",
        lambda outbox_id, success, error="", **kwargs: (
            operation_order.append("outbox-state-rejected"),
            False,
        )[1],
    )
    monkeypatch.setattr(
        jobhunt_main,
        "send_email_newsletter",
        lambda html, total, **kwargs: (operation_order.append("email"), True)[1],
    )
    assert jobhunt_main.main() is False
    assert operation_order == ["email", "outbox-state-rejected"]
    assert len(memory_updates) == 1

    pending_batches.clear()
    operation_order.clear()
    monkeypatch.setattr(
        jobhunt_main,
        "enqueue_email_outbox",
        lambda *args, **kwargs: (operation_order.append("queue-rejected"), False)[1],
    )
    assert jobhunt_main.main() is False
    assert operation_order == ["queue-rejected"]
    assert len(memory_updates) == 1
